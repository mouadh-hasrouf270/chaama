from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.models import Client, LawyerProfile, User
from apps.accounts.permissions import is_admin
from apps.accounts.services import LAWYER_ROLES
from apps.activity.services import record_action
from apps.appointments.services import visible_clients
from .models import Matter, MatterDocument, MatterEvent, MatterNote, Invoice, InvoiceLine, Payment


class PracticeAccess:
    permission_classes = [IsAuthenticated]
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not (is_admin(request.user) or request.user.role in LAWYER_ROLES):
            raise PermissionDenied('Only authorized legal staff may access this section.')
    def scope(self):
        qs = Matter.objects.select_related('client', 'lead_lawyer')
        if is_admin(self.request.user):
            return qs
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            return qs.filter(lead_lawyer__user=self.request.user)
        return qs.filter(Q(created_by=self.request.user) | Q(lead_lawyer__user=self.request.user) | Q(client__created_by=self.request.user)).distinct()


class MatterSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    class Meta:
        model = Matter
        fields = ['id','reference','client','client_name','title','matter_type','description','opposing_party','jurisdiction','court_reference','status','opened_at','closed_at','lead_lawyer','created_at','updated_at']
        read_only_fields = ['id','reference','created_at','updated_at']
    def get_client_name(self, obj):
        return str(obj.client)
    def validate_client(self, client):
        if not visible_clients(self.context['request'].user).filter(pk=client.pk).exists():
            raise serializers.ValidationError('Client is not accessible.')
        return client
    def validate_lead_lawyer(self, lawyer):
        if lawyer and not is_admin(self.context['request'].user):
            raise serializers.ValidationError('Lawyer is not accessible.')
        return lawyer


