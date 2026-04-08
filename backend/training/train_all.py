#!/usr/bin/env python3
"""
Elevate v3 – Master Training Script
======================================
Runs the full training pipeline:
  1. Preprocess CSV data → training pairs
  2. Fine-tune bi-encoder (all-MiniLM-L6-v2)
  3. Fine-tune cross-encoder (ms-marco-MiniLM-L-6)
  4. Train impact classifier (DistilBERT)
  5. Train T5 judge (Flan-T5-small)
  6. Build knowledge graph (NetworkX)

Usage:
    cd backend
    python training/train_all.py
    python training/train_all.py --skip-bi-encoder  # Skip slow bi-encoder training
"""

import os
import sys
import time
import argparse
import pickle

# Ensure imports work
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)


def main():
    parser = argparse.ArgumentParser(description="Elevate v3 — Full Training Pipeline")
    parser.add_argument("--skip-bi-encoder", action="store_true", help="Skip bi-encoder fine-tuning")
    parser.add_argument("--skip-cross-encoder", action="store_true", help="Skip cross-encoder fine-tuning")
    parser.add_argument("--skip-impact", action="store_true", help="Skip impact classifier training")
    parser.add_argument("--skip-judge", action="store_true", help="Skip judge model training")
    parser.add_argument("--skip-kg", action="store_true", help="Skip knowledge graph building")
    args = parser.parse_args()

    start = time.time()
    print("=" * 60)
    print("  ELEVATE v3 — Full Training Pipeline")
    print("=" * 60)

    # ---- Step 1: Build training pairs ----
    print("\n[1/6] Building training pairs from CSV data...")
    from data_pipeline import build_resume_jd_pairs, mine_hard_negatives

    data_path = os.path.join(BACKEND_DIR, "data", "resume_data.csv")
    pairs = build_resume_jd_pairs(data_path)
    print(f"  ✓ Built {len(pairs)} training pairs")

    hard_negs = mine_hard_negatives(pairs)
    print(f"  ✓ Mined {len(hard_negs)} hard negatives")

    # ---- Step 2: Fine-tune bi-encoder ----
    if not args.skip_bi_encoder:
        print("\n[2/6] Fine-tuning bi-encoder...")
        from finetune_bi_encoder import finetune

        finetune(
            pairs=pairs,
            output_path=os.path.join(BACKEND_DIR, "models", "elevate-bi-encoder-v1"),
        )
    else:
        print("\n[2/6] Skipping bi-encoder (--skip-bi-encoder)")

    # ---- Step 3: Fine-tune cross-encoder ----
    if not args.skip_cross_encoder:
        print("\n[3/6] Fine-tuning cross-encoder...")
        from finetune_cross_encoder import finetune_cross_encoder

        finetune_cross_encoder(
            pairs=pairs,
            output_path=os.path.join(BACKEND_DIR, "models", "elevate-cross-encoder-v1"),
        )
    else:
        print("\n[3/6] Skipping cross-encoder (--skip-cross-encoder)")

    # ---- Step 4: Train impact classifier ----
    if not args.skip_impact:
        print("\n[4/6] Training impact classifier...")
        from train_impact_classifier import train_impact_classifier

        train_impact_classifier(
            output_path=os.path.join(BACKEND_DIR, "models", "impact-classifier-v1"),
        )
    else:
        print("\n[4/6] Skipping impact classifier (--skip-impact)")

    # ---- Step 5: Train judge ----
    if not args.skip_judge:
        print("\n[5/6] Training T5 judge model...")
        from train_judge import train_judge

        train_judge(
            pairs=pairs,
            output_path=os.path.join(BACKEND_DIR, "models", "elevate-judge-v1"),
        )
    else:
        print("\n[5/6] Skipping judge model (--skip-judge)")

    # ---- Step 6: Build knowledge graph ----
    if not args.skip_kg:
        print("\n[6/6] Building knowledge graph...")
        from models.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.enrich_from_resume_data(os.path.join(BACKEND_DIR, "data", "resume_data.csv"))
        print(f"  Graph: {kg.G.number_of_nodes()} nodes, {kg.G.number_of_edges()} edges")

        kg_path = os.path.join(BACKEND_DIR, "models", "knowledge_graph.pkl")
        with open(kg_path, "wb") as f:
            pickle.dump(kg, f)
        print(f"  ✓ Knowledge graph saved to {kg_path}")
    else:
        print("\n[6/6] Skipping knowledge graph (--skip-kg)")

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  Training complete in {elapsed / 60:.1f} minutes!")
    print(f"  All models saved to backend/models/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
