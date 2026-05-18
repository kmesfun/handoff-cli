from __future__ import annotations

import re

from handoff.git.models import ChangeType, FileChange


class DiffParser:
    """Parse git diff output into structured FileChange objects."""

    def parse_name_status(self, output: str) -> list[tuple[str, str]]:
        """Parse `git diff --name-status` output into (status_char, path) pairs."""
        results: list[tuple[str, str]] = []
        for line in output.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status_char = parts[0][0]  # First char: A, M, D, R, etc.
                path = parts[-1]           # Last column is always the new/current path
                results.append((status_char, path))
        return results

    def parse_diff(
        self, raw_diff: str, name_status: list[tuple[str, str]]
    ) -> list[FileChange]:
        """Parse unified diff text, enriched with name-status metadata."""
        file_map: dict[str, FileChange] = {}

        # Seed from name-status so we know about deleted files (which have no diff content)
        for status_char, path in name_status:
            try:
                change_type = ChangeType(status_char)
            except ValueError:
                change_type = ChangeType.UNKNOWN
            file_map[path] = FileChange(path=path, change_type=change_type)

        # State machine over the unified diff
        current: FileChange | None = None
        for line in raw_diff.splitlines():
            # New file section: "diff --git a/foo b/bar"
            m = re.match(r"^diff --git a/.+ b/(.+)$", line)
            if m:
                path = m.group(1)
                if path not in file_map:
                    file_map[path] = FileChange(path=path, change_type=ChangeType.MODIFIED)
                current = file_map[path]
                continue

            if current is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                current.additions += 1
                current.added_lines.append(line[1:])  # strip leading +
            elif line.startswith("-") and not line.startswith("---"):
                current.deletions += 1

        return list(file_map.values())
