"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_TENANT_URL = reverse("user:create")
LOGIN_URL = reverse("user:login")

Tenant = get_user_model()


def create_tenant(**params):
    return Tenant.objects.create_user(**params)


class PublicTenantApiTests(TestCase):
    """Test public feature of the Tenant API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_new_tenant_success(self):
        """Test successfully created a new user."""

        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
            "plan": "free",
        }

        res = self.client.post(CREATE_TENANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = Tenant.objects.get(email=payload["email"])

        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_an_api_key_when_tenant_is_created(self):
        """Test to create an API key when a Tenant is created."""

        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
            "plan": "free",
        }

        res = self.client.post(CREATE_TENANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("api_key", res.data)
        self.assertTrue(res.data["api_key"].startswith("rpa_"))
        user = Tenant.objects.get(email=payload["email"])

        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_tenant_with_email_exists_error(self):
        """Test a tenant with email existss error."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
            "plan": "free",
        }

        create_tenant(**payload)
        res = self.client.post(CREATE_TENANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 characters"""

        payload = {
            "email": "test@example.com",
            "password": "ps",
            "name": "Test Name",
        }

        res = self.client.post(CREATE_TENANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        tenant_exists = Tenant.objects.filter(email=payload["email"]).exists()

        self.assertFalse(tenant_exists)

    def test_create_token_when_blank_password(self):
        """Test returns error if credentials invalid"""
        tenant_details = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
        }

        create_tenant(**tenant_details)
        payload = {"email": tenant_details["email"], "password": ""}
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)
