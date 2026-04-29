"""
Tests for resume API.
"""
import secrets
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from core.models import APIKey
from resume.models import (
    Resume,
    Candidate,
    Skill,
    Experience,
    Education,
    Language,
)

Tenant = get_user_model()

RESUME_LIST_URL = reverse("resume:resume_list_create")


def resume_detail_url(resume_id):
    return reverse("resume:resume_detail", args=[resume_id])


def create_tenant(**params):
    """Helper function to create a Tenant."""
    defaults = {
        "email": "tenant@example.com",
        "password": "testpass123",
        "name": "Test Tenant",
        "plan": "free",
    }
    defaults.update(params)
    return Tenant.objects.create_user(**defaults)


def create_api_key(tenant):
    """Helper to create an API key for a tenant."""
    raw_key = "rpa_" + secrets.token_urlsafe(40)

    APIKey.objects.create(
        tenant=tenant, key_hash=APIKey.hash_key(raw_key), label="test key"
    )
    return raw_key


def create_resume(tenant, **params):
    """Helper to create a resume."""
    defaults = {
        "source_type": "text",
        "raw_text": "John Doe, Software Engineer, Python, Django",
        "status": "pending",
    }
    defaults.update(params)
    return Resume.objects.create(tenant=tenant, **defaults)


class PublicResumeAPITests(TestCase):
    """
    Tests for public resume API.
    """

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_request_rejected(self):
        """Test that unauthenticated requests are rejected."""

        res = self.client.get(RESUME_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_api_key_rejected(self):
        """Test that invalid API key is rejected."""
        self.client.credentials(HTTP_X_API_KEY="rpa_invalidkey")

        res = self.client.get(RESUME_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PrivateResumeAPITests(TestCase):
    """Test for authenticated resume API requests."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = create_tenant()

        self.rawkey = create_api_key(self.tenant)
        self.client.credentials(HTTP_X_API_KEY=self.rawkey)

    @patch("resume.views.parse_resume.delay")
    def test_submit_plain_text_resume_successful(self, mock_task):
        """Test submitting a plain text resume."""
        payload = {
            "source_type": "text",
            "raw_text": "John Doe, Software Engineer, Python, Django",
        }
        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("resume_id", res.data)
        self.assertEqual(res.data["status"], "pending")
        mock_task.assert_called_once()

    @patch("resume.views.parse_resume.delay")
    def test_submit_linkedin_url_resume_successful(self, mock_task):
        """Test submitting a LinkedIn URL resume."""
        payload = {
            "source_type": "linkedin",
            "linkedin_url": "https://www.linkedin.com/in/johndoe",
        }
        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("resume_id", res.data)
        self.assertEqual(res.data["status"], "pending")
        mock_task.assert_called_once()

    @patch("resume.views.parse_resume.delay")
    def test_submit_pdf_resume_successful(self, mock_task):
        """Test submitting a PDF resume."""
        pdf_file = SimpleUploadedFile(
            "resume.pdf", b"pdf content", content_type="application/pdf"
        )
        payload = {
            "source_type": "pdf",
            "file": pdf_file,
        }
        res = self.client.post(RESUME_LIST_URL, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once()

    @patch("resume.views.parse_resume.delay")
    def test_submit_docx_resume_successful(self, mock_task):
        """Test submitting a DOCX resume."""
        docx_file = SimpleUploadedFile(
            "resume.docx",
            b"docx content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        payload = {
            "source_type": "docx",
            "file": docx_file,
        }
        res = self.client.post(RESUME_LIST_URL, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once()

    def test_submit_text_without_raw_fails(self):
        """Test that submitting text source without raw_text fails."""

        payload = {"source_type": "text"}

        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_pdf_without_file_fails(self):
        """Test that submitting pdf source without file fails."""
        payload = {"source_type": "pdf"}
        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_linkedin_without_url_fails(self):
        """Test that submitting linkedin source without URL fails."""
        payload = {"source_type": "linkedin"}
        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_exceeding_5mb_rejected(self):
        """Test that files larger than 5MB are rejected."""
        large_file = SimpleUploadedFile(
            "large.pdf", b"x" * (5 * 1024 * 1024 + 1), content_type="application/pdf"
        )
        payload = {"source_type": "pdf", "file": large_file}
        res = self.client.post(RESUME_LIST_URL, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_file_type_rejected(self):
        """Test that non pdf/docx files are rejected."""
        txt_file = SimpleUploadedFile(
            "resume.txt", b"some text", content_type="text/plain"
        )
        payload = {"source_type": "pdf", "file": txt_file}
        res = self.client.post(RESUME_LIST_URL, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ===============================Listing and retrieving resumes tests========================

    @patch("resume.views.parse_resume.delay")
    def test_list_resumes_successful(self, mock_task):
        """Test listing all resumes for authenticated tenant."""
        create_resume(self.tenant)
        create_resume(
            self.tenant,
            source_type="linkedin",
            linkedin_url="https://linkedin.com/in/test",
        )
        res = self.client.get(RESUME_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_filter_resumes_by_status(self):
        """Test filtering resumes by status."""
        create_resume(self.tenant, status="done")
        create_resume(self.tenant, status="pending")

        res = self.client.get(RESUME_LIST_URL, {"status": "done"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_filter_resumes_by_source_type(self):
        """Test filtering resumes by source type."""
        create_resume(self.tenant)
        create_resume(
            self.tenant,
            source_type="linkedin",
            linkedin_url="https://linkedin.com/in/test",
        )
        res = self.client.get(RESUME_LIST_URL, {"source_type": "text"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_retrieve_resume_successful(self):
        """Test retrieving a single resume."""
        resume = create_resume(self.tenant)
        res = self.client.get(resume_detail_url(resume.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(res.data["id"]), str(resume.id))

    def test_retrieve_resume_with_parsed_data(self):
        """Test retrieving a resume with fully parsed data."""
        resume = create_resume(self.tenant, status="done")
        Candidate.objects.create(
            resume=resume, full_name="John Doe", email="john@example.com"
        )
        Skill.objects.create(resume=resume, name="Python")
        Experience.objects.create(resume=resume, company="Safaricom", title="Engineer")
        res = self.client.get(resume_detail_url(resume.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["candidate"]["full_name"], "John Doe")
        self.assertEqual(len(res.data["skills"]), 1)
        self.assertEqual(len(res.data["experiences"]), 1)

    def test_cannot_retrieve_another_tenants_resume(self):
        """Test that a tenant cannot retrieve another tenant's resume."""
        other_tenant = create_tenant(email="other@example.com")
        other_resume = create_resume(other_tenant)

        res = self.client.get(resume_detail_url(other_resume.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_resume_successful(self):
        """Test deleting a resume."""
        resume = create_resume(self.tenant)
        res = self.client.delete(resume_detail_url(resume.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Resume.objects.filter(id=resume.id).exists())

    def test_cannot_delete_another_tenants_resume(self):
        """Test that a tenant cannot delete another tenant's resume."""
        other_tenant = create_tenant(email="other@example.com")
        other_resume = create_resume(other_tenant)

        res = self.client.delete(resume_detail_url(other_resume.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Resume.objects.filter(id=other_resume.id).exists())

    @patch("resume.throttling.cache.get")
    def test_rate_limit_exceeded_returns_429(self, mock_cache_get):
        """Test that exceeding rate limit returns 429."""
        mock_cache_get.return_value = 100
        payload = {
            "source_type": "text",
            "raw_text": "John Doe, Software Engineer",
        }
        res = self.client.post(RESUME_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ResumeParsingTaskTests(TestCase):
    """Tests for the Celery resume parsing task."""

    def setUp(self):
        self.tenant = create_tenant()

    @patch("resume.tasks.parse_resume_with_ai")
    @patch("resume.tasks.extract_text")
    def test_parse_resume_task_successful(self, mock_extract, mock_ai):
        """Test that the parse resume task runs successfully."""
        from resume.tasks import parse_resume

        resume = create_resume(self.tenant)
        mock_extract.return_value = "John Doe Software Engineer Python"
        mock_ai.return_value = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": None,
            "location": "Nairobi",
            "summary": "Software Engineer",
            "skills": [{"name": "Python", "category": "Programming"}],
            "experience": [
                {
                    "company": "Safaricom",
                    "title": "Engineer",
                    "location": "Nairobi",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "is_current": True,
                    "description": "Built APIs",
                    "order": 1,
                }
            ],
            "education": [
                {
                    "institution": "University of Nairobi",
                    "degree": "BSc",
                    "field_of_study": "Computer Science",
                    "start_date": "2015-09-01",
                    "end_date": "2019-06-01",
                    "grade": "First Class",
                    "order": 1,
                }
            ],
            "certifications": [],
            "languages": [{"name": "English", "proficiency": "Native"}],
        }

        parse_resume(str(resume.id))

        resume.refresh_from_db()
        self.assertEqual(resume.status, "done")
        self.assertIsNotNone(resume.parsed_at)
        self.assertTrue(Candidate.objects.filter(resume=resume).exists())
        self.assertTrue(Skill.objects.filter(resume=resume).exists())
        self.assertTrue(Experience.objects.filter(resume=resume).exists())
        self.assertTrue(Education.objects.filter(resume=resume).exists())
        self.assertTrue(Language.objects.filter(resume=resume).exists())

    @patch("resume.tasks.extract_text")
    def test_parse_resume_task_fails_gracefully(self, mock_extract):
        """Test that a failed task updates status to failed."""
        from resume.tasks import parse_resume

        resume = create_resume(self.tenant)
        mock_extract.side_effect = Exception("Could not extract text")

        try:
            parse_resume(str(resume.id))
        except Exception:
            pass

        resume.refresh_from_db()
        self.assertEqual(resume.status, "failed")
        self.assertIsNotNone(resume.error_message)

    @patch("resume.tasks.parse_resume_with_ai")
    @patch("resume.tasks.extract_text")
    def test_parse_resume_saves_candidate(self, mock_extract, mock_ai):
        """Test that parsing saves candidate information correctly."""
        from resume.tasks import parse_resume

        resume = create_resume(self.tenant)
        mock_extract.return_value = "John Doe"
        mock_ai.return_value = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "0712345678",
            "location": "Nairobi",
            "summary": "Engineer",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "languages": [],
        }

        parse_resume(str(resume.id))

        candidate = Candidate.objects.get(resume=resume)
        self.assertEqual(candidate.full_name, "John Doe")
        self.assertEqual(candidate.email, "john@example.com")
        self.assertEqual(candidate.phone, "0712345678")
