"""
Elevate v3 – Impact Classifier Training
==========================================
Trains a DistilBERT classifier on auto-labeled resume bullet points.

Labels (bootstrapped from heuristics):
  0 = DUTY:   "Responsible for maintaining backend services"
  1 = MIXED:  "Led migration to cloud infrastructure"
  2 = IMPACT: "Reduced API latency by 40%, saving $2M annually"

Data source: Resume.csv (2,484 resumes → thousands of extracted bullets)
Model: distilbert-base-uncased (66M params, ~400MB VRAM) — fits 2GB GPU
"""

import os
import sys
import random

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
)
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR

sys.path.insert(0, os.path.dirname(__file__))
from data_pipeline import extract_bullets_for_impact_training


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class BulletDataset(Dataset):
    """PyTorch dataset for bullet classification."""

    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item

    def __len__(self):
        return len(self.labels)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_impact_classifier(
    output_path: str = "models/impact-classifier-v1",
    epochs: int = 3,
    batch_size: int = 32,
    lr: float = 2e-5,
):
    """Full training pipeline for the impact/duty classifier."""

    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_path)
    os.makedirs(output_path, exist_ok=True)

    # --- Step 1: Extract and label bullets ---
    print("  Extracting bullets from Resume.csv...")
    bullets = extract_bullets_for_impact_training(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Resume.csv")
    )
    print(f"  Extracted {len(bullets)} bullets")

    if len(bullets) < 100:
        print("  WARNING: Very few bullets extracted. Check Resume.csv path.")
        return None

    # --- Step 2: Balance classes ---
    from collections import Counter

    label_counts = Counter(b["label"] for b in bullets)
    print(f"  Raw distribution: {dict(label_counts)}")

    per_label = {0: [], 1: [], 2: []}
    for b in bullets:
        per_label[b["label"]].append(b)

    min_count = min(len(v) for v in per_label.values())
    min_count = max(min_count, 50)  # At least 50 per class

    balanced = []
    for label_id, items in per_label.items():
        random.shuffle(items)
        balanced.extend(items[: min(min_count, len(items))])

    random.shuffle(balanced)
    print(f"  Balanced to {len(balanced)} bullets")

    # --- Step 3: Split ---
    split = int(len(balanced) * 0.85)
    train_data = balanced[:split]
    val_data = balanced[split:]

    train_texts = [b["text"] for b in train_data]
    train_labels = [b["label"] for b in train_data]
    val_texts = [b["text"] for b in val_data]
    val_labels = [b["label"] for b in val_data]

    # --- Step 4: Load model ---
    print("  Loading DistilBERT...")
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=3
    )

    train_dataset = BulletDataset(train_texts, train_labels, tokenizer)
    val_dataset = BulletDataset(val_texts, val_labels, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = LambdaLR(
        optimizer,
        lr_lambda=lambda step: max(0.0, 1.0 - step / total_steps),
    )

    # --- Step 5: Train ---
    print(f"  Training on {device} for {epochs} epochs...")
    best_val_acc = 0

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            total_loss += loss.item()

        # Validate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**batch)
                preds = outputs.logits.argmax(dim=-1)
                correct += (preds == batch["labels"]).sum().item()
                total += len(batch["labels"])

        val_acc = correct / max(total, 1)
        avg_loss = total_loss / max(len(train_loader), 1)
        print(f"    Epoch {epoch + 1}: loss={avg_loss:.4f}, val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model.save_pretrained(output_path)
            tokenizer.save_pretrained(output_path)

    print(f"  ✓ Best validation accuracy: {best_val_acc:.4f}")
    print(f"  ✓ Impact classifier saved to {output_path}")
    return model


if __name__ == "__main__":
    train_impact_classifier()
