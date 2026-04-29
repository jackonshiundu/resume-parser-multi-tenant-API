"""Views for the User APi"""
import secrets
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .serializers import (
    APIKeyCreateSerializer,
    APIKeySerializer,
    APIKeyUpdateSerializer,
    TenantSerializer,
    LoginSerializer,
)

from core.models import APIKey


@extend_schema(tags=["Token Management"])
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(tags=["Tenant Management"])
class CreateTenantView(generics.CreateAPIView):
    """Register a new tenant and return their first API key."""

    serializer_class = TenantSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

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


@extend_schema(tags=["Tenant Management"])
class ManageTenantView(generics.RetrieveUpdateDestroyAPIView):
    """View, update, or delete the authenticated tenant."""

    serializer_class = TenantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


@extend_schema(tags=["API Key Management"])
class APIKeyListCreateView(generics.ListCreateAPIView):
    """List existing API keys and create new ones for the authenticated tenant."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return APIKeyCreateSerializer
        return APIKeySerializer

    def get_queryset(self):
        """Return API keys for the authenticated tenant."""
        return APIKey.objects.filter(tenant=self.request.user, is_active=True).order_by(
            "-created_at"
        )

    def perform_create(self, serializer):
        """Create a new API key for the authenticated tenant."""
        raw_key = "rpa_" + secrets.token_urlsafe(40)
        serializer.save(tenant=self.request.user, key_hash=APIKey.hash_key(raw_key))
        self.created_key = raw_key

    def create(self, request, *args, **kwargs):
        """Override to include raw API key in response."""
        response = super().create(request, *args, **kwargs)
        response.data["api_key"] = self.created_key
        response.data[
            "warning"
        ] = "Save your API key now. It will never be shown again."
        return response


@extend_schema(tags=["API Key Management"])
class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update label, or revoke a specific API Key."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = APIKeyUpdateSerializer

    def get_queryset(self):
        """Return only active API Keys for the authenticated tenant."""
        return APIKey.objects.filter(tenant=self.request.user, is_active=True)

    def get_object(self):
        """Ensure the API key belongs to the authenticated tenant."""
        return generics.get_object_or_404(self.get_queryset(), id=self.kwargs["id"])

    def perform_destroy(self, instance):
        """Revoke the API key instead of deleting it."""
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Override to return a custom response on deletion."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "API key revoked successfully."},
            status=status.HTTP_200_OK,
        )
