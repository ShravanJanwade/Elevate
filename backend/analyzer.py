"""
Elevate – Resume Analyzer Engine (v2)
=======================================
This is the unified entry point. It delegates to the multi-model system
in backend/models/ while maintaining backward-compatible function signatures.

The analysis pipeline:
  1. JD Parser → Structured requirements with priority levels
  2. Skill Scorer → Taxonomy-aware skill matching (Spring Boot ↔ Hibernate)
  3. Semantic Engine → Multi-strategy semantic similarity (4 strategies)
  4. Experience Matcher → Seniority signals, impact detection
  5. Education Scorer → Degree & field relevance
  6. Composite Scorer → Weighted combination with role-aware tuning
"""

from models.composite_scorer import CompositeScorer

# Singleton composite scorer (lazy loaded the models inside)
_scorer = None


def _get_scorer() -> CompositeScorer:
    global _scorer
    if _scorer is None:
        _scorer = CompositeScorer()
    return _scorer


def full_analysis(resume_sections: dict, jd_text: str) -> dict:
    """
    Run the complete multi-model analysis pipeline.
    This is the main entry point used by app.py and cli.py.
    """
    scorer = _get_scorer()
    return scorer.analyze(resume_sections, jd_text)


# ---------------------------------------------------------------------------
# Backward-compatible functions (used by app.py endpoints)
# ---------------------------------------------------------------------------

def keyword_score(resume_sections: dict, jd_text: str) -> dict:
    """Backward-compatible keyword scoring."""
    scorer = _get_scorer()
    resume_text = resume_sections.get("raw_text", "")
    resume_skills = scorer.skill_scorer.extract_skills_from_text(resume_text)
    parsed_jd = scorer.jd_parser.parse(jd_text)

    result = scorer.skill_scorer.score(
        resume_skills=resume_skills,
        jd_required_skills=parsed_jd.required_skills,
        jd_preferred_skills=parsed_jd.preferred_skills,
    )

    matched = [m["jd_skill"] for m in result.get("matched_skills", [])]
    missing = [m["skill"] for m in result.get("missing_skills", [])]

    return {
        "match_percentage": result.get("overall_score", 0),
        "matched": matched,
        "missing": missing,
        "total_keywords": result.get("jd_skill_count", 0),
        "primary_matched": len([m for m in result.get("matched_skills", []) if m.get("priority", 0) >= 1.0]),
        "primary_total": len(parsed_jd.required_skills),
    }


def semantic_score(resume_sections: dict, jd_text: str) -> dict:
    """Backward-compatible semantic scoring."""
    scorer = _get_scorer()
    bullets = resume_sections.get("bullet_points", [])
    if not bullets:
        raw = resume_sections.get("raw_text", "")
        bullets = [s.strip() for s in raw.split(".") if len(s.strip()) > 15][:25]

    parsed_jd = scorer.jd_parser.parse(jd_text)
    jd_req_texts = [r.text for r in parsed_jd.requirements + parsed_jd.responsibilities]

    result = scorer.semantic_engine.score_bullets_vs_requirements(
        bullets=bullets,
        jd_requirements=jd_req_texts,
        jd_full_text=jd_text,
    )
    return result


def section_scores(resume_sections: dict, jd_text: str) -> list:
    """Backward-compatible section scoring."""
    scorer = _get_scorer()
    return scorer._score_sections(resume_sections, jd_text)
# debug mode
# timing metrics
# cleanup
