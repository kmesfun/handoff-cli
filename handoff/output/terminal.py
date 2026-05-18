from __future__ import annotations

from pathlib import Path

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from handoff.analysis.impact import ImpactResult
from handoff.analysis.repo import RepoInfo
from handoff.analysis.risk import RiskMatch
from handoff.analysis.score import Score
from handoff.analysis.tests import TestMapping
from handoff.git.models import DiffResult, FileChange

SEVERITY_COLORS = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}
SEVERITY_ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}
CHANGE_ICONS = {"A": "[green]+[/green]", "M": "[yellow]~[/yellow]", "D": "[red]-[/red]", "R": "[cyan]→[/cyan]", "U": "[dim]?[/dim]"}


class TerminalFormatter:
    """Render analysis results to the terminal using Rich."""

    def __init__(self, console: Console | None = None, verbose: bool = False) -> None:
        self.c = console or Console()
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public render methods
    # ------------------------------------------------------------------

    def render_overview(self, info: RepoInfo, branch: str) -> None:
        self.c.print()
        self.c.print(
            Panel(
                f"[bold]Repo:[/bold] [cyan]{info.name}[/cyan]   "
                f"[bold]Branch:[/bold] [green]{branch}[/green]",
                title="[bold white]handoff — Repo Overview[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )

        # Stack
        self.c.print(Rule("[dim]Stack[/dim]", style="dim"))
        if info.languages:
            self.c.print(f"  [bold]Languages:[/bold]   {', '.join(info.languages)}")
        if info.frameworks:
            self.c.print(f"  [bold]Frameworks:[/bold]  {', '.join(info.frameworks)}")
        else:
            self.c.print("  [dim]No frameworks detected[/dim]")

        # Key files
        self.c.print()
        self.c.print(Rule("[dim]Key Files[/dim]", style="dim"))
        if info.key_files:
            t = Table(box=None, show_header=False, padding=(0, 2))
            t.add_column("file", style="cyan", no_wrap=True)
            t.add_column("desc", style="dim")
            for path, desc in info.key_files[:12]:
                t.add_row(path, desc)
            self.c.print(t)

        # Commands
        if info.run_commands or info.test_commands:
            self.c.print()
            self.c.print(Rule("[dim]Commands[/dim]", style="dim"))
            t = Table(box=None, show_header=False, padding=(0, 2))
            t.add_column("name", style="bold")
            t.add_column("cmd", style="cyan")
            for name, cmd in {**info.run_commands, **info.test_commands}.items():
                t.add_row(name, cmd)
            self.c.print(t)

        # Test dirs
        if info.test_dirs:
            self.c.print()
            self.c.print(
                f"  [dim]Test directories:[/dim] "
                + ", ".join(f"[cyan]{d.name}[/cyan]" for d in info.test_dirs)
            )
        self.c.print()

    def render_pr(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
    ) -> None:
        commit_info = f"  [dim]{len(diff.commits)} commit(s) ahead of [/dim][cyan]{diff.base_branch}[/cyan]"
        self.c.print()
        self.c.print(
            Panel(
                f"[bold]Branch:[/bold] [green]{diff.branch}[/green] [dim]→[/dim] [cyan]{diff.base_branch}[/cyan]\n"
                + commit_info,
                title="[bold white]handoff — PR Readiness Report[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )

        self._render_changed_files(diff, risks)
        self._render_pattern_warnings(risks)
        self._render_test_recommendations(mappings)
        self._render_score(score)
        self.c.print()

    def render_risks(self, risks: list[RiskMatch], changed_files: list[FileChange]) -> None:
        self.c.print()
        self.c.print(
            Panel(
                "[dim]Scanning changed files for risky patterns and high-risk areas[/dim]",
                title="[bold white]handoff — Risk Report[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )

        cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
        pat_risks = [r for r in risks if r.risk_type != "CATEGORY"]

        if cat_risks:
            self.c.print(Rule("[dim]Category Risks[/dim]", style="dim"))
            t = Table(box=None, show_header=False, padding=(0, 1))
            t.add_column("sev", width=8)
            t.add_column("cat", style="bold", width=14)
            t.add_column("file", style="cyan")
            for r in cat_risks:
                icon = SEVERITY_ICONS.get(r.severity, "⚪")
                color = SEVERITY_COLORS.get(r.severity, "white")
                t.add_row(
                    f"{icon} [{color}]{r.severity}[/{color}]",
                    r.category,
                    r.file_path,
                )
            self.c.print(t)

        if pat_risks:
            self.c.print()
            self.c.print(Rule("[dim]Pattern Warnings[/dim]", style="dim"))
            t = Table(box=None, show_header=False, padding=(0, 1))
            t.add_column("type", width=10)
            t.add_column("loc", style="cyan", width=40)
            t.add_column("snippet", style="dim")
            for r in pat_risks:
                loc = f"{r.file_path}:{r.line_number}" if r.line_number else r.file_path
                color = SEVERITY_COLORS.get(r.severity, "white")
                t.add_row(
                    f"[{color}]{r.risk_type}[/{color}]",
                    loc,
                    r.line_content[:70],
                )
            self.c.print(t)

        if not risks:
            self.c.print("  [green]✓[/green]  No risks detected.")
        self.c.print()

    def render_tests(self, mappings: list[TestMapping], repo_root: Path) -> None:
        self.c.print()
        self.c.print(
            Panel(
                "[dim]Mapping changed source files to their test counterparts[/dim]",
                title="[bold white]handoff — Test Recommendations[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )
        self.c.print(Rule("[dim]Source → Test[/dim]", style="dim"))

        t = Table(box=None, show_header=True, padding=(0, 1))
        t.add_column("Source file", style="cyan")
        t.add_column("Test file(s)", style="dim")
        t.add_column("", width=2)

        missing: list[str] = []
        for m in mappings:
            if m.test_files:
                test_str = ", ".join(f.name for f in m.test_files)
                t.add_row(m.source_file, test_str, "[green]✓[/green]")
            else:
                t.add_row(m.source_file, "[dim]not found[/dim]", "[red]✗[/red]")
                missing.append(m.source_file)
        self.c.print(t)

        # Combined commands
        all_commands = list(
            dict.fromkeys(cmd for m in mappings for cmd in m.suggested_commands)
        )
        if all_commands:
            self.c.print()
            self.c.print(Rule("[dim]Commands[/dim]", style="dim"))
            for cmd in all_commands:
                self.c.print(f"  [bold cyan]$[/bold cyan] {cmd}")

        if missing:
            self.c.print()
            self.c.print(f"  [yellow]⚠[/yellow]  No test found for {len(missing)} file(s):")
            for f in missing:
                self.c.print(f"    [dim]{f}[/dim]")
        self.c.print()

    def render_impact(self, result: ImpactResult) -> None:
        self.c.print()
        self.c.print(
            Panel(
                f"[bold]Target:[/bold] [cyan]{result.target}[/cyan]",
                title="[bold white]handoff — Impact Analysis[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )

        if result.dependents:
            self.c.print(Rule(f"[dim]{len(result.dependents)} file(s) reference this[/dim]", style="dim"))
            t = Table(box=None, show_header=False, padding=(0, 1))
            t.add_column("file", style="cyan")
            t.add_column("context", style="dim")
            for m in result.dependents[:30]:
                t.add_row(m.file, m.context[:60])
            self.c.print(t)
            if len(result.dependents) > 30:
                self.c.print(f"  [dim]... and {len(result.dependents) - 30} more[/dim]")
        else:
            self.c.print("  [green]✓[/green]  No files found that import this file.")

        if result.risk_warning:
            self.c.print()
            self.c.print(f"  [yellow]⚠[/yellow]  {result.risk_warning}")
        self.c.print()

    def render_before_push(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
        repo_info: RepoInfo,
    ) -> None:
        self.c.print()
        self.c.print(
            Panel(
                f"[bold]Branch:[/bold] [green]{diff.branch}[/green] [dim]→[/dim] [cyan]{diff.base_branch}[/cyan]",
                title="[bold white]handoff — Pre-Push Checklist[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )
        self._render_changed_files(diff, risks)
        self._render_pattern_warnings(risks)
        self._render_test_recommendations(mappings)
        self._render_score(score)
        self.c.print()
        self.c.print(Rule("[dim]PR Description[/dim]", style="dim"))
        self.c.print("  Run [bold cyan]handoff write-pr[/bold cyan] to generate a PR description.")
        self.c.print()

    # ------------------------------------------------------------------
    # Shared section renderers
    # ------------------------------------------------------------------

    def _render_changed_files(self, diff: DiffResult, risks: list[RiskMatch]) -> None:
        risky_paths = {r.file_path: r for r in risks if r.risk_type == "CATEGORY"}
        n = len(diff.changed_files)
        self.c.print()
        self.c.print(Rule(f"[dim]Changed Files ({n})[/dim]", style="dim"))

        t = Table(box=None, show_header=False, padding=(0, 1))
        t.add_column("icon", width=2)
        t.add_column("file", style="cyan")
        t.add_column("+", justify="right", style="green", width=6)
        t.add_column("-", justify="right", style="red", width=6)
        t.add_column("risk", width=22)

        for fc in diff.changed_files:
            icon = CHANGE_ICONS.get(fc.change_type.value, "?")
            risk = risky_paths.get(fc.path)
            if risk:
                color = SEVERITY_COLORS.get(risk.severity, "white")
                sev_icon = SEVERITY_ICONS.get(risk.severity, "")
                risk_text = f"{sev_icon} [{color}]{risk.category}[/{color}]"
            else:
                risk_text = ""
            t.add_row(icon, fc.path, f"+{fc.additions}", f"-{fc.deletions}", risk_text)

        self.c.print(t)

    def _render_pattern_warnings(self, risks: list[RiskMatch]) -> None:
        pat_risks = [r for r in risks if r.risk_type != "CATEGORY"]
        if not pat_risks:
            return
        self.c.print()
        self.c.print(Rule(f"[dim]Pattern Warnings ({len(pat_risks)})[/dim]", style="dim"))
        t = Table(box=None, show_header=False, padding=(0, 1))
        t.add_column("icon", width=3)
        t.add_column("type", width=8)
        t.add_column("location", style="cyan", width=42)
        t.add_column("snippet", style="dim")
        for r in pat_risks:
            color = SEVERITY_COLORS.get(r.severity, "white")
            loc = f"{r.file_path}:{r.line_number}" if r.line_number else r.file_path
            t.add_row(
                "[yellow]⚠[/yellow]",
                f"[{color}]{r.risk_type}[/{color}]",
                loc,
                r.line_content[:60],
            )
        self.c.print(t)

    def _render_test_recommendations(self, mappings: list[TestMapping]) -> None:
        if not mappings:
            return
        self.c.print()
        self.c.print(Rule("[dim]Test Recommendations[/dim]", style="dim"))

        t = Table(box=None, show_header=False, padding=(0, 1))
        t.add_column("source", style="cyan", width=38)
        t.add_column("arrow", width=3)
        t.add_column("test", width=30)
        t.add_column("status", width=3)
        for m in mappings:
            test_str = m.test_files[0].name if m.test_files else "[dim]not found[/dim]"
            status = "[green]✓[/green]" if not m.missing_test else "[red]✗[/red]"
            t.add_row(m.source_file, "→", test_str, status)
        self.c.print(t)

        all_commands = list(
            dict.fromkeys(cmd for m in mappings for cmd in m.suggested_commands)
        )
        if all_commands:
            self.c.print()
            for cmd in all_commands:
                self.c.print(f"  [bold cyan]$[/bold cyan] {cmd}")

    def _render_score(self, score: Score) -> None:
        self.c.print()
        self.c.print(Rule("[dim]Readiness Score[/dim]", style="dim"))

        bar_filled = int(score.value / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        color = score.color

        self.c.print(
            f"  [{color}]{bar}[/{color}]  "
            f"[bold {color}]{score.value}/100[/bold {color}]  "
            f"[dim]{score.label}[/dim]"
        )
        self.c.print()

        for check in score.checks:
            icon = "[green]✓[/green]" if check.passed else "[red]✗[/red]"
            self.c.print(f"  {icon}  {check.name}  [dim]{check.detail}[/dim]")
