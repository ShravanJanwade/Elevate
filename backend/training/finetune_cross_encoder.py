"""
Elevate v3 – Cross-Encoder Fine-Tuning
=========================================
Fine-tunes ms-marco-MiniLM-L-6-v2 on resume-JD pairs from resume_data.csv.

The cross-encoder processes (resume, JD) jointly through the transformer,
producing a relevance score. This is the PRECISION component that refines
the bi-encoder's fast approximate retrieval.

Model: ms-marco-MiniLM-L-6-v2 (22M params, ~200MB VRAM) — fits 2GB GPU.
"""

import os
import sys
import random

from sentence_transformers import CrossEncoder, InputExample
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(__file__))
from data_pipeline import build_resume_jd_pairs


def finetune_cross_encoder(
    pairs=None,
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    output_path: str = "models/elevate-cross-encoder-v1",
    epochs: int = 3,
    batch_size: int = 16,
    lr: float = 1e-5,
):
    """Fine-tune the cross-encoder on resume-JD relevance pairs."""
    if pairs is None:
        print("  Loading training pairs from resume_data.csv...")
        pairs = build_resume_jd_pairs()

    print(f"  Total pairs: {len(pairs)}")

    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    random.shuffle(pairs)

    train_samples = [
        InputExample(texts=[p["resume"][:256], p["jd"][:256]], label=p["score"])
        for p in pairs
    ]

    print(f"  Train samples: {len(train_samples)}")
    print(f"  Loading base model: {base_model}...")

    model = CrossEncoder(base_model, num_labels=1, max_length=512)

    train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=batch_size)

    print(f"  Fine-tuning for {epochs} epochs...")
    model.fit(
        train_dataloader=train_dataloader,
        epochs=epochs,
        warmup_steps=min(50, len(train_dataloader)),
        optimizer_params={"lr": lr},
        output_path=output_path,
        save_best_model=True,
        show_progress_bar=True,
    )

    print(f"  ✓ Fine-tuned cross-encoder saved to {output_path}")
    return model


if __name__ == "__main__":
    finetune_cross_encoder()
