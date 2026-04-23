from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.models import Tenant
from django.utils.translation import gettext_lazy as _


class TenantAdmin(BaseUserAdmin):
    """Define the admin pages for tenants."""

    ordering = ["id"]
    list_display = ["email", "name", "plan", "is_active", "is_staff"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("name", "plan")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = [
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "plan",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    ]


admin.site.register(Tenant, TenantAdmin)
