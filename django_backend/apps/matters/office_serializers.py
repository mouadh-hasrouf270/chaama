import re
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from rest_framework import serializers
from .models import Client, Matter, MatterDocument, MatterHistory, Invoice, InvoicePayment
from .office_access import visible_clients, visible_matters, is_admin


class ClientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=30)
    matters_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'secondary_phone', 'address',
                  'city', 'notes', 'created_at', 'updated_at', 'version', 'matters_count']
        read_only_fields = ['created_at', 'updated_at', 'version']

    def get_matters_count(self, obj):
        return visible_matters(self.context['request'].user).filter(client_profile=obj).count()

    def validate_phone(self, value):
        if not re.fullmatch(r'\+?[\d\s().-]+', value):
            raise serializers.ValidationError('Numéro de téléphone invalide.')
        number = re.sub(r'\D', '', value)
        if not 8 <= len(number) <= 15:
            raise serializers.ValidationError('Le numéro doit contenir de 8 à 15 chiffres.')
        if number.startswith('00'):
            number = number[2:]
        if len(number) == 10 and number.startswith('0'):
            number = '213' + number[1:]
        normalized = '+' + number
        qs = Client.objects.filter(phone=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Un client utilise déjà ce numéro. Recherchez sa fiche.')
        return normalized


class MatterSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client_profile.__str__', read_only=True)
    client_profile = serializers.PrimaryKeyRelatedField(queryset=Client.objects.none())

    class Meta:
        model = Matter
        fields = ['id', 'reference', 'title', 'description', 'client_profile', 'client_name',
                  'status', 'priority', 'opened_at', 'closed_at', 'created_at', 'updated_at', 'version']
        read_only_fields = ['reference', 'status', 'opened_at', 'closed_at', 'created_at', 'updated_at', 'version']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            self.fields['client_profile'].queryset = visible_clients(self.context['request'].user)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatterDocument
        fields = ['id', 'original_name', 'size', 'content_type', 'created_at']


class HistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', default='Utilisateur supprimé')
    class Meta:
        model = MatterHistory
        fields = ['id', 'message', 'actor_name', 'created_at']


class LineSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=250)
    quantity = serializers.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal('0.01'))
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        fields = ['id', 'request_id', 'amount', 'method', 'reference', 'paid_on', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'request_id': {'validators': []}}

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Le montant doit être positif.')
        return value

    def validate_paid_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('La date du règlement ne peut pas être future.')
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    can_approve = serializers.SerializerMethodField()
    matter = serializers.PrimaryKeyRelatedField(queryset=Matter.objects.none())
    matter_title = serializers.CharField(source='matter.title', read_only=True)
    client_name = serializers.CharField(source='matter.client_profile.__str__', read_only=True)
    lines = LineSerializer(many=True, allow_empty=False)
    payments = PaymentSerializer(many=True, read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'reference', 'matter', 'matter_title', 'client_name', 'status', 'currency',
                  'issuer_name', 'issuer_address', 'customer_name', 'customer_address', 'lines', 'tax_rate',
                  'subtotal', 'tax_amount', 'total', 'paid_amount', 'balance', 'issue_date', 'due_date',
                  'notes', 'version', 'payments', 'created_at', 'can_approve']
        read_only_fields = ['reference', 'status', 'currency', 'customer_name', 'customer_address',
                            'subtotal', 'tax_amount', 'total', 'paid_amount', 'issue_date', 'version', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            self.fields['matter'].queryset = visible_matters(self.context['request'].user).exclude(status='ARCHIVED')

    def get_balance(self, obj):
        return str(obj.total - obj.paid_amount)

    def get_can_approve(self, obj):
        return is_admin(self.context['request'].user)

    def validate_tax_rate(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Le taux doit être compris entre 0 et 100.')
        return value

    def validate_due_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError('Choisissez une échéance à partir d’aujourd’hui.')
        return value

    def validate_lines(self, values):
        if len(values) > 100:
            raise serializers.ValidationError('Maximum 100 lignes.')
        return values

    def save(self, **kwargs):
        values = dict(self.validated_data)
        lines = values.get('lines', self.instance.lines if self.instance else [])
        rate = values.get('tax_rate', self.instance.tax_rate if self.instance else Decimal(0))
        subtotal = sum((Decimal(str(line['quantity'])) * Decimal(str(line['unit_price']))).quantize(
            Decimal('.01'), rounding=ROUND_HALF_UP) for line in lines)
        tax = (subtotal * rate / 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        if subtotal + tax > Decimal('999999999999.99'):
            raise serializers.ValidationError('Le montant total dépasse la limite autorisée.')
        values.update(lines=[{k: str(v) for k, v in line.items()} for line in lines],
                      subtotal=subtotal, tax_amount=tax, total=subtotal + tax, **kwargs)
        if self.instance:
            for key, value in values.items():
                setattr(self.instance, key, value)
            self.instance.save()
        else:
            self.instance = Invoice.objects.create(**values)
        return self.instance
