from pathlib import Path


def is_test_file(path: str) -> bool:
    """Return True if the file path looks like a test file."""
    p = path.replace("\\", "/").lower()
    parts = p.split("/")
    filename = parts[-1] if parts else ""

    if any(part in ("tests", "test", "spec", "__tests__", "specs") for part in parts[:-1]):
        return True

    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename.endswith("_test.go")
        or ".test." in filename
        or ".spec." in filename
    )


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk up from start (default: cwd) to find the nearest .git directory."""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def safe_read(path: Path) -> str | None:
    """Read a file, returning None on any error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


IGNORED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        "target",
        "__pycache__",
        ".next",
        ".nuxt",
        ".mypy_cache",
        ".pytest_cache",
        "coverage",
        ".coverage",
        "htmlcov",
        ".tox",
        "vendor",
    }
)


def walk_repo(root: Path, max_depth: int = 6) -> list[Path]:
    """Yield all files in the repo, skipping ignored directories."""
    results: list[Path] = []

    def _walk(path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            for entry in sorted(path.iterdir()):
                if entry.is_dir():
                    if entry.name not in IGNORED_DIRS and not entry.name.startswith("."):
                        _walk(entry, depth + 1)
                elif entry.is_file():
                    results.append(entry)
        except PermissionError:
            pass

    _walk(root, 0)
    return results
