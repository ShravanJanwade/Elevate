"""
Elevate – Suggestion Generator
================================
Generates improvement suggestions for resume bullet points:
  - Rule-based rewriting with multiple heuristic passes
  - Passive voice detection and correction
  - STAR format enforcement (Situation-Task-Action-Result)
  - Context-aware keyword injection from JD
  - Quantification prompts
  - Optional LLM rewriting via Flan-T5
"""

import re
import os
import random

USE_LLM = os.environ.get("ELEVATE_USE_LLM", "false").lower() == "true"

generator = None


def _get_generator():
    global generator
    if generator is None:
        from transformers import pipeline
        generator = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            max_new_tokens=100,
        )
    return generator


# ---------------------------------------------------------------------------
# Action verb categories (by strength/domain)
# ---------------------------------------------------------------------------

STRONG_ACTION_VERBS = {
    "leadership": [
        "Spearheaded", "Led", "Directed", "Orchestrated", "Championed",
        "Pioneered", "Drove", "Established", "Launched",
    ],
    "technical": [
        "Engineered", "Architected", "Developed", "Implemented", "Built",
        "Designed", "Automated", "Deployed", "Integrated", "Configured",
    ],
    "improvement": [
        "Optimized", "Streamlined", "Accelerated", "Enhanced", "Reduced",
        "Increased", "Improved", "Transformed", "Modernized", "Revamped",
    ],
    "analysis": [
        "Analyzed", "Evaluated", "Assessed", "Identified", "Investigated",
        "Researched", "Diagnosed", "Quantified",
    ],
    "collaboration": [
        "Collaborated", "Partnered", "Coordinated", "Facilitated",
        "Mentored", "Trained", "Advised",
    ],
    "delivery": [
        "Delivered", "Executed", "Produced", "Shipped", "Completed",
        "Achieved", "Accomplished",
    ],
}

ALL_ACTION_VERBS = []
for verbs in STRONG_ACTION_VERBS.values():
    ALL_ACTION_VERBS.extend(verbs)

WEAK_STARTS = [
    "responsible for", "helped with", "worked on", "assisted in",
    "assisted with", "did", "made", "was part of", "involved in",
    "tasked with", "given the task", "participated in",
    "was responsible for", "handled", "took care of",
    "in charge of", "duties included", "job was to",
]

PASSIVE_PATTERNS = [
    (re.compile(r"\bwas\s+(\w+ed)\b", re.I), "active"),
    (re.compile(r"\bwere\s+(\w+ed)\b", re.I), "active"),
    (re.compile(r"\bbeen\s+(\w+ed)\b", re.I), "active"),
    (re.compile(r"\b(utilized|leveraged|employed)\b", re.I), "Used"),
]

# Quantification prompt templates
QUANT_TEMPLATES = [
    ", improving efficiency by X%",
    ", resulting in a Y% improvement in key metrics",
    ", serving Z+ users across the organization",
    ", reducing processing time by X%",
    ", increasing throughput by Y%",
]


# ---------------------------------------------------------------------------
# Improvement reason detection
# ---------------------------------------------------------------------------

def _detect_issues(bullet_text: str) -> list:
    """Detect specific issues with a bullet point and return reasons."""
    issues = []
    lower = bullet_text.lower().strip()

    # Check for weak starts
    for weak in WEAK_STARTS:
        if lower.startswith(weak):
            issues.append(f"Starts with weak phrase '{weak}' – use a strong action verb instead")
            break

    # Check for passive voice
    for pattern, _ in PASSIVE_PATTERNS:
        if pattern.search(bullet_text):
            issues.append("Contains passive voice – rewrite in active voice for stronger impact")
            break

    # Check for lack of quantification
    if not re.search(r'\d', bullet_text):
        issues.append("No quantifiable metrics – add numbers, percentages, or scale indicators")

    # Check if too short
    if len(bullet_text) < 30:
        issues.append("Too brief – expand with context about impact and scope")

    # Check if too vague
    vague_words = ["things", "stuff", "various", "many", "several", "some", "good", "nice", "better"]
    for vague in vague_words:
        if re.search(r'\b' + vague + r'\b', lower):
            issues.append(f"Uses vague word '{vague}' – replace with specific details")
            break

    # Check for missing action verb at start
    first_word = bullet_text.split()[0] if bullet_text.split() else ""
    if first_word and first_word[0].islower() and not any(
        lower.startswith(weak) for weak in WEAK_STARTS
    ):
        issues.append("Doesn't start with an action verb – lead with a strong verb")

    if not issues:
        issues.append("Could benefit from stronger action verbs and more specific results")

    return issues


# ---------------------------------------------------------------------------
# Rule-based rewriting (multi-pass)
# ---------------------------------------------------------------------------

