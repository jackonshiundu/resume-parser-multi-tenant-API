"""Function to extract raw test from dirrent file types."""

import pdfplumber
import docx


def extract_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text.strip()


def extract_from_docx(file_path):
    """Extract text from a DOCX file."""
    doc = docx.Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text.strip()


def extract_from_text(raw_text):
    """Return plain text as is."""
    return raw_text.strip()


def extract_from_linkedin(linkedin_url):
    """Pass LinkedIn URL as conext to cloude."""
    return f"LinkedIn Profile URL: {linkedin_url}\nPlease extract whatever \
    information is available from this LinkedIn profile URL. "


def extract_text(resume):
    """Route to the correct extractor based on source type."""
    if resume.source_type == "pdf":
        return extract_from_pdf(resume.file.path)
    elif resume.source_type == "docx":
        return extract_from_docx(resume.file.path)
    elif resume.source_type == "text":
        return extract_from_text(resume.raw_text)
    elif resume.source_type == "linkedin":
        return extract_from_linkedin(resume.linkedin_url)
    else:
        raise ValueError(f"Unsupported source type: {resume.source_type}")
