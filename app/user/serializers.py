"""
Serializers for the user API view
"""
from django.contrib.auth import get_user_model, authenticate
from core.models import APIKey
from rest_framework import serializers


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for the user obejetc."""

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "name", "password", "plan")
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6},
            "plan": {"required": True},
        }

    def create(self, validated_data):
        """Create a new tenant with encrypted password and return it."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a tenant, setting the password correctly and return it."""
        password = validated_data.pop("password", None)
        tenant = super().update(instance, validated_data)
        if password:
            tenant.set_password(password)
            tenant.save()
        return tenant

    def perform_destroy(self, instance):
        """Delete the tenant and all related data."""
        instance.delete()


class LoginSerializer(serializers.Serializer):
    """Serializer for the tenent login."""

    email = serializers.CharField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
        allow_blank=False,
        required=True,
    )

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        tenant = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not tenant:
            raise serializers.ValidationError(
                {
                    "error": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                },
                code="authorization",
            )

        if not tenant.is_active:
            raise serializers.ValidationError(
                {
                    "error": "ACCOUNT_DISABLED",
                    "message": "This account has been disabled.",
                },
                code="authorization",
            )

        data["tenant"] = tenant
        return data


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for listing API keys."""

    class Meta:
        model = APIKey
        fields = ("id", "label", "is_active", "created_at", "last_used_at")
        read_only_fields = ("id", "is_active", "created_at", "last_used_at")


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """ "Serializer for creating API key."""

    class Meta:
        model = APIKey
        fields = ("label",)


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating API key."""

    class Meta:
        model = APIKey
        fields = ("label", "is_active")