class MatterViewSet(PracticeAccess, viewsets.ModelViewSet):
    """An assigned partner may work on a dossier, not create or reassign it."""
    def create(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Only the primary lawyer may create dossiers.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Partners cannot modify dossier master data.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Partners cannot modify dossier master data.")
        return super().partial_update(request, *args, **kwargs)

    serializer_class = MatterSerializer
    def get_queryset(self):
        qs = self.scope()
        if self.request.query_params.get('client'):
            qs = qs.filter(client_id=self.request.query_params['client'])
        return qs
    def perform_create(self, serializer):
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Partners cannot create dossiers.')
        obj=serializer.save(created_by=self.request.user)
        record_action(self.request, "matter.created", obj)
    def perform_update(self, serializer):
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Partners cannot edit the dossier master record or its assignment.')
        if 'lead_lawyer' in serializer.validated_data and not is_admin(self.request.user):
            raise PermissionDenied('Only the administrator can assign a dossier.')
        if 'client' in serializer.validated_data and serializer.validated_data['client'].pk != serializer.instance.client_id:
            raise ValidationError({'client':'Cannot move a dossier to another client.'})
        obj=serializer.save()
        record_action(self.request, "matter.updated", obj, {"status":obj.status})
    def perform_destroy(self, instance):
        raise PermissionDenied('Dossier deletion is disabled; close it instead to preserve records.')


class DocumentSerializer(serializers.ModelSerializer):
    original_name = serializers.CharField(source='title', read_only=True)
    class Meta:
        model = MatterDocument
        fields = ['id','matter','title','original_name','category','uploaded_at']
        read_only_fields = ['id','uploaded_at','file']


class DocumentViewSet(PracticeAccess, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['get','post','delete','head','options']
    def get_queryset(self):
        qs = MatterDocument.objects.filter(matter__in=self.scope()).select_related('matter')
        if self.request.query_params.get('matter'):
            qs = qs.filter(matter_id=self.request.query_params['matter'])
        return qs
    def create(self, request, *args, **kwargs):
        matter = self.scope().filter(pk=request.data.get('matter')).first()
        if not matter:
            raise PermissionDenied('Dossier is inaccessible.')
        uploaded = request.FILES.get('file')
        if not uploaded:
            raise ValidationError({'file':'File is required.'})
        if uploaded.size > settings.PRACTICE_MAX_FILE_BYTES:
            raise ValidationError({'file':'File must not exceed 20 MB.'})
        if Path(uploaded.name).suffix.lower() not in {'.pdf','.jpg','.jpeg','.png','.doc','.docx','.xlsx','.txt'}:
            raise ValidationError({'file':'File format is not allowed.'})
        # File names are generated; never trust original paths.
        from django.core.files.storage import FileSystemStorage
        item = MatterDocument(matter=matter, title=(request.data.get('title') or uploaded.name)[:200], category=str(request.data.get('category',''))[:80], uploaded_by=request.user)
        item.file.storage = FileSystemStorage(location=settings.PRACTICE_PRIVATE_ROOT)
        item.file.save(uploaded.name, uploaded, save=False)
        item.save()
        record_action(request, "matter.document.uploaded", item, {"file_size": uploaded.size})
        return Response(DocumentSerializer(item).data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        item = self.get_object()
        from django.core.files.storage import FileSystemStorage
        storage = FileSystemStorage(location=settings.PRACTICE_PRIVATE_ROOT)
        if not storage.exists(item.file.name):
            raise Http404
        return FileResponse(storage.open(item.file.name,'rb'), as_attachment=True, filename=Path(item.title).name)
    def perform_destroy(self, instance):
        raise PermissionDenied('Documents cannot be deleted without a retention policy.')


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatterEvent
        fields = ['id','matter','title','kind','start_at','end_at','location','notes','created_at']
        read_only_fields = ['id','created_at']
    def validate(self, attrs):
        start = attrs.get('start_at', getattr(self.instance,'start_at',None))
        end = attrs.get('end_at', getattr(self.instance,'end_at',None))
        if start and end and end <= start:
            raise ValidationError({'end_at':'End must be later than start.'})
        return attrs
    def validate_matter(self, matter):
        request = self.context['request']
        qs = Matter.objects.all() if is_admin(request.user) else Matter.objects.filter(lead_lawyer__user=request.user) if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR else Matter.objects.filter(Q(created_by=request.user) | Q(lead_lawyer__user=request.user) | Q(client__created_by=request.user))
        if not qs.filter(pk=matter.pk).exists():
            raise serializers.ValidationError('Dossier is inaccessible.')
        return matter


class EventViewSet(PracticeAccess, viewsets.ModelViewSet):
    serializer_class = EventSerializer
    def get_queryset(self):
        qs = MatterEvent.objects.filter(matter__in=self.scope()).select_related('matter')
        if self.request.query_params.get('matter'):
            qs = qs.filter(matter_id=self.request.query_params['matter'])
        return qs
    def perform_create(self, serializer):
        obj=serializer.save(created_by=self.request.user)
        record_action(self.request, "matter.event.created", obj)
    def perform_update(self, serializer):
        if 'matter' in serializer.validated_data and serializer.validated_data['matter'] != serializer.instance.matter:
            raise ValidationError({'matter':'Cannot move events across dossiers.'})
        obj=serializer.save()
        record_action(self.request, "matter.event.updated", obj)


class NoteSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = MatterNote
        fields = ['id','matter','body','author','created_at']
        read_only_fields = ['id','author','created_at']
    def validate_matter(self, matter):
        user = self.context['request'].user
        if is_admin(user):
            allowed = True
        elif user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            allowed = Matter.objects.filter(pk=matter.pk, lead_lawyer__user=user).exists()
        else:
            allowed = Matter.objects.filter(pk=matter.pk).filter(
                Q(created_by=user) | Q(lead_lawyer__user=user) | Q(client__created_by=user)
            ).exists()
        if not allowed:
            raise serializers.ValidationError('Dossier inaccessible.')
        return matter


class NoteViewSet(PracticeAccess, viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    http_method_names = ['get','post','head','options']
    def get_queryset(self):
        qs = MatterNote.objects.filter(matter__in=self.scope()).select_related('created_by')
        if self.request.query_params.get('matter'):
            qs = qs.filter(matter_id=self.request.query_params['matter'])
        return qs
    def perform_create(self, serializer):
        obj=serializer.save(created_by=self.request.user)
        record_action(self.request, "matter.note.created", obj)


def totals(invoice):
    subtotal = sum((line.quantity * line.unit_price for line in invoice.lines.all()), Decimal('0.00'))
    tax = (subtotal * invoice.tax_rate / 100).quantize(Decimal('0.01'))
    paid = sum((p.amount for p in invoice.payments.all()), Decimal('0.00'))
    return subtotal, tax, subtotal + tax, paid


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ['id','description','quantity','unit_price']
    def validate_quantity(self, value):
        if value <= 0: raise serializers.ValidationError('Must be positive.')
        return value
    def validate_unit_price(self, value):
        if value < 0: raise serializers.ValidationError('Must be nonnegative.')
        return value


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id','amount','paid_at','method','reference','created_at']
        read_only_fields = ['id','created_at']
    def validate_amount(self, value):
        if value <= 0: raise serializers.ValidationError('Must be positive.')
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    payments = PaymentSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='matter.client.__str__', read_only=True)
    subtotal = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    paid = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    class Meta:
        model = Invoice
        fields = ['id','reference','matter','client_name','status','issue_date','due_date','tax_rate','currency','notes','lines','payments','subtotal','tax_amount','total','paid','balance','created_at']
        read_only_fields = ['id','reference','status','payments','created_at']
    def get_subtotal(self,obj): return totals(obj)[0]
    def get_tax_amount(self,obj): return totals(obj)[1]
    def get_total(self,obj): return totals(obj)[2]
    def get_paid(self,obj): return totals(obj)[3]
    def get_balance(self,obj): return totals(obj)[2] - totals(obj)[3]
    def validate_tax_rate(self,value):
        if value < 0 or value > 100: raise serializers.ValidationError('Tax rate must be between 0 and 100.')
        return value
    def validate(self,attrs):
        if attrs.get('due_date',getattr(self.instance,'due_date',None)) < attrs.get('issue_date',getattr(self.instance,'issue_date',None)):
            raise ValidationError({'due_date':'Due date cannot precede issue date.'})
        if self.instance and self.instance.status != Invoice.Status.DRAFT:
            raise ValidationError('Only draft invoices can be edited.')
        if not attrs.get('lines') and not self.instance:
            raise ValidationError({'lines':'At least one line is required.'})
        return attrs
    def validate_matter(self,matter):
        request = self.context['request']
        qs = Matter.objects.all() if is_admin(request.user) else Matter.objects.filter(lead_lawyer__user=request.user) if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR else Matter.objects.filter(Q(created_by=request.user) | Q(lead_lawyer__user=request.user) | Q(client__created_by=request.user))
        if not qs.filter(pk=matter.pk).exists(): raise serializers.ValidationError('Dossier inaccessible.')
        return matter
    @transaction.atomic
    def create(self,validated_data):
        lines = validated_data.pop('lines')
        invoice = Invoice.objects.create(**validated_data, created_by=self.context['request'].user)
        InvoiceLine.objects.bulk_create([InvoiceLine(invoice=invoice,**line) for line in lines])
        return invoice
    @transaction.atomic
    def update(self,instance,validated_data):
        lines = validated_data.pop('lines',None)
        if 'matter' in validated_data and validated_data['matter'].pk != instance.matter_id:
            raise ValidationError({'matter':'Invoice cannot be moved across dossiers.'})
        for field,value in validated_data.items(): setattr(instance,field,value)
        instance.save()
        if lines is not None:
            if not lines: raise ValidationError({'lines':'Invoice requires lines.'})
            instance.lines.all().delete()
            InvoiceLine.objects.bulk_create([InvoiceLine(invoice=instance,**line) for line in lines])
        return instance


class InvoiceViewSet(PracticeAccess, viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    def create(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Only the office can create invoices.')
        return super().create(request, *args, **kwargs)
    def update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Only the office can modify invoices.')
        return super().update(request, *args, **kwargs)
    def partial_update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Only the office can modify invoices.')
        return super().partial_update(request, *args, **kwargs)
    def get_queryset(self):
        qs = Invoice.objects.filter(matter__in=self.scope()).select_related('matter','matter__client').prefetch_related('lines','payments')
        if self.request.query_params.get('matter'): qs = qs.filter(matter_id=self.request.query_params['matter'])
        return qs
    def perform_destroy(self,instance):
        raise PermissionDenied('Invoices are never deleted; cancel them.')
    @action(detail=True,methods=['post'])
    def issue(self,request,pk=None):
        with transaction.atomic():
            invoice = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if not is_admin(request.user): raise PermissionDenied('Only admin may issue invoices.')
            if invoice.status != Invoice.Status.DRAFT: raise ValidationError('Not a draft invoice.')
            if totals(invoice)[2] <= 0: raise ValidationError('Invoice total must be positive.')
            invoice.status = Invoice.Status.ISSUED
            invoice.save(update_fields=['status','updated_at'])
            record_action(request, "invoice.status.changed", invoice, {"status":invoice.status})
        return Response(self.get_serializer(invoice).data)
    @action(detail=True,methods=['post'])
    def cancel(self,request,pk=None):
        with transaction.atomic():
            invoice = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if not is_admin(request.user): raise PermissionDenied('Only admin may cancel.')
            if invoice.status not in [Invoice.Status.DRAFT, Invoice.Status.ISSUED] or invoice.payments.exists():
                raise ValidationError('Cannot cancel paid invoices.')
            invoice.status = Invoice.Status.CANCELLED
            invoice.save(update_fields=['status','updated_at'])
            record_action(request, "invoice.status.changed", invoice, {"status":invoice.status})
        return Response(self.get_serializer(invoice).data)
    @action(detail=True,methods=['post'])
    def record_payment(self,request,pk=None):
        if not is_admin(request.user): raise PermissionDenied('Only admin may record payments.')
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            invoice = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if invoice.status not in [Invoice.Status.ISSUED,Invoice.Status.PARTIAL]:
                raise ValidationError('Invoice is not payable.')
            balance = totals(invoice)[2] - totals(invoice)[3]
            if serializer.validated_data['amount'] > balance:
                raise ValidationError({'amount':'Amount exceeds outstanding balance.'})
            payment=serializer.save(invoice=invoice,recorded_by=request.user)
            record_action(request, "invoice.payment.recorded", payment)
            invoice.status = Invoice.Status.PAID if serializer.validated_data['amount'] == balance else Invoice.Status.PARTIAL
            invoice.save(update_fields=['status','updated_at'])
            record_action(request, "invoice.status.changed", invoice, {"status":invoice.status})
        return Response(self.get_serializer(invoice).data)
