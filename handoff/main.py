from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from handoff import __version__
from handoff.analysis.impact import ImpactAnalyzer
from handoff.analysis.repo import RepoScanner
from handoff.analysis.risk import RiskDetector
from handoff.analysis.score import ScoreCalculator
from handoff.analysis.tests import TestMapper
from handoff.config import load_config
from handoff.git.analyzer import GitAnalyzer, GitError
from handoff.git.models import DiffMode
from handoff.output.json_emitter import JSONEmitter
from handoff.output.markdown import MarkdownWriter
from handoff.output.pr_template import PRDescriptionBuilder
from handoff.output.terminal import TerminalFormatter
from handoff.utils.fs import find_repo_root, is_test_file

app = typer.Typer(
    name="handoff",
    help="Git-aware PR readiness and developer handoff CLI.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

_console = Console()
_err = Console(stderr=True)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _get_root() -> Path:
    root = find_repo_root()
    if root is None:
        _err.print("[red]Error:[/red] Not inside a git repository.")
        raise typer.Exit(code=2)
    return root


def _resolve_base(override: str | None, git: GitAnalyzer) -> str:
    if override:
        return override
    try:
        return git.detect_default_branch()
    except GitError as e:
        _err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2)


def _mode(staged: bool, unstaged: bool) -> DiffMode:
    if staged:
        return DiffMode.STAGED
    if unstaged:
        return DiffMode.UNSTAGED
    return DiffMode.BRANCH


def _get_diff(git: GitAnalyzer, base: str, mode: DiffMode):
    try:
        return git.get_diff(base, mode)
    except GitError as e:
        _err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def version_callback(value: bool) -> None:
    if value:
        _console.print(f"handoff {__version__}")
        raise typer.Exit()


@app.callback()
def _global(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None, "--version", "-V", callback=version_callback, is_eager=True, help="Show version."
    ),
) -> None:
    pass


@app.command()
def overview(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to a Markdown file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color."),
) -> None:
    """Analyze repo structure, detect stack, and show entry points."""
    root = _get_root()
    git = GitAnalyzer(cwd=root)
    branch = git.get_current_branch()
    info = RepoScanner(root).scan()

    if json_output:
        JSONEmitter().emit_overview(info, branch)
    elif output:
        MarkdownWriter(root).write_overview(info, branch, output)
        _console.print(f"[green]✓[/green] Written to {output}")
    else:
        TerminalFormatter(Console(no_color=no_color)).render_overview(info, branch)


