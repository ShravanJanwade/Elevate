"""
Elevate v3 – Data Pipeline
============================
Converts CSV datasets into training pairs for all model fine-tuning.

Sources:
  - resume_data.csv (9,544 rows): resume fields + JD fields + matched_score
  - Resume.csv (2,484 rows): full resume text + category
  - resume_dataset.csv (169 rows): category + resume text

Outputs:
  - Bi-encoder pairs: (resume_text, jd_text, similarity_score)
  - Cross-encoder pairs: same format, used differently
  - Impact classifier bullets: (bullet_text, label)
  - Judge training data: (evidence_packet, evaluation)
"""

import os
import re
import ast
import random
import pandas as pd
from typing import List, Dict, Tuple


# ---------------------------------------------------------------------------
# Resume-JD pair extraction from resume_data.csv
# ---------------------------------------------------------------------------

def _safe_parse_list(val) -> List[str]:
    """Safely parse a string that looks like a Python list."""
    if pd.isna(val) or not isinstance(val, str):
        return []
    val = val.strip()
    if val.startswith("["):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(x) for x in parsed if x]
            return []
        except Exception:
            pass
    return [x.strip() for x in val.split(",") if x.strip()]


def build_resume_jd_pairs(csv_path: str = "data/resume_data.csv") -> List[Dict]:
    """
    Build (resume_text, jd_text, score) triples from resume_data.csv.

    Each row contains both resume fields AND the JD it was matched against,
    with a matched_score (0.0–0.97). This is perfect training signal.
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig", on_bad_lines="skip")
    pairs = []

    for _, row in df.iterrows():
        # --- Build resume representation ---
        skills = _safe_parse_list(row.get("skills", ""))
        positions = _safe_parse_list(row.get("positions", ""))
        companies = _safe_parse_list(row.get("professional_company_names", ""))
        degrees = _safe_parse_list(row.get("degree_names", ""))
        institutions = _safe_parse_list(row.get("educational_institution_name", ""))
        fields = _safe_parse_list(row.get("major_field_of_studies", ""))
        responsibilities = str(row.get("responsibilities", "")) if pd.notna(row.get("responsibilities")) else ""

        resume_parts = []
        if positions:
            resume_parts.append(f"Position: {', '.join(positions)}")
        if companies:
            resume_parts.append(f"Company: {', '.join(companies)}")
        if skills:
            resume_parts.append(f"Skills: {', '.join(skills[:20])}")
        if responsibilities:
            resume_parts.append(f"Experience: {responsibilities[:300]}")
        if degrees and institutions:
            resume_parts.append(f"Education: {', '.join(degrees)} from {', '.join(institutions)}")
        if fields:
            resume_parts.append(f"Field: {', '.join(fields)}")

        resume_text = " | ".join(resume_parts)

        # --- Build JD representation ---
        # The BOM-prefixed column name for job position
        job_col = [c for c in df.columns if "job_position" in c.lower()]
        job_title = str(row[job_col[0]]) if job_col and pd.notna(row.get(job_col[0])) else ""

        jd_responsibilities = str(row.get("responsibilities.1", "")) if pd.notna(row.get("responsibilities.1")) else ""
        skills_required = str(row.get("skills_required", "")) if pd.notna(row.get("skills_required")) else ""
        edu_req = str(row.get("educationaL_requirements", "")) if pd.notna(row.get("educationaL_requirements")) else ""
        exp_req = str(row.get("experiencere_requirement", "")) if pd.notna(row.get("experiencere_requirement")) else ""

        jd_parts = []
        if job_title and job_title != "nan":
            jd_parts.append(f"Role: {job_title}")
        if skills_required and skills_required != "nan":
            jd_parts.append(f"Required Skills: {skills_required[:200]}")
        if jd_responsibilities and jd_responsibilities != "nan":
            jd_parts.append(f"Responsibilities: {jd_responsibilities[:300]}")
        if edu_req and edu_req != "nan":
            jd_parts.append(f"Education: {edu_req}")
        if exp_req and exp_req != "nan":
            jd_parts.append(f"Experience: {exp_req}")

        jd_text = " | ".join(jd_parts)

        score = float(row.get("matched_score", 0.5))

        if len(resume_text) > 50 and len(jd_text) > 30:
            pairs.append({
                "resume": resume_text[:512],
                "jd": jd_text[:512],
                "score": score,
            })

    return pairs


# ---------------------------------------------------------------------------
# Hard negative mining
# ---------------------------------------------------------------------------

def mine_hard_negatives(
    pairs: List[Dict], top_k: int = 3
) -> List[Dict]:
    """
    Mine hard negatives: resumes with HIGH keyword overlap but LOW matched_score.

    These teach the model that keyword matching ≠ quality:
      e.g., a resume listing "Python, AWS, Docker" matched to a JD requiring
      the same, but rejected because the resume shows duties not impact.
    """
    positives = [p for p in pairs if p["score"] >= 0.7]
    negatives = [p for p in pairs if p["score"] < 0.4]

    if not positives or not negatives:
        return []

    hard_negs = []
    for pos in positives[:500]:  # Limit to control runtime
        pos_words = set(pos["resume"].lower().split())

        scored = []
        for neg in random.sample(negatives, min(200, len(negatives))):
            neg_words = set(neg["resume"].lower().split())
            overlap = len(pos_words & neg_words) / max(len(pos_words | neg_words), 1)
            scored.append((neg, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        for neg, overlap in scored[:top_k]:
            if overlap > 0.15:
                hard_negs.append({
                    "anchor_jd": pos["jd"],
                    "positive_resume": pos["resume"],
                    "hard_negative_resume": neg["resume"],
                    "pos_score": pos["score"],
                    "neg_score": neg["score"],
                    "keyword_overlap": round(overlap, 3),
                })

    return hard_negs


# ---------------------------------------------------------------------------
# Bullet extraction for impact classifier training
# ---------------------------------------------------------------------------

def extract_bullets_for_impact_training(
    csv_path: str = "data/Resume.csv",
) -> List[Dict]:
    """
    Extract bullet-point lines from Resume.csv and auto-label them
    as IMPACT / DUTY / MIXED using heuristic patterns.

    This bootstraps labels for the DistilBERT impact classifier.
    """
    IMPACT_PATTERNS = [
        re.compile(r"\b\d+[%xX]\b"),
        re.compile(r"\$[\d,.]+[KkMmBb]?\b"),
        re.compile(r"\b\d{2,}\+?\s*(?:users?|customers?|clients?|requests?|transactions?|servers?|nodes?|teams?|projects?)\b", re.I),
        re.compile(r"\b(?:reduced|increased|improved|grew|saved|cut|boosted|accelerated|doubled|tripled)\b.*\b\d+", re.I),
    ]
    DUTY_PATTERNS = [
        re.compile(r"^(?:responsible for|tasked with|in charge of|handled|worked on|assisted with|assisted in|helped with)", re.I),
        re.compile(r"\bwas\s+\w+ed\b", re.I),
        re.compile(r"^(?:managed|maintained|supported|participated in)\b(?!.*\b\d)", re.I),
    ]

    BULLET_RE = re.compile(r"^\s*[-*•▪▸◦>]\s+(.+)$|^\s*\d+[.)]\s+(.+)$")
    ACTION_RE = re.compile(
        r"^\s{2,}((?:Developed|Built|Led|Managed|Created|Designed|Implemented|"
        r"Engineered|Optimized|Reduced|Increased|Improved|Spearheaded|Architected|"
        r"Streamlined|Automated|Delivered|Launched|Drove|Responsible|Handled|"
        r"Worked|Assisted|Maintained|Supported|Managed|Analyzed|Researched|"
        r"Configured|Deployed|Migrated|Integrated|Tested|Mentored|Trained).+)$",
        re.I,
    )

    try:
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    except Exception:
        df = pd.read_csv(csv_path, encoding="latin-1", on_bad_lines="skip")

    bullets = []
    seen = set()

    for _, row in df.iterrows():
        text = str(row.get("Resume_str", ""))
        for line in text.split("\n"):
            m = BULLET_RE.match(line)
            content = None
            if m:
                content = (m.group(1) or m.group(2) or "").strip()
            else:
                am = ACTION_RE.match(line)
                if am:
                    content = am.group(1).strip()

            if not content or len(content) < 15 or len(content) > 500:
                continue

            key = content.lower()[:60]
            if key in seen:
                continue
            seen.add(key)

            # Auto-label
            has_impact = any(p.search(content) for p in IMPACT_PATTERNS)
            has_duty = any(p.search(content) for p in DUTY_PATTERNS)
            has_number = bool(re.search(r"\d", content))

            if has_impact and has_number:
                label = 2  # impact
            elif has_duty and not has_number:
                label = 0  # duty
            else:
                label = 1  # mixed

            bullets.append({"text": content, "label": label})

    return bullets


# ---------------------------------------------------------------------------
# Category-labeled resume data for augmentation
# ---------------------------------------------------------------------------

def load_categorized_resumes(
    csv_path: str = "data/resume_dataset.csv",
) -> List[Dict]:
    """Load the 169-row category-labeled resume dataset."""
    df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    resumes = []
    for _, row in df.iterrows():
        resumes.append({
            "category": str(row.get("Category", "")),
            "text": str(row.get("Resume", ""))[:1000],
        })
    return resumes


# ---------------------------------------------------------------------------
# Full dataset statistics
# ---------------------------------------------------------------------------

def print_data_stats():
    """Print statistics about all available training data."""
    print("=" * 50)
    print("Elevate v3 — Training Data Statistics")
    print("=" * 50)

    pairs = build_resume_jd_pairs()
    print(f"\nResume-JD Pairs (resume_data.csv): {len(pairs)}")
    scores = [p["score"] for p in pairs]
    print(f"  Score range: {min(scores):.2f} – {max(scores):.2f}")
    print(f"  Mean score:  {sum(scores)/len(scores):.3f}")
    print(f"  Positives (≥0.7): {sum(1 for s in scores if s >= 0.7)}")
    print(f"  Negatives (<0.4): {sum(1 for s in scores if s < 0.4)}")

    bullets = extract_bullets_for_impact_training()
    from collections import Counter
    label_counts = Counter(b["label"] for b in bullets)
    print(f"\nBullet Points (Resume.csv): {len(bullets)}")
    print(f"  Duty (0):   {label_counts[0]}")
    print(f"  Mixed (1):  {label_counts[1]}")
    print(f"  Impact (2): {label_counts[2]}")

    resumes = load_categorized_resumes()
    cats = Counter(r["category"] for r in resumes)
    print(f"\nCategorized Resumes (resume_dataset.csv): {len(resumes)}")
    print(f"  Top categories: {cats.most_common(5)}")

    hard_negs = mine_hard_negatives(pairs)
    print(f"\nHard Negatives Mined: {len(hard_negs)}")

    print("=" * 50)


if __name__ == "__main__":
    print_data_stats()
