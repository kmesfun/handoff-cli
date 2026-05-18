from pathlib import Path

import pytest

from handoff.git.diff_parser import DiffParser
from handoff.git.models import ChangeType

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "diffs"


@pytest.fixture
def auth_patch() -> str:
    return (FIXTURE_DIR / "sample_auth.patch").read_text()


def test_parse_name_status_modified():
    parser = DiffParser()
    output = "M\tapp/auth/token.py\nA\tmigrations/versions/001.py\nD\told_file.py\n"
    result = parser.parse_name_status(output)
    assert ("M", "app/auth/token.py") in result
    assert ("A", "migrations/versions/001.py") in result
    assert ("D", "old_file.py") in result


def test_parse_name_status_renamed():
    parser = DiffParser()
    output = "R100\told_name.py\tnew_name.py\n"
    result = parser.parse_name_status(output)
    assert len(result) == 1
    status, path = result[0]
    assert status == "R"
    assert path == "new_name.py"


def test_parse_name_status_empty():
    parser = DiffParser()
    assert parser.parse_name_status("") == []
    assert parser.parse_name_status("  \n  \n") == []


def test_parse_diff_extracts_files(auth_patch: str):
    parser = DiffParser()
    name_status = [
        ("M", "app/auth/token.py"),
        ("M", "app/auth/middleware.py"),
        ("M", "app/config.py"),
        ("A", "migrations/versions/001_add_last_login.py"),
        ("A", "tests/test_token.py"),
    ]
    files = parser.parse_diff(auth_patch, name_status)
    paths = [f.path for f in files]
    assert "app/auth/token.py" in paths
    assert "app/auth/middleware.py" in paths
    assert "migrations/versions/001_add_last_login.py" in paths
    assert "tests/test_token.py" in paths


def test_parse_diff_counts_additions(auth_patch: str):
    parser = DiffParser()
    name_status = [("M", "app/auth/token.py")]
    files = parser.parse_diff(auth_patch, name_status)
    token_file = next(f for f in files if f.path == "app/auth/token.py")
    assert token_file.additions > 0


def test_parse_diff_collects_added_lines(auth_patch: str):
    parser = DiffParser()
    name_status = [("M", "app/auth/token.py")]
    files = parser.parse_diff(auth_patch, name_status)
    token_file = next(f for f in files if f.path == "app/auth/token.py")
    combined = "\n".join(token_file.added_lines)
    assert "create_token" in combined


def test_parse_diff_change_types(auth_patch: str):
    parser = DiffParser()
    name_status = [
        ("M", "app/auth/token.py"),
        ("A", "migrations/versions/001_add_last_login.py"),
    ]
    files = parser.parse_diff(auth_patch, name_status)
    file_map = {f.path: f for f in files}
    assert file_map["app/auth/token.py"].change_type == ChangeType.MODIFIED
    assert file_map["migrations/versions/001_add_last_login.py"].change_type == ChangeType.ADDED


def test_parse_diff_handles_empty():
    parser = DiffParser()
    files = parser.parse_diff("", [])
    assert files == []


def test_file_change_is_test_file():
    parser = DiffParser()
    files = parser.parse_diff(
        "diff --git a/tests/test_foo.py b/tests/test_foo.py\n+pass\n",
        [("A", "tests/test_foo.py")],
    )
    assert files[0].is_test_file is True


def test_file_change_not_test_file():
    parser = DiffParser()
    files = parser.parse_diff(
        "diff --git a/app/auth/token.py b/app/auth/token.py\n+pass\n",
        [("M", "app/auth/token.py")],
    )
    assert files[0].is_test_file is False
