from __future__ import annotations

import subprocess
from pathlib import Path

from handoff.git.diff_parser import DiffParser
from handoff.git.models import Commit, DiffMode, DiffResult

MAX_DIFF_LINES = 10_000


class GitError(Exception):
    pass


class GitAnalyzer:
    """Runs git subprocesses and returns structured data. All git I/O lives here."""

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = cwd or Path.cwd()
        self._parser = DiffParser()

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=self.cwd,
        )
        if check and result.returncode != 0:
            raise GitError(result.stderr.strip() or f"git {args[0]} failed")
        return result.stdout

    def get_repo_root(self) -> Path:
        root = self._run("rev-parse", "--show-toplevel").strip()
        return Path(root)

    def get_current_branch(self) -> str:
        branch = self._run("rev-parse", "--abbrev-ref", "HEAD").strip()
        if branch == "HEAD":
            # Detached HEAD — fall back to short SHA
            return self._run("rev-parse", "--short", "HEAD").strip()
        return branch

    def detect_default_branch(self) -> str:
        # 1. Ask the remote tracking ref
        out = self._run("symbolic-ref", "refs/remotes/origin/HEAD", check=False).strip()
        if out:
            return out.split("/")[-1]

        # 2. Probe common branch names
        for candidate in ("main", "master", "develop", "trunk"):
            result = subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                capture_output=True,
                cwd=self.cwd,
            )
            if result.returncode == 0:
                return candidate

        raise GitError(
            "Could not detect the default branch. Use --base to specify one (e.g. --base main)."
        )

    def get_commits(self, base: str) -> list[Commit]:
        out = self._run("log", "--oneline", f"{base}..HEAD", check=False)
        commits = []
        for line in out.strip().splitlines():
            if line:
                parts = line.split(" ", 1)
                sha = parts[0]
                message = parts[1] if len(parts) > 1 else ""
                commits.append(Commit(sha=sha, message=message))
        return commits

    def get_diff(self, base: str, mode: DiffMode = DiffMode.BRANCH) -> DiffResult:
        branch = self.get_current_branch()

        if mode == DiffMode.BRANCH:
            name_status_out = self._run("diff", "--name-status", f"{base}...HEAD")
            raw_diff = self._run("diff", f"{base}...HEAD")
            commits = self.get_commits(base)
        elif mode == DiffMode.STAGED:
            name_status_out = self._run("diff", "--name-status", "--cached")
            raw_diff = self._run("diff", "--cached")
            commits = []
        else:  # UNSTAGED
            name_status_out = self._run("diff", "--name-status")
            raw_diff = self._run("diff")
            commits = []

        # Warn on very large diffs, then truncate
        lines = raw_diff.splitlines()
        if len(lines) > MAX_DIFF_LINES:
            raw_diff = "\n".join(lines[:MAX_DIFF_LINES])

        name_status = self._parser.parse_name_status(name_status_out)
        changed_files = self._parser.parse_diff(raw_diff, name_status)

        return DiffResult(
            branch=branch,
            base_branch=base,
            changed_files=changed_files,
            commits=commits,
            raw_diff=raw_diff,
            mode=mode,
        )
