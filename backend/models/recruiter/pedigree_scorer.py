"""
Elevate v3 – Pedigree Scorer
===============================
Evaluates the quality of a candidate's professional background
using the Knowledge Graph to assess:
  - Company tier (FAANG/Tier-1 vs Tier-3)
  - Industry alignment between past employers and target role
  - Skill stack overlap with target company
  - Culture fit signals
"""

from typing import Dict, List, Optional


class PedigreeScorer:
    """Score candidate's company pedigree via the Knowledge Graph."""

    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph

    def score(
        self,
        candidate_companies: List[str],
        target_company: str = "",
        target_industry: str = "",
        target_skills: List[str] = None,
    ) -> Dict:
        """
        Score the pedigree of a candidate's employment history.

        Args:
            candidate_companies: List of past employer names
            target_company: Company name from the JD (if known)
            target_industry: Industry of the target role
            target_skills: Required skills from the JD
        """
        if not candidate_companies:
            return {
                "score": 50,
                "signals": [],
                "breakdown": [],
                "summary": "No company history detected.",
            }

        target_skills = target_skills or []
        signals = []
        company_scores = []

        # Get target company skills for overlap calculation
        target_skill_set = set(s.lower() for s in target_skills)
        if target_company:
            kg_skills = self.kg.get_company_skills(target_company)
            target_skill_set.update(s.lower() for s in kg_skills)

        for company in candidate_companies:
            company_clean = company.strip()
            if not company_clean or company_clean.lower() == "nan":
                continue

            tier = self.kg.get_company_tier(company_clean)
            industry = self.kg.get_company_industry(company_clean)
            comp_skills = self.kg.get_company_skills(company_clean)

            # --- Tier scoring (0-40 points) ---
            if tier == 1:
                tier_score = 40
                signals.append({
                    "type": "green",
                    "signal": "tier1_company",
                    "detail": f"{company_clean.title()} is a Tier-1 employer — strong signal",
                })
            elif tier == 2:
                tier_score = 25
            else:
                tier_score = 15

            # --- Industry alignment (0-30 points) ---
            industry_score = 15  # baseline
            if target_industry and industry != "unknown":
                if industry == target_industry:
                    industry_score = 30
                    signals.append({
                        "type": "green",
                        "signal": "industry_match",
                        "detail": f"{company_clean.title()} is in the same industry ({industry})",
                    })
                elif industry in ("tech", "fintech") and target_industry in ("tech", "fintech"):
                    industry_score = 25

            # --- Skill overlap (0-30 points) ---
            skill_score = 10  # baseline
            if comp_skills and target_skill_set:
                comp_skill_set = set(s.lower() for s in comp_skills)
                overlap = comp_skill_set & target_skill_set
                if overlap:
                    overlap_ratio = len(overlap) / max(len(target_skill_set), 1)
                    skill_score = min(30, int(10 + overlap_ratio * 25))
                    if len(overlap) >= 3:
                        signals.append({
                            "type": "green",
                            "signal": "skill_overlap",
                            "detail": (
                                f"{company_clean.title()} shares skills: "
                                f"{', '.join(list(overlap)[:5])}"
                            ),
                        })

            total = min(100, tier_score + industry_score + skill_score)
            company_scores.append({
                "company": company_clean,
                "score": total,
                "tier": tier,
                "industry": industry,
            })

        if not company_scores:
            return {
                "score": 50,
                "signals": [],
                "breakdown": [],
                "summary": "Could not evaluate company pedigree.",
            }

        # Weight recent companies more (first in list = most recent)
        weights = []
        for i, cs in enumerate(company_scores):
            w = 1.0 / (1 + i * 0.3)  # Decay: 1.0, 0.77, 0.63, ...
            weights.append(w)

        weighted_sum = sum(cs["score"] * w for cs, w in zip(company_scores, weights))
        total_weight = sum(weights)
        overall = weighted_sum / total_weight

        # Summary
        top_tier = min(cs["tier"] for cs in company_scores)
        if top_tier == 1:
            summary = "Strong pedigree with Tier-1 employer experience."
        elif top_tier == 2:
            summary = "Solid pedigree with reputable employers."
        else:
            summary = "Standard employer background."

        return {
            "score": round(min(100, max(0, overall))),
            "signals": signals,
            "breakdown": company_scores,
            "summary": summary,
        }
