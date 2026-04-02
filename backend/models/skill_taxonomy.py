"""
Elevate – Skill Taxonomy Engine
=================================
A comprehensive skill relationship graph that understands:
  - Synonyms/aliases (JS ↔ JavaScript)
  - Parent-child relationships (React → JavaScript → Programming)
  - Sibling/related skills (Spring Boot ↔ Hibernate ↔ Spring Security)
  - Domain clusters (AWS, GCP, Azure → Cloud)
  - Tool-concept mappings (Git → Version Control, Docker → Containerization)

This is the foundation that makes the analyzer think like a recruiter:
"If someone knows Spring Boot, they likely know Java, Maven, REST APIs,
and have exposure to Spring Security and Hibernate."
"""

from collections import defaultdict
from typing import Set, Dict, List, Tuple


# ============================================================================
# SKILL GRAPH DATA
# ============================================================================

# Each entry: canonical_name → {
#   "aliases": [...],          synonyms/abbreviations
#   "parent": "...",           broader category
#   "children": [...],         more specific skills in this area
#   "related": [...],          commonly co-occurring skills (siblings)
#   "domain": "...",           high-level domain cluster
# }

SKILL_GRAPH: Dict[str, dict] = {
    # ========== PROGRAMMING LANGUAGES ==========
    "python": {
        "aliases": ["py", "python3", "cpython"],
        "parent": "programming",
        "related": ["django", "flask", "fastapi", "pandas", "numpy", "pip", "conda"],
        "domain": "programming",
    },
    "java": {
        "aliases": ["jdk", "jvm", "java se", "java ee", "j2ee", "openjdk"],
        "parent": "programming",
        "related": ["spring", "spring boot", "hibernate", "maven", "gradle",
                     "jpa", "tomcat", "spring security", "junit"],
        "domain": "programming",
    },
    "javascript": {
        "aliases": ["js", "es6", "es2015", "ecmascript", "es2020", "vanilla js"],
        "parent": "programming",
        "related": ["node.js", "react", "vue", "angular", "typescript",
                     "npm", "webpack", "babel", "express"],
        "domain": "programming",
    },
    "typescript": {
        "aliases": ["ts"],
        "parent": "programming",
        "related": ["javascript", "react", "angular", "node.js", "npm"],
        "domain": "programming",
    },
    "c++": {
        "aliases": ["cpp", "c plus plus", "cxx"],
        "parent": "programming",
        "related": ["c", "cmake", "stl", "boost"],
        "domain": "programming",
    },
    "c#": {
        "aliases": ["csharp", "c sharp", "dotnet c#"],
        "parent": "programming",
        "related": [".net", "asp.net", "unity", "azure"],
        "domain": "programming",
    },
    "c": {
        "aliases": ["c language", "ansi c"],
        "parent": "programming",
        "related": ["c++", "embedded systems", "linux"],
        "domain": "programming",
    },
    "go": {
        "aliases": ["golang"],
        "parent": "programming",
        "related": ["docker", "kubernetes", "microservices", "grpc"],
        "domain": "programming",
    },
    "rust": {
        "aliases": [],
        "parent": "programming",
        "related": ["c++", "systems programming", "webassembly"],
        "domain": "programming",
    },
    "ruby": {
        "aliases": ["rb"],
        "parent": "programming",
        "related": ["rails", "sinatra"],
        "domain": "programming",
    },
    "swift": {
        "aliases": [],
        "parent": "programming",
        "related": ["ios", "xcode", "cocoapods", "swiftui"],
        "domain": "programming",
    },
    "kotlin": {
        "aliases": ["kt"],
        "parent": "programming",
        "related": ["android", "java", "gradle", "jetpack compose"],
        "domain": "programming",
    },
    "scala": {
        "aliases": [],
        "parent": "programming",
        "related": ["spark", "akka", "java", "functional programming"],
        "domain": "programming",
    },
    "r": {
        "aliases": ["r language", "r programming"],
        "parent": "programming",
        "related": ["data analysis", "statistics", "ggplot", "tidyverse"],
        "domain": "data_science",
    },
    "php": {
        "aliases": [],
        "parent": "programming",
        "related": ["laravel", "wordpress", "mysql", "composer"],
        "domain": "programming",
    },
    "sql": {
        "aliases": ["structured query language", "sql queries"],
        "parent": "programming",
        "related": ["postgresql", "mysql", "oracle", "sql server",
                     "database", "data modeling", "stored procedures"],
        "domain": "data",
    },
    "bash": {
        "aliases": ["shell", "shell scripting", "sh", "zsh", "bash scripting"],
        "parent": "programming",
        "related": ["linux", "unix", "command line", "automation"],
        "domain": "devops",
    },
    "node.js": {
        "aliases": ["nodejs", "node"],
        "parent": "javascript",
        "related": ["express", "npm", "javascript", "typescript", "rest api"],
        "domain": "backend",
    },

    # ========== WEB FRAMEWORKS ==========
    "react": {
        "aliases": ["reactjs", "react.js", "react js"],
        "parent": "frontend",
        "related": ["javascript", "redux", "next.js", "jsx", "hooks",
                     "typescript", "webpack", "component library"],
        "domain": "frontend",
    },
    "angular": {
        "aliases": ["angularjs", "angular.js", "angular 2+"],
        "parent": "frontend",
        "related": ["typescript", "rxjs", "ngrx"],
        "domain": "frontend",
    },
    "vue": {
        "aliases": ["vuejs", "vue.js", "vue 3"],
        "parent": "frontend",
        "related": ["javascript", "nuxt.js", "vuex", "pinia"],
        "domain": "frontend",
    },
    "next.js": {
        "aliases": ["nextjs"],
        "parent": "react",
        "related": ["react", "vercel", "server-side rendering", "ssr"],
        "domain": "frontend",
    },
    "django": {
        "aliases": [],
        "parent": "python",
        "related": ["python", "rest api", "orm", "postgresql"],
        "domain": "backend",
    },
    "flask": {
        "aliases": [],
        "parent": "python",
        "related": ["python", "rest api", "jinja", "sqlalchemy"],
        "domain": "backend",
    },
    "fastapi": {
        "aliases": ["fast api"],
        "parent": "python",
        "related": ["python", "rest api", "pydantic", "async"],
        "domain": "backend",
    },
    "express": {
        "aliases": ["expressjs", "express.js"],
        "parent": "node.js",
        "related": ["node.js", "javascript", "rest api", "middleware"],
        "domain": "backend",
    },
    "spring": {
        "aliases": ["spring framework"],
        "parent": "java",
        "related": ["spring boot", "java", "hibernate", "spring security",
                     "spring mvc", "jpa", "maven", "gradle", "rest api"],
        "domain": "backend",
    },
    "spring boot": {
        "aliases": ["springboot"],
        "parent": "spring",
        "related": ["java", "spring", "hibernate", "spring security",
                     "maven", "gradle", "rest api", "microservices",
                     "jpa", "spring mvc", "spring cloud"],
        "domain": "backend",
    },
    "spring security": {
        "aliases": [],
        "parent": "spring",
        "related": ["spring boot", "java", "oauth", "jwt", "authentication"],
        "domain": "backend",
    },
    "hibernate": {
        "aliases": ["hibernate orm"],
        "parent": "java",
        "related": ["spring boot", "java", "jpa", "orm", "sql", "database"],
        "domain": "backend",
    },
    "rails": {
        "aliases": ["ruby on rails", "ror"],
        "parent": "ruby",
        "related": ["ruby", "postgresql", "rest api", "active record"],
        "domain": "backend",
    },
    "laravel": {
        "aliases": [],
        "parent": "php",
        "related": ["php", "mysql", "eloquent", "composer"],
        "domain": "backend",
    },
    ".net": {
        "aliases": ["dotnet", "dot net"],
        "parent": "programming",
        "related": ["c#", "asp.net", "azure", "entity framework"],
        "domain": "backend",
    },
    "asp.net": {
        "aliases": ["aspnet"],
        "parent": ".net",
        "related": [".net", "c#", "azure", "mvc"],
        "domain": "backend",
    },

    # ========== CLOUD PLATFORMS ==========
    "aws": {
        "aliases": ["amazon web services", "amazon aws"],
        "parent": "cloud",
        "related": ["ec2", "s3", "lambda", "rds", "cloudwatch",
                     "dynamodb", "sqs", "sns", "iam", "cloudformation",
                     "ecs", "eks", "api gateway"],
        "domain": "cloud",
    },
    "gcp": {
        "aliases": ["google cloud", "google cloud platform"],
        "parent": "cloud",
        "related": ["bigquery", "cloud functions", "gke", "pub/sub",
                     "cloud storage", "cloud run", "firebase"],
        "domain": "cloud",
    },
    "azure": {
        "aliases": ["microsoft azure", "azure cloud"],
        "parent": "cloud",
        "related": [".net", "azure devops", "azure functions",
                     "cosmos db", "azure ad", "aks"],
        "domain": "cloud",
    },
    "firebase": {
        "aliases": [],
        "parent": "gcp",
        "related": ["gcp", "nosql", "cloud functions", "authentication"],
        "domain": "cloud",
    },

    # ========== DEVOPS & INFRA ==========
    "docker": {
        "aliases": ["docker containers", "containerization", "containers"],
        "parent": "devops",
        "related": ["kubernetes", "docker compose", "container orchestration",
                     "ci/cd", "microservices"],
        "domain": "devops",
    },
    "kubernetes": {
        "aliases": ["k8s", "kube"],
        "parent": "devops",
        "related": ["docker", "helm", "container orchestration",
                     "microservices", "cloud"],
        "domain": "devops",
    },
    "terraform": {
        "aliases": ["tf", "hashicorp terraform"],
        "parent": "devops",
        "related": ["infrastructure as code", "aws", "azure", "gcp",
                     "ansible", "cloud"],
        "domain": "devops",
    },
    "ci/cd": {
        "aliases": ["cicd", "ci cd", "continuous integration",
                     "continuous deployment", "continuous delivery",
                     "ci/cd pipelines", "ci/cd pipeline"],
        "parent": "devops",
        "related": ["jenkins", "github actions", "gitlab ci",
                     "docker", "automation", "devops"],
        "domain": "devops",
    },
    "jenkins": {
        "aliases": [],
        "parent": "ci/cd",
        "related": ["ci/cd", "devops", "automation"],
        "domain": "devops",
    },
    "github actions": {
        "aliases": ["gh actions"],
        "parent": "ci/cd",
        "related": ["ci/cd", "github", "automation", "devops"],
        "domain": "devops",
    },
    "ansible": {
        "aliases": [],
        "parent": "devops",
        "related": ["terraform", "automation", "infrastructure as code"],
        "domain": "devops",
    },
    "git": {
        "aliases": ["version control", "vcs", "source control"],
        "parent": "devops",
        "related": ["github", "gitlab", "bitbucket", "version control"],
        "domain": "devops",
    },
    "github": {
        "aliases": [],
        "parent": "git",
        "related": ["git", "version control", "github actions", "open source"],
        "domain": "devops",
    },
    "linux": {
        "aliases": ["unix", "linux administration", "ubuntu", "centos", "debian"],
        "parent": "devops",
        "related": ["bash", "command line", "ssh", "docker", "servers"],
        "domain": "devops",
    },

    # ========== DATABASES ==========
    "postgresql": {
        "aliases": ["postgres", "psql"],
        "parent": "database",
        "related": ["sql", "database", "orm", "data modeling"],
        "domain": "data",
    },
    "mysql": {
        "aliases": ["my sql"],
        "parent": "database",
        "related": ["sql", "database", "mariadb"],
        "domain": "data",
    },
    "mongodb": {
        "aliases": ["mongo"],
        "parent": "database",
        "related": ["nosql", "database", "mongoose", "document database"],
        "domain": "data",
    },
    "redis": {
        "aliases": [],
        "parent": "database",
        "related": ["caching", "in-memory database", "nosql"],
        "domain": "data",
    },
    "dynamodb": {
        "aliases": ["dynamo db", "dynamo"],
        "parent": "database",
        "related": ["aws", "nosql", "database", "serverless"],
        "domain": "data",
    },
    "elasticsearch": {
        "aliases": ["elastic search", "es"],
        "parent": "database",
        "related": ["search", "kibana", "logstash", "elk stack"],
        "domain": "data",
    },
    "snowflake": {
        "aliases": [],
        "parent": "database",
        "related": ["data warehouse", "sql", "cloud", "analytics"],
        "domain": "data",
    },
    "bigquery": {
        "aliases": ["big query"],
        "parent": "database",
        "related": ["gcp", "sql", "data warehouse", "analytics"],
        "domain": "data",
    },

    # ========== AI / ML / DATA SCIENCE ==========
    "machine learning": {
        "aliases": ["ml", "machine-learning"],
        "parent": "ai",
        "related": ["deep learning", "scikit-learn", "tensorflow", "pytorch",
                     "data science", "statistics", "feature engineering",
                     "model training", "nlp", "computer vision"],
        "domain": "ai_ml",
    },
    "deep learning": {
        "aliases": ["dl", "deep-learning", "neural networks"],
        "parent": "machine learning",
        "related": ["tensorflow", "pytorch", "keras", "cnn", "rnn",
                     "transformer", "gpu computing"],
        "domain": "ai_ml",
    },
    "nlp": {
        "aliases": ["natural language processing", "text mining", "text analysis"],
        "parent": "machine learning",
        "related": ["transformers", "bert", "gpt", "spacy", "nltk",
                     "sentiment analysis", "text classification"],
        "domain": "ai_ml",
    },
    "computer vision": {
        "aliases": ["cv", "image recognition", "image processing"],
        "parent": "deep learning",
        "related": ["opencv", "cnn", "object detection", "image classification"],
        "domain": "ai_ml",
    },
    "tensorflow": {
        "aliases": ["tf"],
        "parent": "deep learning",
        "related": ["keras", "deep learning", "machine learning", "python"],
        "domain": "ai_ml",
    },
    "pytorch": {
        "aliases": ["torch"],
        "parent": "deep learning",
        "related": ["deep learning", "machine learning", "python", "neural networks"],
        "domain": "ai_ml",
    },
    "scikit-learn": {
        "aliases": ["sklearn", "scikit learn"],
        "parent": "machine learning",
        "related": ["python", "machine learning", "data science", "pandas"],
        "domain": "ai_ml",
    },
    "pandas": {
        "aliases": [],
        "parent": "data science",
        "related": ["python", "numpy", "data analysis", "jupyter"],
        "domain": "ai_ml",
    },
    "numpy": {
        "aliases": [],
        "parent": "data science",
        "related": ["python", "pandas", "scientific computing", "scipy"],
        "domain": "ai_ml",
    },
    "data science": {
        "aliases": ["data-science"],
        "parent": "ai",
        "related": ["machine learning", "statistics", "python", "pandas",
                     "visualization", "jupyter", "data analysis"],
        "domain": "ai_ml",
    },

    # ========== DATA ENGINEERING ==========
    "spark": {
        "aliases": ["apache spark", "pyspark"],
        "parent": "data engineering",
        "related": ["hadoop", "scala", "data pipeline", "big data"],
        "domain": "data",
    },
    "kafka": {
        "aliases": ["apache kafka"],
        "parent": "data engineering",
        "related": ["streaming", "event-driven", "microservices", "pub/sub"],
        "domain": "data",
    },
    "airflow": {
        "aliases": ["apache airflow"],
        "parent": "data engineering",
        "related": ["data pipeline", "etl", "orchestration", "python"],
        "domain": "data",
    },
    "etl": {
        "aliases": ["extract transform load", "data pipeline", "data pipelines"],
        "parent": "data engineering",
        "related": ["data engineering", "sql", "spark", "airflow"],
        "domain": "data",
    },

    # ========== API & ARCHITECTURE ==========
    "rest api": {
        "aliases": ["rest", "restful", "restful api", "restful apis",
                     "rest apis", "api", "apis", "web api", "web apis",
                     "api development", "api concepts"],
        "parent": "architecture",
        "related": ["http", "json", "swagger", "openapi", "postman",
                     "microservices", "backend", "web services"],
        "domain": "architecture",
    },
    "graphql": {
        "aliases": ["gql", "graph ql"],
        "parent": "architecture",
        "related": ["api", "apollo", "rest api"],
        "domain": "architecture",
    },
    "grpc": {
        "aliases": [],
        "parent": "architecture",
        "related": ["protobuf", "microservices", "api"],
        "domain": "architecture",
    },
    "microservices": {
        "aliases": ["micro services", "microservice architecture"],
        "parent": "architecture",
        "related": ["docker", "kubernetes", "rest api", "message queue",
                     "service mesh", "api gateway"],
        "domain": "architecture",
    },

    # ========== FRONTEND / UI ==========
    "html": {
        "aliases": ["html5"],
        "parent": "frontend",
        "related": ["css", "javascript", "web development"],
        "domain": "frontend",
    },
    "css": {
        "aliases": ["css3", "cascading style sheets"],
        "parent": "frontend",
        "related": ["html", "sass", "less", "tailwind", "responsive design"],
        "domain": "frontend",
    },
    "sass": {
        "aliases": ["scss"],
        "parent": "css",
        "related": ["css", "less", "frontend"],
        "domain": "frontend",
    },
    "tailwind": {
        "aliases": ["tailwindcss", "tailwind css"],
        "parent": "css",
        "related": ["css", "frontend", "utility-first"],
        "domain": "frontend",
    },

    # ========== METHODOLOGIES ==========
    "agile": {
        "aliases": ["agile methodology", "agile development", "agile methodologies",
                     "agile scrum", "agile scrum methodologies"],
        "parent": "methodology",
        "related": ["scrum", "kanban", "sprint", "jira", "user stories"],
        "domain": "methodology",
    },
    "scrum": {
        "aliases": ["scrum master", "scrum methodology"],
        "parent": "agile",
        "related": ["agile", "sprint", "daily standup", "retrospective"],
        "domain": "methodology",
    },
    "kanban": {
        "aliases": [],
        "parent": "agile",
        "related": ["agile", "flow", "wip limits"],
        "domain": "methodology",
    },
    "jira": {
        "aliases": [],
        "parent": "agile",
        "related": ["agile", "scrum", "project management", "atlassian"],
        "domain": "methodology",
    },

    # ========== TESTING ==========
    "testing": {
        "aliases": ["software testing", "test", "tests", "unit testing"],
        "parent": "engineering",
        "related": ["unit tests", "integration tests", "tdd", "jest",
                     "pytest", "junit", "selenium"],
        "domain": "engineering",
    },

    # ========== MONITORING / OBSERVABILITY ==========
    "monitoring": {
        "aliases": ["observability", "logging and monitoring",
                     "observability and monitoring"],
        "parent": "devops",
        "related": ["datadog", "splunk", "cloudwatch", "grafana",
                     "prometheus", "elk stack", "logging"],
        "domain": "devops",
    },
    "datadog": {
        "aliases": [],
        "parent": "monitoring",
        "related": ["monitoring", "observability", "apm", "logging"],
        "domain": "devops",
    },
    "splunk": {
        "aliases": [],
        "parent": "monitoring",
        "related": ["monitoring", "logging", "siem"],
        "domain": "devops",
    },
    "cloudwatch": {
        "aliases": ["aws cloudwatch"],
        "parent": "monitoring",
        "related": ["aws", "monitoring", "logging", "alarms"],
        "domain": "devops",
    },

    # ========== INTEGRATION PLATFORMS ==========
    "workato": {
        "aliases": [],
        "parent": "ipaas",
        "related": ["integration", "automation", "ipaas", "low-code"],
        "domain": "integration",
    },
    "mulesoft": {
        "aliases": ["mule soft", "mule"],
        "parent": "ipaas",
        "related": ["integration", "api", "ipaas", "middleware"],
        "domain": "integration",
    },

    # ========== SOFT SKILLS / CONCEPTS ==========
    "communication": {
        "aliases": ["verbal communication", "written communication"],
        "parent": "soft skills",
        "related": ["teamwork", "presentation", "documentation"],
        "domain": "soft_skills",
    },
    "leadership": {
        "aliases": ["team leadership", "technical leadership"],
        "parent": "soft skills",
        "related": ["management", "mentoring", "teamwork"],
        "domain": "soft_skills",
    },
    "teamwork": {
        "aliases": ["collaboration", "team player", "cross-functional"],
        "parent": "soft skills",
        "related": ["communication", "agile", "collaboration"],
        "domain": "soft_skills",
    },
    "problem solving": {
        "aliases": ["problem-solving", "analytical thinking", "critical thinking"],
        "parent": "soft skills",
        "related": ["debugging", "troubleshooting", "analytical skills"],
        "domain": "soft_skills",
    },
    "documentation": {
        "aliases": ["technical documentation", "technical writing", "docs"],
        "parent": "soft skills",
        "related": ["communication", "markdown", "confluence", "jira"],
        "domain": "soft_skills",
    },
}


