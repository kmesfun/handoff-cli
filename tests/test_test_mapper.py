from pathlib import Path

import pytest

from handoff.analysis.tests import TestMapper


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Create a minimal fake Python repo with test files."""
    (tmp_path / "app" / "auth").mkdir(parents=True)
    (tmp_path / "app" / "models").mkdir(parents=True)
    (tmp_path / "app" / "api").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    # Source files
    (tmp_path / "app" / "auth" / "token.py").write_text("def create(): pass")
    (tmp_path / "app" / "models" / "user.py").write_text("class User: pass")
    (tmp_path / "app" / "api" / "routes.py").write_text("def router(): pass")

    # Test files
    (tmp_path / "tests" / "test_token.py").write_text("def test_create(): pass")
    (tmp_path / "tests" / "test_user.py").write_text("def test_user(): pass")

    return tmp_path


def test_maps_python_source_to_test(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/auth/token.py")
    assert not result.missing_test
    assert any("test_token.py" in str(f) for f in result.test_files)


def test_maps_user_model_to_test(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/models/user.py")
    assert not result.missing_test
    assert any("test_user.py" in str(f) for f in result.test_files)


def test_missing_test_flagged(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/api/routes.py")
    assert result.missing_test
    assert result.test_files == []


def test_suggests_pytest_command(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/auth/token.py")
    assert any("pytest" in cmd for cmd in result.suggested_commands)


def test_no_command_for_missing_test(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/api/routes.py")
    assert result.suggested_commands == []


def test_source_file_field_preserved(repo: Path):
    mapper = TestMapper(repo)
    result = mapper.map_file("app/auth/token.py")
    assert result.source_file == "app/auth/token.py"


def test_map_all_filters_test_files(repo: Path):
    mapper = TestMapper(repo)
    sources = ["app/auth/token.py", "tests/test_token.py", "app/models/user.py"]
    mappings = mapper.map_all(sources)
    mapped_sources = [m.source_file for m in mappings]
    assert "tests/test_token.py" not in mapped_sources
    assert "app/auth/token.py" in mapped_sources


def test_combined_commands_deduplicates(repo: Path):
    mapper = TestMapper(repo)
    m1 = mapper.map_file("app/auth/token.py")
    m2 = mapper.map_file("app/models/user.py")
    commands = mapper.combined_commands([m1, m2])
    # Should combine into a single pytest call
    assert len(commands) == 1
    assert "pytest" in commands[0]


@pytest.fixture
def ts_repo(tmp_path: Path) -> Path:
    """Create a minimal TypeScript repo."""
    (tmp_path / "src" / "components").mkdir(parents=True)
    (tmp_path / "src" / "components" / "Button.tsx").write_text("export const Button = () => null;")
    (tmp_path / "src" / "components" / "Button.test.tsx").write_text("test('button', () => {})")
    return tmp_path


def test_maps_tsx_to_test(ts_repo: Path):
    mapper = TestMapper(ts_repo)
    result = mapper.map_file("src/components/Button.tsx")
    assert not result.missing_test
    assert any("Button.test.tsx" in str(f) for f in result.test_files)


def test_suggests_npm_command_for_tsx(ts_repo: Path):
    mapper = TestMapper(ts_repo)
    result = mapper.map_file("src/components/Button.tsx")
    assert any("npm test" in cmd for cmd in result.suggested_commands)


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    (tmp_path / "pkg" / "auth").mkdir(parents=True)
    (tmp_path / "pkg" / "auth" / "token.go").write_text("package auth")
    (tmp_path / "pkg" / "auth" / "token_test.go").write_text("package auth_test")
    return tmp_path


def test_maps_go_source_to_test(go_repo: Path):
    mapper = TestMapper(go_repo)
    result = mapper.map_file("pkg/auth/token.go")
    assert not result.missing_test
    assert any("token_test.go" in str(f) for f in result.test_files)


def test_suggests_go_test_command(go_repo: Path):
    mapper = TestMapper(go_repo)
    result = mapper.map_file("pkg/auth/token.go")
    assert any("go test" in cmd for cmd in result.suggested_commands)
