"""Claudi AI integration for resume parsing."""
import anthropic
import json
from django.conf import settings


def parse_resume_with_ai(raw_text):
    """Send raw resume text to Claude and get staructured JSON back."""

    client = anthropic.Athropic(api=settings.ANTHROPIC_API_KEY)
    prompt = f"""
You are an expert resume parser. Extract all information from the resume text below.
Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Return exactly this structure:
{{
    "full_name": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "summary": "string or null",
    "skills": [
        {{"name": "string", "category": "string or null"}}
    ],
    "experience": [
        {{
            "company": "string or null",
            "title": "string or null",
            "location": "string or null",
            "start_date": "YYYY-MM or null",
            "end_date": "YYYY-MM or null",
            "is_current": true or false,
            "description": "string or null",
            "order": 1
        }}
    ],
    "education": [
        {{
            "institution": "string or null",
            "degree": "string or null",
            "field_of_study": "string or null",
            "start_date": "YYYY-MM or null",
            "end_date": "YYYY-MM or null",
            "grade": "string or null",
            "order": 1
        }}
    ],
    "certifications": [
        {{
            "name": "string",
            "issuer": "string or null",
            "issue_date": "YYYY-MM or null",
            "expiry_date": "YYYY-MM or null"
        }}
    ],
    "languages": [
        {{
            "name": "string",
            "proficiency": "string or null"
        }}
    ]
}}

Resume text:
{raw_text}
"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = message.content[0].text
    parsed_data = json.loads(response_text)
    return parsed_data
