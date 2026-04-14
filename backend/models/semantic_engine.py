"""
Elevate – Semantic Engine
===========================
Multi-strategy semantic matching that goes beyond simple cosine similarity:

Strategy 1: Sentence-to-Requirement matching (bi-encoder)
  Each resume bullet is matched against each JD requirement independently.
  Uses max-pooling so a bullet gets credit for matching ANY requirement.

Strategy 2: Paragraph-level context (bi-encoder)
  Entire resume sections scored against JD as thematic blocks.

Strategy 3: Cross-encoder verification
  High-confidence reranking of top bi-encoder results.
  Cross-encoder attends to both texts jointly → refines ranking.

Strategy 4: Mean-pooled section-level matching (bi-encoder)
  Average bi-encoder score across all requirements for broader relevance.

Key insight: The cross-encoder (ms-marco-MiniLM-L-6-v2) is trained on
search queries, not resume-JD pairs. Its logits can be extreme negatives
for items that are relevant but not phrased as search queries. So we
use it as a RERANKING signal (to distinguish good from great matches)
rather than as a primary scorer.
"""

import math
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_bi_encoder = None
_cross_encoder = None


def _get_bi_encoder():
    """all-mpnet-base-v2 — best general-purpose bi-encoder."""
    global _bi_encoder
    if _bi_encoder is None:
        from sentence_transformers import SentenceTransformer
        _bi_encoder = SentenceTransformer("all-mpnet-base-v2")
    return _bi_encoder


