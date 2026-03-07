import re
import os

USE_LLM = os.environ.get("ELEVATE_USE_LLM", "false").lower() == "true"

generator = None


def _get_generator():
    global generator
    if generator is None:
        from transformers import pipeline
        generator = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            max_new_tokens=80,
        )
    return generator


ACTION_VERBS = [
    "Spearheaded", "Engineered", "Optimized", "Developed", "Implemented",
    "Architected", "Streamlined", "Automated", "Delivered", "Designed",
    "Led", "Drove", "Reduced", "Increased", "Built", "Launched",
]

WEAK_STARTS = [
    "responsible for", "helped with", "worked on", "assisted in",
    "did", "made", "was part of", "involved in", "tasked with",
]


def _rule_based_rewrite(bullet_text, jd_text):
    improved = bullet_text.strip()

    for weak in WEAK_STARTS:
        pattern = re.compile(re.escape(weak), re.IGNORECASE)
        if pattern.search(improved):
            verb = ACTION_VERBS[hash(bullet_text) % len(ACTION_VERBS)]
            improved = pattern.sub(verb.lower() + " ", improved, count=1)
            break

    first_word = improved.split()[0] if improved.split() else ""
    if first_word and first_word[0].islower():
        verb = ACTION_VERBS[hash(bullet_text) % len(ACTION_VERBS)]
        improved = verb + " " + improved[0].lower() + improved[1:]

    if not re.search(r'\d', improved):
        improved = improved.rstrip(".")
        improved += ", resulting in measurable improvements"

    if improved == bullet_text.strip():
        verb = ACTION_VERBS[hash(bullet_text) % len(ACTION_VERBS)]
        improved = verb + " — " + improved[0].lower() + improved[1:]

    return improved


def rewrite_bullet(bullet_text, jd_text):
    if USE_LLM:
        gen = _get_generator()
        prompt = (
            f"Rewrite this resume bullet point to be more impactful and "
            f"relevant to the following job description. Use strong action verbs, "
            f"include quantifiable results where possible, and keep it concise.\n\n"
            f"Job description context: {jd_text[:300]}\n\n"
            f"Original bullet: {bullet_text}\n\n"
            f"Improved bullet:"
        )
        result = gen(prompt)
        improved = result[0]["generated_text"].strip()
        if not improved or improved.lower() == bullet_text.lower():
            improved = _rule_based_rewrite(bullet_text, jd_text)
    else:
        improved = _rule_based_rewrite(bullet_text, jd_text)

    return {
        "original": bullet_text,
        "improved": improved,
    }


def generate_suggestions(resume_sections, jd_text, semantic_results, max_suggestions=5):
    bullet_scores = semantic_results.get("bullet_scores", [])

    if not bullet_scores:
        return []

    weak_bullets = sorted(bullet_scores, key=lambda x: x["similarity"])
    weak_bullets = weak_bullets[:max_suggestions]

    suggestions = []
    for entry in weak_bullets:
        rewrite = rewrite_bullet(entry["text"], jd_text)
        rewrite["original_score"] = entry["similarity"]
        suggestions.append(rewrite)

    return suggestions
