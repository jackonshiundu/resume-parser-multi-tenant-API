"""Celery Tasks for resume parsing."""
from celery import shared_task
from django.utils import timezone
import logging
from .extractors import extract_text
from .ai import parse_resume_with_ai

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def parse_resume(self, resume_id):
    """Background task to parse a resume."""

    from .models import (
        Resume,
        Candidate,
        Skill,
        Experience,
        Education,
        Certification,
        Language,
    )

    # Fetch resume separately so we can always reference it in except block
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found.")
        return

    try:
        # Update status to processing
        Resume.objects.filter(id=resume_id).update(status="processing")
        resume.refresh_from_db()

        # 1. Extract raw text
        raw_text = extract_text(resume)
        Resume.objects.filter(id=resume_id).update(raw_text=raw_text)
        resume.refresh_from_db()

        # 2. Send to Claude
        parsed_data = parse_resume_with_ai(raw_text)

        # 3. Save candidate info
        Candidate.objects.get_or_create(
            resume=resume,
            defaults={
                "full_name": parsed_data.get("full_name"),
                "email": parsed_data.get("email"),
                "phone": parsed_data.get("phone"),
                "location": parsed_data.get("location"),
                "summary": parsed_data.get("summary"),
            }
        )
        # 4. Save skills
        for skill in parsed_data.get("skills", []):
            Skill.objects.get_or_create(
                resume=resume,
                name=skill.get("name"),
                defaults={
                    "category": skill.get("category"),
                }
            )

        # 5. Save experience
        for exp in parsed_data.get("experience", []):
            Experience.objects.get_or_create(
                resume=resume,
                company=exp.get("company"),
                title=exp.get("title"),
                start_date=exp.get("start_date"),
                defaults={
                    "location": exp.get("location"),
                    "end_date": exp.get("end_date"),
                    "is_current": exp.get("is_current", False),
                    "description": exp.get("description"),
                    "order": exp.get("order", 0),
                }
            )

        # 6. Save education
        for edu in parsed_data.get("education", []):
            Education.objects.get_or_create(
                resume=resume,
                institution=edu.get("institution"),
                degree=edu.get("degree"),
                defaults={
                    "field_of_study": edu.get("field_of_study"),
                    "start_date": edu.get("start_date"),
                    "end_date": edu.get("end_date"),
                    "grade": edu.get("grade"),
                    "order": edu.get("order", 0),
                }
            )

        # 7. Save certifications
        for cert in parsed_data.get("certifications", []):
            Certification.objects.get_or_create(
                resume=resume,
                name=cert.get("name"),
                issuer=cert.get("issuer"),
                issue_date=cert.get("issue_date"),
                expiry_date=cert.get("expiry_date"),
                defaults={
                    "credential_id": cert.get("credential_id"),
                }
            )

        # 8. Save languages
        for lang in parsed_data.get("languages", []):
            Language.objects.get_or_create(
                resume=resume,
                name=lang.get("name"),
                defaults={
                    "proficiency": lang.get("proficiency"),
                }
            )

        # Mark as done
        Resume.objects.filter(id=resume_id).update(
            status="done", parsed_at=timezone.now()
        )

        logger.info(f"Resume {resume_id} parsed successfully.")

    except Exception as exc:
        logger.error(f"Resume {resume_id} failed: {str(exc)}")
        Resume.objects.filter(id=resume_id).update(
            status="failed", error_message=str(exc)
        )
        raise self.retry(exc=exc, countdown=60)
