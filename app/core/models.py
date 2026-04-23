"""
User Models.
"""
import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.conf import settings


class TenantManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a new user."""

        if not email:
            raise ValueError("Tenant must have an email address.")
        tenant = self.model(email=self.normalize_email(email), **extra_fields)
        tenant.set_password(password)
        tenant.save(using=self._db)
        return tenant

    def create_superuser(self, email, password):
        """Create and return a superuser."""
        tenant = self.create_user(email, password)
        tenant.is_staff = True
        tenant.is_superuser = True
        tenant.save(using=self._db)
        return tenant


class Tenant(AbstractBaseUser, PermissionsMixin):
    """Custom tenant model."""

    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("enterprice", "Enterprise"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email


class APIKey(models.Model):
    """API key for tenant authentication."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys"
    )
    key_hash = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=100, blank=True, default="default")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.tenant.email} - {self.label}"

    @staticmethod
    def hash_key(row_key):
        """Hash a raw API key for Storage."""
        return hashlib.sha256(row_key.encode()).hexdigest()
