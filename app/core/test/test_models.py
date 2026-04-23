from django.test import TestCase
from django.contrib.auth import get_user_model

Tenant = get_user_model()


class ModelTest(TestCase):
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

    def test_create_user_user(self):
        """Test create a new superuser."""
        super_user = Tenant.objects.create_superuser(
            email="admin@example.com", password="admin12345"
        )
        self.assertTrue(super_user.is_superuser)
