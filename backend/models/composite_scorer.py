"""
Elevate v3 – Composite Scorer (Master Orchestrator)
=====================================================
Combines all specialized models into a final analysis
that thinks like a senior hiring manager.

v3 Dimensions (7 total):
  1. Semantic Alignment (25%)  — Fine-tuned bi+cross encoder
  2. Skill Match        (20%)  — Taxonomy-aware coverage
  3. Experience Quality  (10%) — Seniority fit + bullet quality
  4. Education Fit       (5%)  — Degree & field relevance
  5. Impact Density      (15%) — DistilBERT impact classifier  [NEW]
  6. Career Trajectory   (15%) — Progression & tenure analysis  [NEW]
  7. Document Quality    (10%) — Layout & formatting analysis   [NEW]

Plus: LLM Judge evaluation for final SHORTLIST/MAYBE/REJECT decision.
"""

from typing import Dict, List, Optional
from .jd_parser import JDParser
from .skill_scorer import SkillScorer
from .semantic_engine import SemanticEngine, score_to_strength, calibrate_semantic
from .experience_matcher import ExperienceMatcher
from .education_scorer import EducationScorer
from .skill_taxonomy import get_taxonomy
from .layout_analyzer import LayoutAnalyzer
from .knowledge_graph import get_knowledge_graph
from .recruiter import (
    ImpactClassifier,
    CareerTrajectoryAnalyzer,
    PedigreeScorer,
    JudgeModel,
)


# Weight profiles by seniority — v3 with 7 dimensions
WEIGHT_PROFILES = {
    "intern": {
        "semantic": 0.20, "skill": 0.20, "experience": 0.05,
        "education": 0.20, "impact": 0.10, "trajectory": 0.10, "layout": 0.15,
    },
    "junior": {
        "semantic": 0.20, "skill": 0.25, "experience": 0.10,
        "education": 0.15, "impact": 0.10, "trajectory": 0.10, "layout": 0.10,
    },
    "mid": {
        "semantic": 0.25, "skill": 0.20, "experience": 0.10,
        "education": 0.05, "impact": 0.15, "trajectory": 0.15, "layout": 0.10,
    },
    "senior": {
        "semantic": 0.25, "skill": 0.15, "experience": 0.10,
        "education": 0.05, "impact": 0.20, "trajectory": 0.15, "layout": 0.10,
    },
    "lead": {
        "semantic": 0.20, "skill": 0.15, "experience": 0.10,
        "education": 0.05, "impact": 0.20, "trajectory": 0.20, "layout": 0.10,
    },
}


