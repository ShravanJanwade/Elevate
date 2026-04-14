"""
Elevate – Resume Parser
========================
Structural resume parsing:
  - PDF text extraction (pdfplumber)
  - Section detection (case-insensitive, flexible matching)
  - Header entity extraction (name, email, phone, LinkedIn)
  - Bullet point extraction with cleaning
  - Experience duration computation
"""

import re
import pdfplumber


# ---------------------------------------------------------------------------
# Section header patterns
# ---------------------------------------------------------------------------

SECTION_HEADERS = [
    "experience", "work experience", "professional experience", "employment",
    "employment history", "career history", "relevant experience",
    "education", "academic background", "academic history",
    "skills", "technical skills", "core competencies", "technologies",
    "key skills", "areas of expertise", "proficiencies", "tech stack",
    "projects", "personal projects", "academic projects", "side projects",
    "key projects", "selected projects",
    "summary", "objective", "profile", "professional summary",
    "career objective", "about", "about me", "executive summary",
    "certifications", "certificates", "professional certifications",
    "licenses and certifications",
    "awards", "achievements", "honors", "accomplishments",
    "publications", "research", "research publications",
    "volunteer", "volunteering", "volunteer experience",
    "community involvement",
    "languages", "language proficiency",
    "interests", "hobbies", "activities",
    "references",
]

# Build a pattern that matches section headers flexibly:
# - Case insensitive
# - Optional trailing colon, dash, pipe
# - May be ALL CAPS, Title Case, etc.
# - May have leading bullets or numbers
_HEADER_SET = set(h.lower() for h in SECTION_HEADERS)

SECTION_PATTERN = re.compile(
    r"^\s*(?:[-•*]?\s*)"
    r"(" + "|".join(re.escape(h) for h in SECTION_HEADERS) + r")"
    r"\s*[:\-|]?\s*$",
    re.IGNORECASE,
)

# Also match ALL CAPS versions
SECTION_PATTERN_CAPS = re.compile(
    r"^\s*([A-Z][A-Z &/]{3,})\s*[:\-|]?\s*$"
)


# ---------------------------------------------------------------------------
# Entity extraction from header
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
)
LINKEDIN_PATTERN = re.compile(
    r"(?:linkedin\.com/in/|linkedin:\s*)([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(
    r"https?://[^\s,;]+|(?:github|portfolio|website)\.com/[^\s,;]+",
    re.IGNORECASE,
)

# Date patterns for experience duration
DATE_PATTERN = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
    r"\d{1,2}/\d{4}|"
    r"\d{4})\s*[-–—to]+\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|"
    r"\d{1,2}/\d{4}|"
    r"\d{4}|"
    r"[Pp]resent|[Cc]urrent)",
    re.IGNORECASE,
)


def extract_entities(text: str) -> dict:
    """Extract structured entities from resume header/text."""
    entities = {}

    # Email
    emails = EMAIL_PATTERN.findall(text)
    if emails:
        entities["email"] = emails[0]

    # Phone
    phones = PHONE_PATTERN.findall(text)
    if phones:
        entities["phone"] = phones[0].strip()

    # LinkedIn
    linkedin = LINKEDIN_PATTERN.findall(text)
    if linkedin:
        entities["linkedin"] = linkedin[0]

    # URLs
    urls = URL_PATTERN.findall(text)
    if urls:
        entities["urls"] = urls[:3]

    # Try to extract name (first non-empty line that isn't email/phone/url)
    lines = text.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if not line or len(line) < 2 or len(line) > 60:
            continue
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue
        if URL_PATTERN.search(line):
            continue
        if any(c.isdigit() for c in line) and len(line) < 10:
            continue
        # Likely the name
        entities["name"] = line
        break

    return entities


# ---------------------------------------------------------------------------
# Deep Heuristic Entity Augmentation
# ---------------------------------------------------------------------------

