"""
Elevate – Experience Matcher
===============================
Matches resume experience bullets against JD responsibilities by understanding:

1. Action-Responsibility Alignment
   "Developed scalable REST APIs" → matches → "Build high-performance APIs"

2. Impact-Scope Matching
   "Reduced latency by 40%" → matches → "Improve system performance"

3. Technology Context
   "Built with Python/Django" → matches → "Python backend development"

4. Seniority Signal Detection
   "Led team of 5 engineers" → signals senior experience
   "Assisted in development" → signals junior experience
"""

import re
from typing import List, Dict


# ---------------------------------------------------------------------------
# Seniority signal detection
# ---------------------------------------------------------------------------

SENIOR_SIGNALS = [
    re.compile(r"\b(?:led|managed|directed|oversaw|mentored|architected|"
               r"spearheaded|established|pioneered|drove|owned)\b", re.I),
    re.compile(r"\bteam of \d+", re.I),
    re.compile(r"\b(?:senior|lead|principal|staff|head)\b", re.I),
    re.compile(r"\b\d+\+?\s*(?:years?|yrs?)\b", re.I),
]

JUNIOR_SIGNALS = [
    re.compile(r"\b(?:assisted|helped|supported|participated|contributed|"
               r"shadowed|observed|learned|exposed)\b", re.I),
    re.compile(r"\b(?:intern|internship|co-op|fellowship|trainee)\b", re.I),
    re.compile(r"\b(?:coursework|academic|class project|school)\b", re.I),
]

# Impact/quantification patterns
IMPACT_PATTERN = re.compile(
    r"\b\d+[%xX]\b|"           # Percentages (40%, 3x)
    r"\$\d+[KkMmBb]?\b|"      # Dollar amounts
    r"\b\d{2,}[+]?\s*(?:users?|customers?|clients?|requests?|records?|"
    r"transactions?|employees?|teams?|projects?|services?)\b|"
    r"\breduced|increased|improved|grew|saved|cut\b",
    re.I,
)


class ExperienceMatcher:
    """
    Analyze resume experience for seniority signals, impact indicators,
    and generate experience-level compatibility assessment.
    """

    def analyze_bullets(self, bullets: List[str]) -> Dict:
        """
        Analyze a set of experience bullets for quality signals.

        Returns:
          - seniority_signal: "intern"/"junior"/"mid"/"senior"/"lead"
          - impact_count: number of bullets with quantification
          - leadership_count: number of bullets showing leadership
          - bullet_quality: [{text, has_impact, has_leadership, seniority, quality_score}]
          - overall_quality: 0-100
        """
        bullet_quality = []
        impact_count = 0
        leadership_count = 0
        senior_signals = 0
        junior_signals = 0

        for bullet in bullets:
            has_impact = bool(IMPACT_PATTERN.search(bullet))
            has_leadership = any(p.search(bullet) for p in SENIOR_SIGNALS)
            is_junior = any(p.search(bullet) for p in JUNIOR_SIGNALS)

            if has_impact:
                impact_count += 1
            if has_leadership:
                leadership_count += 1
                senior_signals += 1
            if is_junior:
                junior_signals += 1

            # Quality score for individual bullet
            quality = 30  # baseline
            if has_impact:
                quality += 30
            if has_leadership:
                quality += 20
            if len(bullet) > 40:
                quality += 10  # detailed bullets
            if bullet[0].isupper() and re.match(r"^[A-Z][a-z]+ed\b", bullet):
                quality += 10  # starts with strong past-tense verb

            bullet_quality.append({
                "text": bullet,
                "has_impact": has_impact,
                "has_leadership": has_leadership,
                "is_junior": is_junior,
                "quality_score": min(quality, 100),
            })

        # Determine overall seniority signal
        if senior_signals >= 3:
            seniority = "senior"
        elif senior_signals >= 1 and junior_signals == 0:
            seniority = "mid"
        elif junior_signals >= 2:
            seniority = "junior"
        elif junior_signals >= 1:
            seniority = "intern"
        else:
            seniority = "mid"

        # Overall quality
        if bullet_quality:
            overall_quality = sum(b["quality_score"] for b in bullet_quality) / len(bullet_quality)
        else:
            overall_quality = 0

        return {
            "seniority_signal": seniority,
            "impact_count": impact_count,
            "leadership_count": leadership_count,
            "bullet_count": len(bullets),
            "bullet_quality": bullet_quality,
            "overall_quality": round(overall_quality, 1),
        }

    def check_seniority_fit(self, resume_seniority: str, jd_seniority: str) -> Dict:
        """
        Check if the resume's experience level matches the JD's requirements.

        Returns:
          - fit: "perfect", "close", "overqualified", "underqualified"
          - fit_score: 0-100
          - explanation: str
        """
        levels = {"intern": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4}
        r_level = levels.get(resume_seniority, 2)
        j_level = levels.get(jd_seniority, 2)

        diff = r_level - j_level

        if diff == 0:
            return {
                "fit": "perfect",
                "fit_score": 100,
                "explanation": f"Experience level aligns well with the {jd_seniority} role.",
            }
        elif diff == 1:
            return {
                "fit": "close",
                "fit_score": 80,
                "explanation": f"Slightly more experienced than typical {jd_seniority} candidate. Strong fit.",
            }
        elif diff == -1:
            return {
                "fit": "close",
                "fit_score": 75,
                "explanation": f"Slightly less experienced for a {jd_seniority} role, but could be a fit with strong skills.",
            }
        elif diff >= 2:
            return {
                "fit": "overqualified",
                "fit_score": 50,
                "explanation": f"May be overqualified for a {jd_seniority} role based on demonstrated experience.",
            }
        else:
            return {
                "fit": "underqualified",
                "fit_score": 40,
                "explanation": f"Experience level suggests more junior than what this {jd_seniority} role requires.",
            }
# init matcher
# finalize weights
