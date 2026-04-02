"""
Elevate – Skill Scorer
========================
Taxonomy-aware skill matching that thinks like a recruiter:

Scoring levels:
  1.0  — Exact match: resume says "Python", JD wants "Python"
  0.95 — Synonym match: resume says "JS", JD wants "JavaScript"
  0.85 — Parent-child: resume says "React", JD wants "Frontend"
  0.70 — Related skill: resume says "Spring Boot", JD wants "Hibernate"
  0.50 — Same domain: resume says "PostgreSQL", JD wants "MySQL"
  0.30 — Domain adjacency: resume says "Docker", JD in "Cloud"
  0.00 — No relationship

Also provides:
  - Domain coverage analysis (how much of each domain is covered)
  - Skill gap analysis (what's missing, what's extra)
  - Related skills suggestions (what resume skills imply)
"""

import re
from typing import List, Dict, Tuple, Set
from .skill_taxonomy import get_taxonomy, DOMAIN_CLUSTERS


class SkillScorer:
    """Score resume skills against JD requirements using the taxonomy."""

    def __init__(self):
        self.taxonomy = get_taxonomy()

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract all known skills from a text using the taxonomy."""
        text_lower = text.lower()
        found = []
        found_canonical = set()

        # Check each canonical skill and its aliases
        for canonical in self.taxonomy._canonical_set:
            if canonical in found_canonical:
                continue

            # Direct match
            pattern = r"\b" + re.escape(canonical) + r"\b"
            if re.search(pattern, text_lower):
                found.append(canonical)
                found_canonical.add(canonical)
                continue

            # Alias match
            for alias, canon in self.taxonomy._alias_to_canonical.items():
                if canon == canonical and alias != canonical:
                    pattern = r"\b" + re.escape(alias) + r"\b"
                    if re.search(pattern, text_lower):
                        found.append(canonical)
                        found_canonical.add(canonical)
                        break

        return found

    def score(
        self,
        resume_skills: List[str],
        jd_required_skills: List[str],
        jd_preferred_skills: List[str],
    ) -> Dict:
        """
        Compute comprehensive skill matching score.

        Returns:
          - overall_score (0-100)
          - required_coverage (0-100)
          - preferred_coverage (0-100)
          - matched_skills: [{"jd_skill": ..., "resume_skill": ..., "match_type": ..., "strength": ...}]
          - missing_skills: [{"skill": ..., "priority": ..., "suggested_related": [...]}]
          - extra_skills: [skills in resume not in JD]
          - domain_coverage: {...}
        """
        resume_canonical = [self.taxonomy.canonicalize(s) for s in resume_skills]
        resume_set = set(resume_canonical)

        # Expand resume skills with their implied skills
        resume_implied = self._get_implied_skills(resume_canonical)

        all_jd_skills = jd_required_skills + jd_preferred_skills
        jd_canonical = [self.taxonomy.canonicalize(s) for s in all_jd_skills]

        matched = []
        missing = []
        matched_jd_skills = set()

        # Score each JD skill against resume
        for i, jd_skill in enumerate(jd_canonical):
            is_required = i < len(jd_required_skills)
            priority = 1.0 if is_required else 0.5

            best_match = None
            best_strength = 0.0
            best_type = ""

            for resume_skill in resume_canonical:
                strength = self.taxonomy.match_strength(jd_skill, resume_skill)
                if strength > best_strength:
                    best_strength = strength
                    best_match = resume_skill
                    if strength >= 0.95:
                        best_type = "exact"
                    elif strength >= 0.80:
                        best_type = "parent_child"
                    elif strength >= 0.60:
                        best_type = "related"
                    elif strength >= 0.35:
                        best_type = "domain"
                    else:
                        best_type = "weak"

            # Also check implied skills
            if best_strength < 0.6:
                for impl_skill, impl_strength in resume_implied:
                    tax_strength = self.taxonomy.match_strength(jd_skill, impl_skill)
                    combined = tax_strength * impl_strength  # Dampened by implied strength
                    if combined > best_strength:
                        best_strength = combined
                        best_match = impl_skill + " (implied)"
                        best_type = "implied"

            if best_strength >= 0.3:
                matched.append({
                    "jd_skill": jd_skill,
                    "resume_skill": best_match,
                    "match_type": best_type,
                    "strength": round(best_strength, 3),
                    "priority": priority,
                })
                matched_jd_skills.add(jd_skill)
            else:
                # Find suggestions from resume
                suggestions = self._suggest_related_from_resume(jd_skill, resume_canonical)
                missing.append({
                    "skill": jd_skill,
                    "priority": priority,
                    "is_required": is_required,
                    "suggested_related": suggestions[:3],
                })

        # Extra skills (in resume but not in JD)
        jd_set = set(jd_canonical)
        extra = [s for s in resume_canonical if s not in jd_set and s not in matched_jd_skills]

        # Calculate scores
        if jd_required_skills:
            required_matched = sum(
                1 for m in matched
                if m["priority"] >= 1.0 and m["strength"] >= 0.5
            )
            required_coverage = (required_matched / len(jd_required_skills)) * 100
        else:
            required_coverage = 0

        if jd_preferred_skills:
            preferred_matched = sum(
                1 for m in matched
                if m["priority"] <= 0.5 and m["strength"] >= 0.5
            )
            preferred_coverage = (preferred_matched / len(jd_preferred_skills)) * 100
        else:
            preferred_coverage = 0

        # Overall: weighted average
        # Required skills count 2x, strong matches count more
        if matched:
            weighted_score = sum(
                m["strength"] * m["priority"] * 100
                for m in matched
            )
            max_possible = sum(
                m["priority"] * 100 for m in matched
            ) + sum(
                m["priority"] * 100 for m in missing
            )
            overall = (weighted_score / max_possible * 100) if max_possible > 0 else 0
        else:
            overall = 0

        # Domain coverage
        domain_coverage = self.taxonomy.get_domain_overlap(resume_canonical, jd_canonical)

        return {
            "overall_score": round(min(overall, 100), 1),
            "required_coverage": round(min(required_coverage, 100), 1),
            "preferred_coverage": round(min(preferred_coverage, 100), 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "extra_skills": extra,
            "domain_coverage": domain_coverage,
            "resume_skill_count": len(resume_set),
            "jd_skill_count": len(set(jd_canonical)),
        }

    def _get_implied_skills(self, skills: List[str]) -> List[Tuple[str, float]]:
        """
        Get skills implied by the resume skills.
        E.g., knowing "Spring Boot" implies familiarity with "Java", "Maven", "REST API".
        """
        implied = []
        direct_set = set(skills)

        for skill in skills:
            related = self.taxonomy.get_related(skill)
            for r in related:
                if r not in direct_set:
                    # Implied strength depends on relationship
                    strength = self.taxonomy.match_strength(skill, r) * 0.7
                    if strength > 0.2:
                        implied.append((r, strength))

            # Parent skills are also implied
            parent = self.taxonomy.get_parent(skill)
            if parent and parent not in direct_set:
                implied.append((parent, 0.6))

        return implied

    def _suggest_related_from_resume(
        self, missing_skill: str, resume_skills: List[str]
    ) -> List[str]:
        """
        For a missing JD skill, find closest matches from resume
        to suggest what the candidate could highlight.
        """
        matches = self.taxonomy.find_all_matches(missing_skill, resume_skills)
        return [m[0] for m in matches if m[1] > 0.2]
# handle duplicates
