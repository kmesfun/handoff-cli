from pathlib import Path

import pytest

from handoff.analysis.repo import RepoScanner


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\n\n[project.dependencies]\nfastapi = ">=0.100"'
    )
    (tmp_path / "requirements.txt").write_text("fastapi>=0.100\npytest>=7.0\nsqlalchemy>=2.0\n")
    (tmp_path / "Makefile").write_text("test:\n\tpytest -v\nrun:\n\tuvicorn main:app\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
    return tmp_path


@pytest.fixture
def node_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "package.json").write_text(
        '{"name":"myapp","scripts":{"start":"node index.js","test":"jest"},'
        '"dependencies":{"react":"^18.0"},"devDependencies":{"jest":"^29.0"}}'
    )
    return tmp_path


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    (tmp_path / "cmd").mkdir()
    (tmp_path / "go.mod").write_text("module github.com/example/myapp\n\ngo 1.21\n")
    return tmp_path


def test_detects_python(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    assert "Python" in info.languages


def test_detects_fastapi_framework(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    assert "FastAPI" in info.frameworks


def test_detects_test_directory(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    assert any(d.name == "tests" for d in info.test_dirs)


def test_detects_makefile_run_command(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    assert any("make" in cmd for cmd in info.run_commands.values())


def test_detects_dockerfile_as_key_file(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    key_paths = [p for p, _ in info.key_files]
    assert "Dockerfile" in key_paths


def test_detects_javascript(node_repo: Path):
    info = RepoScanner(node_repo).scan()
    assert "JavaScript" in info.languages or "TypeScript" in info.languages


def test_detects_react(node_repo: Path):
    info = RepoScanner(node_repo).scan()
    assert "React" in info.frameworks


def test_detects_npm_test_command(node_repo: Path):
    info = RepoScanner(node_repo).scan()
    assert any("npm" in cmd for cmd in info.test_commands.values())


def test_detects_go(go_repo: Path):
    info = RepoScanner(go_repo).scan()
    assert "Go" in info.languages


def test_detects_go_test_command(go_repo: Path):
    info = RepoScanner(go_repo).scan()
    assert any("go test" in cmd for cmd in info.test_commands.values())


def test_repo_name_is_dir_name(python_repo: Path):
    info = RepoScanner(python_repo).scan()
    assert info.name == python_repo.name


def test_empty_repo_has_unknown_language(tmp_path: Path):
    info = RepoScanner(tmp_path).scan()
    assert info.languages == ["Unknown"]