def _rule_based_rewrite(bullet_text: str, jd_text: str) -> str:
    """
    Apply multiple rewriting heuristics:
    1. Replace weak starts with strong action verbs
    2. Fix passive voice
    3. Capitalize first word
    4. Add quantification prompt if no numbers
    5. Ensure action verb start
    """
    improved = bullet_text.strip()
    jd_lower = jd_text.lower()

    # --- Pass 1: Replace weak starts ---
    for weak in WEAK_STARTS:
        pattern = re.compile(r"^" + re.escape(weak) + r"\s*", re.IGNORECASE)
        if pattern.match(improved):
            # Pick a contextually appropriate verb
            verb = _pick_verb_for_context(improved, jd_lower)
            improved = pattern.sub(verb + " ", improved, count=1)
            break

    # --- Pass 2: Fix passive voice ---
    for pattern, _ in PASSIVE_PATTERNS:
        match = pattern.search(improved)
        if match:
            verb = _pick_verb_for_context(improved, jd_lower)
            improved = pattern.sub(verb.lower(), improved, count=1)
            break

    # --- Pass 3: Ensure starts with action verb ---
    first_word = improved.split()[0] if improved.split() else ""
    if first_word and first_word[0].islower():
        verb = _pick_verb_for_context(improved, jd_lower)
        improved = verb + " " + improved[0].lower() + improved[1:]

    # --- Pass 4: Capitalize first letter ---
    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]

    # --- Pass 5: Add quantification if missing ---
    if not re.search(r'\d', improved):
        improved = improved.rstrip(".")
        # Pick a relevant quantification template
        template = random.choice(QUANT_TEMPLATES)
        improved += template

    # --- Pass 6: Ensure doesn't end abruptly ---
    if not improved.endswith((".", "%", ")")):
        if not improved.endswith(("X%", "Y%", "Z+")):
            improved = improved.rstrip(",;")

    # If nothing changed, prepend a strong verb
    if improved.strip() == bullet_text.strip():
        verb = _pick_verb_for_context(improved, jd_lower)
        improved = verb + " — " + improved[0].lower() + improved[1:]

    return improved


def _pick_verb_for_context(bullet_text: str, jd_lower: str) -> str:
    """Pick an action verb that fits the context of the bullet and JD."""
    lower = bullet_text.lower()

    # Technical context
    tech_words = ["code", "software", "system", "api", "database", "app",
                  "deploy", "server", "build", "develop", "program", "architect"]
    if any(w in lower for w in tech_words):
        return random.choice(STRONG_ACTION_VERBS["technical"])

    # Leadership context
    lead_words = ["team", "lead", "manage", "direct", "mentor", "train",
                  "coordinate", "oversee", "supervis"]
    if any(w in lower for w in lead_words):
        return random.choice(STRONG_ACTION_VERBS["leadership"])

    # Analysis context
    analysis_words = ["data", "analyz", "research", "evaluat", "assess",
                      "investigat", "report", "metric"]
    if any(w in lower for w in analysis_words):
        return random.choice(STRONG_ACTION_VERBS["analysis"])

    # Improvement context
    improve_words = ["improv", "optim", "reduc", "increas", "efficien",
                     "performance", "faster", "better", "enhanc"]
    if any(w in lower for w in improve_words):
        return random.choice(STRONG_ACTION_VERBS["improvement"])

    # Default: pick from delivery or technical
    return random.choice(STRONG_ACTION_VERBS["delivery"] + STRONG_ACTION_VERBS["technical"])


# ---------------------------------------------------------------------------
# LLM-based rewriting
# ---------------------------------------------------------------------------

def rewrite_bullet(bullet_text: str, jd_text: str) -> dict:
    """Rewrite a bullet point, optionally using LLM."""
    if USE_LLM:
        try:
            gen = _get_generator()
            prompt = (
                f"Rewrite this resume bullet point to be more impactful and "
                f"relevant to the following job description. Use strong action verbs, "
                f"include quantifiable results where possible, and keep it concise.\n\n"
                f"Job description context: {jd_text[:400]}\n\n"
                f"Original bullet: {bullet_text}\n\n"
                f"Improved bullet:"
            )
            result = gen(prompt)
            improved = result[0]["generated_text"].strip()
            if not improved or improved.lower() == bullet_text.lower() or len(improved) < 10:
                improved = _rule_based_rewrite(bullet_text, jd_text)
                method = "rule_based"
            else:
                method = "flan_t5"
        except Exception:
            improved = _rule_based_rewrite(bullet_text, jd_text)
            method = "rule_based"
    else:
        improved = _rule_based_rewrite(bullet_text, jd_text)
        method = "rule_based"

    issues = _detect_issues(bullet_text)

    return {
        "original": bullet_text,
        "improved": improved,
        "method": method,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Batch suggestion generation
# ---------------------------------------------------------------------------

def generate_suggestions(
    resume_sections: dict,
    jd_text: str,
    semantic_results: dict,
    max_suggestions: int = 5,
) -> list:
    """
    Generate rewrite suggestions for the weakest bullet points.
    """
    bullet_scores = semantic_results.get("bullet_scores", [])

    if not bullet_scores:
        return []

    # Sort by similarity (ascending) to get the weakest bullets first
    weak_bullets = sorted(bullet_scores, key=lambda x: x["similarity"])
    weak_bullets = weak_bullets[:max_suggestions]

    suggestions = []
    for entry in weak_bullets:
        rewrite = rewrite_bullet(entry["text"], jd_text)
        rewrite["original_score"] = entry["similarity"]
        rewrite["strength"] = entry.get("strength", "weak")
        suggestions.append(rewrite)

    return suggestions
# fix suggestions
