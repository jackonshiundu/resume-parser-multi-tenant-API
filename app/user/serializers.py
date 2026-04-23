"""
Serializers for the user API view
"""
from django.contrib.auth import get_user_model, authenticate

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
        return get_user_model().objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for the tenent login."""

    email = serializers.CharField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
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
