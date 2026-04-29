"""AI integration for resume parsing.
Supports Groq (default), Anthropic, and Gemini.
Uncomment the relevant section to switch providers.
"""
import json
from django.conf import settings
from groq import Groq


def parse_resume_with_ai(raw_text):
    """Send raw resume text to AI and get structured JSON back."""

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
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null",
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
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null",
            "grade": "string or null",
            "order": 1
        }}
    ],
    "certifications": [
        {{
            "name": "string",
            "issuer": "string or null",
            "issue_date": "YYYY-MM-DD or null",
            "expiry_date": "YYYY-MM-DD or null"
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

    # ─── GROQ (Default — free tier available at console.groq.com) ─────────────

    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert resume parser. Return valid JSON only. No markdown, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    response_text = response.choices[0].message.content
    return json.loads(response_text)

    # ─── ANTHROPIC (Uncomment to use Claude) ──────────────────────────────────
    # Requires: pip install anthropic
    # Add to .env: ANTHROPIC_API_KEY=sk-ant-your-key-here
    #
    # import anthropic
    # client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    # message = client.messages.create(
    #     model="claude-haiku-4-5-20251001",
    #     max_tokens=2000,
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # response_text = message.content[0].text
    # return json.loads(response_text)
