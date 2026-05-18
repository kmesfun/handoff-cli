from __future__ import annotations

import re
from dataclasses import dataclass

from handoff.git.models import DiffResult


# ---------------------------------------------------------------------------
# Category rules — matched against file path segments (case-insensitive)
# ---------------------------------------------------------------------------

RISK_CATEGORIES: dict[str, tuple[list[str], str]] = {
    "auth": (
        ["auth", "authentication", "login", "oauth", "jwt", "session", "password", "credential"],
        "HIGH",
    ),
    "payments": (
        ["payment", "billing", "stripe", "checkout", "invoice", "subscription", "charge"],
        "HIGH",
    ),
    "migration": (
        ["migration", "migrate", "alembic", "flyway", "liquibase", "schema", "versions"],
        "HIGH",
    ),
    "security": (
        ["security", "permission", "authorization", "acl", "policy", "role", "rbac"],
        "HIGH",
    ),
    "database": (
        ["database", "db", "query", "sql", "orm", "repository", "dao"],
        "MEDIUM",
    ),
    "config": (
        ["config", "settings", "environment", "secrets"],
        "MEDIUM",
    ),
    "deployment": (
        ["deploy", "infrastructure", "terraform", "helm", "kubernetes", "k8s", "docker"],
        "MEDIUM",
    ),
    "api": (
        ["route", "endpoint", "controller", "handler", "webhook"],
        "LOW",
    ),
}


# ---------------------------------------------------------------------------
# Pattern rules — matched against added lines in the diff
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatternRule:
    name: str
    pattern: str
    risk_type: str   # "DEBUG" | "TODO" | "SECRET"
    severity: str    # "HIGH" | "MEDIUM" | "LOW"


PATTERN_RULES: list[PatternRule] = [
    # Debug statements
    PatternRule("console.log",    r"\bconsole\.(log|warn|error|debug|trace)\s*\(",  "DEBUG",  "MEDIUM"),
    PatternRule("debugger",       r"\bdebugger\b",                                   "DEBUG",  "HIGH"),
    PatternRule("print()",        r"^\s*print\s*\(",                                 "DEBUG",  "MEDIUM"),
    PatternRule("pdb/breakpoint", r"\bpdb\.set_trace\(\)|\bbreakpoint\(\)",          "DEBUG",  "HIGH"),
    PatternRule("fmt.Print",      r"\bfmt\.Print(?:ln|f)?\s*\(",                     "DEBUG",  "MEDIUM"),
    PatternRule("var_dump",       r"\bvar_dump\s*\(",                                "DEBUG",  "MEDIUM"),
    PatternRule("dd()",           r"(?<!\w)dd\s*\(",                                 "DEBUG",  "MEDIUM"),
    PatternRule("System.out",     r"\bSystem\.out\.print",                           "DEBUG",  "MEDIUM"),
    # TODOs
    PatternRule("TODO",           r"\bTODO\b",                                       "TODO",   "LOW"),
    PatternRule("FIXME",          r"\bFIXME\b",                                      "TODO",   "MEDIUM"),
    PatternRule("HACK",           r"\bHACK\b",                                       "TODO",   "MEDIUM"),
    PatternRule("XXX",            r"\bXXX\b",                                        "TODO",   "LOW"),
    # Possible secrets (require an assignment to a non-placeholder value)
    PatternRule(
        "api_key",
        r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']',
        "SECRET", "HIGH",
    ),
    PatternRule(
        "secret",
        r'(?i)(secret|private[_-]?key)\s*[=:]\s*["\'][^"\']{8,}["\']',
        "SECRET", "HIGH",
    ),
    PatternRule(
        "password",
        r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']',
        "SECRET", "HIGH",
    ),
    PatternRule(
        "token",
        r'(?i)(token|auth[_-]?token|bearer)\s*[=:]\s*["\'][^"\']{8,}["\']',
        "SECRET", "HIGH",
    ),
]

_PLACEHOLDER_RE = re.compile(
    r"example|placeholder|your[_-]|changeme|<.*?>|\{.*?\}|\$\{|xxxx|dummy|fake|test|sample",
    re.IGNORECASE,
)


@dataclass
class RiskMatch:
    file_path: str
    line_number: int | None       # None for category-level risks
    line_content: str             # Truncated snippet
    risk_type: str                # "CATEGORY" | "DEBUG" | "TODO" | "SECRET"
    severity: str                 # "HIGH" | "MEDIUM" | "LOW"
    category: str                 # Category name or pattern name


class RiskDetector:
    """Detect risk patterns in a DiffResult. Pure analysis — no I/O."""

    def __init__(
        self,
        extra_patterns: list[PatternRule] | None = None,
        extra_categories: dict[str, tuple[list[str], str]] | None = None,
    ) -> None:
        self._patterns = PATTERN_RULES + (extra_patterns or [])
        self._categories = {**RISK_CATEGORIES, **(extra_categories or {})}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, diff: DiffResult) -> list[RiskMatch]:
        risks: list[RiskMatch] = []
        paths = [f.path for f in diff.changed_files]
        risks.extend(self._category_risks(paths))
        for fc in diff.changed_files:
            risks.extend(self._pattern_risks(fc.path, fc.added_lines, fc.is_test_file))
        return risks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _category_risks(self, paths: list[str]) -> list[RiskMatch]:
        risks: list[RiskMatch] = []
        for path in paths:
            path_lower = path.lower()
            for category, (keywords, severity) in self._categories.items():
                if any(kw in path_lower for kw in keywords):
                    risks.append(
                        RiskMatch(
                            file_path=path,
                            line_number=None,
                            line_content="",
                            risk_type="CATEGORY",
                            severity=severity,
                            category=category,
                        )
                    )
                    break  # Only the first (highest-priority) match per file
        return risks

    def _pattern_risks(
        self, path: str, added_lines: list[str], is_test: bool
    ) -> list[RiskMatch]:
        risks: list[RiskMatch] = []
        for lineno, line in enumerate(added_lines, start=1):
            for rule in self._patterns:
                if is_test and rule.risk_type in ("SECRET", "DEBUG"):
                    continue  # Skip secret and debug checks in test files
                if not re.search(rule.pattern, line):
                    continue
                if rule.risk_type == "SECRET" and _PLACEHOLDER_RE.search(line):
                    continue  # Obvious placeholder — skip
                risks.append(
                    RiskMatch(
                        file_path=path,
                        line_number=lineno,
                        line_content=line.strip()[:120],
                        risk_type=rule.risk_type,
                        severity=rule.severity,
                        category=rule.name,
                    )
                )
                break  # One match per line (first rule wins)
        return risks
