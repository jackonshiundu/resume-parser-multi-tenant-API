"""
Serializers for the Resume API.
"""
from .models import (
    Candidate,
    Resume,
    Skill,
    Experience,
    Education,
    Certification,
    Language,
)
from rest_framework import serializers


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for Candidate objects."""

    class Meta:
        model = Candidate
        fields = ("id", "full_name", "email", "phone")
        read_only_fields = ("id",)


class SkillsSerializer(serializers.ModelSerializer):
    """Serializer for Skills objects."""

    class Meta:
        model = Skill
        fields = ("id", "name", "category")
        read_only_fields = ("id",)


class ExperienceSerializer(serializers.ModelSerializer):
    """Serializer for Experience objects."""

    class Meta:
        model = Experience
        fields = (
            "id",
            "company",
            "title",
            "location",
            "start_date",
            "end_date",
            "is_current",
            "description",
            "order",
        )
        read_only_fields = ("id",)


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = (
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "grade",
            "order",
        )


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ("id", "name", "issuer", "issue_date", "expiry_date")


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("id", "name", "proficiency")


class ResumeSubmitSerializer(serializers.ModelSerializer):
    """Serializer for submitting a resume file."""

    file = serializers.FileField(required=False)

    class Meta:
        model = Resume
        fields = ("source_type", "file", "raw_text", "linkedin_url")

    def validate(self, data):
        source = data.get("source_type")

        if source in ("pdf", "docx") and not data.get("file"):
            raise serializers.ValidationError(
                "File is required for PDF or DOCX source type."
            )

        if source == "text" and not data.get("raw_text"):
            raise serializers.ValidationError(
                "Raw text is required for text source type."
            )

        if source == "linkedin" and not data.get("linkedin_url"):
            raise serializers.ValidationError(
                "LinkedIn URL is required for linkedin source type."
            )

        return data

    def validate_file(self, value):
        allowed = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        if value.content_type not in allowed:
            raise serializers.ValidationError("Only PDF and DOCX files are allowed.")

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 5MB.")

        return value


class ResumeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing resumes."""

    candidate_name = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ("id", "source_type", "status", "created_at", "candidate_name")

    def get_candidate_name(self, obj):
        if hasattr(obj, "candidate"):
            return obj.candidate.full_name
        return None


class ResumeDetailsSerializer(serializers.ModelSerializer):
    """Full nested serializer for a parsed resume."""

    candidate = CandidateSerializer(read_only=True)
    skills = SkillsSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Resume
        fields = [
            "id",
            "source_type",
            "status",
            "error_message",
            "created_at",
            "parsed_at",
            "candidate",
            "skills",
            "experiences",
            "education",
            "certifications",
            "languages",
        ]