def _augment_entities(entities: dict, sections: dict):
    """Augment basic header entities with deep heuristic scanning on education/experience."""
    # 1. Expand URLs
    urls = entities.get("urls", [])
    for u in urls:
        ul = u.lower()
        if "github" in ul:
            entities["github_link"] = u
        elif "leetcode" in ul:
            entities["leetcode_link"] = u

    # 2. Extract University
    edu_text = sections.get("education", "")
    if edu_text:
        for line in edu_text.split("\n"):
            line_str = line.strip()
            if len(line_str) > 5 and re.search(r"(university|college|institute|school|academy)", line_str, re.IGNORECASE):
                # Strip dates cleanly
                clean_uni = re.sub(DATE_PATTERN, '', line_str).strip()
                clean_uni = re.sub(r'[^A-Za-z\s,.-]', '', clean_uni).strip(", .-")
                if clean_uni:
                    entities["university"] = clean_uni
                    break

    # 3. Extract Core Experience Metadata + all companies list
    exp_text = sections.get("experience", "")
    loc_pattern = r"\b([A-Z][a-zA-Z\s.-]+,\s*[A-Z]{2})\b"
    companies_found = []

    if exp_text:
        lines = [x.strip() for x in exp_text.split("\n") if x.strip()]
        first_match = True
        for i, line in enumerate(lines):
            date_match = DATE_PATTERN.search(line)
            if not date_match:
                continue

            if first_match:
                entities["years"] = date_match.group(0).strip()

            clean_line = re.sub(DATE_PATTERN, '', line).strip(' |,-()')

            # Strip location from the line
            loc1 = re.search(loc_pattern, line)
            if loc1:
                if first_match:
                    entities["location"] = loc1.group(1).strip()
                clean_line = re.sub(loc_pattern, '', clean_line).strip(' |,-')
            elif first_match and i > 0 and re.search(loc_pattern, lines[i-1]):
                entities["location"] = re.search(loc_pattern, lines[i-1]).group(1).strip()

            # Determine if clean_line is a role or company
            is_role = re.search(
                r"(engineer|developer|manager|analyst|associate|consultant|"
                r"lead|director|intern|trainee|scientist|architect|designer|"
                r"officer|specialist|coordinator|executive|head|vp|vice president)",
                clean_line, re.I
            )
            company_candidate = None
            if is_role:
                if first_match and "role" not in entities:
                    entities["role"] = clean_line
                # Company is likely on the previous or next non-date line
                if i > 0 and not DATE_PATTERN.search(lines[i-1]):
                    company_candidate = re.sub(loc_pattern, '', lines[i-1]).strip(' |,-')
                elif i + 1 < len(lines) and not DATE_PATTERN.search(lines[i+1]):
                    company_candidate = re.sub(loc_pattern, '', lines[i+1]).strip(' |,-')
            elif len(clean_line) > 3:
                company_candidate = clean_line
                if first_match and "company" not in entities:
                    entities["company"] = clean_line
                # Role may be on adjacent line
                if first_match and "role" not in entities and i + 1 < len(lines):
                    nxt = lines[i+1]
                    if not DATE_PATTERN.search(nxt) and not nxt.startswith("-"):
                        entities["role"] = re.sub(loc_pattern, '', nxt).strip(' |,-')

            if company_candidate:
                # Clean noise and de-duplicate
                c = re.sub(r'[|•·–—]', '', company_candidate).strip()
                c = re.sub(r'\s+', ' ', c).strip()
                if (len(c) > 2 and c.lower() not in ("nan", "present", "current")
                        and c not in companies_found):
                    companies_found.append(c)

            first_match = False

    if companies_found:
        entities["companies"] = companies_found
        if "company" not in entities:
            entities["company"] = companies_found[0]

# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Pull all text out of a PDF file, page by page."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)

    text = "\n".join(full_text)

    # If pdfplumber returned very little text, try extracting from tables
    if len(text.strip()) < 50:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            cells = [str(c) for c in row if c]
                            full_text.append(" | ".join(cells))
        text = "\n".join(full_text)

    return text


# ---------------------------------------------------------------------------
# Section classification
# ---------------------------------------------------------------------------

def _classify_section(header_text: str) -> str:
    """Map a raw header string to a normalized section name."""
    header_lower = header_text.strip().lower()

    # Experience variants
    if header_lower in ("experience", "work experience", "professional experience",
                        "employment", "employment history", "career history",
                        "relevant experience"):
        return "experience"

    # Education variants
    if header_lower in ("education", "academic background", "academic history"):
        return "education"

    # Skills variants
    if header_lower in ("skills", "technical skills", "core competencies",
                        "technologies", "key skills", "areas of expertise",
                        "proficiencies", "tech stack"):
        return "skills"

    # Projects variants
    if header_lower in ("projects", "personal projects", "academic projects",
                        "side projects", "key projects", "selected projects"):
        return "projects"

    # Summary variants
    if header_lower in ("summary", "objective", "profile", "professional summary",
                        "career objective", "about", "about me", "executive summary"):
        return "summary"

    # Certifications
    if header_lower in ("certifications", "certificates",
                        "professional certifications",
                        "licenses and certifications"):
        return "certifications"

    # Awards
    if header_lower in ("awards", "achievements", "honors", "accomplishments"):
        return "awards"

    # Publications
    if header_lower in ("publications", "research", "research publications"):
        return "publications"

    # Volunteer
    if header_lower in ("volunteer", "volunteering", "volunteer experience",
                        "community involvement"):
        return "volunteer"

    return header_lower


