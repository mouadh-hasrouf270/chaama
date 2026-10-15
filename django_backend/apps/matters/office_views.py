from pathlib import Path
from uuid import uuid4
from django.db import transaction, IntegrityError, OperationalError, connection
from django.db.models import F
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, mixins, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Client, Matter, MatterHistory, MatterDocument, Invoice, InvoicePayment
from .office_access import OfficeAccess, is_admin, visible_matters, visible_clients
from .office_serializers import (ClientSerializer, MatterSerializer, DocumentSerializer,
                                 HistorySerializer, InvoiceSerializer, PaymentSerializer)


class Conflict(APIException):
    status_code = 409
    default_detail = 'Les données ont changé. Actualisez puis réessayez.'


def version_of(request):
    return serializers.IntegerField(min_value=1).run_validation(request.data.get('version'))


def claim(model, pk, version):
    if not model.objects.filter(pk=pk, version=version).update(version=F('version') + 1):
        raise Conflict()
    return model.objects.get(pk=pk)


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseOfficeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [OfficeAccess]
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def handle_exception(self, exc):
        # SQLite can reject concurrent writes immediately (especially its shared
        # test database). The atomic block has rolled back; return a retryable
        # conflict rather than reporting success or leaking a server traceback.
        if isinstance(exc, OperationalError) and connection.vendor == 'sqlite' and 'locked' in str(exc).lower():
            exc = Conflict('Une autre opération est en cours. Actualisez et réessayez.')
        return super().handle_exception(exc)


class ClientViewSet(BaseOfficeViewSet):
    serializer_class = ClientSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'phone', 'email']

    def get_queryset(self):
        return visible_clients(self.request.user)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(created_by=self.request.user)
        except IntegrityError:
            raise Conflict('Ce numéro est déjà associé à un client.')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance = claim(Client, instance.pk, version_of(request))
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            try:
                with transaction.atomic():
                    serializer.save()
            except IntegrityError:
                raise Conflict('Ce numéro est déjà associé à un client.')
        return Response(serializer.data)


TRANSITIONS = {'OPEN': ['ACTIVE', 'WAITING', 'CLOSED'], 'ACTIVE': ['WAITING', 'CLOSED'],
               'WAITING': ['ACTIVE', 'CLOSED'], 'CLOSED': ['ACTIVE', 'ARCHIVED'], 'ARCHIVED': []}


class MatterViewSet(BaseOfficeViewSet):
    serializer_class = MatterSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'reference', 'client_profile__first_name', 'client_profile__last_name']

    def get_queryset(self):
        qs = visible_matters(self.request.user).order_by('-created_at', '-pk')
        if self.request.query_params.get('client'):
            client_id = serializers.IntegerField(min_value=1).run_validation(self.request.query_params['client'])
            qs = qs.filter(client_profile_id=client_id)
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            obj = serializer.save(reference='DOS-' + uuid4().hex[:16].upper(),
                                  created_by=self.request.user, opened_at=timezone.localdate())
            MatterHistory.objects.create(matter=obj, actor=self.request.user, message='Dossier créé')

    def update(self, request, *args, **kwargs):
        original = self.get_object()
        if any(key in request.data for key in ['status', 'closed_at', 'opened_at']):
            raise serializers.ValidationError('Utilisez l’action de changement de statut.')
        with transaction.atomic():
            instance = claim(Matter, original.pk, version_of(request))
            if instance.status in ['CLOSED', 'ARCHIVED']:
                raise Conflict('Rouvrez le dossier avant de le modifier.')
            if 'client_profile' in request.data and str(request.data['client_profile']) != str(instance.client_profile_id):
                raise serializers.ValidationError('Le client d’un dossier existant ne peut pas être remplacé.')
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            MatterHistory.objects.create(matter=instance, actor=request.user, message='Informations du dossier modifiées')
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='status')
    def change_status(self, request, pk=None):
        original = self.get_object()
        target = serializers.ChoiceField(choices=Matter.Status.choices).run_validation(request.data.get('status'))
        with transaction.atomic():
            obj = claim(Matter, original.pk, version_of(request))
            if target not in TRANSITIONS[obj.status]:
                raise Conflict('Transition de statut non autorisée.')
            if target == 'ARCHIVED' and obj.invoices.exclude(status__in=['PAID', 'CANCELLED']).exists():
                raise Conflict('Réglez ou annulez les factures avant d’archiver le dossier.')
            previous = obj.status
            obj.status = target
            obj.closed_at = timezone.localdate() if target in ['CLOSED', 'ARCHIVED'] else None
            obj.save()
            MatterHistory.objects.create(matter=obj, actor=request.user, message=f'Statut : {previous} → {target}')
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        return Response(HistorySerializer(self.get_object().history.select_related('actor'), many=True).data)

    @action(detail=True, methods=['get', 'post'])
    def documents(self, request, pk=None):
        matter = self.get_object()
        if request.method == 'GET':
            return Response(DocumentSerializer(matter.documents.all(), many=True).data)
        upload = request.FILES.get('file')
        if not upload or not 0 < upload.size <= 10 * 1024 * 1024:
            raise serializers.ValidationError({'file': 'Choisissez un fichier non vide de 10 Mo maximum.'})
        name = Path(upload.name.replace('\\', '/')).name
        if len(name) > 255:
            raise serializers.ValidationError({'file': 'Nom de fichier trop long.'})
        extension = Path(name).suffix.lower()
        signatures = {'.pdf': (b'%PDF-', 'application/pdf'), '.png': (b'\x89PNG\r\n\x1a\n', 'image/png'),
                      '.jpg': (b'\xff\xd8\xff', 'image/jpeg'), '.jpeg': (b'\xff\xd8\xff', 'image/jpeg')}
        header = upload.read(16)
        upload.seek(0)
        if extension not in signatures or not header.startswith(signatures[extension][0]):
            raise serializers.ValidationError({'file': 'Formats autorisés : PDF, PNG, JPG. Le contenu doit correspondre au format.'})
        document = None
        try:
            with transaction.atomic():
                matter = claim(Matter, matter.pk, version_of(request))
                if matter.status in ['CLOSED', 'ARCHIVED']:
                    raise Conflict('Rouvrez le dossier avant d’ajouter un document.')
                document = MatterDocument.objects.create(matter=matter, file=upload, original_name=name,
                    size=upload.size, content_type=signatures[extension][1], uploaded_by=request.user)
                MatterHistory.objects.create(matter=matter, actor=request.user, message=f'Document ajouté : {name}'[:255])
        except Exception:
            if document and document.file:
                document.file.delete(save=False)
            raise
        return Response(DocumentSerializer(document).data, status=201)

    @action(detail=True, methods=['get'], url_path=r'documents/(?P<document_id>\d+)/content')
    def document_content(self, request, pk=None, document_id=None):
        from django.shortcuts import get_object_or_404
        document = get_object_or_404(self.get_object().documents, pk=document_id)
        try:
            stream = document.file.open('rb')
        except FileNotFoundError:
            raise Http404('Fichier introuvable.')
        response = FileResponse(stream, content_type=document.content_type, as_attachment=True, filename=document.original_name)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'
        return response


