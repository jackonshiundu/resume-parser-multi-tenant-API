from django.test import TestCase
from django.contrib.auth import get_user_model
from resume.models import (
    Resume,
    Candidate,
    Skill,
    Experience,
    Education,
    Certification,
    Language,
)

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


def create_resume(tenant):
    """Helper to create a resume."""
    return Resume.objects.create(
        tenant=tenant,
        source_type="pdf",
    )


class ResumeModelsTest(TestCase):
    """Test to test all the system Models."""

    def setUp(self):
        self.tenant = create_tenant()
        self.resume = create_resume(self.tenant)

    def test_create_resume_successful(self):
        """Test creating a new resume."""
        resume = Resume.objects.create(
            tenant=self.tenant,
            source_type="pdf",
            raw_text="Sample resume text",
            status="pending",
        )
        self.assertEqual(
            str(resume), f"{self.tenant.email} - {resume.source_type} - {resume.status}"
        )
        self.assertEqual(resume.tenant, self.tenant)
        self.assertEqual(resume.source_type, "pdf")
        self.assertEqual(resume.raw_text, "Sample resume text")
        self.assertEqual(resume.status, "pending")

    def test_resume_status_transitions(self):
        """Test that status can move throught all states."""
        resume = Resume.objects.create(
            tenant=self.tenant,
            source_type="pdf",
        )

        for status in ["preprocessing", "done", "failed"]:
            resume.status = status
            resume.save()
            self.assertEqual(resume.status, status)

    def test_resume_cascade_deletes_with_tenant(self):
        """Test that resumes are deleted when tenant is deleted."""
        Resume.objects.create(
            tenant=self.tenant,
            source_type="pdf",
        )
        self.tenant.delete()
        self.assertEqual(Resume.objects.count(), 0)

    def test_create_candidate_successful(self):
        """Test that a candidate can be created and linked to a resume."""
        candidate = Candidate.objects.create(
            resume=self.resume, full_name="John Doe", email="john.doe@example.com"
        )
        self.assertEqual(candidate.resume, self.resume)
        self.assertEqual(candidate.full_name, "John Doe")
        self.assertEqual(candidate.email, "john.doe@example.com")
        self.assertEqual(str(candidate), f"John Doe - {self.resume.id}")

    def test_one_to_one_resume_candidate(self):
        """Test that each resume can only have one candidate."""
        Candidate.objects.create(resume=self.resume, full_name="John Doe")
        with self.assertRaises(Exception):
            Candidate.objects.create(resume=self.resume, full_name="Jane Smith")

    def test_candidate_cascades_with_resume_deletion(self):
        """Test that candidate is deleted when resume is deleted."""
        Candidate.objects.create(resume=self.resume, full_name="John Doe")
        self.resume.delete()
        self.assertEqual(Candidate.objects.count(), 0)

    def test_create_skill_successful(self):
        """Test that a skill can be created and linked to a resume."""
        skill = Skill.objects.create(
            resume=self.resume, name="Python", category="Programming"
        )
        self.assertEqual(skill.resume, self.resume)
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, "Programming")
        self.assertEqual(str(skill), f"Python - {self.resume.id}")

    def test_resume_can_have_multiple_skills(self):
        """Test that a resume can have many skills."""
        Skill.objects.create(resume=self.resume, name="Python")
        Skill.objects.create(resume=self.resume, name="Django")
        Skill.objects.create(resume=self.resume, name="PostgreSQL")
        self.assertEqual(self.resume.skills.count(), 3)

    def test_skill_cascades_with_resume_deletion(self):
        """Test that skills are deleted when resume is deleted."""
        Skill.objects.create(resume=self.resume, name="Python")
        self.resume.delete()
        self.assertEqual(Skill.objects.count(), 0)

    def test_create_experience_successful(self):
        """Test that an experience can be created and linked to a resume."""
        experience = Experience.objects.create(
            resume=self.resume,
            company="Safaricom",
            title="Backend Engineer",
            is_current=True,
        )
        self.assertEqual(experience.resume, self.resume)
        self.assertEqual(experience.company, "Safaricom")
        self.assertEqual(experience.title, "Backend Engineer")
        self.assertTrue(experience.is_current)
        self.assertEqual(
            str(experience), f"Backend Engineer at Safaricom - {self.resume.id}"
        )

    def test_experience_cascades_with_resume_deletion(self):
        """Test that experiences are deleted when resume is deleted."""
        Experience.objects.create(resume=self.resume, company="Safaricom")
        self.resume.delete()
        self.assertEqual(Experience.objects.count(), 0)

    def test_create_education_successful(self):
        """Test that an education record can be created and linked to a resume."""
        education = Education.objects.create(
            resume=self.resume,
            institution="University of Nairobi",
            degree="BSc Computer Science",
            field_of_study="Computer Science",
        )
        self.assertEqual(education.resume, self.resume)
        self.assertEqual(education.institution, "University of Nairobi")
        self.assertEqual(education.degree, "BSc Computer Science")
        self.assertEqual(
            str(education),
            f"BSc Computer Science at University of Nairobi - {self.resume.id}",
        )

    def test_education_cascades_with_resume_deletion(self):
        """Test that education records are deleted when resume is deleted."""
        Education.objects.create(
            resume=self.resume, institution="University of Nairobi"
        )
        self.resume.delete()
        self.assertEqual(Education.objects.count(), 0)

    def test_create_certification_successful(self):
        """Test that a certification can be created and linked to a resume."""
        certification = Certification.objects.create(
            resume=self.resume,
            name="AWS Solutions Architect",
            issuer="Amazon Web Services",
        )
        self.assertEqual(certification.resume, self.resume)
        self.assertEqual(certification.name, "AWS Solutions Architect")
        self.assertEqual(certification.issuer, "Amazon Web Services")
        self.assertEqual(
            str(certification), f"AWS Solutions Architect - {self.resume.id}"
        )

    def test_certification_cascades_with_resume_deletion(self):
        """Test that certifications are deleted when resume is deleted."""
        Certification.objects.create(resume=self.resume, name="AWS Solutions Architect")
        self.resume.delete()
        self.assertEqual(Certification.objects.count(), 0)

    def test_create_language_successful(self):
        """Test that a language can be created and linked to a resume."""
        language = Language.objects.create(
            resume=self.resume,
            name="Swahili",
            proficiency="Native",
        )
        self.assertEqual(language.resume, self.resume)
        self.assertEqual(language.name, "Swahili")
        self.assertEqual(language.proficiency, "Native")
        self.assertEqual(str(language), f"Swahili - {self.resume.id}")

    def test_language_cascades_with_resume_deletion(self):
        """Test that languages are deleted when resume is deleted."""
        Language.objects.create(resume=self.resume, name="Swahili")
        self.resume.delete()
        self.assertEqual(Language.objects.count(), 0)
