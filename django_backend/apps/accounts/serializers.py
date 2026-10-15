from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Client, LawyerProfile, PracticeArea, User
from .services import normalize_phone


class PhoneField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if not value:
            return value
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    phone = PhoneField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone', 'password', 'role']
        read_only_fields = ['id']

    def validate_role(self, value):
        if value != User.Role.CLIENT:
            raise serializers.ValidationError('Public registration only accepts the CLIENT role.')
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('This phone number is already registered.')
        return value

    def validate(self, attrs):
        try:
            validate_password(attrs['password'], User(**{k: v for k, v in attrs.items() if k != 'password'}))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError('An account with these details already exists.')


class ManagedUserSerializer(RegisterSerializer):
    """Only administrators can create users with privileged roles."""

    def validate_role(self, value):
        return value


class PhoneEnrollmentSerializer(serializers.Serializer):
    phone = PhoneField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('This phone number is already registered.')
        return value


class UserSerializer(serializers.ModelSerializer):
    client_profile_id = serializers.SerializerMethodField()
    lawyer_profile_id = serializers.SerializerMethodField()
    client_link_pending = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone',
                  'phone_verified', 'client_profile_id', 'lawyer_profile_id', 'client_link_pending']
        read_only_fields = fields

    def get_client_profile_id(self, obj) -> int | None:
        return getattr(getattr(obj, 'client_profile', None), 'pk', None)

    def get_lawyer_profile_id(self, obj) -> int | None:
        return getattr(getattr(obj, 'lawyer_profile', None), 'pk', None)

    def get_client_link_pending(self, obj) -> bool:
        return bool(obj.role == User.Role.CLIENT and obj.phone and not self.get_client_profile_id(obj))


class PracticeAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeArea
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LawyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerProfile
        fields = ['id', 'user', 'bar_number', 'bar_association', 'jurisdiction', 'bio',
                  'years_experience', 'is_verified', 'created_at', 'practice_areas',
                  'organization', 'availability_status', 'updated_at']
        read_only_fields = ['id', 'user', 'is_verified', 'created_at', 'organization', 'updated_at']


class LawyerVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerProfile
        fields = ['is_verified']
        extra_kwargs = {'is_verified': {'required': True}}


class ClientSerializer(serializers.ModelSerializer):
    phone = PhoneField()
    secondary_phone = PhoneField(required=False, allow_blank=True)

    class Meta:
        model = Client
        fields = ['id', 'user', 'first_name', 'last_name', 'email', 'phone', 'secondary_phone',
                  'address', 'city', 'notes', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_by', 'created_at', 'updated_at']

    def validate_phone(self, value):
        if self.instance and self.instance.user_id and value != self.instance.phone:
            raise serializers.ValidationError('The phone of a linked account cannot be changed here.')
        matches = Client.objects.filter(phone=value)
        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError('A client with this phone number already exists.')
        if (not self.instance or value != self.instance.phone) and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('This phone belongs to an existing account.')
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'phone': 'A client with this phone number already exists.'})

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'phone': 'A client with this phone number already exists.'})


class ClientSelfSerializer(ClientSerializer):
    phone = PhoneField(read_only=True)

    class Meta(ClientSerializer.Meta):
        fields = [field for field in ClientSerializer.Meta.fields if field not in ['notes', 'created_by']]
        read_only_fields = ClientSerializer.Meta.read_only_fields + ['phone']
