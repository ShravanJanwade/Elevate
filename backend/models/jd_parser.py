"""
Elevate – JD Parser
====================
Parses a job description into structured requirements:
  - Required skills vs. preferred/nice-to-have
  - Responsibilities (action items the role does)
  - Education requirements (degree level, field)
  - Experience requirements (years, seniority)
  - Soft skills vs. hard/technical skills

A recruiter doesn't score all JD requirements equally.
"Must have 5 years Python" ≠ "Nice to have: Kubernetes exposure"
This parser assigns priority weights to each requirement.
"""

import re
from typing import List, Dict, Optional
from .skill_taxonomy import get_taxonomy


# ============================================================================
# SECTION CLASSIFICATION PATTERNS
# ============================================================================

# Patterns that indicate "required" sections
REQUIRED_PATTERNS = [
    re.compile(r"(?:requirements|required|must[\s-]have|qualifications|minimum)", re.I),
    re.compile(r"(?:what you(?:'ll|\s+will) need|what we(?:'re| are) looking for)", re.I),
    re.compile(r"(?:essential|mandatory|core requirements)", re.I),
]

# Patterns that indicate "preferred/nice-to-have" sections
PREFERRED_PATTERNS = [
    re.compile(r"(?:preferred|nice[\s-]to[\s-]have|bonus|plus|desired)", re.I),
    re.compile(r"(?:additional|extra|good[\s-]to[\s-]have)", re.I),
    re.compile(r"(?:it(?:'s| is) a plus|would be a plus|not required)", re.I),
]

# Patterns that indicate responsibilities
RESPONSIBILITY_PATTERNS = [
    re.compile(r"(?:responsibilities|what you(?:'ll|\s+will) do|duties)", re.I),
    re.compile(r"(?:role overview|about the role|the role|day[\s-]to[\s-]day)", re.I),
    re.compile(r"(?:key tasks|scope|you will|you'll)", re.I),
]

# Patterns for education requirements
EDUCATION_PATTERNS = [
    re.compile(r"(?:bachelor|master|phd|doctorate|bs|ms|ba|ma|b\.?s\.?|m\.?s\.?)", re.I),
    re.compile(r"(?:computer science|software engineering|information technology|IT)", re.I),
    re.compile(r"(?:degree|diploma|certification|enrolled|returning to school)", re.I),
]

# Experience level indicators
EXPERIENCE_PATTERNS = [
    re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", re.I),
    re.compile(r"(?:senior|sr\.?|lead|principal|staff)\b", re.I),
    re.compile(r"(?:junior|jr\.?|entry[\s-]level|intern|associate|new grad)", re.I),
    re.compile(r"(?:mid[\s-]?level|intermediate)", re.I),
]

# "Is a plus" / "nice to have" modifiers on specific lines
PLUS_MODIFIER = re.compile(r"(?:is a plus|nice to have|preferred|bonus|desired|a\s+plus)\b", re.I)


# ============================================================================
# PARSED REQUIREMENT STRUCTURE
# ============================================================================

class JDRequirement:
    """A single parsed requirement from the JD."""

    def __init__(
        self,
        text: str,
        category: str = "general",
        priority: float = 1.0,
        skills: List[str] = None,
        is_technical: bool = True,
    ):
        self.text = text
        self.category = category       # "required", "preferred", "responsibility", "education"
        self.priority = priority       # 1.0 = must have, 0.5 = nice to have, etc.
        self.skills = skills or []     # Extracted skill names
        self.is_technical = is_technical

    def to_dict(self):
        return {
            "text": self.text,
            "category": self.category,
            "priority": self.priority,
            "skills": self.skills,
            "is_technical": self.is_technical,
        }


