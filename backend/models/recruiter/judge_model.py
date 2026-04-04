"""
Elevate v3 – Judge Model (Inference)
=======================================
Self-hosted LLM judge using fine-tuned Flan-T5-small (60M params).
Generates structured recruiter evaluations from evidence packets.

Falls back to template-based evaluation if the model hasn't been trained.
"""

import os
import re
from typing import Dict, Optional

import torch


class JudgeModel:
    """
    Flan-T5-small fine-tuned to generate recruiter evaluations.
    Input: Structured evidence packet with all pipeline scores.
    Output: "Decision: SHORTLIST|MAYBE|REJECT | Score: X/100 | Reasoning..."
    """

    def __init__(self, model_path: str = None):
        self._model = None
        self._tokenizer = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models", "elevate-judge-v1",
            )

        self._model_path = model_path
        self._try_load_model()

    def _try_load_model(self):
        """Attempt to load the fine-tuned T5 model."""
        if not os.path.exists(self._model_path):
            return

        try:
            from transformers import T5Tokenizer, T5ForConditionalGeneration

            self._tokenizer = T5Tokenizer.from_pretrained(self._model_path)
            self._model = T5ForConditionalGeneration.from_pretrained(self._model_path)
            self._model.eval()
            self._model.to(self._device)
        except Exception as e:
            print(f"  Warning: Could not load judge model: {e}")
            self._model = None

    def evaluate(
        self,
        overall_score: float,
        skill_coverage: float = 0,
        semantic_score: float = 0,
        impact_density: float = 0,
        trajectory_score: float = 0,
        layout_score: float = 0,
        resume_snippet: str = "",
        jd_snippet: str = "",
    ) -> Dict:
        """
        Generate a structured evaluation from pipeline evidence.

        Returns:
            {
                "decision": "SHORTLIST" | "MAYBE" | "REJECT",
                "confidence": 0-1,
                "reasoning": str,
                "method": "neural" | "template",
            }
        """
        evidence = self._build_evidence(
            overall_score, skill_coverage, semantic_score,
            impact_density, trajectory_score, layout_score,
            resume_snippet, jd_snippet,
        )

        if self._model is not None:
            return self._evaluate_neural(evidence, overall_score)

        return self._evaluate_template(overall_score, skill_coverage,
                                        impact_density, trajectory_score)

    def _build_evidence(
        self, overall, skills, semantic, impact, trajectory, layout,
        resume, jd
    ) -> str:
        """Build the evidence packet string for T5 input."""
        return (
            f"Evaluate candidate for this role. "
            f"Match Score: {overall:.0f}/100 | "
            f"Skill Coverage: {skills:.0f}% | "
            f"Semantic Alignment: {semantic:.0f}/100 | "
            f"Impact Density: {impact:.0f}% | "
            f"Career Score: {trajectory:.0f}/100 | "
            f"Layout Score: {layout:.0f}/100 | "
            f"Resume: {resume[:200]} | "
            f"JD: {jd[:150]}"
        )

    def _evaluate_neural(self, evidence: str, overall: float) -> Dict:
        """Generate evaluation using the fine-tuned T5 model."""
        inputs = self._tokenizer(
            evidence, max_length=384, truncation=True,
            padding=True, return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_length=192,
                num_beams=3,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )

        result_text = self._tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # Parse the output
        decision = "MAYBE"
        if "SHORTLIST" in result_text.upper():
            decision = "SHORTLIST"
        elif "REJECT" in result_text.upper():
            decision = "REJECT"

        # Extract reasoning (after the second |)
        parts = result_text.split("|")
        reasoning = parts[-1].strip() if len(parts) > 2 else result_text

        return {
            "decision": decision,
            "confidence": min(0.95, 0.5 + overall / 200),
            "reasoning": reasoning,
            "method": "neural",
            "raw_output": result_text,
        }

    def _evaluate_template(
        self, overall: float, skill_cov: float,
        impact: float, trajectory: float,
    ) -> Dict:
        """Template-based evaluation (fallback)."""
        strengths = []
        concerns = []

        if skill_cov >= 70:
            strengths.append("strong skill alignment")
        elif skill_cov < 40:
            concerns.append("significant skill gaps")

        if impact >= 60:
            strengths.append("quantified achievements")
        elif impact < 30:
            concerns.append("lacks measurable impact")

        if trajectory >= 70:
            strengths.append("solid career progression")
        elif trajectory < 40:
            concerns.append("unstable career trajectory")

        if overall >= 75:
            decision = "SHORTLIST"
            reasoning = (
                f"Strong candidate. "
                f"{'Strengths: ' + ', '.join(strengths) + '. ' if strengths else ''}"
                f"Recommend advancing to interview stage."
            )
        elif overall >= 55:
            decision = "MAYBE"
            reasoning = (
                f"Moderate match. "
                f"{'Strengths: ' + ', '.join(strengths) + '. ' if strengths else ''}"
                f"{'Concerns: ' + ', '.join(concerns) + '. ' if concerns else ''}"
                f"Consider with additional screening."
            )
        else:
            decision = "REJECT"
            reasoning = (
                f"Below threshold. "
                f"{'Concerns: ' + ', '.join(concerns) + '. ' if concerns else 'Limited alignment. '}"
                f"Not recommended for this role."
            )

        return {
            "decision": decision,
            "confidence": min(0.9, 0.4 + overall / 200),
            "reasoning": reasoning,
            "method": "template",
        }
