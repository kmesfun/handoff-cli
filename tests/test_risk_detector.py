from pathlib import Path

import pytest

from handoff.analysis.risk import RiskDetector
from handoff.git.diff_parser import DiffParser
from handoff.git.models import ChangeType, DiffResult, DiffMode, FileChange, Commit

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "diffs"


def make_diff(changed_files: list[FileChange]) -> DiffResult:
    return DiffResult(
        branch="feature",
        base_branch="main",
        changed_files=changed_files,
        commits=[],
        raw_diff="",
        mode=DiffMode.BRANCH,
    )


def make_file(path: str, added_lines: list[str]) -> FileChange:
    return FileChange(
        path=path,
        change_type=ChangeType.MODIFIED,
        additions=len(added_lines),
        deletions=0,
        added_lines=added_lines,
    )


# ---------------------------------------------------------------------------
# Category detection tests
# ---------------------------------------------------------------------------


def test_detects_auth_category():
    detector = RiskDetector()
    diff = make_diff([make_file("app/auth/token.py", [])])
    risks = detector.analyze(diff)
    cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
    assert any(r.category == "auth" for r in cat_risks)


def test_detects_migration_category():
    detector = RiskDetector()
    diff = make_diff([make_file("migrations/versions/001.py", [])])
    risks = detector.analyze(diff)
    cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
    assert any(r.category == "migration" for r in cat_risks)


def test_detects_payments_category():
    detector = RiskDetector()
    diff = make_diff([make_file("app/billing/invoice.py", [])])
    risks = detector.analyze(diff)
    cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
    assert any(r.category == "payments" for r in cat_risks)


def test_no_false_positive_regular_file():
    detector = RiskDetector()
    diff = make_diff([make_file("app/models/product.py", [])])
    risks = detector.analyze(diff)
    cat_risks = [r for r in risks if r.risk_type == "CATEGORY"]
    # product.py should not match auth/payments/migration
    risky = [r for r in cat_risks if r.severity == "HIGH"]
    assert len(risky) == 0


def test_only_first_category_matched_per_file():
    detector = RiskDetector()
    # File path matches both "auth" and "security"
    diff = make_diff([make_file("app/auth/security/token.py", [])])
    risks = detector.analyze(diff)
    cat_risks = [r for r in risks if r.risk_type == "CATEGORY" and r.file_path == "app/auth/security/token.py"]
    assert len(cat_risks) == 1  # Only one category matched


# ---------------------------------------------------------------------------
# Pattern detection tests
# ---------------------------------------------------------------------------


def test_detects_console_log():
    detector = RiskDetector()
    diff = make_diff([make_file("app/api.js", ['console.log("debug", data)'])])
    risks = detector.analyze(diff)
    pat = [r for r in risks if r.risk_type == "DEBUG"]
    assert len(pat) == 1
    assert pat[0].category == "console.log"


def test_detects_print_statement():
    detector = RiskDetector()
    diff = make_diff([make_file("app/service.py", ["    print('debug value:', x)"])])
    risks = detector.analyze(diff)
    pat = [r for r in risks if r.risk_type == "DEBUG"]
    assert any(r.category == "print()" for r in pat)


def test_detects_debugger():
    detector = RiskDetector()
    diff = make_diff([make_file("src/app.js", ["debugger"])])
    risks = detector.analyze(diff)
    pat = [r for r in risks if r.risk_type == "DEBUG"]
    assert any(r.severity == "HIGH" for r in pat)


def test_detects_pdb():
    detector = RiskDetector()
    diff = make_diff([make_file("app/view.py", ["pdb.set_trace()"])])
    risks = detector.analyze(diff)
    assert any(r.risk_type == "DEBUG" and r.severity == "HIGH" for r in risks)


def test_detects_todo():
    detector = RiskDetector()
    diff = make_diff([make_file("app/handler.py", ["# TODO: fix this before release"])])
    risks = detector.analyze(diff)
    assert any(r.risk_type == "TODO" and r.category == "TODO" for r in risks)


def test_detects_fixme():
    detector = RiskDetector()
    diff = make_diff([make_file("app/handler.py", ["# FIXME: broken edge case"])])
    risks = detector.analyze(diff)
    assert any(r.risk_type == "TODO" and r.category == "FIXME" for r in risks)


def test_detects_possible_secret_api_key():
    detector = RiskDetector()
    diff = make_diff([make_file("app/config.py", ['api_key = "sk-abc123supersecretXYZ"'])])
    risks = detector.analyze(diff)
    assert any(r.risk_type == "SECRET" for r in risks)


def test_detects_possible_secret_password():
    detector = RiskDetector()
    diff = make_diff([make_file("app/config.py", ['password = "hardcoded1234!"'])])
    risks = detector.analyze(diff)
    assert any(r.risk_type == "SECRET" for r in risks)


def test_no_secret_for_placeholder():
    detector = RiskDetector()
    diff = make_diff([make_file("app/config.py", ['api_key = "your_api_key_here"'])])
    risks = detector.analyze(diff)
    assert not any(r.risk_type == "SECRET" for r in risks)


def test_no_secret_for_example():
    detector = RiskDetector()
    diff = make_diff([make_file("app/config.py", ['password = "example_password"'])])
    risks = detector.analyze(diff)
    assert not any(r.risk_type == "SECRET" for r in risks)


def test_secrets_skipped_in_test_files():
    detector = RiskDetector()
    diff = make_diff([make_file("tests/test_auth.py", ['api_key = "sk-real123supersecretXYZ"'])])
    risks = detector.analyze(diff)
    assert not any(r.risk_type == "SECRET" for r in risks)


def test_one_risk_per_line():
    detector = RiskDetector()
    # Line matches both console.log and TODO but we only report the first match
    diff = make_diff([make_file("app/api.js", ['console.log("TODO: fix")'])])
    risks = detector.analyze(diff)
    pattern_risks = [r for r in risks if r.risk_type == "DEBUG"]
    assert len(pattern_risks) == 1


def test_risk_includes_line_number():
    detector = RiskDetector()
    diff = make_diff([make_file("app/api.py", ["x = 1", "print('debug')", "y = 2"])])
    risks = detector.analyze(diff)
    debug = [r for r in risks if r.risk_type == "DEBUG"]
    assert debug[0].line_number == 2


def test_analyze_full_patch():
    parser = DiffParser()
    patch = (Path(__file__).parent / "fixtures" / "diffs" / "sample_auth.patch").read_text()
    name_status = [
        ("M", "app/auth/token.py"),
        ("M", "app/auth/middleware.py"),
        ("M", "app/config.py"),
        ("A", "migrations/versions/001_add_last_login.py"),
        ("A", "tests/test_token.py"),
    ]
    files = parser.parse_diff(patch, name_status)
    diff = make_diff(files)
    detector = RiskDetector()
    risks = detector.analyze(diff)

    risk_types = {r.risk_type for r in risks}
    assert "CATEGORY" in risk_types
    assert "DEBUG" in risk_types   # print() in token.py
    assert "TODO" in risk_types    # TODO in token.py
    assert "SECRET" in risk_types  # api_key in config.py