class InvoiceViewSet(BaseOfficeViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        qs = Invoice.objects.filter(matter__in=visible_matters(self.request.user)).select_related('matter__client_profile').prefetch_related('payments')
        if self.request.query_params.get('matter'):
            qs = qs.filter(matter_id=serializers.IntegerField(min_value=1).run_validation(self.request.query_params['matter']))
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            if not Matter.objects.filter(pk=serializer.validated_data['matter'].pk).exclude(status='ARCHIVED').update(version=F('version') + 1):
                raise Conflict('Le dossier est archivé.')
            serializer.save(reference='FAC-' + uuid4().hex[:16].upper(), created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        original = self.get_object()
        if any(key in request.data for key in ['status', 'paid_amount', 'total', 'issue_date']):
            raise serializers.ValidationError('Utilisez les actions de validation et de règlement.')
        with transaction.atomic():
            obj = claim(Invoice, original.pk, version_of(request))
            if obj.status != 'DRAFT':
                raise Conflict('Seule une facture brouillon est modifiable.')
            serializer = self.get_serializer(obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='status')
    def change_status(self, request, pk=None):
        if not is_admin(request.user):
            raise PermissionDenied('La validation et l’annulation des factures sont réservées à l’administrateur.')
        original = self.get_object()
        with transaction.atomic():
            obj = claim(Invoice, original.pk, version_of(request))
            target = request.data.get('status')
            if target == 'ISSUED' and obj.status == 'DRAFT':
                if obj.due_date < timezone.localdate():
                    raise serializers.ValidationError('Actualisez la date d’échéance avant émission.')
                obj.issue_date = timezone.localdate()
                client = obj.matter.client_profile
                if not client:
                    raise serializers.ValidationError('Le dossier doit être associé à un client.')
                obj.customer_name = str(client)
                obj.customer_address = ', '.join(filter(None, [client.address, client.city]))
            elif target == 'CANCELLED' and obj.status in ['DRAFT', 'ISSUED'] and obj.paid_amount == 0:
                pass
            else:
                raise Conflict('Transition interdite. Une facture réglée ne peut pas être annulée.')
            obj.status = target
            obj.save()
            MatterHistory.objects.create(matter=obj.matter, actor=request.user, message=f'Facture {obj.reference} : {target}')
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=['post'])
    def payments(self, request, pk=None):
        if not is_admin(request.user):
            raise PermissionDenied('L’enregistrement des règlements est réservé à l’administrateur.')
        original = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        duplicate = InvoicePayment.objects.filter(request_id=values['request_id']).first()
        if duplicate:
            if duplicate.invoice_id != original.pk or any(getattr(duplicate, key) != value for key, value in values.items()):
                raise Conflict('Cette référence de paiement a déjà été utilisée.')
            return Response(self.get_serializer(original).data)
        with transaction.atomic():
            # Claim first: serializes writes even on SQLite and rejects stale totals.
            obj = claim(Invoice, original.pk, version_of(request))
            if obj.status not in ['ISSUED', 'PARTIALLY_PAID']:
                raise Conflict('La facture doit être émise et non soldée.')
            if values['paid_on'] < obj.issue_date:
                raise serializers.ValidationError('Le règlement ne peut pas précéder l’émission.')
            if values['amount'] > obj.total - obj.paid_amount:
                raise serializers.ValidationError('Le règlement dépasse le solde restant.')
            try:
                with transaction.atomic():
                    serializer.save(invoice=obj, recorded_by=request.user)
            except IntegrityError:
                raise Conflict('Le règlement a déjà été enregistré. Actualisez la facture.')
            obj.paid_amount += values['amount']
            obj.status = 'PAID' if obj.paid_amount == obj.total else 'PARTIALLY_PAID'
            obj.save()
            MatterHistory.objects.create(matter=obj.matter, actor=request.user, message=f'Règlement {values["amount"]} DZD — {obj.reference}')
        return Response(self.get_serializer(obj).data, status=201)
