"""
Evaluation script for Elevate semantic scoring.

Now evaluates with:
  - Upgraded bi-encoder (all-mpnet-base-v2)
  - Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
  - Calibrated score mapping
  - Multiple threshold sweep

Usage:
    python backend/evaluation/run_eval.py
    python backend/evaluation/run_eval.py --threshold 0.45
    python backend/evaluation/run_eval.py --sweep
    python backend/evaluation/run_eval.py --threshold 0.4 --save
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, CrossEncoder

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(threshold: float = 0.4, use_cross_encoder: bool = True):
    """Run evaluation with bi-encoder + optional cross-encoder reranking."""
    bi_encoder = SentenceTransformer("all-mpnet-base-v2")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2") if use_cross_encoder else None

    dataset = load_dataset()

    aggregate_tp = aggregate_fp = aggregate_fn = 0
    per_pair_results = []

    for entry in dataset:
        jd = entry["job_description"]
        relevant = entry["relevant_bullets"]
        irrelevant = entry["irrelevant_bullets"]
        all_bullets = relevant + irrelevant
        labels = [1] * len(relevant) + [0] * len(irrelevant)

        # Bi-encoder scores
        jd_emb = bi_encoder.encode([jd])
        bullet_embs = bi_encoder.encode(all_bullets)
        bi_sims = cosine_similarity(bullet_embs, jd_emb).flatten()

        if cross_encoder:
            # Cross-encoder reranking
            pairs = [(bullet, jd) for bullet in all_bullets]
            cross_raw = cross_encoder.predict(pairs)
            cross_sims = np.array([1.0 / (1.0 + math.exp(-s)) for s in cross_raw])
            # Combine: 35% bi-encoder + 65% cross-encoder
            combined = 0.35 * bi_sims + 0.65 * cross_sims
        else:
            combined = bi_sims

        predictions = [1 if s >= threshold else 0 for s in combined]

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
        "cross_encoder": use_cross_encoder,
    }


def print_table(per_pair, aggregate):
    """Print evaluation results in a rich table format."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()

        console.print()
        method = "Bi-Encoder + Cross-Encoder" if aggregate["cross_encoder"] else "Bi-Encoder Only"
        console.print(Panel(
            f"[bold]Threshold:[/] {aggregate['threshold']}  |  [bold]Method:[/] {method}",
            title="[bold bright_magenta]Elevate Evaluation[/]",
            border_style="bright_magenta",
        ))

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
        table.add_column("Pair ID", width=10)
        table.add_column("Role", width=25)
        table.add_column("Precision", width=12, justify="center")
        table.add_column("Recall", width=12, justify="center")
        table.add_column("F1", width=12, justify="center")

        for r in per_pair:
            f1_color = "green" if r["f1"] >= 0.8 else ("yellow" if r["f1"] >= 0.5 else "red")
            table.add_row(
                r["id"], r["role"],
                str(r["precision"]), str(r["recall"]),
                f"[{f1_color}]{r['f1']}[/{f1_color}]",
            )

        # Aggregate row
        f1_color = "green" if aggregate["f1"] >= 0.8 else ("yellow" if aggregate["f1"] >= 0.5 else "red")
        table.add_row(
            "[bold]TOTAL[/]",
            f"[bold]({aggregate['num_pairs']} pairs)[/]",
            f"[bold]{aggregate['precision']}[/]",
            f"[bold]{aggregate['recall']}[/]",
            f"[bold {f1_color}]{aggregate['f1']}[/bold {f1_color}]",
            style="on #1a1a2e",
        )

        console.print(table)
        console.print()

    except ImportError:
        # Fallback: plain text table
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
        agg_row = ["AGGREGATE", f"({aggregate['num_pairs']} pairs)",
                    str(aggregate['precision']), str(aggregate['recall']), str(aggregate['f1'])]
        print("  ".join(v.ljust(w) for v, w in zip(agg_row, col_widths)))
        print(sep)
        print()


def threshold_sweep():
    """Evaluate across multiple thresholds to find the optimal one."""
    print("\n--- Threshold Sweep ---\n")

    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()
        table = Table(box=box.ROUNDED, title="[bold]Threshold Sweep Results[/]")
        table.add_column("Threshold", width=12, justify="center")
        table.add_column("Precision", width=12, justify="center")
        table.add_column("Recall", width=12, justify="center")
        table.add_column("F1", width=12, justify="center")

        best_f1, best_thresh = 0, 0
        for t in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            _, agg = evaluate(threshold=t)
            if agg["f1"] > best_f1:
                best_f1 = agg["f1"]
                best_thresh = t
            f1_color = "green" if agg["f1"] >= 0.8 else ("yellow" if agg["f1"] >= 0.5 else "red")
            table.add_row(
                str(t), str(agg["precision"]), str(agg["recall"]),
                f"[{f1_color}]{agg['f1']}[/{f1_color}]",
            )

        console.print(table)
        console.print(f"\n[bold green]Best threshold: {best_thresh} (F1 = {best_f1})[/]\n")

    except ImportError:
        best_f1, best_thresh = 0, 0
        print(f"{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
        print("-" * 48)
        for t in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            _, agg = evaluate(threshold=t)
            if agg["f1"] > best_f1:
                best_f1 = agg["f1"]
                best_thresh = t
            print(f"{t:<12} {agg['precision']:<12} {agg['recall']:<12} {agg['f1']:<12}")
        print(f"\nBest threshold: {best_thresh} (F1 = {best_f1})\n")


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
    parser.add_argument("--sweep", action="store_true", help="Run threshold sweep to find optimal threshold")
    parser.add_argument("--no-cross-encoder", action="store_true", help="Disable cross-encoder reranking")
    args = parser.parse_args()

    if args.sweep:
        threshold_sweep()
    else:
        per_pair, aggregate = evaluate(
            threshold=args.threshold,
            use_cross_encoder=not args.no_cross_encoder,
        )
        print_table(per_pair, aggregate)

        if args.save:
            save_to_supabase(aggregate)
