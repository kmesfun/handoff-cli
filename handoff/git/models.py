from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from handoff.utils.fs import is_test_file


class ChangeType(str, Enum):
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    UNKNOWN = "U"


class DiffMode(str, Enum):
    BRANCH = "branch"
    STAGED = "staged"
    UNSTAGED = "unstaged"


@dataclass
class FileChange:
    path: str
    change_type: ChangeType
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] = field(default_factory=list)

    @property
    def is_test_file(self) -> bool:
        return is_test_file(self.path)

    @property
    def extension(self) -> str:
        return self.path.rsplit(".", 1)[-1] if "." in self.path else ""


@dataclass
class Commit:
    sha: str
    message: str


@dataclass
class DiffResult:
    branch: str
    base_branch: str
    changed_files: list[FileChange]
    commits: list[Commit]
    raw_diff: str
    mode: DiffMode = DiffMode.BRANCH

    @property
    def source_files(self) -> list[FileChange]:
        return [f for f in self.changed_files if not f.is_test_file]

    @property
    def test_files(self) -> list[FileChange]:
        return [f for f in self.changed_files if f.is_test_file]

    @property
    def total_additions(self) -> int:
        return sum(f.additions for f in self.changed_files)

    @property
    def total_deletions(self) -> int:
        return sum(f.deletions for f in self.changed_files)
