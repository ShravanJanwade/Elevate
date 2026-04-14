"""
Elevate v3 – Impact Classifier (Inference)
=============================================
Classifies resume bullet points as:
  0 = DUTY:   Generic responsibility without measurable outcome
  1 = MIXED:  Some action but no quantification
  2 = IMPACT: Quantified achievement with metrics

Uses a fine-tuned DistilBERT model when available, falling back
to heuristic classification if the model hasn't been trained yet.
"""

import os
import re
from typing import Dict, List, Optional

import torch


# Heuristic fallback patterns (used before model is trained)
_IMPACT_PATTERNS = [
    re.compile(r"\b\d+[%xX]\b"),
    re.compile(r"\$[\d,.]+[KkMmBb]?\b"),
    re.compile(r"\b\d{2,}\+?\s*(?:users?|requests?|transactions?)\b", re.I),
    re.compile(
        r"\b(?:reduced|increased|improved|grew|saved|cut|boosted|"
        r"accelerated|doubled|tripled)\b.*\b\d+",
        re.I,
    ),
]
_DUTY_PATTERNS = [
    re.compile(r"^(?:responsible for|tasked with|in charge of|worked on)", re.I),
    re.compile(r"\bwas\s+\w+ed\b", re.I),
    re.compile(r"^(?:managed|maintained|supported|participated)\b(?!.*\d)", re.I),
]

LABEL_NAMES = {0: "duty", 1: "mixed", 2: "impact"}


class ImpactClassifier:
    """Classify resume bullet points as impact / duty / mixed."""

    def __init__(self, model_path: str = None):
        self._model = None
        self._tokenizer = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models", "impact-classifier-v1",
            )

        self._model_path = model_path
        self._try_load_model()

    def _try_load_model(self):
        """Attempt to load the fine-tuned DistilBERT model."""
        if not os.path.exists(self._model_path):
            return

        try:
            from transformers import (
                DistilBertTokenizer,
                DistilBertForSequenceClassification,
            )

            self._tokenizer = DistilBertTokenizer.from_pretrained(self._model_path)
            self._model = DistilBertForSequenceClassification.from_pretrained(
                self._model_path
            )
            self._model.eval()
            self._model.to(self._device)
        except Exception as e:
            print(f"  Warning: Could not load impact classifier: {e}")
            self._model = None

    def classify(self, bullet: str) -> Dict:
        """
        Classify a single bullet point.
        Returns: {"label": "impact"|"duty"|"mixed", "confidence": 0-1}
        """
        if self._model is not None:
            return self._classify_neural(bullet)
        return self._classify_heuristic(bullet)

    def classify_batch(self, bullets: List[str]) -> List[Dict]:
        """Classify multiple bullet points."""
        if self._model is not None:
            return self._classify_batch_neural(bullets)
        return [self._classify_heuristic(b) for b in bullets]

    def score_impact_density(self, bullets: List[str]) -> Dict:
        """
        Calculate the 'impact density' of a resume's bullet points.
        Returns score (0-100) and breakdown.
        """
        if not bullets:
            return {
                "score": 50.0,
                "impact_count": 0,
                "duty_count": 0,
                "mixed_count": 0,
                "total": 0,
                "impact_ratio": 0.0,
            }

        results = self.classify_batch(bullets)

        counts = {"duty": 0, "mixed": 0, "impact": 0}
        for r in results:
            counts[r["label"]] += 1

        total = len(bullets)
        impact_ratio = counts["impact"] / total
        duty_ratio = counts["duty"] / total

        # Score: heavily reward impact, penalize duty
        score = (
            impact_ratio * 100 * 0.6
            + (counts["mixed"] / total) * 100 * 0.3
            + (1 - duty_ratio) * 100 * 0.1
        )
        score = max(10, min(100, score))

        return {
            "score": round(score, 1),
            "impact_count": counts["impact"],
            "duty_count": counts["duty"],
            "mixed_count": counts["mixed"],
            "total": total,
            "impact_ratio": round(impact_ratio, 3),
            "details": results,
        }

    # ----- Neural classification -----

    def _classify_neural(self, bullet: str) -> Dict:
        """Classify using the fine-tuned DistilBERT model."""
        inputs = self._tokenizer(
            bullet, truncation=True, padding=True,
            max_length=128, return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
            label_id = probs.argmax().item()
            confidence = probs[label_id].item()

        return {
            "label": LABEL_NAMES[label_id],
            "confidence": round(confidence, 3),
            "probabilities": {
                LABEL_NAMES[i]: round(probs[i].item(), 3)
                for i in range(3)
            },
        }

    def _classify_batch_neural(self, bullets: List[str]) -> List[Dict]:
        """Batch neural classification for efficiency."""
        if not bullets:
            return []

        inputs = self._tokenizer(
            bullets, truncation=True, padding=True,
            max_length=128, return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        results = []
        for i in range(len(bullets)):
            label_id = probs[i].argmax().item()
            confidence = probs[i][label_id].item()
            results.append({
                "label": LABEL_NAMES[label_id],
                "confidence": round(confidence, 3),
            })

        return results

    # ----- Heuristic fallback -----

    def _classify_heuristic(self, bullet: str) -> Dict:
        """Classify using regex patterns (fallback)."""
        has_impact = any(p.search(bullet) for p in _IMPACT_PATTERNS)
        has_duty = any(p.search(bullet) for p in _DUTY_PATTERNS)
        has_number = bool(re.search(r"\d", bullet))

        if has_impact and has_number:
            return {"label": "impact", "confidence": 0.75}
        elif has_duty and not has_number:
            return {"label": "duty", "confidence": 0.70}
        else:
            return {"label": "mixed", "confidence": 0.60}