class CompositeScorer:
    """
    v3 Master scorer — orchestrates 7 specialized analysis dimensions
    plus a recruiter judge evaluation.
    """

    def __init__(self):
        self.jd_parser = JDParser()
        self.skill_scorer = SkillScorer()
        self.semantic_engine = SemanticEngine()
        self.experience_matcher = ExperienceMatcher()
        self.education_scorer = EducationScorer()
        self.taxonomy = get_taxonomy()

        # v3 new modules
        self.layout_analyzer = LayoutAnalyzer()
        self.impact_classifier = ImpactClassifier()
        self.trajectory_analyzer = CareerTrajectoryAnalyzer()
        self.knowledge_graph = get_knowledge_graph()
        self.pedigree_scorer = PedigreeScorer(self.knowledge_graph)
        self.judge = JudgeModel()

    def analyze(self, resume_sections: Dict, jd_text: str) -> Dict:
        """
        Run full v3 multi-model analysis.

        Parameters:
          resume_sections: parsed resume dict from resume_parser
          jd_text: raw job description text

        Returns comprehensive analysis dict with 7 dimensions + judge.
        """
        # ============================================
        # Step 1: Parse the JD into structured requirements
        # ============================================
        parsed_jd = self.jd_parser.parse(jd_text)

        # ============================================
        # Step 2: Extract skills from resume
        # ============================================
        resume_text = resume_sections.get("raw_text", "")
        resume_skills = self.skill_scorer.extract_skills_from_text(resume_text)

        # ============================================
        # Step 3: Skill scoring (taxonomy-aware)
        # ============================================
        skill_result = self.skill_scorer.score(
            resume_skills=resume_skills,
            jd_required_skills=parsed_jd.required_skills,
            jd_preferred_skills=parsed_jd.preferred_skills,
        )

        # ============================================
        # Step 4: Semantic scoring (multi-strategy)
        # ============================================
        bullets = resume_sections.get("bullet_points", [])
        if not bullets:
            raw = resume_sections.get("raw_text", "")
            bullets = [s.strip() for s in raw.split(".") if len(s.strip()) > 15][:25]

        jd_req_texts = []
        for req in parsed_jd.requirements:
            jd_req_texts.append(req.text)
        for resp in parsed_jd.responsibilities:
            jd_req_texts.append(resp.text)

        semantic_result = self.semantic_engine.score_bullets_vs_requirements(
            bullets=bullets,
            jd_requirements=jd_req_texts,
            jd_full_text=jd_text,
        )

        # ============================================
        # Step 5: Experience analysis (existing)
        # ============================================
        experience_result = self.experience_matcher.analyze_bullets(bullets)
        seniority_fit = self.experience_matcher.check_seniority_fit(
            resume_seniority=experience_result["seniority_signal"],
            jd_seniority=parsed_jd.seniority,
        )

        # ============================================
        # Step 6: Education scoring (existing)
        # ============================================
        education_result = self.education_scorer.score(
            resume_sections=resume_sections,
            jd_education_level=parsed_jd.education_level,
            jd_education_field=parsed_jd.education_field,
            jd_seniority=parsed_jd.seniority,
        )

        # ============================================
        # Step 7: Section-level scoring
        # ============================================
        section_scores = self._score_sections(resume_sections, jd_text)

        # ============================================
        #  v3 Step 8: Impact Density Analysis [NEW]
        # ============================================
        impact_result = self.impact_classifier.score_impact_density(bullets)

        # ============================================
        #  v3 Step 9: Career Trajectory Analysis [NEW]
        # ============================================
        experience_text = resume_sections.get("experience", "")
        trajectory_result = self.trajectory_analyzer.analyze(
            experience_text=experience_text,
        )

        # ============================================
        #  v3 Step 10: Layout / Document Quality [NEW]
        # ============================================
        layout_result = self.layout_analyzer.analyze(raw_text=resume_text)

        # ============================================
        #  v3 Step 11: Pedigree Scoring via KG [NEW]
        # ============================================
        entities = resume_sections.get("entities", {})
        candidate_companies = entities.get("companies", [])
        pedigree_result = self.pedigree_scorer.score(
            candidate_companies=candidate_companies,
            target_industry=parsed_jd.title.lower() if parsed_jd.title else "",
            target_skills=parsed_jd.all_skills,
        )

        # ============================================
        # Step 12: Compute weighted overall score (v3 — 7 dimensions)
        # ============================================
        weights = WEIGHT_PROFILES.get(parsed_jd.seniority, WEIGHT_PROFILES["mid"])

        # Individual dimension scores (all 0-100)
        semantic_score = semantic_result.get("overall_score", 0)
        skill_score = skill_result.get("overall_score", 0)
        experience_score = self._compute_experience_score(experience_result, seniority_fit)
        education_score = education_result.get("score", 0)
        impact_score = impact_result.get("score", 50)
        trajectory_score = trajectory_result.get("score", 50)
        layout_score = layout_result.get("overall_quality", 50)

        overall = (
            semantic_score * weights["semantic"]
            + skill_score * weights["skill"]
            + experience_score * weights["experience"]
            + education_score * weights["education"]
            + impact_score * weights["impact"]
            + trajectory_score * weights["trajectory"]
            + layout_score * weights["layout"]
        )

        overall = round(min(100, max(0, overall)), 1)
        strength = score_to_strength(overall)

        # ============================================
        #  v3 Step 13: Judge Evaluation [NEW]
        # ============================================
        judge_result = self.judge.evaluate(
            overall_score=overall,
            skill_coverage=skill_score,
            semantic_score=semantic_score,
            impact_density=impact_score,
            trajectory_score=trajectory_score,
            layout_score=layout_score,
            resume_snippet=resume_text[:300],
            jd_snippet=jd_text[:200],
        )

        interpretation = self._generate_interpretation(
            overall, skill_result, semantic_result,
            seniority_fit, parsed_jd, impact_result, trajectory_result,
        )

        # ============================================
        # Build response (backward-compatible + v3 enriched)
        # ============================================
        matched_keywords = [m["jd_skill"] for m in skill_result.get("matched_skills", [])]
        missing_keywords = [m["skill"] for m in skill_result.get("missing_skills", [])]

        keyword_analysis = {
            "match_percentage": skill_result.get("overall_score", 0),
            "matched": matched_keywords,
            "missing": missing_keywords,
            "total_keywords": skill_result.get("jd_skill_count", 0),
            "primary_matched": len([
                m for m in skill_result.get("matched_skills", [])
                if m.get("priority", 0) >= 1.0
            ]),
            "primary_total": len(parsed_jd.required_skills),
            "matched_details": skill_result.get("matched_skills", []),
            "missing_details": skill_result.get("missing_skills", []),
            "domain_coverage": skill_result.get("domain_coverage", {}),
            "required_coverage": skill_result.get("required_coverage", 0),
            "preferred_coverage": skill_result.get("preferred_coverage", 0),
        }

        # All flags aggregated
        all_flags = []
        all_flags.extend(trajectory_result.get("flags", []))
        all_flags.extend(layout_result.get("flags", []))
        all_flags.extend(pedigree_result.get("signals", []))

        return {
            "overall_score": overall,
            "strength": strength,
            "interpretation": interpretation,

            # Core analysis results
            "keyword_analysis": keyword_analysis,
            "semantic_analysis": {
                "overall_score": semantic_score,
                "bullet_scores": semantic_result.get("bullet_scores", []),
                "requirement_coverage": semantic_result.get("requirement_coverage", []),
            },
            "section_scores": section_scores,

            # Existing analysis (enhanced)
            "experience_analysis": {
                "seniority_signal": experience_result.get("seniority_signal", "mid"),
                "seniority_fit": seniority_fit,
                "impact_count": experience_result.get("impact_count", 0),
                "leadership_count": experience_result.get("leadership_count", 0),
                "overall_quality": experience_result.get("overall_quality", 0),
                "score": experience_score,
            },
            "education_analysis": education_result,

            # ===== v3 NEW =====
            "impact_analysis": {
                "score": impact_score,
                "impact_count": impact_result.get("impact_count", 0),
                "duty_count": impact_result.get("duty_count", 0),
                "mixed_count": impact_result.get("mixed_count", 0),
                "total_bullets": impact_result.get("total", 0),
                "impact_ratio": impact_result.get("impact_ratio", 0),
                "details": impact_result.get("details", []),
            },
            "trajectory_analysis": {
                "score": trajectory_score,
                "entry_count": trajectory_result.get("entry_count", 0),
                "total_years": trajectory_result.get("total_years", 0),
                "avg_tenure_months": trajectory_result.get("avg_tenure_months", 0),
                "progressions": trajectory_result.get("progressions", 0),
                "regressions": trajectory_result.get("regressions", 0),
                "flags": trajectory_result.get("flags", []),
            },
            "layout_analysis": {
                "score": layout_score,
                "dimensions": layout_result.get("dimensions", {}),
                "flags": layout_result.get("flags", []),
            },
            "pedigree_analysis": {
                "score": pedigree_result.get("score", 50),
                "summary": pedigree_result.get("summary", ""),
                "signals": pedigree_result.get("signals", []),
                "breakdown": pedigree_result.get("breakdown", []),
            },
            "judge_evaluation": {
                "decision": judge_result.get("decision", "MAYBE"),
                "confidence": judge_result.get("confidence", 0.5),
                "reasoning": judge_result.get("reasoning", ""),
                "method": judge_result.get("method", "template"),
            },
            "all_flags": all_flags,
            # ===== END v3 =====

            # JD metadata
            "jd_analysis": parsed_jd.to_dict(),

            # Entities
            "entities": resume_sections.get("entities", {}),

            # Dimension breakdown for radar chart
            "dimensions": {
                "semantic": round(semantic_score, 1),
                "skills": round(skill_score, 1),
                "experience": round(experience_score, 1),
                "education": round(education_score, 1),
                "impact": round(impact_score, 1),
                "trajectory": round(trajectory_score, 1),
                "layout": round(layout_score, 1),
            },
            "weights_used": weights,
        }

    def _score_sections(self, resume_sections: Dict, jd_text: str) -> List[Dict]:
        """Score each resume section against the JD."""
        SECTION_WEIGHTS = {
            "experience": 1.0,
            "skills": 0.9,
            "projects": 0.85,
            "summary": 0.7,
            "certifications": 0.6,
            "education": 0.5,
            "awards": 0.4,
            "publications": 0.5,
            "volunteer": 0.3,
        }

        skip_keys = {"raw_text", "bullet_points", "header", "entities"}
        results = []

        for section_name, section_text in resume_sections.items():
            if section_name in skip_keys:
                continue
            if not isinstance(section_text, str) or len(section_text.strip()) < 20:
                continue

            score_result = self.semantic_engine.score_section(section_text, jd_text)
            weight = SECTION_WEIGHTS.get(section_name, 0.5)

            results.append({
                "section": section_name,
                "name": section_name,
                "score": score_result["score"],
                "strength": score_result["strength"],
                "weight": weight,
                "weighted_score": round(score_result["score"] * weight, 1),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _compute_experience_score(self, experience_result: Dict, seniority_fit: Dict) -> float:
        """Combine experience quality and seniority fit into a single score."""
        quality = experience_result.get("overall_quality", 50)
        fit_score = seniority_fit.get("fit_score", 50)
        return (quality * 0.5 + fit_score * 0.5)

    def _generate_interpretation(
        self,
        overall: float,
        skill_result: Dict,
        semantic_result: Dict,
        seniority_fit: Dict,
        parsed_jd,
        impact_result: Dict = None,
        trajectory_result: Dict = None,
    ) -> str:
        """Generate recruiter-style interpretation with v3 insights."""
        parts = []

        # Overall match statement
        if overall >= 80:
            parts.append("Excellent match for this role!")
        elif overall >= 65:
            parts.append("Strong candidate for this position.")
        elif overall >= 45:
            parts.append("Moderate fit — some areas to strengthen.")
        elif overall >= 25:
            parts.append("Below average match — significant gaps identified.")
        else:
            parts.append("Weak match for this specific role.")

        # Skill coverage insight
        missing = skill_result.get("missing_skills", [])
        required_missing = [m for m in missing if m.get("is_required", False)]
        if not required_missing:
            parts.append("All required skills are covered.")
        elif len(required_missing) <= 2:
            names = ", ".join(m["skill"] for m in required_missing[:2])
            parts.append(f"Missing required skill(s): {names}.")
        else:
            parts.append(f"Missing {len(required_missing)} required skills.")

        # v3: Impact insight
        if impact_result:
            impact_ratio = impact_result.get("impact_ratio", 0)
            if impact_ratio >= 0.5:
                parts.append("Resume shows strong quantified impact.")
            elif impact_ratio < 0.15:
                parts.append("Resume lacks quantified achievements — consider adding metrics.")

        # v3: Trajectory insight
        if trajectory_result:
            flags = trajectory_result.get("flags", [])
            green_flags = [f for f in flags if f.get("type") == "green"]
            red_flags = [f for f in flags if f.get("type") == "red"]
            if green_flags:
                parts.append(green_flags[0].get("detail", ""))
            elif red_flags:
                parts.append(red_flags[0].get("detail", ""))

        # Seniority insight
        fit = seniority_fit.get("fit", "close")
        if fit == "perfect":
            parts.append(f"Experience level aligns well with the {parsed_jd.seniority} role.")
        elif fit == "underqualified":
            parts.append(f"Experience may be below what this {parsed_jd.seniority} role expects.")
        elif fit == "overqualified":
            parts.append(f"Experience level exceeds typical {parsed_jd.seniority} requirements.")

        return " ".join(parts)
# weighted sum
# logic update