@app.command()
def pr(
    base: Optional[str] = typer.Option(None, "--base", "-b", help="Base branch (default: auto-detect)."),
    staged: bool = typer.Option(False, "--staged", help="Only staged changes."),
    unstaged: bool = typer.Option(False, "--unstaged", help="Only unstaged changes."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to a Markdown file."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="More detail."),
) -> None:
    """Full PR readiness analysis of the current branch vs base."""
    root = _get_root()
    config = load_config(root)
    git = GitAnalyzer(cwd=root)
    base_branch = _resolve_base(base or config.base_branch, git)
    diff = _get_diff(git, base_branch, _mode(staged, unstaged))

    if not diff.changed_files:
        _console.print(f"[dim]No changes between [bold]{diff.branch}[/bold] and {base_branch}.[/dim]")
        raise typer.Exit(0)

    risks = RiskDetector().analyze(diff)
    source_paths = [f.path for f in diff.changed_files if not is_test_file(f.path)]
    mapper = TestMapper(root)
    mappings = [mapper.map_file(p) for p in source_paths]
    score = ScoreCalculator().score(diff, risks, mappings)
    repo_info = RepoScanner(root).scan()

    if json_output:
        JSONEmitter().emit_pr(diff, risks, mappings, score)
    elif output:
        MarkdownWriter(root).write_pr_report(diff, risks, mappings, score, repo_info, output)
        _console.print(f"[green]✓[/green] Written to {output}")
    else:
        TerminalFormatter(Console(no_color=no_color), verbose=verbose).render_pr(
            diff, risks, mappings, score
        )

    # Non-zero exit if there are pattern warnings so CI can gate on this
    pattern_risks = [r for r in risks if r.risk_type in ("DEBUG", "SECRET")]
    if pattern_risks:
        raise typer.Exit(1)


@app.command()
def risks(
    base: Optional[str] = typer.Option(None, "--base", "-b"),
    staged: bool = typer.Option(False, "--staged"),
    unstaged: bool = typer.Option(False, "--unstaged"),
    json_output: bool = typer.Option(False, "--json"),
    no_color: bool = typer.Option(False, "--no-color"),
) -> None:
    """Scan changed files for risky patterns and high-risk file categories."""
    root = _get_root()
    config = load_config(root)
    git = GitAnalyzer(cwd=root)
    base_branch = _resolve_base(base or config.base_branch, git)
    diff = _get_diff(git, base_branch, _mode(staged, unstaged))

    found = RiskDetector().analyze(diff)

    if json_output:
        JSONEmitter().emit_risks(found)
    else:
        TerminalFormatter(Console(no_color=no_color)).render_risks(found, diff.changed_files)

    high = [r for r in found if r.severity == "HIGH" and r.risk_type in ("DEBUG", "SECRET")]
    if high:
        raise typer.Exit(1)


@app.command()
def tests(
    base: Optional[str] = typer.Option(None, "--base", "-b"),
    staged: bool = typer.Option(False, "--staged"),
    unstaged: bool = typer.Option(False, "--unstaged"),
    json_output: bool = typer.Option(False, "--json"),
    no_color: bool = typer.Option(False, "--no-color"),
) -> None:
    """Recommend tests based on changed source files."""
    root = _get_root()
    config = load_config(root)
    git = GitAnalyzer(cwd=root)
    base_branch = _resolve_base(base or config.base_branch, git)
    diff = _get_diff(git, base_branch, _mode(staged, unstaged))

    source_paths = [f.path for f in diff.changed_files if not is_test_file(f.path)]
    mappings = [TestMapper(root).map_file(p) for p in source_paths]

    if json_output:
        JSONEmitter().emit_tests(mappings)
    else:
        TerminalFormatter(Console(no_color=no_color)).render_tests(mappings, root)


@app.command()
def impact(
    file: str = typer.Argument(help="File path to analyze (relative to cwd)."),
    json_output: bool = typer.Option(False, "--json"),
    no_color: bool = typer.Option(False, "--no-color"),
) -> None:
    """Show files that import or depend on the given file."""
    root = _get_root()
    target = (Path.cwd() / file).resolve()
    if not target.exists():
        _err.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    result = ImpactAnalyzer(root).analyze(target)

    if json_output:
        JSONEmitter().emit_impact(result)
    else:
        TerminalFormatter(Console(no_color=no_color)).render_impact(result)


@app.command(name="write-pr")
def write_pr(
    base: Optional[str] = typer.Option(None, "--base", "-b"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file."),
    no_color: bool = typer.Option(False, "--no-color"),
) -> None:
    """Generate a Markdown PR description from the current diff."""
    root = _get_root()
    config = load_config(root)
    git = GitAnalyzer(cwd=root)
    base_branch = _resolve_base(base or config.base_branch, git)
    diff = _get_diff(git, base_branch, DiffMode.BRANCH)

    risks_found = RiskDetector().analyze(diff)
    source_paths = [f.path for f in diff.changed_files if not is_test_file(f.path)]
    mappings = [TestMapper(root).map_file(p) for p in source_paths]
    repo_info = RepoScanner(root).scan()

    content = PRDescriptionBuilder().build(diff, risks_found, mappings, repo_info)

    if output:
        output.write_text(content)
        _console.print(f"[green]✓[/green] PR description written to [cyan]{output}[/cyan]")
    else:
        Console(no_color=no_color).print(content)


@app.command(name="before-push")
def before_push(
    base: Optional[str] = typer.Option(None, "--base", "-b"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    json_output: bool = typer.Option(False, "--json"),
    no_color: bool = typer.Option(False, "--no-color"),
) -> None:
    """Full pre-push checklist: risks + test recommendations + PR description draft."""
    root = _get_root()
    config = load_config(root)
    git = GitAnalyzer(cwd=root)
    base_branch = _resolve_base(base or config.base_branch, git)
    diff = _get_diff(git, base_branch, DiffMode.BRANCH)

    if not diff.changed_files:
        _console.print("[dim]No changes detected. Nothing to check.[/dim]")
        raise typer.Exit(0)

    risks_found = RiskDetector().analyze(diff)
    source_paths = [f.path for f in diff.changed_files if not is_test_file(f.path)]
    mappings = [TestMapper(root).map_file(p) for p in source_paths]
    score = ScoreCalculator().score(diff, risks_found, mappings)
    repo_info = RepoScanner(root).scan()

    if json_output:
        JSONEmitter().emit_before_push(diff, risks_found, mappings, score)
    elif output:
        MarkdownWriter(root).write_before_push(diff, risks_found, mappings, score, repo_info, output)
        _console.print(f"[green]✓[/green] Report written to [cyan]{output}[/cyan]")
    else:
        TerminalFormatter(Console(no_color=no_color), verbose=True).render_before_push(
            diff, risks_found, mappings, score, repo_info
        )

    # Non-zero exit if any debug or secret patterns found
    blocking = [r for r in risks_found if r.risk_type in ("DEBUG", "SECRET")]
    if blocking:
        raise typer.Exit(1)


@app.command(name="install-hook")
def install_hook() -> None:
    """Install a Git pre-push hook that runs handoff before-push automatically."""
    root = _get_root()
    hooks_dir = root / ".git" / "hooks"
    hook_path = hooks_dir / "pre-push"

    hook_content = """#!/bin/sh
# Installed by handoff-cli
handoff before-push
"""
    if hook_path.exists():
        overwrite = typer.confirm(
            f"A pre-push hook already exists at {hook_path}. Overwrite?"
        )
        if not overwrite:
            raise typer.Exit(0)

    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)
    _console.print(f"[green]✓[/green] Pre-push hook installed at [cyan]{hook_path}[/cyan]")
    _console.print("[dim]handoff before-push will run automatically before each git push.[/dim]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    app()


if __name__ == "__main__":
    main()
