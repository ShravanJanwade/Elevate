"""
Elevate v3 – T5 Judge Training
=================================
Fine-tunes Flan-T5-small (60M params) to act as a recruiter evaluation judge.

The judge receives a structured evidence packet (neural scores, skill coverage,
impact density, trajectory flags) and generates a Decision + Reasoning string.

This replaces the need for an external LLM API (GPT-4o).
Model: google/flan-t5-small (~250MB VRAM) — fits 2GB GPU.
"""

import os
import sys
import random

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration

sys.path.insert(0, os.path.dirname(__file__))
from data_pipeline import build_resume_jd_pairs


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class JudgeDataset(Dataset):
    """Dataset of (evidence_packet → evaluation) pairs."""

    def __init__(self, inputs, outputs, tokenizer, max_input=384, max_output=192):
        self.input_enc = tokenizer(
            inputs,
            max_length=max_input,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        self.output_enc = tokenizer(
            outputs,
            max_length=max_output,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )

    def __getitem__(self, idx):
        labels = self.output_enc["input_ids"][idx].clone()
        labels[labels == 0] = -100  # Ignore padding in loss
        return {
            "input_ids": self.input_enc["input_ids"][idx],
            "attention_mask": self.input_enc["attention_mask"][idx],
            "labels": labels,
        }

    def __len__(self):
        return len(self.input_enc["input_ids"])


# ---------------------------------------------------------------------------
# Training data generation
# ---------------------------------------------------------------------------

def _generate_judge_training_data(pairs):
    """
    Convert scored pairs into (input_evidence, output_evaluation) strings.

    The input mimics what the model will see at inference time:
      a structured summary of all pipeline scores.

    The output is the evaluation the judge should generate.
    """
    inputs = []
    outputs = []

    # Shuffle to mix score distributions
    random.shuffle(pairs)

    for p in pairs:
        score = p["score"]
        resume_snippet = p["resume"][:250]
        jd_snippet = p["jd"][:150]

        # Simulate sub-system scores based on the overall matched_score
        skill_cov = min(100, int(score * 100 + random.randint(-10, 10)))
        impact_pct = max(0, min(100, int(score * 80 + random.randint(-15, 20))))
        trajectory = max(0, min(100, int(60 + random.randint(-20, 30))))

        evidence = (
            f"Evaluate candidate for this role. "
            f"Match Score: {score * 100:.0f}/100 | "
            f"Skill Coverage: {skill_cov}% | "
            f"Impact Density: {impact_pct}% | "
            f"Career Score: {trajectory}/100 | "
            f"Resume: {resume_snippet} | "
            f"JD: {jd_snippet}"
        )

        # Generate target evaluation based on score ranges
        if score >= 0.8:
            decision = "SHORTLIST"
            rationale = (
                "Strong match. Candidate demonstrates relevant skills and experience. "
                "Skills coverage is excellent. Resume shows quantified impact. "
                "Recommend advancing to interview stage."
            )
        elif score >= 0.65:
            decision = "SHORTLIST"
            rationale = (
                "Good match with solid skill alignment. "
                "Some areas could be stronger but overall a viable candidate. "
                "Recommend interview with focus on specific technical depth."
            )
        elif score >= 0.5:
            decision = "MAYBE"
            rationale = (
                "Moderate match. Candidate has some relevant experience but gaps exist "
                "in key required skills. Consider if candidate pool is limited. "
                "Would benefit from additional screening."
            )
        elif score >= 0.35:
            decision = "MAYBE"
            rationale = (
                "Below average match. Limited overlap in required skills and experience. "
                "Resume lacks quantified impact. Consider only if no stronger candidates."
            )
        else:
            decision = "REJECT"
            rationale = (
                "Weak match. Significant gaps in required skills and experience level. "
                "Resume does not demonstrate relevant qualifications for this role. "
                "Not recommended for this position."
            )

        output_text = f"Decision: {decision} | Score: {score * 100:.0f}/100 | {rationale}"

        inputs.append(evidence)
        outputs.append(output_text)

    return inputs, outputs


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_judge(
    pairs=None,
    output_path: str = "models/elevate-judge-v1",
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 3e-4,
):
    """Fine-tune Flan-T5-small as the recruiter evaluation judge."""

    if pairs is None:
        print("  Loading training pairs from resume_data.csv...")
        pairs = build_resume_jd_pairs()

    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_path)
    os.makedirs(output_path, exist_ok=True)

    print(f"  Generating judge training data from {len(pairs)} pairs...")
    inputs, outputs = _generate_judge_training_data(pairs)
    print(f"  Generated {len(inputs)} training examples")

    print("  Loading Flan-T5-small...")
    tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
    model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")

    dataset = JudgeDataset(inputs, outputs, tokenizer)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    print(f"  Training on {device} for {epochs} epochs...")
    model.train()

    for epoch in range(epochs):
        total_loss = 0
        for i, batch in enumerate(loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs_model = model(**batch)
            loss = outputs_model.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
            total_loss += loss.item()

            if (i + 1) % 100 == 0:
                print(f"    Step {i + 1}/{len(loader)}: loss={loss.item():.4f}")

        avg_loss = total_loss / max(len(loader), 1)
        print(f"    Epoch {epoch + 1}: avg_loss={avg_loss:.4f}")

    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    print(f"  ✓ Judge model saved to {output_path}")
    return model


if __name__ == "__main__":
    train_judge()
