"""
User Models.
"""
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


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
