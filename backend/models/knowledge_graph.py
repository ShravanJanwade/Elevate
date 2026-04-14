"""
Elevate v3 – Knowledge Graph
===============================
In-memory knowledge graph built with NetworkX.
No external database (Neo4j) required.

Data Sources:
  1. Manually seeded company profiles for 25+ companies
     (from interview-experiences GitHub repo)
  2. resume_data.csv (9,544 company→skill→role mappings)

Entity Types: company, role, skill, industry, trait
Relations: OPERATES_IN, KNOWN_FOR, USES_SKILL, HIRES_FOR, RELATED_TO
"""

import os
import re
import ast
import pickle
from typing import Dict, List, Optional

import networkx as nx
import pandas as pd


# ============================================================================
# Company Profiles — seeded from interview-experiences GitHub repo
# Each entry contains: industry, tier, culture, scale, known_for (tech/traits),
# interview_style, and any roles found in the repo.
# ============================================================================

COMPANY_PROFILES = {
    # --- Tier 1: FAANG / Top Tech ---
    "google": {
        "industry": "tech", "tier": 1, "culture": "engineering-heavy",
        "scale": "public",
        "known_for": ["distributed-systems", "ml-at-scale", "cloud", "search",
                      "infrastructure", "kubernetes", "tensorflow", "go", "python"],
        "interview_style": "algorithmic + system-design",
        "roles": ["Technical Solutions Engineer"],
    },
    "amazon": {
        "industry": "tech", "tier": 1, "culture": "ownership-driven",
        "scale": "public",
        "known_for": ["cloud-aws", "microservices", "scale", "distributed-systems",
                      "java", "dynamodb", "s3", "leadership-principles"],
        "interview_style": "behavioral-LP + coding + system-design",
        "roles": ["SDE1", "SDE2", "Business Analyst"],
    },
    "microsoft": {
        "industry": "tech", "tier": 1, "culture": "growth-mindset",
        "scale": "public",
        "known_for": ["cloud-azure", "enterprise", "ai", "dotnet", "c-sharp",
                      "typescript", "vscode", "teams", "windows"],
        "interview_style": "coding + design + behavioral",
    },

    # --- Tier 1: Finance ---
    "goldman sachs": {
        "industry": "finance", "tier": 1, "culture": "performance-driven",
        "scale": "public",
        "known_for": ["fintech", "quant", "risk", "trading-systems", "java",
                      "python", "low-latency", "securities"],
        "interview_style": "coding + finance domain",
        "aliases": ["gs"],
    },
    "jp morgan": {
        "industry": "finance", "tier": 1, "culture": "enterprise",
        "scale": "public",
        "known_for": ["fintech", "trading-systems", "data-engineering", "java",
                      "python", "spring-boot", "cloud", "athena"],
        "interview_style": "coding + behavioral + domain",
        "roles": ["Python Developer", "Software Engineering"],
        "aliases": ["jpmc", "jp morgan chase"],
    },
    "morgan stanley": {
        "industry": "finance", "tier": 1, "culture": "enterprise",
        "scale": "public",
        "known_for": ["fintech", "low-latency", "risk-systems", "java",
                      "python", "fixed-income", "wealth-management"],
        "interview_style": "coding + technical depth",
        "roles": ["Python Developer"],
    },
    "blackrock": {
        "industry": "finance", "tier": 1, "culture": "quant-driven",
        "scale": "public",
        "known_for": ["aladdin", "risk", "portfolio-management", "python",
                      "data-engineering", "quantitative-analysis"],
        "interview_style": "coding + quant + system-design",
    },
    "visa": {
        "industry": "fintech", "tier": 1, "culture": "engineering",
        "scale": "public",
        "known_for": ["payments", "security", "scale", "java", "microservices",
                      "distributed-systems", "real-time-processing"],
        "interview_style": "coding + system-design",
    },

    # --- Tier 1: Other ---
    "samsung": {
        "industry": "electronics", "tier": 1, "culture": "hardware-software",
        "scale": "public",
        "known_for": ["ml", "embedded", "computer-vision", "deep-learning",
                      "c-plus-plus", "python", "android", "iot"],
        "interview_style": "coding + ML + domain",
        "roles": ["ML-DL Engineer"],
    },
    "deloitte": {
        "industry": "consulting", "tier": 1, "culture": "consulting",
        "scale": "public",
        "known_for": ["strategy", "audit", "tech-consulting", "python",
                      "data-analytics", "cloud", "sap", "enterprise-solutions"],
        "interview_style": "behavioral + case + technical",
        "roles": ["Python Developer"],
    },

    # --- Tier 2: Strong Tech ---
    "cisco": {
        "industry": "networking", "tier": 2, "culture": "enterprise",
        "scale": "public",
        "known_for": ["networking", "security", "collaboration", "python",
                      "c", "linux", "embedded", "cloud-networking", "sdwan"],
        "interview_style": "coding + networking domain",
        "roles": ["Software Engineer", "Senior Software Engineer"],
    },
    "vmware": {
        "industry": "tech", "tier": 2, "culture": "engineering",
        "scale": "public",
        "known_for": ["virtualization", "cloud", "kubernetes", "esxi",
                      "nsx", "vsan", "golang", "python"],
        "interview_style": "coding + system knowledge",
        "roles": ["Technical Support Engineer"],
    },
    "walmart": {
        "industry": "retail", "tier": 2, "culture": "data-driven",
        "scale": "public",
        "known_for": ["data-engineering", "supply-chain", "ecommerce",
                      "spark", "hadoop", "java", "python", "kafka"],
        "interview_style": "coding + data engineering",
        "roles": ["Data Engineer"],
    },
    "hrt": {
        "industry": "finance", "tier": 1, "culture": "quant-trading",
        "scale": "private",
        "known_for": ["quantitative-trading", "low-latency", "c-plus-plus",
                      "python", "algo-trading", "statistics"],
        "interview_style": "math + coding + probability",
        "aliases": ["hudson river trading"],
    },
    "alphagrep": {
        "industry": "finance", "tier": 2, "culture": "quant-trading",
        "scale": "private",
        "known_for": ["algorithmic-trading", "python", "c-plus-plus",
                      "quantitative-analysis", "low-latency"],
        "interview_style": "coding + quant",
        "roles": ["Python Developer"],
    },

    # --- Tier 2: Consulting / IT Services ---
    "accenture": {
        "industry": "consulting", "tier": 2, "culture": "consulting",
        "scale": "public",
        "known_for": ["enterprise-solutions", "sap", "integration", "cloud",
                      "digital-transformation", "python", "java"],
        "interview_style": "behavioral + technical",
        "roles": ["Python Developer", "SAP Consultant"],
    },
    "tcs": {
        "industry": "it-services", "tier": 2, "culture": "services",
        "scale": "public",
        "known_for": ["enterprise-it", "outsourcing", "support", "java",
                      "python", "mainframe", "testing"],
        "interview_style": "coding + HR",
        "roles": ["Python Developer"],
    },
    "infosys": {
        "industry": "it-services", "tier": 2, "culture": "services",
        "scale": "public",
        "known_for": ["digital-transformation", "consulting", "ai", "java",
                      "python", "cloud", "automation"],
        "interview_style": "coding + aptitude",
        "roles": ["Python Developer"],
    },
    "persistent": {
        "industry": "it-services", "tier": 3, "culture": "product-engineering",
        "scale": "public",
        "known_for": ["product-engineering", "healthcare-tech", "cloud",
                      "java", "python", "devops"],
        "interview_style": "coding + domain",
    },
    "virtusa": {
        "industry": "it-services", "tier": 3, "culture": "services",
        "scale": "public",
        "known_for": ["digital-engineering", "bfsi", "healthcare",
                      "java", "python", "cloud"],
        "interview_style": "coding + project discussion",
    },

    # --- Tier 2-3: Other ---
    "dassault systems": {
        "industry": "tech", "tier": 2, "culture": "engineering",
        "scale": "public",
        "known_for": ["3d-design", "plm", "simulation", "catia",
                      "solidworks", "python", "c-plus-plus"],
        "interview_style": "coding + domain",
        "roles": ["Python Developer"],
        "aliases": ["dassault"],
    },
    "blue sky analytics": {
        "industry": "data-analytics", "tier": 3, "culture": "startup",
        "scale": "startup",
        "known_for": ["geospatial", "remote-sensing", "data-science",
                      "python", "machine-learning", "satellite-data"],
        "interview_style": "ML + data science",
        "roles": ["Data Scientist"],
    },
    "disecto": {
        "industry": "tech", "tier": 3, "culture": "startup",
        "scale": "startup",
        "known_for": ["ai", "computer-vision", "deep-learning",
                      "python", "pytorch"],
        "interview_style": "coding + ML",
        "roles": ["Software Engineer"],
    },
    "kisan network": {
        "industry": "agritech", "tier": 3, "culture": "startup",
        "scale": "startup",
        "known_for": ["agritech", "supply-chain", "python", "django",
                      "data-analytics"],
        "interview_style": "coding + product",
    },
    "luxpmsoft": {
        "industry": "tech", "tier": 3, "culture": "startup",
        "scale": "startup",
        "known_for": ["computer-vision", "3d-reconstruction", "ar-vr",
                      "python", "deep-learning", "opencv"],
        "interview_style": "portfolio + technical",
        "roles": ["Data Scientist", "Computer Vision Engineer"],
    },
    "streamhub": {
        "industry": "ad-tech", "tier": 3, "culture": "startup",
        "scale": "startup",
        "known_for": ["ad-tech", "streaming", "real-time-analytics",
                      "python", "big-data"],
        "interview_style": "coding + system design",
    },
    "pwc": {
        "industry": "consulting", "tier": 1, "culture": "consulting",
        "scale": "public",
        "known_for": ["audit", "tax", "consulting", "pyspark",
                      "data-engineering", "cloud", "analytics"],
        "interview_style": "behavioral + technical",
        "roles": ["PySpark Developer", "Data Engineer"],
        "aliases": ["pricewaterhousecoopers"],
    },
    "bp": {
        "industry": "energy", "tier": 2, "culture": "enterprise",
        "scale": "public",
        "known_for": ["energy", "data-engineering", "cloud", "sustainability",
                      "python", "spark", "azure"],
        "interview_style": "technical + behavioral",
        "roles": ["Data Engineer"],
    },
}