def _is_section_header(line: str) -> str | None:
    """
    Check if a line is a section header.
    Returns normalized section name or None.
    """
    stripped = line.strip()
    if not stripped:
        return None

    # Check standard pattern
    match = SECTION_PATTERN.match(stripped)
    if match:
        return _classify_section(match.group(1))

    # Check ALL CAPS pattern
    caps_match = SECTION_PATTERN_CAPS.match(stripped)
    if caps_match:
        header_text = caps_match.group(1).strip().lower()
        if header_text in _HEADER_SET:
            return _classify_section(header_text)
        # Fuzzy match for ALL CAPS headers
        for known in _HEADER_SET:
            if known in header_text or header_text in known:
                return _classify_section(known)

    return None


# ---------------------------------------------------------------------------
# Main resume parser
# ---------------------------------------------------------------------------

def parse_resume(text: str) -> dict:
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
        "bullet_points": [...],
        "entities": {...},
    }
    """
    sections = {}
    current_section = "header"
    current_lines = []

    for line in text.split("\n"):
        section_name = _is_section_header(line)
        if section_name:
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    # If section already exists, append to it
                    if current_section in sections:
                        sections[current_section] += "\n" + content
                    else:
                        sections[current_section] = content
            current_section = section_name
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            if current_section in sections:
                sections[current_section] += "\n" + content
            else:
                sections[current_section] = content

    bullet_points = extract_bullet_points(text)
    entities = extract_entities(sections.get("header", text[:500]))

    # Augment unstructured text with mapped data
    _augment_entities(entities, sections)

    sections["raw_text"] = text
    sections["bullet_points"] = bullet_points
    sections["entities"] = entities

    return sections


# ---------------------------------------------------------------------------
# Bullet point extraction
# ---------------------------------------------------------------------------

def extract_bullet_points(text: str) -> list:
    """
    Grab all bullet-point lines from the resume text.
    Handles common bullet markers: -, *, •, >, ▪, ▸, ◦, and numbered bullets.
    Also extracts indented lines that look like achievements.
    """
    bullet_pattern = re.compile(
        r"^\s*[-*•▪▸◦⁃›»>]\s+(.+)$|"    # Symbol bullets
        r"^\s*\d+[.)]\s+(.+)$|"            # Numbered bullets  
        r"^\s*[a-z]\)\s+(.+)$"             # Lettered bullets
    )

    # Achievement pattern: lines starting with action verbs
    achievement_pattern = re.compile(
        r"^\s{2,}((?:Developed|Built|Led|Managed|Created|Designed|"
        r"Implemented|Engineered|Optimized|Reduced|Increased|Improved|"
        r"Spearheaded|Architected|Streamlined|Automated|Delivered|"
        r"Launched|Drove|Established|Initiated|Coordinated|Collaborated|"
        r"Analyzed|Researched|Maintained|Wrote|Configured|Deployed|"
        r"Migrated|Integrated|Tested|Debugged|Mentored|Trained|"
        r"Conducted|Performed|Executed|Facilitated|Oversaw|Directed|"
        r"Supervised|Negotiated|Secured|Achieved|Generated|Produced|"
        r"Published|Presented|Proposed|Recommended).+)$",
        re.IGNORECASE,
    )

    bullets = []
    seen = set()

    for line in text.split("\n"):
        content = None

        m = bullet_pattern.match(line)
        if m:
            content = m.group(1) or m.group(2) or m.group(3)
        else:
            am = achievement_pattern.match(line)
            if am:
                content = am.group(1)

        if content:
            content = content.strip()
            # Filter too short or too long
            if 10 < len(content) < 500:
                # Deduplicate
                key = content.lower()[:50]
                if key not in seen:
                    seen.add(key)
                    bullets.append(content)

    return bullets


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def parse_resume_from_pdf(pdf_path: str) -> dict:
    """Convenience wrapper: read PDF then parse it."""
    text = extract_text_from_pdf(pdf_path)
    return parse_resume(text)
# added parser setup
# fix date parsing
# fix layout parsing bugs
# docx support
