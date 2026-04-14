"""
Elevate v3 – Bi-Encoder Fine-Tuning
======================================
Fine-tunes all-MiniLM-L6-v2 on resume-JD pairs from resume_data.csv
using CosineSimilarityLoss with continuous matched_score labels.

This teaches the bi-encoder that resume embeddings should be CLOSE to
relevant JD embeddings and FAR from irrelevant ones in cosine space.

Model: all-MiniLM-L6-v2 (22M params, ~200MB VRAM) — fits 2GB GPU.
"""

import os
import sys
import random

from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    evaluation,
)
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(__file__))
from data_pipeline import build_resume_jd_pairs


def finetune(
    pairs=None,
    base_model: str = "all-MiniLM-L6-v2",
    output_path: str = "models/elevate-bi-encoder-v1",
    epochs: int = 4,
    batch_size: int = 32,
    lr: float = 2e-5,
):
    """Fine-tune the bi-encoder on resume-JD similarity pairs."""
    if pairs is None:
        print("  Loading training pairs from resume_data.csv...")
        pairs = build_resume_jd_pairs()

    print(f"  Total pairs: {len(pairs)}")

    # Make output path absolute relative to backend/
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    random.shuffle(pairs)
    split = int(len(pairs) * 0.9)

    train_examples = [
        InputExample(texts=[p["resume"], p["jd"]], label=p["score"])
        for p in pairs[:split]
    ]
    eval_examples = [
        InputExample(texts=[p["resume"], p["jd"]], label=p["score"])
        for p in pairs[split:]
    ]

    print(f"  Train: {len(train_examples)}, Eval: {len(eval_examples)}")
    print(f"  Loading base model: {base_model}...")

    model = SentenceTransformer(base_model)

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.CosineSimilarityLoss(model)

    evaluator = evaluation.EmbeddingSimilarityEvaluator.from_input_examples(
        eval_examples, name="val"
    )

    print(f"  Fine-tuning for {epochs} epochs...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=epochs,
        warmup_steps=min(100, len(train_dataloader)),
        optimizer_params={"lr": lr},
        evaluation_steps=max(1, len(train_dataloader) // 2),
        output_path=output_path,
        save_best_model=True,
        show_progress_bar=True,
    )

    print(f"  ✓ Fine-tuned bi-encoder saved to {output_path}")
    return model


if __name__ == "__main__":
    finetune()
