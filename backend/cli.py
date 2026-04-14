#!/usr/bin/env python3
"""
Elevate – CLI Resume Analyzer (Rich TUI)
==========================================
Analyze resumes directly from the terminal with a beautiful rich interface.

Usage:
    python cli.py resume.pdf --jd "Looking for a Python backend engineer..."
    python cli.py resume.pdf --jd-file job_description.txt
    python cli.py resume.pdf --jd "..." --export results.json
    python cli.py resume.pdf --jd "..." --interactive

Examples:
    python backend/cli.py my_resume.pdf --jd "We need a senior Python developer with AWS experience"
    python backend/cli.py my_resume.pdf --jd-file jd.txt --export analysis.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich import box

console = Console(force_terminal=True)


# ---------------------------------------------------------------------------
# Color scheme and styling
# ---------------------------------------------------------------------------

COLORS = {
    "excellent": "#22c55e",
    "strong": "#4ade80",
    "moderate": "#f59e0b",
    "weak": "#f97316",
    "poor": "#ef4444",
    "accent": "#818cf8",
    "primary": "#a78bfa",
    "muted": "#64748b",
    "bg": "#1e1b4b",
}


def score_color(score: float) -> str:
    if score >= 80:
        return COLORS["excellent"]
    if score >= 65:
        return COLORS["strong"]
    if score >= 45:
        return COLORS["moderate"]
    if score >= 25:
        return COLORS["weak"]
    return COLORS["poor"]


def score_bar(score: float, width: int = 20) -> str:
    """Create a colored progress bar string."""
    filled = int(score / 100 * width)
    empty = width - filled
    color = score_color(score)
    bar = f"[{color}]{'━' * filled}[/{color}][dim]{'─' * empty}[/dim]"
    return bar


def strength_badge(strength: str) -> str:
    """Create a colored strength badge."""
    color_map = {
        "excellent": "green",
        "strong": "bright_green",
        "moderate": "yellow",
        "weak": "bright_red",
        "poor": "red",
    }
    color = color_map.get(strength, "white")
    return f"[bold {color}]⬤ {strength.upper()}[/bold {color}]"


# ---------------------------------------------------------------------------
# Header / Banner
# ---------------------------------------------------------------------------

BANNER = """
[bold bright_magenta]  ███████╗██╗     ███████╗██╗   ██╗ █████╗ ████████╗███████╗[/]
[bold bright_magenta]  ██╔════╝██║     ██╔════╝██║   ██║██╔══██╗╚══██╔══╝██╔════╝[/]
[bold bright_magenta]  █████╗  ██║     █████╗  ██║   ██║███████║   ██║   █████╗  [/]
[bold bright_magenta]  ██╔══╝  ██║     ██╔══╝  ╚██╗ ██╔╝██╔══██║   ██║   ██╔══╝  [/]
[bold bright_magenta]  ███████╗███████╗███████╗ ╚████╔╝ ██║  ██║   ██║   ███████╗[/]
[bold bright_magenta]  ╚══════╝╚══════╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝   ╚═╝   ╚══════╝[/]
[dim]                  AI Resume Analyzer & Optimizer[/dim]
"""


def print_banner():
    console.print(BANNER)
    console.print()


# ---------------------------------------------------------------------------
# Analysis display functions
# ---------------------------------------------------------------------------

def display_overall_scores(analysis: dict):
    """Display the three main scores in a stylized panel."""
    overall = analysis["overall_score"]
    keyword_pct = analysis["keyword_analysis"]["match_percentage"]
    semantic_pct = analysis["semantic_analysis"]["overall_score"]
    strength = analysis.get("strength", "moderate")
    interpretation = analysis.get("interpretation", "")

    # Create score cards
    cards = []

    # Overall score
    ov_color = score_color(overall)
    ov_card = Panel(
        Align.center(
            Text.from_markup(
                f"[bold {ov_color}]{overall}%[/]\n"
                f"[dim]Overall Match[/dim]\n"
                f"{strength_badge(strength)}"
            )
        ),
        title="[bold bright_magenta]⚡ OVERALL[/]",
        border_style="bright_magenta",
        box=HEAVY,
        padding=(1, 3),
    )
    cards.append(ov_card)

    # Keyword score
    kw_color = score_color(keyword_pct)
    kw_matched = len(analysis["keyword_analysis"]["matched"])
    kw_total = analysis["keyword_analysis"]["total_keywords"]
    kw_card = Panel(
        Align.center(
            Text.from_markup(
                f"[bold {kw_color}]{keyword_pct}%[/]\n"
                f"[dim]Keyword Match[/dim]\n"
                f"[dim]{kw_matched}/{kw_total} keywords[/dim]"
            )
        ),
        title="[bold cyan]🔑 KEYWORDS[/]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 3),
    )
    cards.append(kw_card)

    # Semantic score  
    sem_color = score_color(semantic_pct)
    sem_card = Panel(
        Align.center(
            Text.from_markup(
                f"[bold {sem_color}]{semantic_pct}%[/]\n"
                f"[dim]Semantic Similarity[/dim]\n"
                f"[dim]AI-powered matching[/dim]"
            )
        ),
        title="[bold green]🧠 SEMANTIC[/]",
        border_style="green",
        box=ROUNDED,
        padding=(1, 3),
    )
    cards.append(sem_card)

    console.print(Columns(cards, equal=True, expand=True))

    if interpretation:
        console.print()
        console.print(
            Panel(
                f"[italic]{interpretation}[/italic]",
                border_style="dim",
                box=ROUNDED,
                padding=(0, 2),
            )
        )


def display_keyword_analysis(kw_analysis: dict):
    """Display keyword analysis with matched/missing breakdown."""
    console.print()
    console.print(Rule("[bold cyan]🔑 Keyword Analysis[/]", style="cyan"))
    console.print()

    matched = kw_analysis["matched"]
    missing = kw_analysis["missing"]

    if matched:
        tags = " ".join([f"[bold green]✓ {kw}[/]" for kw in matched])
        console.print(Panel(
            tags,
            title="[green]Found in Resume[/]",
            border_style="green",
            box=ROUNDED,
        ))

    if missing:
        tags = " ".join([f"[bold red]✗ {kw}[/]" for kw in missing])
        console.print(Panel(
            tags,
            title="[red]Missing from Resume[/]",
            border_style="red",
            box=ROUNDED,
        ))

    primary_matched = kw_analysis.get("primary_matched", 0)
    primary_total = kw_analysis.get("primary_total", 0)
    console.print(
        f"  [dim]Primary skills matched: {primary_matched}/{primary_total} | "
        f"Total keywords: {len(matched)}/{kw_analysis['total_keywords']}[/dim]"
    )


def display_bullet_scores(sem_analysis: dict):
    """Display per-bullet semantic scores in a table."""
    console.print()
    console.print(Rule("[bold green]📊 Bullet-Point Analysis[/]", style="green"))
    console.print()

    bullet_scores = sem_analysis.get("bullet_scores", [])
    if not bullet_scores:
        console.print("[dim]No bullet points detected.[/dim]")
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        expand=True,
        pad_edge=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Score", width=8, justify="center")
    table.add_column("Bar", width=22)
    table.add_column("Strength", width=12)
    table.add_column("Bullet Point", ratio=1)

    for i, b in enumerate(bullet_scores[:15], 1):
        score = b["similarity"]
        color = score_color(score)
        strength = b.get("strength", "moderate")
        bar = score_bar(score)

        table.add_row(
            str(i),
            f"[bold {color}]{score}%[/]",
            bar,
            strength_badge(strength),
            b["text"][:120] + ("..." if len(b["text"]) > 120 else ""),
        )

    console.print(table)


def display_section_scores(sec_scores: list):
    """Display section-level scores."""
    if not sec_scores:
        return

    console.print()
    console.print(Rule("[bold yellow]🗂 Section Scores[/]", style="yellow"))
    console.print()

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        expand=True,
    )
    table.add_column("Section", width=20)
    table.add_column("Score", width=8, justify="center")
    table.add_column("Progress", width=24)
    table.add_column("Strength", width=12)
    table.add_column("Weight", width=8, justify="center")

    for s in sec_scores:
        score = s["score"]
        color = score_color(score)
        strength = s.get("strength", "moderate")
        bar = score_bar(score)
        weight = s.get("weight", 0.5)

        table.add_row(
            f"[bold]{s['section'].title()}[/]",
            f"[bold {color}]{score}%[/]",
            bar,
            strength_badge(strength),
            f"[dim]×{weight:.1f}[/dim]",
        )

    console.print(table)


def display_suggestions(suggestions: list):
    """Display AI rewrite suggestions."""
    if not suggestions:
        return

    console.print()
    console.print(Rule("[bold bright_magenta]✨ AI Rewrite Suggestions[/]", style="bright_magenta"))
    console.print()

    for i, s in enumerate(suggestions, 1):
        orig_score = s.get("original_score", 0)
        issues = s.get("issues", [])

        panel_content = ""
        panel_content += f"[red]ORIGINAL:[/red] [dim]{s['original']}[/dim]\n"
        panel_content += f"[dim]Score: {orig_score}%[/dim]\n\n"

        if issues:
            panel_content += "[yellow]Issues detected:[/yellow]\n"
            for issue in issues:
                panel_content += f"  [dim]• {issue}[/dim]\n"
            panel_content += "\n"

        panel_content += f"[green]IMPROVED:[/green] [bold]{s['improved']}[/bold]\n"
        panel_content += f"[dim]Method: {s.get('method', 'rule_based')}[/dim]"

        console.print(Panel(
            panel_content,
            title=f"[bold]Suggestion {i}[/]",
            border_style="bright_magenta",
            box=ROUNDED,
        ))


def display_entities(entities: dict):
    """Display extracted entities from resume header."""
    if not entities:
        return

    console.print()
    console.print(Rule("[bold bright_blue]👤 Resume Metadata[/]", style="bright_blue"))
    console.print()

    items = []
    if "name" in entities:
        items.append(f"[bold]Name:[/] {entities['name']}")
    if "email" in entities:
        items.append(f"[bold]Email:[/] {entities['email']}")
    if "phone" in entities:
        items.append(f"[bold]Phone:[/] {entities['phone']}")
    if "linkedin" in entities:
        items.append(f"[bold]LinkedIn:[/] {entities['linkedin']}")
    if "urls" in entities:
        items.append(f"[bold]Links:[/] {', '.join(entities['urls'][:3])}")

    if items:
        console.print(Panel(
            "\n".join(items),
            border_style="bright_blue",
            box=ROUNDED,
        ))


# ---------------------------------------------------------------------------
# Enhanced analysis display (new multi-model dimensions)
# ---------------------------------------------------------------------------

def display_jd_metadata(analysis: dict):
    """Display parsed JD metadata."""
    jd = analysis.get("jd_analysis", {})
    if not jd:
        return

    console.print()
    console.print(Rule("[bold bright_cyan]📋 Job Description Analysis[/]", style="bright_cyan"))
    console.print()

    items = []
    if jd.get("title"):
        items.append(f"[bold]Role:[/] {jd['title']}")
    items.append(f"[bold]Seniority:[/] {jd.get('seniority', 'mid').title()}")
    if jd.get("years_experience"):
        items.append(f"[bold]Experience:[/] {jd['years_experience']}+ years")
    if jd.get("education_level"):
        items.append(f"[bold]Education:[/] {jd['education_level'].title()} in {jd.get('education_field', 'any field').title()}")

    req_count = jd.get("num_requirements", 0)
    resp_count = jd.get("num_responsibilities", 0)
    items.append(f"[bold]Requirements:[/] {req_count} items | [bold]Responsibilities:[/] {resp_count} items")

    if jd.get("required_skills"):
        skills = ", ".join(jd["required_skills"][:10])
        items.append(f"[bold]Required Skills:[/] {skills}")
    if jd.get("preferred_skills"):
        skills = ", ".join(jd["preferred_skills"][:8])
        items.append(f"[bold]Preferred Skills:[/] [dim]{skills}[/dim]")

    console.print(Panel(
        "\n".join(items),
        border_style="bright_cyan",
        box=ROUNDED,
    ))


def display_dimensions(analysis: dict):
    """Display the 4-dimension score breakdown."""
    dims = analysis.get("dimensions", {})
    weights = analysis.get("weights_used", {})
    if not dims:
        return

    console.print()
    console.print(Rule("[bold bright_yellow]🎯 Dimension Breakdown[/]", style="bright_yellow"))
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold bright_white",
                  border_style="dim", expand=True)
    table.add_column("Dimension", width=18)
    table.add_column("Score", width=8, justify="center")
    table.add_column("Progress", width=24)
    table.add_column("Weight", width=8, justify="center")
    table.add_column("Contribution", width=14, justify="center")

    dim_labels = {
        "semantic": "🧠 Semantic",
        "skills": "🔑 Skills",
        "experience": "💼 Experience",
        "education": "🎓 Education",
    }

    for dim_key, label in dim_labels.items():
        score = dims.get(dim_key, 0)
        weight = weights.get(dim_key.replace("skills", "skill"), 0)
        contribution = round(score * weight, 1)
        color = score_color(score)
        bar = score_bar(score)

        table.add_row(
            f"[bold]{label}[/]",
            f"[bold {color}]{score}%[/]",
            bar,
            f"[dim]{int(weight * 100)}%[/dim]",
            f"[bold {color}]{contribution}pts[/]",
        )

    console.print(table)


def display_experience_analysis(analysis: dict):
    """Display experience quality analysis."""
    exp = analysis.get("experience_analysis", {})
    if not exp:
        return

    console.print()
    console.print(Rule("[bold bright_green]💼 Experience Analysis[/]", style="bright_green"))
    console.print()

    fit = exp.get("seniority_fit", {})
    items = [
        f"[bold]Detected Seniority:[/] {exp.get('seniority_signal', 'mid').title()}",
        f"[bold]Seniority Fit:[/] {fit.get('fit', 'unknown').title()} ({fit.get('fit_score', 0)}%)",
        f"[bold]Impact Bullets:[/] {exp.get('impact_count', 0)} / {exp.get('bullet_count', 0)}",
        f"[bold]Leadership Signals:[/] {exp.get('leadership_count', 0)}",
        f"[bold]Overall Quality:[/] {exp.get('overall_quality', 0)}%",
    ]

    if fit.get("explanation"):
        items.append(f"\n[italic dim]{fit['explanation']}[/]")

    console.print(Panel(
        "\n".join(items),
        border_style="bright_green",
        box=ROUNDED,
    ))


def display_education_analysis(analysis: dict):
    """Display education analysis."""
    edu = analysis.get("education_analysis", {})
    if not edu or not edu.get("resume_degree"):
        return

    console.print()
    console.print(Rule("[bold bright_blue]🎓 Education Analysis[/]", style="bright_blue"))
    console.print()

    items = []
    if edu.get("resume_degree"):
        items.append(f"[bold]Degree:[/] {edu['resume_degree'].title()}")
    if edu.get("resume_field"):
        items.append(f"[bold]Field:[/] {edu['resume_field'].title()}")
    if edu.get("resume_gpa"):
        items.append(f"[bold]GPA:[/] {edu['resume_gpa']}")
    if edu.get("is_current_student"):
        items.append("[bold]Status:[/] Currently enrolled")
    items.append(f"[bold]Degree Match:[/] {edu.get('degree_match', 'N/A')}")
    items.append(f"[bold]Field Match:[/] {edu.get('field_match', 'N/A')}")
    items.append(f"[bold]Education Score:[/] {edu.get('score', 0)}%")

    console.print(Panel(
        "\n".join(items),
        border_style="bright_blue",
        box=ROUNDED,
    ))


def display_skill_matches(analysis: dict):
    """Display detailed skill match information with match types."""
    kw = analysis.get("keyword_analysis", {})
    matched_details = kw.get("matched_details", [])
    missing_details = kw.get("missing_details", [])

    if not matched_details and not missing_details:
        return

    console.print()
    console.print(Rule("[bold bright_magenta]🔗 Detailed Skill Matching[/]", style="bright_magenta"))
    console.print()

    if matched_details:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold bright_white",
                      border_style="dim", expand=True, title="[green]Matched Skills[/]")
        table.add_column("JD Skill", width=20)
        table.add_column("Resume Match", width=20)
        table.add_column("Match Type", width=15)
        table.add_column("Strength", width=10, justify="center")

        type_colors = {
            "exact": "green",
            "parent_child": "bright_green",
            "related": "yellow",
            "domain": "bright_yellow",
            "implied": "bright_cyan",
            "weak": "dim",
        }

        for m in matched_details[:15]:
            match_type = m.get("match_type", "exact")
            color = type_colors.get(match_type, "white")
            strength = m.get("strength", 0)
            sc = score_color(strength * 100)

            table.add_row(
                m.get("jd_skill", ""),
                m.get("resume_skill", ""),
                f"[{color}]{match_type}[/{color}]",
                f"[bold {sc}]{strength:.0%}[/]",
            )

        console.print(table)

    if missing_details:
        console.print()
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold bright_white",
                      border_style="dim", expand=True, title="[red]Missing Skills[/]")
        table.add_column("Missing Skill", width=20)
        table.add_column("Priority", width=12, justify="center")
        table.add_column("Related in Resume", ratio=1)

        for m in missing_details[:10]:
            priority = m.get("priority", 1.0)
            pri_label = "[bold red]Required[/]" if m.get("is_required") else "[dim]Preferred[/]"
            related = ", ".join(m.get("suggested_related", [])) or "[dim]—[/dim]"

            table.add_row(
                f"[bold]{m.get('skill', '')}[/]",
                pri_label,
                f"[dim]{related}[/dim]",
            )

        console.print(table)

    # Domain coverage
    domain_cov = kw.get("domain_coverage", {})
    if domain_cov:
        console.print()
        covered = sum(1 for d in domain_cov.values() if d.get("coverage", 0) > 0)
        total = len(domain_cov)
        console.print(f"  [dim]Domain coverage: {covered}/{total} domains | "
                      f"Required skills: {kw.get('required_coverage', 0)}% | "
                      f"Preferred skills: {kw.get('preferred_coverage', 0)}%[/dim]")


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive_mode(analysis: dict, resume_sections: dict, jd_text: str):
    """Interactive mode: select bullets to rewrite."""
    from suggestion_generator import rewrite_bullet

    bullet_scores = analysis["semantic_analysis"].get("bullet_scores", [])
    if not bullet_scores:
        console.print("[yellow]No bullets available for interactive rewriting.[/]")
        return

    console.print()
    console.print(Rule("[bold]Interactive Rewrite Mode[/]", style="bright_magenta"))
    console.print("[dim]Enter a bullet number to rewrite, or 'q' to quit.[/dim]")
    console.print()

    while True:
        try:
            choice = console.input("[bold bright_magenta]Bullet # → [/]").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice.lower() in ("q", "quit", "exit", ""):
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(bullet_scores):
                bullet = bullet_scores[idx]
                console.print(f"\n[dim]Original: {bullet['text']}[/dim]")
                console.print("[dim]Rewriting...[/dim]")

                result = rewrite_bullet(bullet["text"], jd_text)
                console.print(f"[bold green]Improved:[/] {result['improved']}")

                if result.get("issues"):
                    console.print("[yellow]Issues fixed:[/]")
                    for issue in result["issues"]:
                        console.print(f"  [dim]• {issue}[/dim]")
                console.print()
            else:
                console.print(f"[red]Invalid number. Choose 1-{len(bullet_scores)}.[/red]")
        except ValueError:
            console.print("[red]Please enter a number or 'q' to quit.[/red]")


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Elevate – AI Resume Analyzer (TUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py resume.pdf --jd "We need a Python developer with AWS experience"
  python cli.py resume.pdf --jd-file job.txt
  python cli.py resume.pdf --jd "..." --export results.json
  python cli.py resume.pdf --jd "..." --interactive
        """,
    )
    parser.add_argument("resume", help="Path to resume file (PDF or text)")
    parser.add_argument("--jd", help="Job description text")
    parser.add_argument("--jd-file", help="Path to job description file")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--interactive", action="store_true", help="Interactive rewrite mode")
    parser.add_argument("--no-banner", action="store_true", help="Skip the ASCII banner")
    args = parser.parse_args()

    # Print banner
    if not args.no_banner:
        print_banner()

    # Validate inputs
    resume_path = Path(args.resume)
    if not resume_path.exists():
        console.print(f"[bold red]Error:[/] Resume file not found: {resume_path}")
        sys.exit(1)

    jd_text = args.jd
    if args.jd_file:
        jd_path = Path(args.jd_file)
        if not jd_path.exists():
            console.print(f"[bold red]Error:[/] JD file not found: {jd_path}")
            sys.exit(1)
        jd_text = jd_path.read_text(encoding="utf-8")

    if not jd_text:
        console.print("[bold red]Error:[/] Job description is required. Use --jd or --jd-file.")
        sys.exit(1)

    # Run analysis with progress
    console.print()
    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style="bright_magenta", complete_style="bright_magenta"),
        console=console,
    ) as progress:
        # Step 1: Parse resume
        task = progress.add_task("[bold]Parsing resume...", total=4)
        from resume_parser import parse_resume, parse_resume_from_pdf

        if resume_path.suffix.lower() == ".pdf":
            resume_sections = parse_resume_from_pdf(str(resume_path))
        else:
            raw = resume_path.read_text(encoding="utf-8", errors="ignore")
            resume_sections = parse_resume(raw)
        progress.update(task, advance=1, description="[bold]Loading AI models...")

        # Step 2: Run analysis
        from analyzer import full_analysis
        progress.update(task, description="[bold]Running semantic analysis...")
        analysis = full_analysis(resume_sections, jd_text)
        progress.update(task, advance=1, description="[bold]Generating suggestions...")

        # Step 3: Generate suggestions  
        from suggestion_generator import generate_suggestions
        suggestions = generate_suggestions(
            resume_sections, jd_text,
            analysis["semantic_analysis"],
            max_suggestions=5,
        )
        analysis["suggestions"] = suggestions
        progress.update(task, advance=1, description="[bold]Preparing results...")

        time.sleep(0.3)
        progress.update(task, advance=1, description="[bold green]✓ Analysis complete!")

    console.print()

    # Display results
    display_entities(resume_sections.get("entities", {}))
    display_jd_metadata(analysis)
    display_overall_scores(analysis)
    display_dimensions(analysis)
    display_skill_matches(analysis)
    display_keyword_analysis(analysis["keyword_analysis"])
    display_bullet_scores(analysis["semantic_analysis"])
    display_section_scores(analysis.get("section_scores", []))
    display_experience_analysis(analysis)
    display_education_analysis(analysis)
    display_suggestions(suggestions)

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        # Clean up non-serializable data
        export_data = {
            "overall_score": analysis["overall_score"],
            "strength": analysis.get("strength", ""),
            "interpretation": analysis.get("interpretation", ""),
            "keyword_analysis": analysis["keyword_analysis"],
            "semantic_analysis": {
                "overall_score": analysis["semantic_analysis"]["overall_score"],
                "bullet_scores": [
                    {"text": b["text"], "similarity": b["similarity"], "strength": b.get("strength", "")}
                    for b in analysis["semantic_analysis"]["bullet_scores"]
                ],
            },
            "section_scores": [
                {"section": s["section"], "score": s["score"], "strength": s.get("strength", "")}
                for s in analysis.get("section_scores", [])
            ],
            "suggestions": [
                {"original": s["original"], "improved": s["improved"], "issues": s.get("issues", [])}
                for s in suggestions
            ],
        }
        export_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[bold green]✓[/] Results exported to [bold]{export_path}[/]")

    # Interactive mode
    if args.interactive:
        interactive_mode(analysis, resume_sections, jd_text)

    # Final summary
    console.print()
    console.print(Rule(style="dim"))
    console.print(
        Align.center(
            f"[dim]Elevate — AI Resume Analyzer & Optimizer • "
            f"Analyzed {len(resume_sections.get('bullet_points', []))} bullets across "
            f"{len(analysis.get('section_scores', []))} sections[/dim]"
        )
    )
    console.print()


if __name__ == "__main__":
    main()