# ============================================================================
# Knowledge Graph Class
# ============================================================================

class KnowledgeGraph:
    """
    In-memory knowledge graph using NetworkX.
    No external database — perfect for a course project.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self._alias_map: Dict[str, str] = {}
        self._build_graph()

    def _build_graph(self):
        """Build graph from seeded company profiles."""
        for company, profile in COMPANY_PROFILES.items():
            self.G.add_node(company, type="company", **{
                k: v for k, v in profile.items()
                if k not in ("known_for", "roles", "aliases")
            })

            # Build alias map
            if "aliases" in profile:
                for alias in profile["aliases"]:
                    self._alias_map[alias.lower()] = company

            # Industry edges
            ind = profile["industry"]
            if not self.G.has_node(ind):
                self.G.add_node(ind, type="industry")
            self.G.add_edge(company, ind, relation="OPERATES_IN")

            # Known-for trait edges
            for trait in profile.get("known_for", []):
                if not self.G.has_node(trait):
                    self.G.add_node(trait, type="trait")
                self.G.add_edge(company, trait, relation="KNOWN_FOR")

            # Role edges
            for role in profile.get("roles", []):
                role_lower = role.lower()
                if not self.G.has_node(role_lower):
                    self.G.add_node(role_lower, type="role")
                self.G.add_edge(company, role_lower, relation="HIRES_FOR")

    def _resolve(self, name: str) -> str:
        """Resolve company name including aliases."""
        name = name.strip().lower()
        if self.G.has_node(name):
            return name
        if name in self._alias_map:
            return self._alias_map[name]
        # Fuzzy match
        for node in self.G.nodes():
            if self.G.nodes[node].get("type") != "company":
                continue
            if name in node or node in name:
                return node
        return name

    def enrich_from_resume_data(self, csv_path: str = "data/resume_data.csv"):
        """Add company→skill edges from resume_data.csv."""
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            print(f"  Warning: Could not load {csv_path}")
            return

        for _, row in df.iterrows():
            companies_str = str(row.get("professional_company_names", ""))
            skills_str = str(row.get("skills", ""))
            position_str = str(row.get("positions", ""))

            try:
                companies = ast.literal_eval(companies_str) if companies_str.startswith("[") else [companies_str]
            except Exception:
                companies = [companies_str]

            try:
                skills = ast.literal_eval(skills_str) if skills_str.startswith("[") else skills_str.split(",")
            except Exception:
                skills = skills_str.split(",")

            for comp in companies:
                if comp is None:
                    continue
                comp_clean = comp.strip().lower()
                if len(comp_clean) < 2 or comp_clean == "nan":
                    continue

                resolved = self._resolve(comp_clean)
                if not self.G.has_node(resolved):
                    self.G.add_node(resolved, type="company")

                for skill in skills:
                    skill_clean = skill.strip().lower()
                    if len(skill_clean) < 2 or skill_clean == "nan":
                        continue
                    if not self.G.has_node(skill_clean):
                        self.G.add_node(skill_clean, type="skill")
                    if not self.G.has_edge(resolved, skill_clean):
                        self.G.add_edge(resolved, skill_clean, relation="USES_SKILL", count=1)
                    else:
                        self.G[resolved][skill_clean]["count"] = \
                            self.G[resolved][skill_clean].get("count", 1) + 1

    # ----- Query methods -----

    def get_company_context(self, company_name: str) -> str:
        """Generate enriched textual context for embedding injection."""
        name = self._resolve(company_name)

        if not self.G.has_node(name):
            return ""

        data = self.G.nodes[name]
        skills = []
        industries = []

        for _, target, edge_data in self.G.out_edges(name, data=True):
            rel = edge_data.get("relation", "")
            if rel in ("USES_SKILL", "KNOWN_FOR"):
                skills.append(target)
            elif rel == "OPERATES_IN":
                industries.append(target)

        parts = [f"Company: {name.title()}"]
        if industries:
            parts.append(f"Industry: {', '.join(industries)}")
        if data.get("tier"):
            parts.append(f"Tier: {data['tier']}")
        if data.get("culture"):
            parts.append(f"Culture: {data['culture']}")
        if data.get("interview_style"):
            parts.append(f"Interview: {data['interview_style']}")
        if skills:
            parts.append(f"Tech: {', '.join(skills[:20])}")

        return " | ".join(parts)

    def get_company_tier(self, company_name: str) -> int:
        """Get company tier (1=top, 2=strong, 3=other)."""
        name = self._resolve(company_name)
        if self.G.has_node(name):
            return self.G.nodes[name].get("tier", 3)
        return 3

    def get_company_industry(self, company_name: str) -> str:
        """Get company's primary industry."""
        name = self._resolve(company_name)
        if not self.G.has_node(name):
            return "unknown"
        for _, target, data in self.G.out_edges(name, data=True):
            if data.get("relation") == "OPERATES_IN":
                return target
        return "unknown"

    def get_company_skills(self, company_name: str) -> List[str]:
        """Get skills associated with a company."""
        name = self._resolve(company_name)
        if not self.G.has_node(name):
            return []
        return [
            target
            for _, target, data in self.G.out_edges(name, data=True)
            if data.get("relation") in ("USES_SKILL", "KNOWN_FOR")
        ]

    def get_similar_companies(
        self, company_name: str, top_k: int = 5
    ) -> List[Dict]:
        """Find companies with overlapping skill/trait profiles."""
        name = self._resolve(company_name)
        if not self.G.has_node(name):
            return []

        my_traits = set(
            t
            for _, t, d in self.G.out_edges(name, data=True)
            if d.get("relation") in ("USES_SKILL", "KNOWN_FOR")
        )
        if not my_traits:
            return []

        scores = []
        for node in self.G.nodes():
            node_data = self.G.nodes[node]
            if node_data.get("type") != "company" or node == name:
                continue
            their_traits = set(
                t
                for _, t, d in self.G.out_edges(node, data=True)
                if d.get("relation") in ("USES_SKILL", "KNOWN_FOR")
            )
            overlap = len(my_traits & their_traits)
            if overlap > 0:
                scores.append({
                    "company": node,
                    "overlap": overlap,
                    "shared": list(my_traits & their_traits)[:10],
                })

        scores.sort(key=lambda x: x["overlap"], reverse=True)
        return scores[:top_k]

    def get_industry_companies(self, industry: str) -> List[str]:
        """Get all companies in a given industry."""
        ind = industry.strip().lower()
        if not self.G.has_node(ind):
            return []
        return [
            src
            for src, _, d in self.G.in_edges(ind, data=True)
            if d.get("relation") == "OPERATES_IN"
        ]

    def get_graph_stats(self) -> Dict:
        """Get summary statistics of the knowledge graph."""
        types = {}
        for node, data in self.G.nodes(data=True):
            t = data.get("type", "unknown")
            types[t] = types.get(t, 0) + 1

        relations = {}
        for _, _, data in self.G.edges(data=True):
            r = data.get("relation", "unknown")
            relations[r] = relations.get(r, 0) + 1

        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": types,
            "relation_types": relations,
        }

    # ----- Persistence -----

    def save(self, path: str = "models/knowledge_graph.pkl"):
        """Serialize the knowledge graph to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str = "models/knowledge_graph.pkl") -> "KnowledgeGraph":
        """Load a saved knowledge graph."""
        with open(path, "rb") as f:
            return pickle.load(f)


# Singleton instance
_kg_instance = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create the global KnowledgeGraph instance."""
    global _kg_instance
    if _kg_instance is None:
        kg_path = os.path.join(os.path.dirname(__file__), "..", "models", "knowledge_graph.pkl")
        if os.path.exists(kg_path):
            _kg_instance = KnowledgeGraph.load(kg_path)
        else:
            _kg_instance = KnowledgeGraph()
    return _kg_instance


if __name__ == "__main__":
    kg = KnowledgeGraph()
    kg.enrich_from_resume_data()
    stats = kg.get_graph_stats()
    print(f"Knowledge Graph Stats: {stats}")
    print(f"\nGoogle context: {kg.get_company_context('google')}")
    print(f"Amazon context: {kg.get_company_context('amazon')}")
    print(f"\nCompanies similar to Google: {kg.get_similar_companies('google')}")
# node updates
