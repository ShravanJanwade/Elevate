"""
Elevate v3 – Career Trajectory Analyzer
==========================================
Analyzes career progression from parsed experience section.

Evaluates:
  - Tenure patterns (job-hopping vs. stability)
  - Title progression (Engineer → Senior → Lead)
  - Career gaps (> 6 months unexplained)
  - Total experience years
"""

import re
from datetime import datetime
from typing import Dict, List


class CareerTrajectoryAnalyzer:
    """Analyze career trajectory quality from resume experience text."""

    TITLE_HIERARCHY = {
        "intern": 0, "trainee": 0, "apprentice": 0,
        "associate": 1, "junior": 1, "jr": 1, "entry": 1,
        "engineer": 2, "developer": 2, "analyst": 2, "programmer": 2,
        "consultant": 2, "specialist": 2, "designer": 2,
        "senior": 3, "sr": 3,
        "lead": 4, "principal": 4, "staff": 4, "architect": 4,
        "manager": 5, "head": 5,
        "director": 6, "vp": 7, "cto": 8, "ceo": 9,
    }

    def analyze(
        self,
        experience_text: str = "",
        experience_entries: List[Dict] = None,
    ) -> Dict:
        """
        Analyze career trajectory.

        Args:
            experience_text: Raw experience section text
            experience_entries: Pre-parsed entries from resume_parser
        """
        if experience_entries:
            entries = self._normalize_entries(experience_entries)
        elif experience_text:
            entries = self._parse_entries(experience_text)
        else:
            return {
                "score": 50, "flags": [],
                "narrative": "No experience data to analyze.",
                "entry_count": 0, "total_years": 0,
            }

        if not entries:
            return {
                "score": 50, "flags": [],
                "narrative": "Could not parse career history entries.",
                "entry_count": 0, "total_years": 0,
            }

        flags = []
        dimension_scores = []

        # ---- 1. Tenure analysis ----
        tenures_months = []
        for e in entries:
            if e.get("duration_months"):
                tenures_months.append(e["duration_months"])
                if e["duration_months"] < 10 and e != entries[-1]:
                    flags.append({
                        "type": "red", "signal": "short_tenure",
                        "detail": f"Only {e['duration_months']:.0f} months"
                        f" at {e.get('company', 'unknown')}",
                    })

        if tenures_months:
            avg = sum(tenures_months) / len(tenures_months)
            if avg >= 24:
                dimension_scores.append(90)
                flags.append({"type": "green", "signal": "stable_tenure",
                    "detail": f"Average tenure: {avg:.0f} months — excellent stability"})
            elif avg >= 18:
                dimension_scores.append(72)
            elif avg >= 12:
                dimension_scores.append(50)
                flags.append({"type": "yellow", "signal": "moderate_tenure",
                    "detail": f"Average tenure: {avg:.0f} months"})
            else:
                dimension_scores.append(25)
                flags.append({"type": "red", "signal": "job_hopping",
                    "detail": f"Average tenure: {avg:.0f} months — potential concern"})
        else:
            dimension_scores.append(55)

        # ---- 2. Title progression ----
        levels = [self._title_to_level(e.get("title", "")) for e in entries]
        valid_levels = [(i, l) for i, l in enumerate(levels) if l > 0]

        progressions = 0
        regressions = 0
        for i in range(1, len(valid_levels)):
            if valid_levels[i][1] > valid_levels[i - 1][1]:
                progressions += 1
            elif valid_levels[i][1] < valid_levels[i - 1][1]:
                regressions += 1

        if progressions > 0 and regressions == 0:
            dimension_scores.append(90)
            flags.append({"type": "green", "signal": "clear_growth",
                "detail": f"{progressions} career advancement(s) detected"})
        elif progressions > regressions:
            dimension_scores.append(70)
            flags.append({"type": "green", "signal": "net_growth",
                "detail": f"{progressions} promotions, {regressions} lateral/down moves"})
        elif regressions > 0:
            dimension_scores.append(40)
            flags.append({"type": "yellow", "signal": "title_regression",
                "detail": f"{regressions} title regression(s) detected"})
        else:
            dimension_scores.append(60)

        # ---- 3. Gap detection ----
        for i in range(1, len(entries)):
            gap = entries[i].get("gap_before_months", 0)
            if gap and gap > 6:
                flags.append({"type": "yellow", "signal": "career_gap",
                    "detail": f"{gap:.0f} month gap before {entries[i].get('company', 'next role')}"})
                dimension_scores.append(max(30, 70 - gap * 3))

        # ---- 4. Experience depth ----
        total_months = sum(tenures_months) if tenures_months else 0
        total_years = total_months / 12

        overall = sum(dimension_scores) / max(len(dimension_scores), 1)

        return {
            "score": round(min(100, max(0, overall))),
            "flags": flags,
            "entry_count": len(entries),
            "total_years": round(total_years, 1),
            "avg_tenure_months": round(
                sum(tenures_months) / len(tenures_months), 1
            ) if tenures_months else 0,
            "progressions": progressions,
            "regressions": regressions,
        }

    # ----- Parsing -----

    def _parse_entries(self, text: str) -> List[Dict]:
        """Extract career entries from free-text experience section."""
        date_re = re.compile(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s*\d{4}|"
            r"\d{1,2}/\d{4}|\d{4})\s*[-–—to]+\s*"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s*\d{4}|"
            r"\d{1,2}/\d{4}|\d{4}|[Pp]resent|[Cc]urrent|[Oo]ngoing)",
            re.I,
        )

        entries = []
        for line in text.split("\n"):
            m = date_re.search(line)
            if not m:
                continue

            start = self._parse_date(m.group(1))
            end_str = m.group(2)
            if end_str.lower() in ("present", "current", "ongoing"):
                end = datetime.now()
            else:
                end = self._parse_date(end_str)

            duration = None
            if start and end:
                duration = max(1, (end - start).days / 30)

            clean = re.sub(date_re, "", line).strip(" |,-()")
            title = ""
            company = ""
            title_words = {"engineer", "developer", "analyst", "manager",
                           "lead", "director", "intern", "scientist",
                           "architect", "designer", "consultant", "specialist"}
            if clean and any(w in clean.lower() for w in title_words):
                title = clean
            elif clean:
                company = clean

            entries.append({
                "company": company, "title": title,
                "start": start, "end": end,
                "duration_months": duration,
            })

        # Sort chronologically
        entries.sort(key=lambda e: e.get("start") or datetime.min)

        # Compute gaps
        for i in range(1, len(entries)):
            if entries[i].get("start") and entries[i - 1].get("end"):
                gap = (entries[i]["start"] - entries[i - 1]["end"]).days / 30
                entries[i]["gap_before_months"] = max(0, gap)

        return entries

    def _normalize_entries(self, raw_entries: List[Dict]) -> List[Dict]:
        """Normalize pre-parsed entries from resume_parser."""
        entries = []
        for e in raw_entries:
            title = e.get("title", "") or e.get("position", "")
            company = e.get("company", "") or ""
            start = self._parse_date(e.get("start_date", ""))
            end_str = e.get("end_date", "")

            if end_str and end_str.lower() in ("present", "current", "ongoing"):
                end = datetime.now()
            else:
                end = self._parse_date(end_str)

            duration = None
            if start and end:
                duration = max(1, (end - start).days / 30)

            entries.append({
                "company": company, "title": title,
                "start": start, "end": end,
                "duration_months": duration,
            })

        entries.sort(key=lambda e: e.get("start") or datetime.min)

        for i in range(1, len(entries)):
            if entries[i].get("start") and entries[i - 1].get("end"):
                gap = (entries[i]["start"] - entries[i - 1]["end"]).days / 30
                entries[i]["gap_before_months"] = max(0, gap)

        return entries

    def _parse_date(self, s) -> datetime:
        """Attempt to parse a date string."""
        if not s or not isinstance(s, str):
            return None
        s = s.strip()
        for fmt in ("%B %Y", "%b %Y", "%b. %Y", "%m/%Y", "%Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    def _title_to_level(self, title: str) -> int:
        """Map a job title to a seniority level."""
        if not title:
            return 2
        best = 0
        for keyword, level in self.TITLE_HIERARCHY.items():
            if keyword in title.lower():
                best = max(best, level)
        return best if best > 0 else 2