def _get_cross_encoder():
    """Cross-encoder for pairwise relevance scoring."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


# ---------------------------------------------------------------------------
# Score calibration — tuned for bi-encoder cosine similarity ranges
# ---------------------------------------------------------------------------

def calibrate_semantic(raw_cosine: float) -> float:
    """
    Map raw cosine similarity to interpretable percentage.
    
    For all-mpnet-base-v2, typical cosine ranges for resume-JD pairs:
      - Highly relevant bullet to requirement: 0.45-0.70
      - Moderately relevant: 0.25-0.45
      - Weakly relevant: 0.10-0.25
      - Irrelevant: 0.00-0.10
    
    This calibration maps those ranges to recruiter-intuitive scores:
      - 0.55+ → 80-100% (excellent)
      - 0.40-0.55 → 60-80% (strong)
      - 0.25-0.40 → 35-60% (moderate)
      - 0.15-0.25 → 15-35% (weak)
      - 0.00-0.15 → 0-15% (poor)
    """
    if raw_cosine >= 0.55:
        return min(100, 80 + (raw_cosine - 0.55) * 133.3)
    elif raw_cosine >= 0.40:
        return 60 + (raw_cosine - 0.40) * 133.3
    elif raw_cosine >= 0.25:
        return 35 + (raw_cosine - 0.25) * 166.7
    elif raw_cosine >= 0.15:
        return 15 + (raw_cosine - 0.15) * 200
    elif raw_cosine >= 0.05:
        return 3 + (raw_cosine - 0.05) * 120
    else:
        return max(0, raw_cosine * 60)


def score_to_strength(score: float) -> str:
    """Map calibrated score to strength label."""
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "strong"
    if score >= 45:
        return "moderate"
    if score >= 25:
        return "weak"
    return "poor"


# ---------------------------------------------------------------------------
# Cross-encoder score normalization
# ---------------------------------------------------------------------------

def _normalize_cross_score(logit: float) -> float:
    """
    Normalize cross-encoder logit to 0-1 range.
    
    ms-marco cross-encoder outputs logits typically in [-10, +10].
    For resume-JD pairs (not normal search queries), logits are
    often in the -8 to +2 range. We use a softened sigmoid
    that spreads this range more evenly.
    """
    # Shift the center point: ms-marco scores center around -3 for
    # "somewhat relevant" resume-JD pairs
    shifted = (logit + 3.0) * 0.5  # Center at -3, scale down
    return 1.0 / (1.0 + math.exp(-min(max(shifted, -10), 10)))


# ---------------------------------------------------------------------------
# SEMANTIC ENGINE
# ---------------------------------------------------------------------------

class SemanticEngine:
    """Multi-strategy semantic matching engine."""

    def __init__(self):
        self.bi_encoder = _get_bi_encoder()
        self.cross_encoder = _get_cross_encoder()

    def score_bullets_vs_requirements(
        self,
        bullets: List[str],
        jd_requirements: List[str],
        jd_full_text: str = "",
    ) -> Dict:
        """
        Match resume bullets against JD requirements using multiple strategies.

        Returns:
          - overall_score (0-100, calibrated)
          - bullet_scores: [{text, similarity, strength, best_match_req, strategies}]
          - requirement_coverage: [{req_text, coverage_score, best_bullet}]
        """
        if not bullets:
            return {"overall_score": 0, "bullet_scores": [], "requirement_coverage": []}

        # Use requirements if available, otherwise chunk the JD
        if not jd_requirements:
            jd_requirements = self._chunk_text(jd_full_text)

        if not jd_requirements:
            return {"overall_score": 0, "bullet_scores": [], "requirement_coverage": []}

        # ============================================
        # Strategy 1: Bi-encoder sentence-to-requirement
        # (PRIMARY SCORER — cosine similarity is well-calibrated)
        # ============================================
        bullet_embs = self.bi_encoder.encode(bullets, show_progress_bar=False)
        req_embs = self.bi_encoder.encode(jd_requirements, show_progress_bar=False)

        # Sim matrix: bullets × requirements
        bi_sim_matrix = cosine_similarity(bullet_embs, req_embs)

        # Max-sim per bullet (best matching requirement)
        bi_max_scores = bi_sim_matrix.max(axis=1)
        bi_best_req_idx = bi_sim_matrix.argmax(axis=1)

        # Top-3 average per bullet (captures breadth of relevance)
        bi_top3_scores = np.sort(bi_sim_matrix, axis=1)[:, -min(3, bi_sim_matrix.shape[1]):]
        bi_top3_mean = bi_top3_scores.mean(axis=1)

        # ============================================
        # Strategy 2: Full JD context scoring
        # ============================================
        if jd_full_text:
            jd_full_emb = self.bi_encoder.encode([jd_full_text], show_progress_bar=False)
            bi_full_scores = cosine_similarity(bullet_embs, jd_full_emb).flatten()
        else:
            jd_mean_emb = req_embs.mean(axis=0, keepdims=True)
            bi_full_scores = cosine_similarity(bullet_embs, jd_mean_emb).flatten()

        # ============================================
        # Strategy 3: Cross-encoder reranking
        # (RERANKING SIGNAL — refines bi-encoder ordering)
        # ============================================
        cross_pairs = []
        for i, bullet in enumerate(bullets):
            best_req = jd_requirements[bi_best_req_idx[i]]
            cross_pairs.append((bullet, best_req))

        cross_scores_raw = self.cross_encoder.predict(cross_pairs)
        cross_scores = np.array([
            _normalize_cross_score(s) for s in cross_scores_raw
        ])

        # ============================================
        # Combine strategies
        # ============================================
        # Bi-encoder dominates because it's calibrated for this task.
        # Cross-encoder is used as a refinement signal.
        combined_raw = (
            0.40 * bi_max_scores +         # Best matching requirement (primary)
            0.20 * bi_top3_mean +           # Breadth across requirements
            0.15 * bi_full_scores +         # Full JD context
            0.25 * cross_scores             # Cross-encoder refinement
        )

        # Build bullet score results
        bullet_scores = []
        for i, bullet in enumerate(bullets):
            raw = float(combined_raw[i])
            calibrated = round(calibrate_semantic(raw), 1)
            strength = score_to_strength(calibrated)

            bullet_scores.append({
                "text": bullet,
                "similarity": calibrated,
                "strength": strength,
                "best_match_req": jd_requirements[bi_best_req_idx[i]][:120],
                "raw_combined": round(raw, 4),
                "strategies": {
                    "bi_req": round(float(bi_max_scores[i]), 4),
                    "bi_top3": round(float(bi_top3_mean[i]), 4),
                    "bi_full": round(float(bi_full_scores[i]), 4),
                    "cross_req": round(float(cross_scores[i]), 4),
                },
            })

        bullet_scores.sort(key=lambda x: x["similarity"], reverse=True)

        # ============================================
        # Requirement coverage analysis
        # ============================================
        req_coverage = []
        req_max_scores = bi_sim_matrix.max(axis=0)
        req_best_bullet_idx = bi_sim_matrix.argmax(axis=0)

        for j, req in enumerate(jd_requirements):
            raw_cov = float(req_max_scores[j])
            calibrated_cov = round(calibrate_semantic(raw_cov), 1)
            req_coverage.append({
                "req_text": req[:150],
                "coverage_score": calibrated_cov,
                "best_bullet": bullets[req_best_bullet_idx[j]][:100] if req_best_bullet_idx[j] < len(bullets) else "",
            })

        req_coverage.sort(key=lambda x: x["coverage_score"])

        # ============================================
        # Overall score: weighted mean of bullet scores
        # ============================================
        if bullet_scores:
            scores = [b["similarity"] for b in bullet_scores]
            n = len(scores)
            # Top-heavy weighting: best bullets matter more
            weights = [max(0.3, 1.0 - (i * 0.04)) for i in range(n)]
            overall = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            overall = 0

        return {
            "overall_score": round(overall, 1),
            "bullet_scores": bullet_scores,
            "requirement_coverage": req_coverage,
        }

    def score_section(self, section_text: str, jd_text: str) -> Dict:
        """Score an entire resume section against the JD (paragraph-level)."""
        if not section_text or len(section_text.strip()) < 20:
            return {"score": 0, "strength": "poor", "raw": 0}

        # Bi-encoder (primary)
        sec_emb = self.bi_encoder.encode([section_text], show_progress_bar=False)
        jd_emb = self.bi_encoder.encode([jd_text], show_progress_bar=False)
        bi_sim = float(cosine_similarity(sec_emb, jd_emb).flatten()[0])

        # Cross-encoder (refinement, truncate to avoid overflow)
        sec_trunc = section_text[:512]
        jd_trunc = jd_text[:512]
        cross_raw = float(self.cross_encoder.predict([(sec_trunc, jd_trunc)])[0])
        cross_sim = _normalize_cross_score(cross_raw)

        # Combine — bi-encoder dominant
        combined = 0.65 * bi_sim + 0.35 * cross_sim
        calibrated = round(calibrate_semantic(combined), 1)
        strength = score_to_strength(calibrated)

        return {
            "score": calibrated,
            "strength": strength,
            "raw": round(combined, 4),
        }

    def _chunk_text(self, text: str, max_len: int = 200) -> List[str]:
        """Split text into semantic chunks."""
        import re
        raw_chunks = re.split(r"(?<=[.!?])\s+|[\n\r]+|(?<=;)\s+", text)
        chunks = []
        current = ""
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if len(chunk) < 15:
                if current:
                    current += " " + chunk
                continue
            if len(current) + len(chunk) < max_len:
                current = (current + " " + chunk).strip()
            else:
                if current:
                    chunks.append(current)
                current = chunk
        if current:
            chunks.append(current)
        return chunks if len(chunks) >= 2 else [text]
# base engine model
# tuning
