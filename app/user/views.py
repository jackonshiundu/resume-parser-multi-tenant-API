"""Views for the User APi"""
import secrets
from rest_framework import generics, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .serializers import TenantSerializer, LoginSerializer

from core.models import APIKey


@extend_schema(tags=["Tenant Management"])
class CreateTenantView(generics.CreateAPIView):
    """Register a new tenant and return their first API key."""

    serializer_class = TenantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()

        raw_key = "rpa_" + secrets.token_urlsafe(40)

        APIKey.objects.create(
            tenant=tenant, key_hash=APIKey.hash_key(raw_key), label="default"
        )
        return Response(
            {
                "message": "User created successfully",
                "warning": "Save your API key now. It will never be shown again.",
                "email": tenant.email,
                "api_key": raw_key,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Tenant Management"])
class LoginView(APIView):
    """Login and receive a JWT session token."""

    serializer_class = LoginSerializer

    def post(self, request):

        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        tenant = serializer.validated_data["tenant"]

        refresh = RefreshToken.for_user(tenant)

        return Response(
            {
                "message": "Login successful.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
        )
