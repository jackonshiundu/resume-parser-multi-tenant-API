"""Celery Tasks form resume parsing."""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def parse_resume(self, resume_id):
    """Background tasks to parse a resume."""

    from .models import (
        Resume,
        Candidate,
        Skill,
        Experience,
        Education,
        Certification,
        Language,
    )
    from .extractors import extract_text
    from .ai import parse_resume_with_ai

    try:
        resume = Resume.objects.get(id)

        # updating the status to processing for the resume.
        resume.status = "processing"
        resume.save()

        # 1. Extract raw text.
        raw_text = extract_text(resume)
        resume.raw_text = raw_text
        resume.save()

        # 2. Send to Claude
        parsed_data = parse_resume_with_ai(raw_text)

        # 3. Save candidate info
        Candidate.objects.create(
            resume=resume,
            full_name=parsed_data.get("full_name"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            location=parsed_data.get("location"),
            summary=parsed_data.get("summary"),
        )

        # 4. Save skills
        for skill in parsed_data.get("skills", []):
            Skill.objects.create(
                resume=resume,
                name=skill.get("name"),
                category=skill.get("category"),
            )
        # 5. Save experience
        for exp in parsed_data.get("experience", []):
            Experience.objects.create(
                resume=resume,
                company=exp.get("company"),
                title=exp.get("title"),
                location=exp.get("location"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                is_current=exp.get("is_current", False),
                description=exp.get("description"),
                order=exp.get("order", 0),
            )

        # 6. Save education
        for edu in parsed_data.get("education", []):
            Education.objects.create(
                resume=resume,
                institution=edu.get("institution"),
                degree=edu.get("degree"),
                field_of_study=edu.get("field_of_study"),
                start_date=edu.get("start_date"),
                end_date=edu.get("end_date"),
                grade=edu.get("grade"),
                order=edu.get("order", 0),
            )

        # 7. Save certifications
        for cert in parsed_data.get("certifications", []):
            Certification.objects.create(
                resume=resume,
                name=cert.get("name"),
                issuer=cert.get("issuer"),
                issue_date=cert.get("issue_date"),
                expiry_date=cert.get("expiry_date"),
            )

        # 8. Save languages
        for lang in parsed_data.get("languages", []):
            Language.objects.create(
                resume=resume,
                name=lang.get("name"),
                proficiency=lang.get("proficiency"),
            )

        # save the resume as done
        resume.status = "done"
        resume.parsed_at = timezone.now()
        resume.save()

        logger.info(f"Resume {resume_id} parsed successfully.")

    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found, please try with a working resume.")

    except Exception as exc:
        logger.error(f"Resume {resume_id} failed: {str(exc)}")
        resume.status = "failed"
        resume.error_message = str(exc)

        resume.save()
        raise self.retry(exc=exc, countdown=60)
