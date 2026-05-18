from __future__ import annotations

from pathlib import Path

from handoff.analysis.repo import RepoInfo
from handoff.analysis.risk import RiskMatch
from handoff.analysis.score import Score
from handoff.analysis.tests import TestMapping
from handoff.git.models import DiffResult
from handoff.output.pr_template import PRDescriptionBuilder

SEVERITY_ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}


class MarkdownWriter:
    """Write analysis results to a Markdown file."""

    def __init__(self, repo_root: Path) -> None:
        self.root = repo_root

    def write_pr_report(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
        repo_info: RepoInfo,
        output_path: Path,
    ) -> None:
        lines: list[str] = []
        lines.append(f"# PR Readiness Report — `{diff.branch}`\n")
        lines.append(f"**Base:** `{diff.base_branch}` | **Score:** {score.value}/100 ({score.label})\n")

        lines.append("## Changed Files\n")
        lines.append("| File | Type | +/- |")
        lines.append("|------|------|-----|")
        for fc in diff.changed_files:
            stats = f"+{fc.additions}/-{fc.deletions}"
            lines.append(f"| `{fc.path}` | {fc.change_type.value} | {stats} |")

        if risks:
            lines.append("\n## Risk Areas\n")
            cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
            pat_risks = [r for r in risks if r.risk_type != "CATEGORY"]
            if cat_risks:
                lines.append("### Category Risks\n")
                for r in cat_risks:
                    icon = SEVERITY_ICONS.get(r.severity, "⚪")
                    lines.append(f"- {icon} **{r.severity} / {r.category}** — `{r.file_path}`")
            if pat_risks:
                lines.append("\n### Pattern Warnings\n")
                for r in pat_risks:
                    loc = f":{r.line_number}" if r.line_number else ""
                    lines.append(
                        f"- ⚠ **{r.risk_type}** `{r.file_path}{loc}` — `{r.line_content}`"
                    )

        lines.append("\n## Test Recommendations\n")
        if mappings:
            for m in mappings:
                status = "✓" if not m.missing_test else "✗ no test found"
                tests = ", ".join(f"`{f.name}`" for f in m.test_files) or "_none_"
                lines.append(f"- `{m.source_file}` → {tests} {status}")
            commands = list(dict.fromkeys(c for m in mappings for c in m.suggested_commands))
            if commands:
                lines.append("\n**Run:**")
                for cmd in commands:
                    lines.append(f"```\n{cmd}\n```")

        lines.append("\n## Readiness Score\n")
        lines.append(f"**{score.value}/100 — {score.label}**\n")
        for c in score.checks:
            icon = "✓" if c.passed else "✗"
            lines.append(f"- {icon} {c.name} ({c.points_earned}/{c.max_points} pts) — {c.detail}")

        output_path.write_text("\n".join(lines) + "\n")

    def write_overview(self, info: RepoInfo, branch: str, output_path: Path) -> None:
        lines = [
            f"# Repo Overview — `{info.name}`\n",
            f"**Branch:** `{branch}`\n",
            f"## Stack\n",
            f"**Languages:** {', '.join(info.languages)}",
            f"**Frameworks:** {', '.join(info.frameworks) or 'none detected'}\n",
            "## Key Files\n",
        ]
        for path, desc in info.key_files:
            lines.append(f"- `{path}` — {desc}")

        if info.run_commands:
            lines.append("\n## Run Commands\n")
            for name, cmd in info.run_commands.items():
                lines.append(f"- `{name}`: `{cmd}`")

        if info.test_commands:
            lines.append("\n## Test Commands\n")
            for name, cmd in info.test_commands.items():
                lines.append(f"- `{name}`: `{cmd}`")

        output_path.write_text("\n".join(lines) + "\n")

    def write_before_push(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
        repo_info: RepoInfo,
        output_path: Path,
    ) -> None:
        pr_desc = PRDescriptionBuilder().build(diff, risks, mappings, repo_info)
        report_section = self._before_push_report(diff, risks, mappings, score)
        output_path.write_text(report_section + "\n\n---\n\n" + pr_desc + "\n")

    def _before_push_report(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
    ) -> str:
        lines = [
            f"# Pre-Push Checklist — `{diff.branch}`\n",
            f"**Readiness Score:** {score.value}/100 ({score.label})\n",
        ]
        for c in score.checks:
            icon = "✓" if c.passed else "✗"
            lines.append(f"- {icon} {c.name}: {c.detail}")
        return "\n".join(lines)
