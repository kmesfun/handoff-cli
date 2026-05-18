from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from handoff.analysis.risk import RISK_CATEGORIES
from handoff.utils.fs import IGNORED_DIRS

SOURCE_EXTENSIONS = (
    "*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.go", "*.rs", "*.java", "*.kt", "*.rb"
)


@dataclass
class ImportMatch:
    file: str
    context: str


@dataclass
class ImpactResult:
    target: str
    dependents: list[ImportMatch] = field(default_factory=list)
    risk_warning: str | None = None


class ImpactAnalyzer:
    """Find files that import or reference a given file using grep."""

    def __init__(self, repo_root: Path) -> None:
        self.root = repo_root

    def analyze(self, target: Path) -> ImpactResult:
        try:
            rel = target.relative_to(self.root)
        except ValueError:
            rel = target

        terms = self._build_search_terms(rel)
        seen: dict[str, ImportMatch] = {}

        for term in terms:
            for match in self._grep(term):
                # Skip the file itself
                if match.file == str(rel):
                    continue
                seen.setdefault(match.file, match)

        dependents = list(seen.values())
        risk = self._risk_warning(dependents)
        return ImpactResult(target=str(rel), dependents=dependents, risk_warning=risk)

    def _build_search_terms(self, rel: Path) -> list[str]:
        stem = rel.stem
        # e.g. "app/utils/http.py" → ["http", "app.utils.http", "app/utils/http"]
        module_dotted = str(rel).replace("/", ".").removesuffix(".py").removesuffix(".ts")
        module_slash = str(rel).removesuffix(rel.suffix)
        terms: list[str] = list(dict.fromkeys([stem, module_dotted, module_slash]))
        return [t for t in terms if len(t) > 2]  # Skip trivially short terms

    def _grep(self, term: str) -> list[ImportMatch]:
        # Build --exclude-dir flags for ignored directories
        exclude_flags = [f"--exclude-dir={d}" for d in IGNORED_DIRS]
        include_flags = [f"--include={ext}" for ext in SOURCE_EXTENSIONS]

        cmd = [
            "grep", "-rn",
            *exclude_flags,
            *include_flags,
            term,
            str(self.root),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        matches: list[ImportMatch] = []
        for line in result.stdout.strip().splitlines():
            if ":" not in line:
                continue
            parts = line.split(":", 2)
            if len(parts) < 2:
                continue
            filepath = parts[0].removeprefix(str(self.root) + "/")
            context = parts[2].strip() if len(parts) > 2 else ""
            matches.append(ImportMatch(file=filepath, context=context[:80]))
        return matches

    def _risk_warning(self, dependents: list[ImportMatch]) -> str | None:
        for dep in dependents:
            path_lower = dep.file.lower()
            for category, (keywords, severity) in RISK_CATEGORIES.items():
                if severity == "HIGH" and any(kw in path_lower for kw in keywords):
                    return f"{dep.file} touches {category} — verify impact carefully"
        return None
