from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from handoff.utils.fs import is_test_file


@dataclass
class TestMapping:
    source_file: str
    test_files: list[Path] = field(default_factory=list)
    suggested_commands: list[str] = field(default_factory=list)
    missing_test: bool = False


class TestMapper:
    """Map changed source files to their likely test counterparts."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def map_file(self, source_path: str) -> TestMapping:
        candidates = self._candidate_paths(source_path)
        existing = [c for c in candidates if c.exists()]
        commands = self._suggest_commands(existing)
        return TestMapping(
            source_file=source_path,
            test_files=existing,
            suggested_commands=commands,
            missing_test=(len(existing) == 0),
        )

    def map_all(self, source_paths: list[str]) -> list[TestMapping]:
        """Map a list of source file paths, filtering out test files themselves."""
        return [self.map_file(p) for p in source_paths if not is_test_file(p)]

    def combined_commands(self, mappings: list[TestMapping]) -> list[str]:
        """Return deduplicated test commands covering all mapped test files."""
        all_tests: list[Path] = []
        for m in mappings:
            all_tests.extend(m.test_files)
        if not all_tests:
            return []
        return self._suggest_commands(list(dict.fromkeys(all_tests)))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _candidate_paths(self, source_path: str) -> list[Path]:
        p = Path(source_path)
        stem = p.stem
        parent = p.parent.name
        suffix = p.suffix
        root = self.repo_root

        candidates: list[Path] = []

        if suffix == ".py":
            candidates = [
                root / "tests" / f"test_{stem}.py",
                root / "tests" / f"test_{parent}_{stem}.py",
                root / "tests" / parent / f"test_{stem}.py",
                root / "test" / f"test_{stem}.py",
                root / "tests" / f"{stem}_test.py",
                root / "tests" / parent / f"test_{parent}.py",
            ]
        elif suffix in (".ts", ".tsx", ".js", ".jsx"):
            test_ext = f".test{suffix}"
            spec_ext = f".spec{suffix}"
            file_dir = root / p.parent
            candidates = [
                file_dir / f"{stem}{test_ext}",
                file_dir / f"{stem}{spec_ext}",
                file_dir / "__tests__" / f"{stem}{test_ext}",
                root / "src" / "__tests__" / f"{stem}{test_ext}",
                root / "__tests__" / f"{stem}{test_ext}",
                root / "tests" / f"{stem}{test_ext}",
            ]
        elif suffix == ".go":
            file_dir = root / p.parent
            candidates = [
                file_dir / f"{stem}_test.go",
                file_dir / f"{parent}_test.go",
            ]
        elif suffix in (".rs",):
            # Rust: tests live in the same file (mod tests {}) or tests/ dir
            candidates = [root / "tests" / f"{stem}.rs"]
        else:
            candidates = [
                root / "tests" / f"test_{stem}{suffix}",
                root / "test" / f"test_{stem}{suffix}",
            ]

        return candidates

    def _suggest_commands(self, test_files: list[Path]) -> list[str]:
        if not test_files:
            return []

        py = [f for f in test_files if f.suffix == ".py"]
        js_ts = [f for f in test_files if f.suffix in (".js", ".jsx", ".ts", ".tsx")]
        go = [f for f in test_files if f.suffix == ".go"]
        rs = [f for f in test_files if f.suffix == ".rs"]

        commands: list[str] = []

        if py:
            rel = [str(f.relative_to(self.repo_root)) for f in py]
            commands.append(f"pytest {' '.join(rel)} -v")

        if js_ts:
            patterns = "|".join(dict.fromkeys(f.stem for f in js_ts))
            commands.append(f"npm test -- --testPathPattern='{patterns}'")

        if go:
            pkgs = dict.fromkeys(str(f.parent.relative_to(self.repo_root)) for f in go)
            pkg_str = " ".join(f"./{p}/..." for p in pkgs)
            commands.append(f"go test {pkg_str}")

        if rs:
            commands.append("cargo test")

        return commands
