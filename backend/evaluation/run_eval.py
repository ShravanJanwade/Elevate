"""
Evaluation script for Elevate semantic scoring.

Usage:
    python backend/evaluation/run_eval.py
    python backend/evaluation/run_eval.py --threshold 0.45
    python backend/evaluation/run_eval.py --threshold 0.4 --save
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(threshold: float = 0.4):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dataset = load_dataset()

    aggregate_tp = aggregate_fp = aggregate_fn = 0
    per_pair_results = []

    for entry in dataset:
        jd = entry["job_description"]
        relevant = entry["relevant_bullets"]
        irrelevant = entry["irrelevant_bullets"]
        all_bullets = relevant + irrelevant
        labels = [1] * len(relevant) + [0] * len(irrelevant)

        jd_emb = model.encode([jd])
        bullet_embs = model.encode(all_bullets)
        similarities = cosine_similarity(bullet_embs, jd_emb).flatten()

        predictions = [1 if s >= threshold else 0 for s in similarities]

        tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
        fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
        fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        aggregate_tp += tp
        aggregate_fp += fp
        aggregate_fn += fn

        per_pair_results.append({
            "id": entry["id"],
            "role": entry["role"],
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        })

    agg_precision = aggregate_tp / (aggregate_tp + aggregate_fp) if (aggregate_tp + aggregate_fp) > 0 else 0.0
    agg_recall = aggregate_tp / (aggregate_tp + aggregate_fn) if (aggregate_tp + aggregate_fn) > 0 else 0.0
    agg_f1 = (2 * agg_precision * agg_recall / (agg_precision + agg_recall)) if (agg_precision + agg_recall) > 0 else 0.0

    return per_pair_results, {
        "threshold": threshold,
        "precision": round(agg_precision, 3),
        "recall": round(agg_recall, 3),
        "f1": round(agg_f1, 3),
        "num_pairs": len(dataset),
    }


def print_table(per_pair, aggregate):
    col_widths = [10, 30, 12, 12, 12]
    header = ["Pair ID", "Role", "Precision", "Recall", "F1"]
    sep = "-" * sum(col_widths + [3 * len(col_widths)])

    print(f"\nEvaluation Results  (threshold = {aggregate['threshold']})")
    print(sep)
    print("  ".join(h.ljust(w) for h, w in zip(header, col_widths)))
    print(sep)
    for r in per_pair:
        row = [r["id"], r["role"], str(r["precision"]), str(r["recall"]), str(r["f1"])]
        print("  ".join(v.ljust(w) for v, w in zip(row, col_widths)))
    print(sep)
    agg_row = ["AGGREGATE", f"({aggregate['num_pairs']} pairs)", str(aggregate['precision']), str(aggregate['recall']), str(aggregate['f1'])]
    print("  ".join(v.ljust(w) for v, w in zip(agg_row, col_widths)))
    print(sep)
    print()


def save_to_supabase(aggregate):
    import requests
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url or not service_key or service_key == "your_service_role_key":
        print("WARNING: SUPABASE_SERVICE_ROLE_KEY not set — skipping save.")
        return

    payload = {
        "threshold": aggregate["threshold"],
        "precision": aggregate["precision"],
        "recall": aggregate["recall"],
        "f1": aggregate["f1"],
        "num_pairs": aggregate["num_pairs"],
    }
    resp = requests.post(
        f"{supabase_url}/rest/v1/eval_results",
        json=payload,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        timeout=10,
    )
    if resp.status_code in (200, 201):
        print(f"Results saved to Supabase eval_results (id={resp.json()[0]['id']})")
    else:
        print(f"Failed to save to Supabase: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Elevate semantic scoring")
    parser.add_argument("--threshold", type=float, default=0.4, help="Cosine similarity threshold (default: 0.4)")
    parser.add_argument("--save", action="store_true", help="Save results to Supabase eval_results table")
    args = parser.parse_args()

    per_pair, aggregate = evaluate(threshold=args.threshold)
    print_table(per_pair, aggregate)

    if args.save:
        save_to_supabase(aggregate)
