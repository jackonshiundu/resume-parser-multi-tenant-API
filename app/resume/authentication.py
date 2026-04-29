"""Custom API key authentication for the resume API."""

from django.utils import timezone
import hashlib
from core.models import APIKey
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class APIKeyAuthentication(BaseAuthentication):
    """Authentication requests using X-API-KEy header."""

    def authenticate(self, request):
        """Authenticate the request and return (tenant, api_key) if valid \
              or AuthenticationFailed if not."""
        raw_key = request.headers.get("X-API-KEY")

        if not raw_key:
            raise AuthenticationFailed("No API key provided")

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = APIKey.objects.select_related("tenant").get(
                key_hash=key_hash, is_active=True
            )

        except APIKey.DoesNotExist:
            raise AuthenticationFailed(
                {"error": "INVALID_API_KEY", "message": "Invalid or inactive API key."}
            )

        if not api_key.tenant.is_active:
            raise AuthenticationFailed(
                {
                    "error": "INACTIVE_TENANT",
                    "message": "The tenant associated with this API key is inactive.",
                }
            )

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        return (api_key.tenant, api_key)


class APIKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "resume.authentication.APIKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
