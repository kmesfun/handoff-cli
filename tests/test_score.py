import pytest

from handoff.analysis.risk import RiskMatch
from handoff.analysis.score import ScoreCalculator, Score
from handoff.analysis.tests import TestMapping
from handoff.git.models import ChangeType, DiffResult, DiffMode, FileChange, Commit


def make_diff(files: list[FileChange] | None = None) -> DiffResult:
    return DiffResult(
        branch="feature",
        base_branch="main",
        changed_files=files or [],
        commits=[],
        raw_diff="",
        mode=DiffMode.BRANCH,
    )


def make_risk(risk_type: str, severity: str = "HIGH", category: str = "test") -> RiskMatch:
    return RiskMatch(
        file_path="app/foo.py",
        line_number=1,
        line_content="...",
        risk_type=risk_type,
        severity=severity,
        category=category,
    )


def make_mapping(missing: bool = False) -> TestMapping:
    return TestMapping(source_file="app/foo.py", missing_test=missing)


def test_perfect_score_no_risks_with_tests():
    diff = make_diff([FileChange("tests/test_foo.py", ChangeType.ADDED)])
    calc = ScoreCalculator()
    score = calc.score(diff, [], [make_mapping(missing=False)])
    assert score.value == 100


def test_score_deducted_for_debug():
    diff = make_diff()
    risks = [make_risk("DEBUG", "MEDIUM")]
    score = ScoreCalculator().score(diff, risks, [])
    assert score.value < 100


def test_score_deducted_for_secret():
    diff = make_diff()
    risks = [make_risk("SECRET", "HIGH")]
    score = ScoreCalculator().score(diff, risks, [])
    # Secrets cost 30 points
    assert score.value <= 70


def test_score_deducted_for_todo():
    diff = make_diff()
    risks = [make_risk("TODO", "LOW", "TODO")]
    score = ScoreCalculator().score(diff, risks, [])
    assert score.value < 100


def test_score_deducted_for_missing_tests():
    diff = make_diff()
    score = ScoreCalculator().score(diff, [], [make_mapping(missing=True)])
    # Missing tests costs 25 points
    assert score.value <= 75


def test_score_zero_minimum():
    diff = make_diff()
    # Pile on many bad things
    risks = (
        [make_risk("SECRET")] * 5
        + [make_risk("DEBUG")] * 5
        + [make_risk("TODO", "MEDIUM", "FIXME")] * 5
    )
    score = ScoreCalculator().score(diff, risks, [make_mapping(missing=True)])
    assert score.value >= 0


def test_score_label_excellent():
    diff = make_diff([FileChange("tests/test_foo.py", ChangeType.ADDED)])
    score = ScoreCalculator().score(diff, [], [make_mapping(missing=False)])
    assert score.label == "Excellent"


def test_score_label_needs_attention():
    diff = make_diff()
    risks = [make_risk("SECRET"), make_risk("DEBUG"), make_risk("DEBUG")]
    score = ScoreCalculator().score(diff, risks, [make_mapping(missing=True)])
    assert score.label in ("Needs attention", "Not ready")


def test_score_has_checks():
    diff = make_diff()
    score = ScoreCalculator().score(diff, [], [])
    assert len(score.checks) > 0
    for check in score.checks:
        assert check.name
        assert 0 <= check.points_earned <= check.max_points


def test_score_checks_total_matches_value():
    diff = make_diff()
    risks = [make_risk("DEBUG")]
    score = ScoreCalculator().score(diff, risks, [make_mapping(missing=True)])
    total = sum(c.points_earned for c in score.checks)
    assert score.value == total


def test_score_color_green_for_high_score():
    diff = make_diff([FileChange("tests/test_foo.py", ChangeType.ADDED)])
    score = ScoreCalculator().score(diff, [], [make_mapping(missing=False)])
    assert score.color == "green"


def test_score_color_red_for_low_score():
    diff = make_diff()
    risks = [make_risk("SECRET"), make_risk("DEBUG"), make_risk("DEBUG")]
    score = ScoreCalculator().score(diff, risks, [make_mapping(missing=True)])
    assert score.color in ("red", "yellow")
