"""
Elevate – Education Scorer
============================
Evaluates how well the candidate's education matches the JD requirements:

  - Degree level match (bachelor's, master's, PhD)
  - Field relevance (CS vs. unrelated)
  - Currently enrolled status (for intern roles)
  - GPA if available (above-threshold bonus)
"""

import re
from typing import Dict, Optional


# Education field relevance mapping
FIELD_RELEVANCE = {
    # Primary CS/tech fields → 1.0
    "computer science": 1.0,
    "software engineering": 1.0,
    "computer engineering": 1.0,
    "information technology": 0.9,
    "information systems": 0.85,
    "data science": 0.9,
    "artificial intelligence": 0.95,
    "cybersecurity": 0.85,
    "information security": 0.85,

    # Adjacent engineering fields → 0.6 - 0.8
    "electrical engineering": 0.7,
    "electronics": 0.65,
    "mechanical engineering": 0.5,
    "industrial engineering": 0.5,
    "engineering": 0.6,
    "mathematics": 0.75,
    "statistics": 0.7,
    "physics": 0.6,
    "applied mathematics": 0.75,

    # Business/other → 0.2 - 0.4
    "business": 0.3,
    "economics": 0.35,
    "finance": 0.3,
    "marketing": 0.2,
    "communications": 0.2,
}

DEGREE_LEVELS = {
    "phd": 4,
    "doctorate": 4,
    "master": 3,
    "bachelor": 2,
    "associate": 1,
}


class EducationScorer:
    """Score education section against JD requirements."""

    def score(
        self,
        resume_sections: Dict,
        jd_education_level: str = "",
        jd_education_field: str = "",
        jd_seniority: str = "mid",
    ) -> Dict:
        """
        Evaluate education fit.

        Returns:
          - score (0-100)
          - degree_match: str
          - field_match: str
          - details: dict
        """
        education_text = resume_sections.get("education", "")
        if not education_text:
            education_text = resume_sections.get("raw_text", "")[:1000]

        # Extract what we can from resume education
        resume_degree = self._detect_degree_level(education_text)
        resume_field = self._detect_field(education_text)
        resume_gpa = self._detect_gpa(education_text)
        is_current_student = self._detect_current_student(education_text)

        # Calculate degree level match
        degree_score = self._score_degree_level(resume_degree, jd_education_level)

        # Calculate field match
        field_score = self._score_field(resume_field, jd_education_field)

        # Bonuses
        gpa_bonus = 0
        if resume_gpa and resume_gpa >= 3.5:
            gpa_bonus = 10
        elif resume_gpa and resume_gpa >= 3.0:
            gpa_bonus = 5

        student_bonus = 0
        if is_current_student and jd_seniority in ("intern", "junior"):
            student_bonus = 10

        # Combined score
        overall = (
            degree_score * 0.5 +
            field_score * 0.4 +
            gpa_bonus +
            student_bonus
        )
        overall = min(100, max(0, overall))

        return {
            "score": round(overall, 1),
            "resume_degree": resume_degree,
            "resume_field": resume_field,
            "resume_gpa": resume_gpa,
            "is_current_student": is_current_student,
            "degree_match": self._degree_match_label(resume_degree, jd_education_level),
            "field_match": self._field_match_label(resume_field, jd_education_field),
        }

    def _detect_degree_level(self, text: str) -> str:
        text_lower = text.lower()
        if re.search(r"\b(?:ph\.?d|doctorate|doctoral)\b", text_lower):
            return "phd"
        if re.search(r"\b(?:master|m\.?s\.?|m\.?a\.?|mba|m\.?tech|m\.?eng)\b", text_lower):
            return "master"
        if re.search(r"\b(?:bachelor|b\.?s\.?|b\.?a\.?|b\.?tech|b\.?e\.?|b\.?eng|undergraduate)\b", text_lower):
            return "bachelor"
        if re.search(r"\b(?:associate|a\.?s\.?|a\.?a\.?)\b", text_lower):
            return "associate"
        # Check generic "degree" mentions
        if re.search(r"\bdegree\b", text_lower):
            return "bachelor"  # Assume bachelor if unspecified
        return ""

    def _detect_field(self, text: str) -> str:
        text_lower = text.lower()
        for field in FIELD_RELEVANCE:
            if field in text_lower:
                return field
        # Check abbreviations
        if re.search(r"\bcs\b|comp\s*sci", text_lower):
            return "computer science"
        if re.search(r"\bit\b", text_lower) and "information" in text_lower:
            return "information technology"
        return ""

    def _detect_gpa(self, text: str) -> Optional[float]:
        m = re.search(r"(?:gpa|g\.p\.a\.?)[\s:]*(\d\.\d+)", text, re.I)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        # Also check "X.XX/4.0" pattern
        m = re.search(r"(\d\.\d+)\s*/\s*4\.0", text, re.I)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        return None

    def _detect_current_student(self, text: str) -> bool:
        patterns = [
            r"(?:currently|presently)\s+(?:enrolled|pursuing|studying)",
            r"expected\s+(?:graduation|completion)",
            r"(?:graduating|will graduate)\s+(?:in\s+)?\d{4}",
            r"(?:anticipated|expected)\s+\d{4}",
            r"present\b",
        ]
        for p in patterns:
            if re.search(p, text, re.I):
                return True
        return False

    def _score_degree_level(self, resume_degree: str, jd_degree: str) -> float:
        if not jd_degree:
            return 70  # No requirement → give decent baseline

        resume_level = DEGREE_LEVELS.get(resume_degree, 0)
        jd_level = DEGREE_LEVELS.get(jd_degree, 0)

        if resume_level == 0:
            return 30  # Can't determine

        diff = resume_level - jd_level
        if diff >= 0:
            return 100  # Meets or exceeds
        elif diff == -1:
            return 60  # One level below
        else:
            return 30  # Two+ levels below

    def _score_field(self, resume_field: str, jd_field: str) -> float:
        if not jd_field:
            return 70  # No specific field mentioned

        if not resume_field:
            return 40  # Can't determine field

        # Check direct match
        resume_relevance = FIELD_RELEVANCE.get(resume_field, 0.3)
        return resume_relevance * 100

    def _degree_match_label(self, resume_degree: str, jd_degree: str) -> str:
        if not jd_degree:
            return "No specific degree required"
        if not resume_degree:
            return "Degree level not detected"

        resume_level = DEGREE_LEVELS.get(resume_degree, 0)
        jd_level = DEGREE_LEVELS.get(jd_degree, 0)

        if resume_level >= jd_level:
            return f"{resume_degree.title()} meets/exceeds {jd_degree.title()} requirement"
        else:
            return f"{resume_degree.title()} is below {jd_degree.title()} requirement"

    def _field_match_label(self, resume_field: str, jd_field: str) -> str:
        if not jd_field:
            return "No specific field required"
        if not resume_field:
            return "Field of study not detected"
        relevance = FIELD_RELEVANCE.get(resume_field, 0.3)
        if relevance >= 0.9:
            return f"{resume_field.title()} is directly relevant"
        elif relevance >= 0.6:
            return f"{resume_field.title()} is related to the required field"
        else:
            return f"{resume_field.title()} is less relevant to the role"
# init ed scorer