# ============================================================================
# DOMAIN CLUSTERS — High-level groupings for domain affinity scoring
# ============================================================================

DOMAIN_CLUSTERS = {
    "programming": {"label": "Programming Languages", "weight": 1.0},
    "frontend": {"label": "Frontend Development", "weight": 0.9},
    "backend": {"label": "Backend Development", "weight": 1.0},
    "cloud": {"label": "Cloud Platforms", "weight": 0.8},
    "devops": {"label": "DevOps & Infrastructure", "weight": 0.7},
    "data": {"label": "Data & Databases", "weight": 0.8},
    "ai_ml": {"label": "AI / ML / Data Science", "weight": 0.9},
    "architecture": {"label": "Architecture & APIs", "weight": 0.85},
    "methodology": {"label": "Methodologies", "weight": 0.5},
    "engineering": {"label": "Engineering Practices", "weight": 0.6},
    "soft_skills": {"label": "Soft Skills", "weight": 0.3},
    "integration": {"label": "Integration Platforms", "weight": 0.6},
}


# ============================================================================
# TAXONOMY CLASS
# ============================================================================

class SkillTaxonomy:
    """
    Graph-based skill taxonomy that enables intelligent matching:
    - Exact match: "python" == "python" → 1.0
    - Synonym match: "js" → "javascript" → 1.0
    - Parent/child match: "react" → "frontend" → 0.6
    - Related match: "spring boot" → "hibernate" → 0.7
    - Domain match: both in "backend" → 0.4
    """

    def __init__(self):
        # Build lookup indices
        self._alias_to_canonical: Dict[str, str] = {}
        self._canonical_set: Set[str] = set()
        self._related_cache: Dict[str, Set[str]] = {}
        self._domain_cache: Dict[str, str] = {}
        self._parent_cache: Dict[str, str] = {}

        for canonical, data in SKILL_GRAPH.items():
            canonical_lower = canonical.lower()
            self._canonical_set.add(canonical_lower)
            self._alias_to_canonical[canonical_lower] = canonical_lower

            for alias in data.get("aliases", []):
                self._alias_to_canonical[alias.lower()] = canonical_lower

            related = set()
            for r in data.get("related", []):
                related.add(r.lower())
            self._related_cache[canonical_lower] = related
            self._domain_cache[canonical_lower] = data.get("domain", "")
            self._parent_cache[canonical_lower] = data.get("parent", "").lower()

    def canonicalize(self, skill: str) -> str:
        """Map a skill string to its canonical form, or return as-is."""
        return self._alias_to_canonical.get(skill.lower().strip(), skill.lower().strip())

    def is_known_skill(self, skill: str) -> bool:
        """Check if a skill is in the taxonomy."""
        canonical = self.canonicalize(skill)
        return canonical in self._canonical_set

    def get_related(self, skill: str) -> Set[str]:
        """Get all related skills for a canonical skill."""
        canonical = self.canonicalize(skill)
        return self._related_cache.get(canonical, set())

    def get_domain(self, skill: str) -> str:
        """Get the domain cluster for a skill."""
        canonical = self.canonicalize(skill)
        return self._domain_cache.get(canonical, "")

    def get_parent(self, skill: str) -> str:
        """Get the parent category of a skill."""
        canonical = self.canonicalize(skill)
        return self._parent_cache.get(canonical, "")

    def match_strength(self, skill_a: str, skill_b: str) -> float:
        """
        Compute how strongly two skills are related.
        Returns a float 0.0 – 1.0:
          1.0  = exact or synonym match
          0.85 = parent-child relationship
          0.7  = related/sibling skills
          0.5  = same domain cluster
          0.2  = both in taxonomy but different domains
          0.0  = no relationship found
        """
        a = self.canonicalize(skill_a)
        b = self.canonicalize(skill_b)

        # Exact / synonym match
        if a == b:
            return 1.0

        # Parent-child
        if self._parent_cache.get(a, "") == b or self._parent_cache.get(b, "") == a:
            return 0.85

        # Grandparent (two hops up)
        parent_a = self._parent_cache.get(a, "")
        parent_b = self._parent_cache.get(b, "")
        if parent_a and parent_a == parent_b:
            return 0.75  # siblings under same parent

        if parent_a and self._parent_cache.get(parent_a, "") == b:
            return 0.65
        if parent_b and self._parent_cache.get(parent_b, "") == a:
            return 0.65

        # Related (explicitly listed)
        related_a = self._related_cache.get(a, set())
        related_b = self._related_cache.get(b, set())
        if b in related_a or a in related_b:
            return 0.7

        # Mutual related (share related skills)
        if related_a and related_b:
            overlap = related_a & related_b
            if len(overlap) >= 3:
                return 0.55
            elif len(overlap) >= 1:
                return 0.4

        # Same domain
        domain_a = self._domain_cache.get(a, "")
        domain_b = self._domain_cache.get(b, "")
        if domain_a and domain_a == domain_b:
            return 0.35

        # Both known but different domains
        if a in self._canonical_set and b in self._canonical_set:
            return 0.1

        return 0.0

    def find_all_matches(self, skill: str, candidate_skills: List[str]) -> List[Tuple[str, float]]:
        """
        Given a target skill and a list of candidate skills,
        return all matches sorted by strength (descending).
        """
        matches = []
        for candidate in candidate_skills:
            strength = self.match_strength(skill, candidate)
            if strength > 0.05:
                matches.append((candidate, strength))
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def get_domain_overlap(self, skills_a: List[str], skills_b: List[str]) -> Dict[str, dict]:
        """
        Compare two skill sets by domain coverage.
        Returns per-domain overview of overlap.
        """
        domains_a = defaultdict(list)
        domains_b = defaultdict(list)

        for s in skills_a:
            domain = self.get_domain(s) or "other"
            domains_a[domain].append(self.canonicalize(s))

        for s in skills_b:
            domain = self.get_domain(s) or "other"
            domains_b[domain].append(self.canonicalize(s))

        all_domains = set(domains_a.keys()) | set(domains_b.keys())
        result = {}

        for domain in all_domains:
            a_skills = set(domains_a.get(domain, []))
            b_skills = set(domains_b.get(domain, []))
            overlap = a_skills & b_skills
            total = a_skills | b_skills
            coverage = len(overlap) / len(total) if total else 0.0

            result[domain] = {
                "in_resume": list(a_skills),
                "in_jd": list(b_skills),
                "overlap": list(overlap),
                "coverage": round(coverage, 3),
            }

        return result


# Singleton instance
_taxonomy = None

def get_taxonomy() -> SkillTaxonomy:
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = SkillTaxonomy()
    return _taxonomy
# custom tax
