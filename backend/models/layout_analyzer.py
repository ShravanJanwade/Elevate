"""
Elevate v3 – Layout Analyzer
===============================
Lightweight resume layout quality analyzer using PDF structure + text heuristics.
No vision model needed — uses pdfplumber extraction + pattern analysis.

Scores 4 dimensions:
  1. STRUCTURE: Section count, heading hierarchy, logical flow
  2. DENSITY: Content per page, white space ratio
  3. FORMATTING: Bullet consistency, indentation, line lengths
  4. PRESENTATION: Page count, margins, overall professional quality
"""

import re
from typing import Dict, List, Optional


class LayoutAnalyzer:
    """Analyze resume layout quality from PDF structure and text."""

    def analyze(
        self,
        pdf_path: str = None,
        raw_text: str = "",
    ) -> Dict:
        """Run full layout analysis. Pass either pdf_path OR raw_text."""
        pdf_features = self._analyze_pdf(pdf_path) if pdf_path else {}
        text = raw_text or pdf_features.get("text", "")

        if not text:
            return {
                "overall_quality": 50.0,
                "dimensions": {
                    "structure": 50.0,
                    "density": 50.0,
                    "formatting": 50.0,
                    "presentation": 50.0,
                },
                "flags": [{"type": "yellow", "signal": "no_content",
                           "detail": "No content to analyze."}],
            }

        text_features = self._analyze_text(text)

        structure = self._score_structure(text_features)
        density = self._score_density(text_features, pdf_features)
        formatting = self._score_formatting(text_features)
        presentation = self._score_presentation(text_features, pdf_features)

        overall = (
            structure * 0.25
            + density * 0.25
            + formatting * 0.25
            + presentation * 0.25
        )

        flags = self._generate_flags(structure, density, formatting,
                                      presentation, text_features, pdf_features)

        return {
            "overall_quality": round(overall, 1),
            "dimensions": {
                "structure": round(structure, 1),
                "density": round(density, 1),
                "formatting": round(formatting, 1),
                "presentation": round(presentation, 1),
            },
            "flags": flags,
        }

    # ---- PDF analysis ----

    def _analyze_pdf(self, pdf_path: str) -> Dict:
        """Extract PDF-level features using pdfplumber."""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                pages_text = []
                for p in pdf.pages:
                    pages_text.append(p.extract_text() or "")
                text = "\n".join(pages_text)

                first = pdf.pages[0]
                return {
                    "page_count": page_count,
                    "text": text,
                    "page_width": first.width,
                    "page_height": first.height,
                }
        except Exception:
            return {}

    # ---- Text feature extraction ----

    def _analyze_text(self, text: str) -> Dict:
        """Extract structural features from resume text."""
        lines = text.split("\n")
        non_empty = [l for l in lines if l.strip()]

        bullet_lines = sum(
            1 for l in lines if re.match(r"^\s*[-•*▪▸◦>]\s+", l)
        )
        numbered_lines = sum(
            1 for l in lines if re.match(r"^\s*\d+[.)]\s+", l)
        )
        uppercase_lines = sum(
            1 for l in non_empty
            if l.strip().isupper() and len(l.strip()) > 3
        )

        line_lengths = [len(l) for l in non_empty] if non_empty else [0]
        avg_line_length = sum(line_lengths) / len(line_lengths)

        # Detect indentation levels
        indent_levels = set()
        for l in lines:
            leading = len(l) - len(l.lstrip())
            if leading > 0:
                indent_levels.add(leading)

        # Common section headers
        section_re = re.compile(
            r"^\s*(EXPERIENCE|EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|"
            r"SUMMARY|OBJECTIVE|AWARDS|PUBLICATIONS|WORK HISTORY|"
            r"PROFESSIONAL EXPERIENCE|TECHNICAL SKILLS|ACHIEVEMENTS|"
            r"INTERESTS|LANGUAGES|REFERENCES)\s*[:.]?\s*$",
            re.I,
        )
        section_count = sum(1 for l in lines if section_re.match(l.strip()))

        # Formatting issues
        double_spaces = len(re.findall(r"  +", text))
        mixed_bullets = bullet_lines > 0 and numbered_lines > 0

        # Action verbs at line start
        action_re = re.compile(
            r"^\s*[-•*]?\s*(Developed|Built|Led|Managed|Created|Designed|"
            r"Implemented|Engineered|Optimized|Reduced|Improved|Delivered|"
            r"Launched|Architected|Spearheaded|Automated|Analyzed)\b",
            re.I,
        )
        action_bullets = sum(1 for l in lines if action_re.match(l))

        # Contact info presence
        has_email = bool(re.search(r"\b[\w.]+@[\w.]+\.\w+\b", text))
        has_phone = bool(re.search(r"\b\d{3}[-.)]\s*\d{3}[-.)]\s*\d{4}\b", text))
        has_linkedin = bool(re.search(r"linkedin\.com", text, re.I))

        return {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty),
            "empty_line_ratio": (len(lines) - len(non_empty)) / max(len(lines), 1),
            "bullet_lines": bullet_lines,
            "numbered_lines": numbered_lines,
            "section_headers": uppercase_lines,
            "detected_sections": section_count,
            "avg_line_length": avg_line_length,
            "max_line_length": max(line_lengths),
            "indent_levels": len(indent_levels),
            "double_spaces": double_spaces,
            "mixed_bullets": mixed_bullets,
            "action_bullets": action_bullets,
            "char_count": len(text),
            "word_count": len(text.split()),
            "has_email": has_email,
            "has_phone": has_phone,
            "has_linkedin": has_linkedin,
        }

    # ---- Scoring functions ----

    def _score_structure(self, tf: Dict) -> float:
        """Does the resume have clear section organization?"""
        score = 35.0
        sections = tf.get("detected_sections", 0) + tf.get("section_headers", 0)

        if sections >= 5:
            score += 35
        elif sections >= 3:
            score += 25
        elif sections >= 1:
            score += 10

        if tf.get("bullet_lines", 0) >= 8:
            score += 15
        elif tf.get("bullet_lines", 0) >= 4:
            score += 10

        if tf.get("indent_levels", 0) >= 2:
            score += 10

        if tf.get("action_bullets", 0) >= 5:
            score += 5

        return min(100, score)

    def _score_density(self, tf: Dict, pf: Dict) -> float:
        """Is the content appropriately dense?"""
        pages = pf.get("page_count", 1)
        words = tf.get("word_count", 0)
        words_per_page = words / max(pages, 1)

        if 250 <= words_per_page <= 500:
            score = 85.0
        elif 200 <= words_per_page < 250 or 500 < words_per_page <= 600:
            score = 70.0
        elif 150 <= words_per_page < 200 or 600 < words_per_page <= 700:
            score = 55.0
        elif words_per_page < 150:
            score = 35.0
        else:
            score = 30.0

        # Page count
        if pages == 1:
            score += 5
        elif pages == 2:
            pass
        elif pages == 3:
            score -= 10
        elif pages >= 4:
            score -= 25

        return min(100, max(0, score))

    def _score_formatting(self, tf: Dict) -> float:
        """Is formatting clean and consistent?"""
        score = 55.0

        if tf.get("double_spaces", 0) > 10:
            score -= 20
        elif tf.get("double_spaces", 0) > 5:
            score -= 10

        if tf.get("mixed_bullets", False):
            score -= 10

        avg_len = tf.get("avg_line_length", 0)
        if 35 <= avg_len <= 85:
            score += 15
        elif avg_len > 120:
            score -= 10

        if tf.get("bullet_lines", 0) >= 5:
            score += 10

        if tf.get("empty_line_ratio", 0) > 0.45:
            score -= 10

        return min(100, max(0, score))

    def _score_presentation(self, tf: Dict, pf: Dict) -> float:
        """Overall professional appearance."""
        score = 50.0

        pages = pf.get("page_count", 1)
        if pages <= 2:
            score += 15
        else:
            score -= 15

        sections = tf.get("detected_sections", 0) + tf.get("section_headers", 0)
        if sections >= 4:
            score += 10

        if tf.get("bullet_lines", 0) >= 8:
            score += 10

        if tf.get("has_email"):
            score += 5
        if tf.get("has_phone"):
            score += 3
        if tf.get("has_linkedin"):
            score += 7

        return min(100, max(0, score))

    # ---- Flag generation ----

    def _generate_flags(
        self, structure, density, formatting, presentation, tf, pf
    ) -> List[Dict]:
        """Generate actionable layout feedback flags."""
        flags = []
        pages = pf.get("page_count", 1)

        if pages > 2:
            flags.append({
                "type": "red",
                "signal": "too_long",
                "detail": f"Resume is {pages} pages — aim for 1-2 pages maximum.",
            })

        if tf.get("bullet_lines", 0) < 3:
            flags.append({
                "type": "yellow",
                "signal": "few_bullets",
                "detail": "Use bullet points to highlight achievements and responsibilities.",
            })

        sections = tf.get("detected_sections", 0)
        if sections < 2:
            flags.append({
                "type": "yellow",
                "signal": "poor_structure",
                "detail": "Add clear section headers (Experience, Skills, Education, etc.).",
            })

        if formatting < 50:
            flags.append({
                "type": "red",
                "signal": "formatting_issues",
                "detail": "Inconsistent formatting detected. Clean up spacing, bullets, and indentation.",
            })

        if not tf.get("has_email"):
            flags.append({
                "type": "red",
                "signal": "missing_email",
                "detail": "No email address detected. Always include contact information.",
            })

        if tf.get("action_bullets", 0) < 3:
            flags.append({
                "type": "yellow",
                "signal": "weak_verbs",
                "detail": "Start bullet points with strong action verbs (Led, Developed, Optimized).",
            })

        if all(s >= 70 for s in [structure, density, formatting, presentation]):
            flags.append({
                "type": "green",
                "signal": "well_formatted",
                "detail": "Professional, well-structured resume layout.",
            })

        return flags
# cv layout
