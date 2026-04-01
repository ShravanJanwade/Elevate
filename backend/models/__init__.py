"""
Elevate v3 – Multi-Model Analysis Engine
==========================================
Each model in this package is a specialist:

  skill_taxonomy      → Understands skill relationships (Spring Boot ↔ Hibernate ↔ Java)
  jd_parser           → Parses JD into structured requirements with priority levels
  skill_scorer        → Taxonomy-aware skill matching (exact, synonym, related, domain)
  experience_matcher  → Matches experience bullets against JD responsibilities
  education_scorer    → Evaluates education relevance against role requirements
  semantic_engine     → Multi-strategy semantic similarity (sentence, paragraph, cross-attention)
  composite_scorer    → Orchestrates all models and produces final calibrated scores

v3 Additions:
  knowledge_graph     → In-memory NetworkX graph of companies, skills, industries
  layout_analyzer     → Heuristic resume layout quality scoring
  recruiter/          → Impact classifier, trajectory analyzer, pedigree scorer, judge model
"""

from .composite_scorer import CompositeScorer

__all__ = ["CompositeScorer"]