class ParsedJD:
    """Fully parsed job description."""

    def __init__(self):
        self.title: str = ""
        self.seniority: str = "mid"  # "intern", "junior", "mid", "senior", "lead"
        self.years_experience: Optional[int] = None
        self.education_level: str = ""  # "bachelor", "master", "phd"
        self.education_field: str = ""

        self.required_skills: List[str] = []
        self.preferred_skills: List[str] = []
        self.all_skills: List[str] = []

        self.requirements: List[JDRequirement] = []
        self.responsibilities: List[JDRequirement] = []

        self.technical_requirements: List[JDRequirement] = []
        self.soft_requirements: List[JDRequirement] = []

        self.raw_text: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "seniority": self.seniority,
            "years_experience": self.years_experience,
            "education_level": self.education_level,
            "education_field": self.education_field,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "all_skills": self.all_skills,
            "num_requirements": len(self.requirements),
            "num_responsibilities": len(self.responsibilities),
        }


# ============================================================================
# JD PARSER
# ============================================================================

class JDParser:
    """Parse a job description into structured requirements."""

    def __init__(self):
        self.taxonomy = get_taxonomy()

    def parse(self, jd_text: str) -> ParsedJD:
        """Parse a job description text into structured components."""
        parsed = ParsedJD()
        parsed.raw_text = jd_text

        lines = [line.strip() for line in jd_text.split("\n") if line.strip()]

        # Step 1: Extract title (usually first meaningful line)
        parsed.title = self._extract_title(lines)

        # Step 2: Detect seniority level
        parsed.seniority = self._detect_seniority(jd_text)

        # Step 3: Extract years of experience
        parsed.years_experience = self._extract_experience_years(jd_text)

        # Step 4: Extract education requirements
        parsed.education_level, parsed.education_field = self._extract_education(jd_text)

        # Step 5: Classify each line/bullet into categories
        current_section = "general"
        for line in lines:
            # Check if this line is a section header
            new_section = self._classify_section_header(line)
            if new_section:
                current_section = new_section
                continue

            # Skip very short lines or obvious headers
            if len(line) < 10 or line.endswith(":"):
                continue

            # Check for per-line modifiers
            is_preferred = bool(PLUS_MODIFIER.search(line))

            # Extract skills from this line
            skills = self._extract_skills_from_line(line)

            # Determine if technical or soft
            is_technical = self._is_technical_line(line, skills)

            # Assign priority based on section + modifiers
            if current_section == "preferred" or is_preferred:
                priority = 0.5
                category = "preferred"
            elif current_section == "responsibility":
                priority = 0.7
                category = "responsibility"
            elif current_section == "education":
                priority = 0.4
                category = "education"
            else:
                priority = 1.0
                category = "required"

            req = JDRequirement(
                text=line,
                category=category,
                priority=priority,
                skills=skills,
                is_technical=is_technical,
            )

            if category == "responsibility":
                parsed.responsibilities.append(req)
            else:
                parsed.requirements.append(req)

            if is_technical:
                parsed.technical_requirements.append(req)
            else:
                parsed.soft_requirements.append(req)

        # Step 6: Aggregate all skills
        all_found = set()
        required_found = set()
        preferred_found = set()

        for req in parsed.requirements + parsed.responsibilities:
            for skill in req.skills:
                canonical = self.taxonomy.canonicalize(skill)
                all_found.add(canonical)
                if req.category == "preferred" or req.priority <= 0.5:
                    preferred_found.add(canonical)
                else:
                    required_found.add(canonical)

        parsed.all_skills = sorted(all_found)
        parsed.required_skills = sorted(required_found - preferred_found)
        parsed.preferred_skills = sorted(preferred_found)

        return parsed

    def _extract_title(self, lines: List[str]) -> str:
        """Extract job title from the first few lines."""
        title_patterns = [
            re.compile(r"(?:job title|position|role)[\s:]+(.+)", re.I),
        ]
        for line in lines[:5]:
            for pattern in title_patterns:
                m = pattern.search(line)
                if m:
                    return m.group(1).strip()

            # Heuristic: short line that looks like a title
            if 5 < len(line) < 80 and not line.endswith(":"):
                words = line.split()
                title_words = ["engineer", "developer", "manager", "analyst",
                               "designer", "architect", "scientist", "intern",
                               "director", "lead", "specialist", "consultant"]
                if any(w.lower() in title_words for w in words):
                    return line
        return ""

    def _detect_seniority(self, text: str) -> str:
        """Detect the seniority level of the role."""
        text_lower = text.lower()

        if re.search(r"\b(?:intern|internship)\b", text_lower):
            return "intern"
        if re.search(r"\b(?:junior|jr\.?|entry[\s-]level|new[\s-]grad|associate)\b", text_lower):
            return "junior"
        if re.search(r"\b(?:senior|sr\.?|principal|staff|distinguished)\b", text_lower):
            return "senior"
        if re.search(r"\b(?:lead|manager|head|director|vp)\b", text_lower):
            return "lead"
        return "mid"

    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience requirement."""
        m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", text, re.I)
        if m:
            return int(m.group(1))
        return None

    def _extract_education(self, text: str):
        """Extract education level and field."""
        level = ""
        field = ""

        if re.search(r"\b(?:phd|doctorate|doctoral)\b", text, re.I):
            level = "phd"
        elif re.search(r"\b(?:master|ms|m\.s\.|ma|m\.a\.|mba|master's)\b", text, re.I):
            level = "master"
        elif re.search(r"\b(?:bachelor|bs|b\.s\.|ba|b\.a\.|be|b\.e\.|b\.tech|undergraduate)\b", text, re.I):
            level = "bachelor"

        if re.search(r"\b(?:computer\s+science|cs\b|comp\s+sci)", text, re.I):
            field = "computer science"
        elif re.search(r"\b(?:software\s+engineering)", text, re.I):
            field = "software engineering"
        elif re.search(r"\b(?:information\s+technology|IT\b)", text, re.I):
            field = "information technology"
        elif re.search(r"\b(?:engineering|stem|technical)", text, re.I):
            field = "engineering"

        return level, field

    def _classify_section_header(self, line: str) -> Optional[str]:
        """Check if a line is a section header and return the section type."""
        for p in REQUIRED_PATTERNS:
            if p.search(line):
                return "required"
        for p in PREFERRED_PATTERNS:
            if p.search(line):
                return "preferred"
        for p in RESPONSIBILITY_PATTERNS:
            if p.search(line):
                return "responsibility"

        # Check education
        if re.search(r"\beducation\b", line, re.I) and len(line) < 30:
            return "education"

        return None

    def _extract_skills_from_line(self, line: str) -> List[str]:
        """Extract known skills from a line using the taxonomy."""
        line_lower = line.lower()
        found = []
        found_canonical = set()

        # Check all known skills and aliases
        for canonical in self.taxonomy._canonical_set:
            if canonical in found_canonical:
                continue

            # Check canonical
            pattern = r"\b" + re.escape(canonical) + r"\b"
            if re.search(pattern, line_lower):
                found.append(canonical)
                found_canonical.add(canonical)
                continue

            # Check aliases
            data = SKILL_GRAPH.get(canonical, {})
            for alias in data.get("aliases", []):
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, line_lower):
                    found.append(canonical)
                    found_canonical.add(canonical)
                    break

        return found

    def _is_technical_line(self, line: str, skills: List[str]) -> bool:
        """Determine if a line describes a technical vs. soft skill requirement."""
        if skills:
            technical_domains = {"programming", "frontend", "backend", "cloud",
                                "devops", "data", "ai_ml", "architecture", "engineering"}
            for skill in skills:
                domain = self.taxonomy.get_domain(skill)
                if domain in technical_domains:
                    return True

        # Heuristic: check for soft skill keywords
        soft_keywords = [
            "communicat", "collaborat", "team", "leadership", "present",
            "document", "write", "fluent", "english", "stakeholder",
        ]
        line_lower = line.lower()
        soft_count = sum(1 for kw in soft_keywords if kw in line_lower)
        return soft_count < 2


# Import SKILL_GRAPH for the parser
from .skill_taxonomy import SKILL_GRAPH
# refactor
