from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from handoff.utils.fs import safe_read, walk_repo


@dataclass
class RepoInfo:
    name: str
    languages: list[str]
    frameworks: list[str]
    test_dirs: list[Path]
    key_files: list[tuple[str, str]]   # (relative_path, description)
    run_commands: dict[str, str]        # name -> shell command
    test_commands: dict[str, str]       # name -> shell command
    ignore_dirs: list[str] = field(default_factory=list)


class RepoScanner:
    """Detect stack, frameworks, key files, and run commands from the repo root."""

    MANIFEST_FILES = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "package.json",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    ]

    KEY_FILES = [
        ("Dockerfile", "Container definition"),
        ("docker-compose.yml", "Docker Compose services"),
        ("docker-compose.yaml", "Docker Compose services"),
        (".env.example", "Environment variable template"),
        ("alembic.ini", "Alembic migration config"),
        ("Makefile", "Build / run commands"),
        (".github/workflows", "CI/CD workflows"),
        ("CODEOWNERS", "Code ownership rules"),
    ]

    def __init__(self, repo_root: Path) -> None:
        self.root = repo_root

    def scan(self) -> RepoInfo:
        languages: list[str] = []
        frameworks: list[str] = []
        run_commands: dict[str, str] = {}
        test_commands: dict[str, str] = {}
        key_files: list[tuple[str, str]] = []

        # Detect from manifests
        for manifest in self.MANIFEST_FILES:
            path = self.root / manifest
            if not path.exists():
                continue
            content = safe_read(path) or ""

            if manifest == "pyproject.toml":
                languages.append("Python")
                frameworks.extend(_detect_python_frameworks(content))
                key_files.append((manifest, "Python project config"))
                cmds = _parse_pyproject_scripts(content)
                run_commands.update(cmds.get("run", {}))
                test_commands.update(cmds.get("test", {}))

            elif manifest == "requirements.txt":
                if "Python" not in languages:
                    languages.append("Python")
                frameworks.extend(_detect_python_frameworks(content))
                key_files.append((manifest, "Python dependencies"))

            elif manifest == "setup.py" or manifest == "setup.cfg":
                if "Python" not in languages:
                    languages.append("Python")
                key_files.append((manifest, "Python package config"))

            elif manifest == "package.json":
                pkg = json.loads(content) if content else {}
                lang = "TypeScript" if (self.root / "tsconfig.json").exists() else "JavaScript"
                if lang not in languages:
                    languages.append(lang)
                frameworks.extend(_detect_js_frameworks(pkg))
                scripts = pkg.get("scripts", {})
                for name, cmd in scripts.items():
                    if name in ("start", "dev", "serve"):
                        run_commands[name] = f"npm run {name}"
                    elif name in ("test", "test:unit", "test:e2e"):
                        test_commands[name] = f"npm run {name}"
                key_files.append((manifest, "Node.js package config"))

            elif manifest == "go.mod":
                languages.append("Go")
                key_files.append((manifest, "Go module definition"))
                test_commands["test"] = "go test ./..."
                run_commands["run"] = "go run ."

            elif manifest == "Cargo.toml":
                languages.append("Rust")
                key_files.append((manifest, "Rust package config"))
                test_commands["test"] = "cargo test"
                run_commands["run"] = "cargo run"

            elif manifest in ("pom.xml", "build.gradle", "build.gradle.kts"):
                if "Java" not in languages and "Kotlin" not in languages:
                    languages.append("Kotlin" if "kts" in manifest else "Java")
                key_files.append((manifest, "Build config"))
                test_commands["test"] = "mvn test" if "pom" in manifest else "./gradlew test"

        # Makefile commands
        makefile = self.root / "Makefile"
        if makefile.exists():
            content = safe_read(makefile) or ""
            targets = _parse_makefile_targets(content)
            for t in targets:
                if t in ("test", "tests"):
                    test_commands.setdefault("make test", f"make {t}")
                elif t in ("run", "start", "serve", "dev"):
                    run_commands.setdefault(f"make {t}", f"make {t}")
            key_files.append(("Makefile", "Build / run targets"))

        # Pytest fallback
        if "Python" in languages and not test_commands:
            test_dirs = self._find_test_dirs()
            if test_dirs:
                test_commands["pytest"] = "pytest -v"

        # Static key files
        for fname, description in self.KEY_FILES:
            candidate = self.root / fname
            if candidate.exists():
                if not any(fname in kf[0] for kf in key_files):
                    key_files.append((fname, description))

        # Deduplicate
        languages = list(dict.fromkeys(languages))
        frameworks = list(dict.fromkeys(frameworks))

        return RepoInfo(
            name=self.root.name,
            languages=languages or ["Unknown"],
            frameworks=frameworks,
            test_dirs=self._find_test_dirs(),
            key_files=key_files,
            run_commands=run_commands,
            test_commands=test_commands,
        )

    def _find_test_dirs(self) -> list[Path]:
        found = []
        for name in ("tests", "test", "spec", "__tests__", "specs"):
            p = self.root / name
            if p.is_dir():
                found.append(p)
        return found


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _detect_python_frameworks(content: str) -> list[str]:
    found = []
    content_lower = content.lower()
    checks = [
        ("fastapi", "FastAPI"),
        ("django", "Django"),
        ("flask", "Flask"),
        ("starlette", "Starlette"),
        ("sqlalchemy", "SQLAlchemy"),
        ("alembic", "Alembic"),
        ("pytest", "pytest"),
        ("celery", "Celery"),
        ("pydantic", "Pydantic"),
    ]
    for key, label in checks:
        if key in content_lower:
            found.append(label)
    return found


def _detect_js_frameworks(pkg: dict) -> list[str]:
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    found = []
    checks = [
        ("react", "React"),
        ("next", "Next.js"),
        ("vue", "Vue"),
        ("nuxt", "Nuxt"),
        ("express", "Express"),
        ("fastify", "Fastify"),
        ("nestjs/core", "NestJS"),
        ("prisma", "Prisma"),
        ("typeorm", "TypeORM"),
        ("jest", "Jest"),
        ("vitest", "Vitest"),
    ]
    for key, label in checks:
        if any(key in d for d in deps):
            found.append(label)
    return found


def _parse_makefile_targets(content: str) -> list[str]:
    return re.findall(r"^([a-zA-Z][a-zA-Z0-9_-]*):", content, re.MULTILINE)


def _parse_pyproject_scripts(content: str) -> dict[str, dict[str, str]]:
    run: dict[str, str] = {}
    test: dict[str, str] = {}
    # Look for [tool.taskipy.tasks] or [project.scripts]
    if "pytest" in content:
        test["pytest"] = "pytest -v"
    return {"run": run, "test": test}
