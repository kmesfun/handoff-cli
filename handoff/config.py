from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RiskPathConfig:
    pattern: str
    severity: str = "MEDIUM"


@dataclass
class TestMappingConfig:
    source: str
    test: str


@dataclass
class LLMConfig:
    provider: str = "none"
    model: str = ""
    base_url: str = ""


@dataclass
class HandoffConfig:
    base_branch: str | None = None
    ignore_paths: list[str] = field(default_factory=list)
    debug_patterns: list[str] = field(default_factory=list)
    risk_paths: list[RiskPathConfig] = field(default_factory=list)
    test_mappings: list[TestMappingConfig] = field(default_factory=list)
    pr_template: str | None = None
    min_score: int = 0
    llm: LLMConfig = field(default_factory=LLMConfig)


def load_config(repo_root: Path) -> HandoffConfig:
    """Load config from .handoff.yml, falling back to global config, then defaults."""
    search_paths = [
        Path.cwd() / ".handoff.yml",
        repo_root / ".handoff.yml",
        Path.home() / ".config" / "handoff" / "config.yml",
    ]

    for config_path in search_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data: dict[str, Any] = yaml.safe_load(f) or {}
                return _parse_config(data)
            except (yaml.YAMLError, OSError):
                pass  # Fall through to defaults on parse error

    return HandoffConfig()


def _parse_config(data: dict[str, Any]) -> HandoffConfig:
    risk_paths = [
        RiskPathConfig(pattern=r["pattern"], severity=r.get("severity", "MEDIUM"))
        for r in data.get("risk_paths", [])
        if isinstance(r, dict) and "pattern" in r
    ]
    test_mappings = [
        TestMappingConfig(source=m["source"], test=m["test"])
        for m in data.get("test_mappings", [])
        if isinstance(m, dict) and "source" in m and "test" in m
    ]
    llm_data = data.get("llm", {}) or {}
    llm = LLMConfig(
        provider=llm_data.get("provider", "none"),
        model=llm_data.get("model", ""),
        base_url=llm_data.get("base_url", ""),
    )

    return HandoffConfig(
        base_branch=data.get("base_branch"),
        ignore_paths=data.get("ignore_paths", []),
        debug_patterns=data.get("debug_patterns", []),
        risk_paths=risk_paths,
        test_mappings=test_mappings,
        pr_template=data.get("pr_template"),
        min_score=int(data.get("min_score", 0)),
        llm=llm,
    )
