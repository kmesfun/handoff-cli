from __future__ import annotations

import json
import sys
from typing import Any

from handoff.analysis.impact import ImpactResult
from handoff.analysis.repo import RepoInfo
from handoff.analysis.risk import RiskMatch
from handoff.analysis.score import Score
from handoff.analysis.tests import TestMapping
from handoff.git.models import DiffResult


def _dump(data: Any) -> None:
    sys.stdout.write(json.dumps(data, indent=2, default=str) + "\n")


class JSONEmitter:
    """Emit structured JSON to stdout for machine consumption."""

    def emit_overview(self, info: RepoInfo, branch: str) -> None:
        _dump(
            {
                "branch": branch,
                "name": info.name,
                "languages": info.languages,
                "frameworks": info.frameworks,
                "test_dirs": [str(d) for d in info.test_dirs],
                "key_files": [{"path": p, "description": d} for p, d in info.key_files],
                "run_commands": info.run_commands,
                "test_commands": info.test_commands,
            }
        )

    def emit_pr(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
    ) -> None:
        _dump(
            {
                "branch": diff.branch,
                "base_branch": diff.base_branch,
                "commits": [{"sha": c.sha, "message": c.message} for c in diff.commits],
                "changed_files": [
                    {
                        "path": f.path,
                        "change_type": f.change_type.value,
                        "additions": f.additions,
                        "deletions": f.deletions,
                        "is_test_file": f.is_test_file,
                    }
                    for f in diff.changed_files
                ],
                "risks": _risks_to_json(risks),
                "test_mappings": _mappings_to_json(mappings),
                "score": _score_to_json(score),
            }
        )

    def emit_risks(self, risks: list[RiskMatch]) -> None:
        _dump({"risks": _risks_to_json(risks)})

    def emit_tests(self, mappings: list[TestMapping]) -> None:
        _dump({"test_mappings": _mappings_to_json(mappings)})

    def emit_impact(self, result: ImpactResult) -> None:
        _dump(
            {
                "target": result.target,
                "dependents": [
                    {"file": m.file, "context": m.context} for m in result.dependents
                ],
                "risk_warning": result.risk_warning,
            }
        )

    def emit_before_push(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMapping],
        score: Score,
    ) -> None:
        self.emit_pr(diff, risks, mappings, score)


def _risks_to_json(risks: list[RiskMatch]) -> list[dict]:
    return [
        {
            "file_path": r.file_path,
            "line_number": r.line_number,
            "line_content": r.line_content,
            "risk_type": r.risk_type,
            "severity": r.severity,
            "category": r.category,
        }
        for r in risks
    ]


def _mappings_to_json(mappings: list[TestMapping]) -> list[dict]:
    return [
        {
            "source_file": m.source_file,
            "test_files": [str(f) for f in m.test_files],
            "suggested_commands": m.suggested_commands,
            "missing_test": m.missing_test,
        }
        for m in mappings
    ]


def _score_to_json(score: Score) -> dict:
    return {
        "value": score.value,
        "label": score.label,
        "checks": [
            {
                "name": c.name,
                "passed": c.passed,
                "points_earned": c.points_earned,
                "max_points": c.max_points,
                "detail": c.detail,
            }
            for c in score.checks
        ],
    }
