"""CLI integration tests using a real temp git repo."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from handoff.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Real git repo with two commits and a feature branch."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@test.com")
    _git(tmp_path, "config", "user.name", "Test User")

    # Initial commit on main
    (tmp_path / "README.md").write_text("# Test repo")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "testapp"')
    (tmp_path / "requirements.txt").write_text("fastapi\npytest\n")
    (tmp_path / "Makefile").write_text("test:\n\tpytest -v\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "initial commit")

    # Feature branch
    _git(tmp_path, "checkout", "-b", "feature/auth")

    # Tests dir
    (tmp_path / "tests").mkdir()
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "auth").mkdir()

    (tmp_path / "app" / "auth" / "token.py").write_text(
        'def create(uid):\n    print("debug", uid)\n    # TODO: fix this\n    return uid\n'
    )
    (tmp_path / "tests" / "test_token.py").write_text(
        "from app.auth.token import create\ndef test_create(): assert create(1) == 1\n"
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "add auth token module")

    return tmp_path


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)


# ---------------------------------------------------------------------------
# overview command
# ---------------------------------------------------------------------------


def test_overview_exits_zero(git_repo: Path):
    result = runner.invoke(app, ["overview"], catch_exceptions=False)
    # May fail if not in the git_repo dir, use env cwd via invoke
    # We test via JSON output for reliability
    result = runner.invoke(app, ["overview", "--json"], catch_exceptions=False)
    assert result.exit_code == 0


def test_overview_json_structure(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["overview", "--json"], catch_exceptions=False)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "languages" in data
    assert "frameworks" in data
    assert "name" in data


# ---------------------------------------------------------------------------
# pr command
# ---------------------------------------------------------------------------


def test_pr_json_output(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    assert result.exit_code in (0, 1)  # 1 = warnings found (debug print in fixture)
    data = json.loads(result.output)
    assert "changed_files" in data
    assert "risks" in data
    assert "score" in data


def test_pr_json_has_changed_files(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    data = json.loads(result.output)
    paths = [f["path"] for f in data["changed_files"]]
    assert any("token" in p for p in paths)


def test_pr_detects_debug_risk(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    data = json.loads(result.output)
    risk_types = [r["risk_type"] for r in data["risks"]]
    assert "DEBUG" in risk_types


def test_pr_detects_todo(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    data = json.loads(result.output)
    risk_types = [r["risk_type"] for r in data["risks"]]
    assert "TODO" in risk_types


def test_pr_score_present(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    data = json.loads(result.output)
    assert "value" in data["score"]
    assert 0 <= data["score"]["value"] <= 100


def test_pr_nonzero_exit_on_debug(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["pr", "--base", "main", "--json"], catch_exceptions=False)
    # The fixture has a print() statement, so exit code should be 1
    assert result.exit_code == 1


def test_pr_output_file(git_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(git_repo)
    out = tmp_path / "report.md"
    result = runner.invoke(
        app, ["pr", "--base", "main", "--output", str(out)], catch_exceptions=False
    )
    assert out.exists()
    content = out.read_text()
    assert "Changed Files" in content


# ---------------------------------------------------------------------------
# risks command
# ---------------------------------------------------------------------------


def test_risks_json(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["risks", "--base", "main", "--json"], catch_exceptions=False)
    assert result.exit_code in (0, 1)
    data = json.loads(result.output)
    assert "risks" in data


# ---------------------------------------------------------------------------
# tests command
# ---------------------------------------------------------------------------


def test_tests_json(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["tests", "--base", "main", "--json"], catch_exceptions=False)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "test_mappings" in data


def test_tests_maps_token_to_test_file(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["tests", "--base", "main", "--json"], catch_exceptions=False)
    data = json.loads(result.output)
    source_files = [m["source_file"] for m in data["test_mappings"]]
    assert any("token" in s for s in source_files)


# ---------------------------------------------------------------------------
# write-pr command
# ---------------------------------------------------------------------------


def test_write_pr_produces_markdown(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["write-pr", "--base", "main"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "## Summary" in result.output
    assert "## Changes" in result.output


def test_write_pr_output_file(git_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(git_repo)
    out = tmp_path / "pr.md"
    result = runner.invoke(
        app, ["write-pr", "--base", "main", "--output", str(out)], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert out.exists()
    assert "## Summary" in out.read_text()


# ---------------------------------------------------------------------------
# before-push command
# ---------------------------------------------------------------------------


def test_before_push_json(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(git_repo)
    result = runner.invoke(app, ["before-push", "--base", "main", "--json"], catch_exceptions=False)
    assert result.exit_code in (0, 1)
    data = json.loads(result.output)
    assert "score" in data
    assert "risks" in data


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_not_in_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["pr"], catch_exceptions=False)
    assert result.exit_code == 2


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
