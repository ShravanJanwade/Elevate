import re
import pdfplumber


SECTION_HEADERS = [
    "experience", "work experience", "professional experience", "employment",
    "education", "academic background",
    "skills", "technical skills", "core competencies", "technologies",
    "projects", "personal projects", "academic projects",
    "summary", "objective", "profile", "about",
    "certifications", "certificates",
    "awards", "achievements", "honors",
    "publications",
    "volunteer", "volunteering",
    "languages",
    "interests", "hobbies",
]

SECTION_PATTERN = re.compile(
    r"^\s*(" + "|".join(re.escape(h) for h in SECTION_HEADERS) + r")\s*:?\s*$",
    re.IGNORECASE,
)


def extract_text_from_pdf(pdf_path):
    """Pull all text out of a PDF file, page by page."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
    return "\n".join(full_text)


def _classify_section(header_text):
    """Map a raw header string to a normalized section name."""
    header_lower = header_text.strip().lower()

    if header_lower in ("experience", "work experience", "professional experience", "employment"):
        return "experience"
    if header_lower in ("education", "academic background"):
        return "education"
    if header_lower in ("skills", "technical skills", "core competencies", "technologies"):
        return "skills"
    if header_lower in ("projects", "personal projects", "academic projects"):
        return "projects"
    if header_lower in ("summary", "objective", "profile", "about"):
        return "summary"
    if header_lower in ("certifications", "certificates"):
        return "certifications"

    return header_lower


def parse_resume(text):
    """
    Split resume text into structured sections.

    Returns a dict like:
    {
        "summary": "...",
        "experience": "...",
        "skills": "...",
        "education": "...",
        "projects": "...",
        "raw_text": "...",
        "bullet_points": [...]
    }
    """
    sections = {}
    current_section = "header"
    current_lines = []

    for line in text.split("\n"):
        match = SECTION_PATTERN.match(line)
        if match:
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = _classify_section(match.group(1))
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    bullet_points = extract_bullet_points(text)

    sections["raw_text"] = text
    sections["bullet_points"] = bullet_points

    return sections


def extract_bullet_points(text):
    """
    Grab all bullet-point lines from the resume text.
    Handles common bullet markers: -, *, •, >, and numbered bullets like "1."
    """
    bullet_pattern = re.compile(r"^\s*[-*•>]\s+(.+)$|^\s*\d+[.)]\s+(.+)$")
    bullets = []

    for line in text.split("\n"):
        m = bullet_pattern.match(line)
        if m:
            content = m.group(1) or m.group(2)
            content = content.strip()
            if len(content) > 10:
                bullets.append(content)

    return bullets


def parse_resume_from_pdf(pdf_path):
    """Convenience wrapper: read PDF then parse it."""
    text = extract_text_from_pdf(pdf_path)
    return parse_resume(text)
