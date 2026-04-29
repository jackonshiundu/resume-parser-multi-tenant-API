"""Models for the Resume Parser API."""
import uuid
from django.db import models
from django.conf import settings


def resume_upload_path(instance, filename):
    """Generate upload path per tenant."""
    return f"resumes/{instance.tenant.id}/{filename}"


# Create your models here.
class Resume(models.Model):
    """Central resume model. Parent of all extracted data"""

    SOURCE_TYPE = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("text", "Plain Text"),
        ("linkedin", "LinkedIn"),
    ]

    STATUS = [
        ("pending", "Pending"),
        ("preprocessing", "Preprocessing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes"
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE,
    )
    raw_text = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=resume_upload_path, null=True, blank=True)
    file_url = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending",
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.tenant.email} - {self.source_type} - {self.status}"


class Candidate(models.Model):
    """Personal information extracted from the resume. One-to-one with Resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.OneToOneField(
        Resume, on_delete=models.CASCADE, related_name="candidate"
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name or 'Unknown'} - {self.resume.id}"


class Skill(models.Model):
    """One row per skill extracted from the resume."""

    class Meta:
        unique_together = ("resume", "name")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.resume.id}"


class Experience(models.Model):
    """One row per job or role extracted from the resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="experiences"
    )
    company = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} at {self.company} - {self.resume.id}"


class Education(models.Model):
    """One row per qualification or degree extracted from the resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="education"
    )
    institution = models.CharField(max_length=255, blank=True, null=True)
    degree = models.CharField(max_length=255, blank=True, null=True)
    field_of_study = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    grade = models.CharField(max_length=100, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.degree} at {self.institution} - {self.resume.id}"


class Certification(models.Model):
    """One row per certification or credential extracted from the resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.resume.id}"


class Language(models.Model):
    """One row per language extracted from the resume."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="languages"
    )
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.resume.id}"
