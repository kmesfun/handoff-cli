from __future__ import annotations

from dataclasses import dataclass

from handoff.analysis.risk import RiskMatch
from handoff.git.models import DiffResult


@dataclass
class ScoreCheck:
    name: str
    passed: bool
    max_points: int
    points_earned: int
    detail: str


@dataclass
class Score:
    value: int          # 0–100
    checks: list[ScoreCheck]

    @property
    def label(self) -> str:
        if self.value >= 90:
            return "Excellent"
        if self.value >= 75:
            return "Good"
        if self.value >= 50:
            return "Needs attention"
        return "Not ready"

    @property
    def color(self) -> str:
        if self.value >= 90:
            return "green"
        if self.value >= 75:
            return "yellow"
        return "red"


@dataclass
class TestMappingLike:
    """Duck-typed subset of TestMapping that ScoreCalculator actually reads."""
    missing_test: bool


class ScoreCalculator:
    """Compute a 0–100 PR readiness score from analysis results."""

    def score(
        self,
        diff: DiffResult,
        risks: list[RiskMatch],
        mappings: list[TestMappingLike],
    ) -> Score:
        checks: list[ScoreCheck] = []

        # ── Tests (25 pts) ─────────────────────────────────────────────
        test_files_touched = bool(diff.test_files)
        tests_mapped = any(not m.missing_test for m in mappings) if mappings else True
        has_tests = test_files_touched or tests_mapped
        checks.append(
            ScoreCheck(
                name="Tests added or mapped",
                passed=has_tests,
                max_points=25,
                points_earned=25 if has_tests else 0,
                detail="Test files found in diff" if test_files_touched else (
                    "Existing test files mapped" if tests_mapped else "No test files found"
                ),
            )
        )

        # ── No debug statements (25 pts) ────────────────────────────────
        debug_risks = [r for r in risks if r.risk_type == "DEBUG"]
        debug_deduction = min(25, len(debug_risks) * 8)
        checks.append(
            ScoreCheck(
                name="No debug statements",
                passed=len(debug_risks) == 0,
                max_points=25,
                points_earned=max(0, 25 - debug_deduction),
                detail=f"{len(debug_risks)} debug statement(s) found" if debug_risks else "Clean",
            )
        )

        # ── No possible secrets (30 pts) ────────────────────────────────
        secret_risks = [r for r in risks if r.risk_type == "SECRET"]
        checks.append(
            ScoreCheck(
                name="No possible secrets",
                passed=len(secret_risks) == 0,
                max_points=30,
                points_earned=0 if secret_risks else 30,
                detail=f"{len(secret_risks)} possible secret(s) found" if secret_risks else "Clean",
            )
        )

        # ── No TODO/FIXME (10 pts) ──────────────────────────────────────
        todo_risks = [r for r in risks if r.risk_type == "TODO"]
        todo_deduction = min(10, len(todo_risks) * 3)
        checks.append(
            ScoreCheck(
                name="No TODO/FIXME introduced",
                passed=len(todo_risks) == 0,
                max_points=10,
                points_earned=max(0, 10 - todo_deduction),
                detail=f"{len(todo_risks)} TODO/FIXME found" if todo_risks else "Clean",
            )
        )

        # ── Migration has context (10 pts) ──────────────────────────────
        migration_risks = [r for r in risks if r.category == "migration"]
        has_migration = bool(migration_risks)
        # If there IS a migration file in the diff, reward for touching it explicitly
        # (not a penalty — migrations are expected for schema changes)
        checks.append(
            ScoreCheck(
                name="Migration awareness",
                passed=True,  # Always pass; this is informational
                max_points=10,
                points_earned=10,
                detail="Migration file detected — verify rollback plan" if has_migration else "No migration",
            )
        )

        total = sum(c.points_earned for c in checks)
        return Score(value=total, checks=checks)
