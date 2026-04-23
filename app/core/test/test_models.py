from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import APIKey

Tenant = get_user_model()


def create_tenant(**params):
    """Helper function to create a tenant."""
    defaults = {
        "email": "tenant@example.com",
        "password": "testpass123",
        "name": "Test Tenant",
    }
    defaults.update(params)
    return Tenant.objects.create_user(**defaults)


class TenantModelTest(TestCase):
    """Test to test all the system Models."""

    def test_create_tenant_with_email_successful(self):
        """Test creating a new tenant with an email is successful"""
        email = "test@example.com"
        password = "testpass123"

        tenant = Tenant.objects.create_user(email=email, password=password)

        self.assertEqual(tenant.email, email)
        self.assertTrue(tenant.check_password(password))

    def test_tenant_email_normalized(self):
        """Test the email for a new tenant is normalized."""

        sample_emails = [
            ["test1@example.com", "test1@example.com"],
            ["TEST2@EXAMPLE.COM", "TEST2@example.com"],
            ["Test3@Example.Com", "Test3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            tenant = Tenant.objects.create_user(email=email, password="sample123")
            self.assertEqual(tenant.email, expected)

    def test_tenant_without_email_raises_error(self):
        """Test createing a tenant without an email raises a valueError."""

        with self.assertRaises(ValueError):
            Tenant.objects.create_user("", password="example123")

    def test_create_tenant(self):
        """Test create a new superuser."""
        super_user = Tenant.objects.create_superuser(
            email="admin@example.com", password="admin12345"
        )
        self.assertTrue(super_user.is_superuser)


class APIKeyModelTests(TestCase):
    """Tests for the APIKey model."""

    def setUp(self):
        self.tenant = create_tenant()

    def test_create_api_key_successful(self):
        """Test creatign an API key is successful."""

        api_key = APIKey.objects.create(
            tenant=self.tenant,
            key_hash=APIKey.hash_key("rawkey123"),
            label="production",
        )

        self.assertIsNotNone(api_key.id)

    def test_api_key_is_active_by_default(self):
        """Test that a new API key is active by default."""
        api_key = APIKey.objects.create(
            tenant=self.tenant,
            key_hash=APIKey.hash_key("rawkey123"),
        )
        self.assertTrue(api_key.is_active)

    def test_api_key_last_used_at_is_null_by_default(self):
        """Test that last_used_at is null on creation."""
        api_key = APIKey.objects.create(
            tenant=self.tenant,
            key_hash=APIKey.hash_key("rawkey123"),
        )
        self.assertIsNone(api_key.last_used_at)
