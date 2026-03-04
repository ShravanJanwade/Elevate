import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

model = None


def _get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
    "git", "github", "gitlab",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "agile", "scrum", "kanban", "jira",
    "rest", "graphql", "microservices", "api",
    "html", "css", "sass",
    "linux", "bash", "powershell",
    "data analysis", "data engineering", "etl",
    "tableau", "power bi",
    "communication", "leadership", "teamwork", "problem solving",
]


def extract_keywords_from_jd(jd_text):
    
    jd_lower = jd_text.lower()
    found_skills = []

    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, jd_lower):
            found_skills.append(skill)

    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]{2,}\b", jd_text)
    extra_terms = set()
    for w in words:
        w_lower = w.lower()
        if w_lower not in ("the", "and", "for", "with", "that", "this", "are", "was",
                           "will", "can", "you", "our", "has", "have", "from", "your",
                           "experience", "ability", "strong", "work", "working", "team",
                           "role", "position", "company", "looking", "join", "about",
                           "must", "should", "requirements", "required", "preferred",
                           "responsibilities", "including", "including", "plus", "years",
                           "etc", "also"):
            if len(w_lower) > 2 and w_lower not in found_skills:
                extra_terms.add(w_lower)

    return found_skills, list(extra_terms)[:20]


def keyword_score(resume_sections, jd_text):
    
    primary_keywords, secondary_keywords = extract_keywords_from_jd(jd_text)
    all_keywords = primary_keywords + secondary_keywords

    if not all_keywords:
        return {"match_percentage": 0.0, "matched": [], "missing": [], "total_keywords": 0}

    resume_text = resume_sections.get("raw_text", "").lower()
    matched = []
    missing = []

    for kw in all_keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, resume_text):
            matched.append(kw)
        else:
            missing.append(kw)

    pct = (len(matched) / len(all_keywords)) * 100 if all_keywords else 0.0

    return {
        "match_percentage": round(pct, 1),
        "matched": matched,
        "missing": missing,
        "total_keywords": len(all_keywords),
    }


def semantic_score(resume_sections, jd_text):
    
    encoder = _get_model()
    bullets = resume_sections.get("bullet_points", [])

    if not bullets:
        raw = resume_sections.get("raw_text", "")
        sentences = [s.strip() for s in raw.split(".") if len(s.strip()) > 15]
        bullets = sentences[:20]

    if not bullets:
        return {"overall_score": 0.0, "bullet_scores": []}

    jd_embedding = encoder.encode([jd_text])
    bullet_embeddings = encoder.encode(bullets)

    similarities = cosine_similarity(bullet_embeddings, jd_embedding).flatten()

    bullet_scores = []
    for i, bullet in enumerate(bullets):
        bullet_scores.append({
            "text": bullet,
            "similarity": round(float(similarities[i]) * 100, 1),
        })

    bullet_scores.sort(key=lambda x: x["similarity"], reverse=True)

    overall = float(similarities.mean()) * 100

    return {
        "overall_score": round(overall, 1),
        "bullet_scores": bullet_scores,
    }


def full_analysis(resume_sections, jd_text):
    
    kw_result = keyword_score(resume_sections, jd_text)
    sem_result = semantic_score(resume_sections, jd_text)

    combined_score = (kw_result["match_percentage"] * 0.4) + (sem_result["overall_score"] * 0.6)

    return {
        "overall_score": round(combined_score, 1),
        "keyword_analysis": kw_result,
        "semantic_analysis": sem_result,
    }
