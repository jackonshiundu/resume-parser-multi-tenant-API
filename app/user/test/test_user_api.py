"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import APIKey
from rest_framework.test import APIClient
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

CREATE_TENANT_URL = reverse("tenant:create")
LOGIN_URL = reverse("tenant:login")
MANAGE_TENANT_URL = reverse("tenant:manage")
TOKEN_REFRESH_URL = reverse("tenant:token_refresh")
API_KEYS_URL = reverse("tenant:api_keys")


def api_key_detail_url(key_id):
    return reverse("tenant:api_key_detail", kwargs={"id": key_id})


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
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("token", res.data)


class PrivateTenantApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.tenant = create_tenant(
            email="test@example.com",
            password="testpass123",
            name="Test Name",
            plan="free",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.tenant)

    def test_retrieve_tenant_success(self):
        """Test retrieving profile for logged in tenant."""
        res = self.client.get(MANAGE_TENANT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.tenant.email)
        self.assertEqual(res.data["name"], self.tenant.name)

    def test_update_tenant_success(self):
        """Test updating the tenant profile for the authenticated tenant."""
        payload = {"name": "New Name", "password": "newpassword123"}
        res = self.client.patch(MANAGE_TENANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, payload["name"])
        self.assertTrue(self.tenant.check_password(payload["password"]))

    def test_delete_tenant_success(self):
        """Test deleting the tenant profile for the authenticated tenant."""
        res = self.client.delete(MANAGE_TENANT_URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tenant_exists = Tenant.objects.filter(id=self.tenant.id).exists()
        self.assertFalse(tenant_exists)

    def test_unauthenticated_access(self):
        """Test that authentication is required for retrieving tenant profile."""
        self.client.force_authenticate(user=None)
        res = self.client.get(MANAGE_TENANT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        """Test refreshing JWT token successfully."""
        refresh_payload = {"refresh": str(RefreshToken.for_user(self.tenant))}
        res = self.client.post(TOKEN_REFRESH_URL, refresh_payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_list_api_keys(self):
        """Test listing API keys for the authenticated tenant."""
        APIKey.objects.create(
            tenant=self.tenant, key_hash=APIKey.hash_key("key_one"), label="production"
        )
        APIKey.objects.create(
            tenant=self.tenant, key_hash=APIKey.hash_key("key_two"), label="staging"
        )
        res = self.client.get(API_KEYS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 2)

    def test_create_api_key_successfully(self):
        """Test creating a new API key for the authenticated tenant."""
        payload = {"label": "test_key"}
        res = self.client.post(API_KEYS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("api_key", res.data)
        self.assertEqual(res.data["label"], payload["label"])

    def test_cannot_access_another_tenants_api_keys(self):
        """Test that a tenant cannot access another tenant's API keys."""
        other_tenant = create_tenant(
            email="other@example.com",
            password="otherpass123",
            name="Other Name",
            plan="free",
        )
        other_key = APIKey.objects.create(
            tenant=other_tenant,
            key_hash=APIKey.hash_key("other_key"),
            label="other_key",
        )
        res = self.client.delete(api_key_detail_url(other_key.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
