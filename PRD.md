# handoff — Product Requirements Document

**Version:** 1.0  
**Author:** Kennedy Mesfun  
**Date:** 2026-05-18  
**Status:** Draft

---

## Table of Contents

1. [Product Summary](#1-product-summary)
2. [Target Users](#2-target-users)
3. [User Problems](#3-user-problems)
4. [Goals](#4-goals)
5. [Non-Goals](#5-non-goals)
6. [User Stories](#6-user-stories)
7. [Core Workflows](#7-core-workflows)
8. [CLI Command Design](#8-cli-command-design)
9. [MVP Feature Requirements](#9-mvp-feature-requirements)
10. [Advanced Feature Roadmap](#10-advanced-feature-roadmap)
11. [Technical Architecture](#11-technical-architecture)
12. [Recommended Tech Stack](#12-recommended-tech-stack)
13. [Data Flow](#13-data-flow)
14. [File / Module Structure](#14-file--module-structure)
15. [Risk Detection Rules](#15-risk-detection-rules)
16. [Test Recommendation Strategy](#16-test-recommendation-strategy)
17. [PR Description Template](#17-pr-description-template)
18. [Config File Design](#18-config-file-design)
19. [Error Handling](#19-error-handling)
20. [Security and Privacy Considerations](#20-security-and-privacy-considerations)
21. [Testing Strategy](#21-testing-strategy)
22. [Success Metrics](#22-success-metrics)
23. [2–4 Week Build Roadmap](#23-24-week-build-roadmap)
24. [Open Questions](#24-open-questions)
25. [Q&A: Product, Technical, Implementation, and Portfolio Questions](#25-qa)

---

## 1. Product Summary

**handoff** is a local-first CLI tool that turns a Git diff into an actionable engineering summary. It helps software engineers prepare better pull requests, understand code changes faster, and reduce the friction of code review and team handoffs.

Engineers run `handoff pr` before opening a PR and get back: a summary of what changed, a risk checklist, recommended tests to run, and a draft PR description — all computed locally from the Git diff, with no cloud dependency required.

**Positioning statement:**  
*handoff is the pre-PR checklist you wish your team had — automated, local, and smart enough to catch what you miss when you're moving fast.*

---

## 2. Target Users

**Primary:** Mid-level to senior software engineers who regularly open pull requests and value quality, speed, and clear communication.

**Secondary segments:**
- Engineers handing off unfinished work (context switch, vacation, on-call)
- Junior engineers who want guardrails before opening their first PR on a new codebase
- Engineers onboarding to an unfamiliar repo who need to understand what a branch contains
- Code reviewers who want a quick pre-scan before reading a large diff
- Solo developers with no team review process who still want rigor

**Not the target user (for MVP):**
- Non-engineers (PMs, designers)
- Teams with existing mature CI systems that already auto-generate PR summaries
- Users who need cloud / SaaS features

---

## 3. User Problems

| # | Problem | Context |
|---|---------|---------|
| P1 | I open PRs with TODOs and debug logs I forgot to remove | Moving fast, forgot to self-review |
| P2 | My PR description is either empty or too vague for reviewers | It's extra work I skip under time pressure |
| P3 | I don't know which tests to run after touching this file | Unfamiliar codebase, large test suite |
| P4 | I'm not sure if my changes touched something risky | No mental checklist; auth/migrations are easy to miss |
| P5 | I'm handing off unfinished work and have no time to write docs | Context switch, on-call, vacation |
| P6 | I joined this repo last week and don't understand what this branch does | Onboarding or cross-team review |
| P7 | I have to manually piece together what changed across 40 files | Large diff, long day, cognitive load |

---

## 4. Goals

**Product goals:**
- G1: Reduce the time to write a useful PR description from ~10–15 minutes to under 1 minute
- G2: Catch common PR quality issues (TODOs, debug logs, accidental secrets) before push
- G3: Help engineers identify the right tests to run without knowing the full test suite
- G4: Give engineers a structured way to communicate handoffs without writing docs from scratch
- G5: Work out of the box with no config, no account, no API key

**Engineering goals:**
- G6: Produce clean, readable code that demonstrates good software design (portfolio goal)
- G7: Ship a working MVP in 2–4 weeks as a solo project
- G8: Make the tool easy to extend with LLM summarization later

---

## 5. Non-Goals

- Not a code editor or auto-fixer — handoff reads and reports, never writes code
- Not a CI/CD pipeline replacement — it's a local dev tool
- Not an AI coding agent — no autonomous actions
- Not a GUI or web app
- Not a paid SaaS product (for MVP)
- Not a security scanner with legal compliance guarantees (e.g., not SOC2/HIPAA tooling)
- Not a replacement for code review — it's pre-review prep
- Not a perfect language parser — regex-based heuristics are acceptable for MVP

---

## 6. User Stories

**PR preparation:**
- US1: As an engineer preparing a PR, I want a summary of all changed files so I can confirm my intent before opening.
- US2: As an engineer, I want a generated PR description I can paste into GitHub so I don't write it from scratch.
- US3: As an engineer, I want to be warned if I accidentally left `console.log`, `print()`, or `debugger` in my diff.
- US4: As an engineer, I want to know if my changes touched auth, payments, migrations, or config so I can flag it.
- US5: As an engineer, I want to know which tests to run based on what files I changed.

**Handoff:**
- US6: As an engineer handing off work, I want to generate a structured handoff note from the current branch state.
- US7: As an engineer, I want to capture what's done, what's in progress, and what's risky, even when I'm rushed.

**Onboarding / understanding:**
- US8: As a new engineer, I want a quick summary of the repo — what stack it uses, what the main files are, and how to run/test it.
- US9: As a reviewer, I want to understand what a branch does before I read the raw diff.

**Automation:**
- US10: As an engineer, I want to run `handoff before-push` as a pre-push hook that warns me if something is wrong.
- US11: As an engineer, I want to save the handoff output as a Markdown file to attach to a PR.

---

## 7. Core Workflows

### Workflow A: Pre-PR Review

```
1. Engineer finishes feature branch work
2. Runs: handoff before-push
3. handoff reads git diff vs main
4. Output:
   a. Changed files list (grouped by category)
   b. Risk warnings (debug logs, TODOs, possible secrets, risky paths)
   c. Recommended tests
   d. Draft PR description
5. Engineer reviews output, fixes warnings, copies PR description
6. Engineer opens PR with confidence
```

### Workflow B: Generating a PR Description

```
1. Engineer runs: handoff write-pr
2. handoff reads current branch diff
3. Produces a structured Markdown PR description
4. Engineer pastes it into GitHub PR body or saves to a file
```

### Workflow C: Understanding a New Repo

```
1. New engineer clones repo and runs: handoff overview
2. handoff scans the file structure
3. Output:
   a. Detected stack and languages
   b. Key files (entry points, config, package manifests)
   c. How to run and test the project
   d. Important directories
```

### Workflow D: Targeted Test Recommendation

```
1. Engineer modifies app/auth/token.py
2. Runs: handoff tests
3. Output:
   - Recommended test files: tests/test_token.py, tests/test_auth.py
   - Suggested commands: pytest tests/test_auth.py -v
```

### Workflow E: Impact Analysis

```
1. Engineer modifies a shared utility
2. Runs: handoff impact src/utils/http.py
3. Output:
   - Files that import src/utils/http.py (grepped from codebase)
   - Warning if a high-risk area depends on this file
```

---

## 8. CLI Command Design

### Command Overview

```
handoff [command] [options]

Commands:
  overview          Analyze repo structure, detect stack, summarize entry points
  pr                Full PR readiness analysis of current branch vs main
  tests             Recommend tests based on changed files
  risks             Scan diff for risky patterns
  impact <file>     Show files that import or depend on the given file
  write-pr          Generate a PR description from the current diff
  before-push       Full pre-push checklist (risks + tests + PR draft)
  install-hook      Install a Git pre-push hook that runs before-push

Global options:
  --output <file>   Save output to a Markdown file
  --json            Emit JSON instead of formatted terminal output
  --base <branch>   Override the base branch for comparison (default: main/master)
  --staged          Only analyze staged changes
  --unstaged        Only analyze unstaged changes
  --verbose         Show more detail
  --no-color        Disable ANSI colors
  --version         Show version
  --help            Show help
```

### Command: `handoff overview`

```
$ handoff overview

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  handoff — Repo Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Repo: my-app
🌿 Branch: feature/auth-refactor

Stack detected:
  • Python 3.11 (pyproject.toml)
  • FastAPI (requirements.txt: fastapi>=0.100)
  • PostgreSQL (detected from alembic.ini, DATABASE_URL references)
  • Docker (Dockerfile, docker-compose.yml)

Key files:
  • main.py           — likely entry point
  • pyproject.toml    — project config
  • alembic.ini       — database migrations
  • Makefile          — build/run commands

Run commands (from Makefile):
  make run        → uvicorn main:app --reload
  make test       → pytest -v
  make migrate    → alembic upgrade head

Directories:
  app/            — application code
  tests/          — test suite (47 files found)
  migrations/     — Alembic migrations
  docs/           — documentation
```

### Command: `handoff pr`

```
$ handoff pr

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  handoff — PR Readiness Report
  Branch: feature/auth-refactor → main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Changed files (12 total):
  [auth]      app/auth/token.py              +87  -23
  [auth]      app/auth/middleware.py          +12   -4
  [config]    app/config.py                   +5   -2
  [test]      tests/test_auth.py             +34   -0
  [test]      tests/test_token.py            +21   -0
              app/models/user.py             +15   -8
              app/api/routes/users.py        +22  -11
              app/utils/http.py               +3   -1
              requirements.txt               +2   -0
              pyproject.toml                 +1   -0
  [migration] migrations/versions/abc123.py  +45   -0
              README.md                       +3   -2

⚠️  Risk areas detected:
  HIGH   migrations/versions/abc123.py    — database migration modified
  HIGH   app/auth/token.py                — auth/security file modified
  MEDIUM app/auth/middleware.py           — auth middleware modified
  LOW    app/config.py                    — config file modified

🔍 Pattern warnings:
  ⚠  app/api/routes/users.py:42    TODO: remove before merge
  ⚠  app/utils/http.py:17          print("debug response:", r)
  ⚠  app/auth/token.py:88          # FIXME: hardcoded expiry

🧪 Recommended tests:
  pytest tests/test_auth.py tests/test_token.py -v
  pytest tests/ -k "auth or token or user" -v

📋 PR Description (draft):
  Run `handoff write-pr` to generate the full Markdown description.

Readiness score: 74/100
  ✓ Tests added (tests/test_auth.py, tests/test_token.py)
  ✓ Migration present for schema change
  ✗ 3 pattern warnings (TODO, debug print, FIXME)
  ✗ No PR description generated yet
```

### Command: `handoff risks`

```
$ handoff risks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  handoff — Risk Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Category risks:
  🔴 HIGH   app/auth/token.py          Matches: auth
  🔴 HIGH   migrations/versions/*.py   Matches: migration
  🟡 MEDIUM app/config.py              Matches: config

Pattern risks:
  ⚠  app/api/routes/users.py:42   TODO: remove before merge
  ⚠  app/utils/http.py:17         print("debug response:", r)
  ⚠  app/auth/token.py:88         FIXME: hardcoded expiry
  🔑 app/config.py:12             Possible secret: TOKEN_SECRET = "..."
```

### Command: `handoff tests`

```
$ handoff tests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  handoff — Test Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Changed source files and mapped tests:
  app/auth/token.py      → tests/test_token.py       ✓ exists
  app/auth/middleware.py → tests/test_middleware.py  ✗ not found
  app/models/user.py     → tests/test_user.py        ✓ exists
  app/api/routes/users.py→ tests/test_users.py       ✓ exists

Commands to run:
  pytest tests/test_token.py tests/test_user.py tests/test_users.py -v

⚠  No test found for: app/auth/middleware.py
   Consider creating: tests/test_middleware.py
```

### Command: `handoff impact <file>`

```
$ handoff impact app/utils/http.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  handoff — Impact Analysis: app/utils/http.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files that import app/utils/http.py (grep results):
  app/api/routes/users.py:3    from app.utils.http import make_request
  app/api/routes/items.py:5    from app.utils.http import make_request
  app/services/email.py:2      from app.utils.http import post_json
  tests/test_http.py:1         import app.utils.http as http_utils

⚠  app/api/routes/users.py touches auth-related routes — verify impact.

Tests to run:
  pytest tests/test_http.py -v
```

### Command: `handoff write-pr`

Generates a structured Markdown PR description (see Section 17).

### Command: `handoff before-push`

Combines `risks` + `tests` + `write-pr` in one pass. Outputs a full checklist with a pass/fail on each item. Non-zero exit code if HIGH risks are found (for CI/hook integration).

---

## 9. MVP Feature Requirements

### F1: Git Integration

| Requirement | Details |
|-------------|---------|
| F1.1 Detect current branch | `git rev-parse --abbrev-ref HEAD` |
| F1.2 Detect default branch | Try `main`, then `master`, then `git symbolic-ref refs/remotes/origin/HEAD` |
| F1.3 Get changed files | `git diff --name-status <base>...HEAD` |
| F1.4 Get file-level diff | `git diff <base>...HEAD -- <file>` |
| F1.5 Staged diff support | `git diff --cached` |
| F1.6 Unstaged diff support | `git diff` (no flags) |
| F1.7 Line-level diff parsing | Parse unified diff format into added/removed lines |
| F1.8 Commit log | `git log --oneline <base>..HEAD` |

### F2: Repo Scanning

| Requirement | Details |
|-------------|---------|
| F2.1 Detect languages | Presence of pyproject.toml → Python, package.json → JS/TS, go.mod → Go, Cargo.toml → Rust, pom.xml → Java |
| F2.2 Detect framework | Parse requirements.txt / package.json dependencies |
| F2.3 Parse run commands | Read Makefile targets, package.json scripts, pyproject.toml `[tool.taskipy]` |
| F2.4 Find test directories | Look for `tests/`, `test/`, `spec/`, `__tests__/` |
| F2.5 Ignore directories | .git, node_modules, .venv, dist, build, target, __pycache__, .next, .nuxt |

### F3: Risk Detection

| Requirement | Details |
|-------------|---------|
| F3.1 Detect debug statements | console.log, print(), debugger, fmt.Println, System.out.println, var_dump, dd() |
| F3.2 Detect TODO/FIXME | Regex: `TODO`, `FIXME`, `HACK`, `XXX` in added lines |
| F3.3 Detect possible secrets | Regex on added lines: `(api_key|secret|password|token|private_key)\s*[=:]\s*['"][^'"]{8,}['"]` |
| F3.4 Classify risky files | Match file path against risk category keywords (see Section 15) |
| F3.5 Risk severity | HIGH: auth, payments, migrations. MEDIUM: config, security. LOW: infra, deployment |

### F4: Test Recommendation

| Requirement | Details |
|-------------|---------|
| F4.1 Source-to-test mapping | Transform source path to test path using naming patterns (see Section 16) |
| F4.2 Test existence check | Verify mapped test file exists before recommending |
| F4.3 Test command generation | Compose `pytest`, `npm test`, `go test`, `cargo test` commands |
| F4.4 Missing test warning | Warn when no test file found for a changed source file |

### F5: PR Description Generation

| Requirement | Details |
|-------------|---------|
| F5.1 Structured Markdown | Generate PR description with fixed sections (see Section 17) |
| F5.2 File change summary | List changed files with +/- counts grouped by category |
| F5.3 Risk section | Include detected risks in PR description |
| F5.4 Test checklist | Include recommended test commands |
| F5.5 Save to file | `--output pr.md` writes Markdown to disk |

### F6: Output Formatting

| Requirement | Details |
|-------------|---------|
| F6.1 Rich terminal output | Color-coded, tabular, readable in any terminal |
| F6.2 JSON output | `--json` flag emits all data as structured JSON |
| F6.3 Markdown output | `--output <file>` writes Markdown to disk |
| F6.4 Exit codes | 0 = clean, 1 = warnings, 2 = high risks found |

### F7: Readiness Score

| Requirement | Details |
|-------------|---------|
| F7.1 Score computation | Integer 0–100 based on: tests present, no debug patterns, no TODO/FIXME, no secrets, PR description quality |
| F7.2 Score breakdown | Show which items passed and failed in score computation |

---

## 10. Advanced Feature Roadmap

### Phase 2 (post-MVP, weeks 5–8)

| Feature | Description |
|---------|-------------|
| LLM summarization | Optional: pipe diff to OpenAI/Anthropic/Ollama for intelligent summary |
| Config file support | `.handoff.yml` per repo or globally |
| Pre-push Git hook | `handoff install-hook` installs a Git hook |
| Dependency graph (basic) | Grep-based import graph, not full AST |

### Phase 3 (weeks 9–16)

| Feature | Description |
|---------|-------------|
| GitHub Action | Run handoff in CI and post PR comment |
| Reviewer suggestions | Suggest reviewers from git blame / CODEOWNERS |
| PR quality scoring v2 | More signals: PR size, commit message quality, linked issues |
| Monorepo support | Detect packages, recommend package-specific tests |
| Language-specific parsing | Python AST, TypeScript compiler API |

### Phase 4 (future)

| Feature | Description |
|---------|-------------|
| Security scanning (entropy) | Better secret detection using Shannon entropy |
| gitleaks integration | Delegate secret scanning to gitleaks |
| PR scoring history | Track score over time for a team |
| IDE extension | VS Code sidebar showing handoff report |

---

## 11. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│  (Typer commands: pr, overview, tests, risks, impact, etc.) │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Analyzer Layer                           │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  GitAnalyzer │  │ RepoScanner   │  │  RiskDetector    │ │
│  │              │  │               │  │                  │ │
│  │ - branch     │  │ - stack       │  │ - debug patterns │ │
│  │ - diff       │  │ - frameworks  │  │ - todos/fixmes   │ │
│  │ - commits    │  │ - run cmds    │  │ - secrets        │ │
│  │ - file stats │  │ - test dirs   │  │ - risky paths    │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  TestMapper  │  │ ImpactAnalyzer│  │ ScoreCalculator  │ │
│  │              │  │               │  │                  │ │
│  │ - src→test   │  │ - import grep │  │ - 0-100 score    │ │
│  │ - cmd gen    │  │ - risk cross  │  │ - breakdown      │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Output Layer                              │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ TerminalFmt  │  │MarkdownWriter │  │   JSONEmitter    │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key design principles:
- **Each analyzer is pure**: takes data in, returns structured data out. No I/O inside analyzers.
- **Output layer is swappable**: same analysis data rendered as terminal, Markdown, or JSON.
- **Git is accessed only through GitAnalyzer**: all git subprocess calls in one place, easy to mock in tests.
- **Config is loaded once at startup** and passed into analyzers.

---

## 12. Recommended Tech Stack

**Language: Python 3.11+**

Rationale:
- Python is the industry-dominant language for CLIs targeting developers
- Fastest to prototype, best library ecosystem for this use case
- Shows Python proficiency for SWE roles that require it
- `subprocess` is standard for shelling out to git
- Rich, Typer, GitPython are production-quality libraries

**Core libraries:**

| Library | Purpose | Install |
|---------|---------|---------|
| `typer` | CLI framework, auto-generates help, supports subcommands | `pip install typer[all]` |
| `rich` | Beautiful terminal output: tables, panels, progress, colors | `pip install rich` |
| `GitPython` | Git operations with Pythonic API (fallback: `subprocess`) | `pip install GitPython` |
| `tomllib` | Parse pyproject.toml (stdlib in Python 3.11+) | stdlib |
| `pyyaml` | Parse .handoff.yml config | `pip install pyyaml` |

**Dev dependencies:**

| Library | Purpose |
|---------|---------|
| `pytest` | Unit tests |
| `pytest-mock` | Mock subprocess/git calls |
| `mypy` | Type checking |
| `ruff` | Linting + formatting |
| `build` + `twine` | Package for PyPI |

**Why not Go or Rust?**

Go produces a single binary (nice for distribution) but the ecosystem for terminal formatting and Git parsing is less ergonomic. Rust is even more so. Python with PyInstaller or pipx can distribute a single-command install just as well. The interview signal from a clean, well-typed Python project is strong.

**Distribution:**

```bash
pip install handoff-cli        # PyPI
pipx install handoff-cli       # Isolated install (preferred for CLIs)
brew install handoff-cli       # Homebrew tap (post-MVP)
```

---

## 13. Data Flow

```
User runs: handoff pr

    ┌─────────────────────────────────────────────┐
    │  1. CLI parses args                         │
    │     • base branch (--base or auto-detect)   │
    │     • mode: staged/unstaged/branch          │
    │     • output format: terminal/json/md       │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │  2. GitAnalyzer runs                        │
    │     • git rev-parse --abbrev-ref HEAD       │
    │     • git diff --name-status main...HEAD    │
    │     • git diff main...HEAD (full diff)      │
    │     • git log --oneline main..HEAD          │
    │  Returns: DiffResult                        │
    │     • changed_files: list[FileChange]       │
    │     • full_diff: str                        │
    │     • commits: list[Commit]                 │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │  3. Parallel analysis                       │
    │     • RiskDetector.analyze(diff_result)     │
    │     • TestMapper.map(diff_result)           │
    │     • RepoScanner.scan()   (once per run)   │
    │     • ScoreCalculator.score(...)            │
    │  Returns: AnalysisResult                    │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │  4. PRDescriptionBuilder                    │
    │     • Builds Markdown from AnalysisResult   │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │  5. Formatter renders output                │
    │     • TerminalFormatter → stdout            │
    │     • MarkdownWriter → file                 │
    │     • JSONEmitter → stdout                  │
    └─────────────────────────────────────────────┘
```

---

## 14. File / Module Structure

```
handoff-cli/
├── handoff/                    # Main package
│   ├── __init__.py
│   ├── main.py                 # Typer app, all CLI commands defined here
│   ├── config.py               # Config loading (.handoff.yml + defaults)
│   │
│   ├── git/
│   │   ├── __init__.py
│   │   ├── analyzer.py         # GitAnalyzer: all git subprocess calls
│   │   ├── diff_parser.py      # Parse unified diff format → structured data
│   │   └── models.py           # FileChange, DiffResult, Commit dataclasses
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── risk.py             # RiskDetector: patterns, categories, severity
│   │   ├── tests.py            # TestMapper: source→test mapping, cmd generation
│   │   ├── repo.py             # RepoScanner: stack detection, key files
│   │   ├── impact.py           # ImpactAnalyzer: import grep, dep graph
│   │   └── score.py            # ScoreCalculator: readiness score 0–100
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── terminal.py         # Rich-based terminal formatter
│   │   ├── markdown.py         # Markdown writer
│   │   ├── json_emitter.py     # JSON output
│   │   └── pr_template.py      # PR description builder
│   │
│   └── utils/
│       ├── __init__.py
│       ├── fs.py               # File system helpers (walk, exists, read)
│       └── subprocess.py       # Thin wrapper around subprocess.run
│
├── tests/
│   ├── fixtures/
│   │   ├── sample_repo/        # Fake repo for integration tests
│   │   ├── diffs/              # Sample .patch files for unit tests
│   │   └── configs/            # Sample .handoff.yml files
│   ├── test_git_analyzer.py
│   ├── test_diff_parser.py
│   ├── test_risk_detector.py
│   ├── test_test_mapper.py
│   ├── test_repo_scanner.py
│   ├── test_score.py
│   ├── test_pr_template.py
│   └── test_cli.py             # Typer CLI integration tests
│
├── pyproject.toml              # Project config, deps, scripts
├── README.md
├── CHANGELOG.md
├── .handoff.yml.example        # Example config
├── .github/
│   └── workflows/
│       └── ci.yml              # Lint + test on push
└── Makefile                    # make test, make lint, make build, make install
```

---

## 15. Risk Detection Rules

### Category Classification (file path matching)

```python
RISK_CATEGORIES = {
    "auth":        (["auth", "authentication", "login", "oauth", "jwt", "session", "password"], "HIGH"),
    "payments":    (["payment", "billing", "stripe", "checkout", "invoice", "subscription"], "HIGH"),
    "migration":   (["migration", "migrate", "alembic", "flyway", "liquibase", "schema"], "HIGH"),
    "database":    (["database", "db", "query", "sql", "orm", "repository", "dao"], "MEDIUM"),
    "config":      (["config", "settings", "env", "environment", "secrets"], "MEDIUM"),
    "security":    (["security", "permission", "authorization", "acl", "policy", "role"], "HIGH"),
    "deployment":  (["deploy", "infrastructure", "terraform", "helm", "k8s", "kubernetes"], "MEDIUM"),
    "api":         (["api", "endpoint", "route", "controller", "handler", "webhook"], "LOW"),
}
```

Rule: match any keyword against any segment of the file path (case-insensitive).

### Pattern Detection (line-level, applied to added lines only)

```python
PATTERNS = [
    # Debug statements
    PatternRule("console.log",    r"\bconsole\.log\s*\(",         "DEBUG",  "MEDIUM"),
    PatternRule("print()",        r"\bprint\s*\(",                 "DEBUG",  "MEDIUM"),
    PatternRule("debugger",       r"\bdebugger\b",                 "DEBUG",  "HIGH"),
    PatternRule("fmt.Println",    r"\bfmt\.Print(ln|f)?\s*\(",     "DEBUG",  "MEDIUM"),
    PatternRule("var_dump",       r"\bvar_dump\s*\(",              "DEBUG",  "MEDIUM"),
    PatternRule("dd()",           r"\bdd\s*\(",                    "DEBUG",  "MEDIUM"),
    PatternRule("pdb",            r"\bpdb\.set_trace\(\)|breakpoint\(\)", "DEBUG", "HIGH"),

    # TODOs
    PatternRule("TODO",           r"\bTODO\b",                     "TODO",   "LOW"),
    PatternRule("FIXME",          r"\bFIXME\b",                    "TODO",   "MEDIUM"),
    PatternRule("HACK",           r"\bHACK\b",                     "TODO",   "MEDIUM"),
    PatternRule("XXX",            r"\bXXX\b",                      "TODO",   "LOW"),

    # Possible secrets (applied to added lines, case-insensitive key matching)
    PatternRule("api_key",        r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']', "SECRET", "HIGH"),
    PatternRule("secret",         r'(?i)(secret|private[_-]?key)\s*[=:]\s*["\'][^"\']{8,}["\']', "SECRET", "HIGH"),
    PatternRule("password",       r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']', "SECRET", "HIGH"),
    PatternRule("token",          r'(?i)(token|auth[_-]?token|bearer)\s*[=:]\s*["\'][^"\']{8,}["\']', "SECRET", "HIGH"),
]
```

**False positive reduction:**
- Only scan _added_ lines (lines starting with `+` in the diff), never removed lines
- Skip lines that contain obvious test/example strings: `example`, `placeholder`, `your_api_key`, `changeme`, `<`, `{`
- Skip test files for most pattern types (keep TODO/FIXME checks in test files)

---

## 16. Test Recommendation Strategy

### Source → Test Mapping Algorithm

```python
def map_to_tests(source_path: str, repo_root: Path) -> list[Path]:
    """
    Given app/auth/token.py, try to find:
      - tests/test_token.py
      - tests/test_auth_token.py
      - tests/auth/test_token.py
      - tests/auth/token_test.py
      - test/test_token.py
      etc.
    """
    stem = Path(source_path).stem          # "token"
    parent = Path(source_path).parent.name # "auth"

    candidates = [
        f"tests/test_{stem}.py",
        f"tests/test_{parent}_{stem}.py",
        f"tests/{parent}/test_{stem}.py",
        f"test/test_{stem}.py",
        f"tests/{stem}_test.py",
        f"tests/{stem}.test.py",
        # JS/TS variants
        f"src/__tests__/{stem}.test.ts",
        f"src/__tests__/{stem}.test.tsx",
        f"{Path(source_path).parent}/{stem}.test.ts",
        f"{Path(source_path).parent}/{stem}.spec.ts",
    ]
    return [repo_root / c for c in candidates if (repo_root / c).exists()]
```

### Test Command Generation

```python
def suggest_test_commands(
    test_files: list[Path],
    stack: DetectedStack,
    changed_dirs: set[str],
) -> list[str]:
    if stack.language == "python":
        if test_files:
            files = " ".join(str(f) for f in test_files)
            return [f"pytest {files} -v"]
        return ["pytest tests/ -v"]

    if stack.language in ("javascript", "typescript"):
        if "jest" in stack.test_runner:
            keywords = " or ".join(f.stem for f in test_files)
            return [f"npm test -- --testPathPattern='{keywords}'"]
        return ["npm test"]

    if stack.language == "go":
        pkgs = {f"./{ Path(f).parent }..." for f in test_files}
        return [f"go test {' '.join(pkgs)}"]

    if stack.language == "rust":
        return ["cargo test"]

    return []
```

---

## 17. PR Description Template

```markdown
## Summary

<!-- What does this PR do? (auto-filled from changed file analysis) -->

This PR refactors the authentication token module to use RS256 instead of HS256,
updates middleware to validate expiry correctly, and adds a new user routes endpoint.

## Changes

| File | Change Type | Summary |
|------|------------|---------|
| app/auth/token.py | Modified | JWT signing algorithm refactor |
| app/auth/middleware.py | Modified | Expiry validation fix |
| app/models/user.py | Modified | Added `last_login` field |
| app/api/routes/users.py | Modified | New GET /users/{id}/profile endpoint |
| migrations/versions/abc123.py | Added | Add last_login column to users table |
| tests/test_auth.py | Added | New tests for RS256 flow |

## Risk Areas

- 🔴 **Database migration** — adds `last_login` column to users table (irreversible)
- 🔴 **Auth changes** — JWT signing algorithm changed from HS256 to RS256
- 🟡 **Config** — `app/config.py` now expects `RS256_PRIVATE_KEY` env var

## Testing

- [x] `pytest tests/test_auth.py tests/test_token.py -v` — all passing
- [ ] Manual test: login flow, token refresh, expiry
- [ ] Verify migration runs cleanly: `alembic upgrade head`

## Checklist

- [ ] No debug logs left in diff
- [ ] No TODO/FIXME introduced
- [ ] No hardcoded secrets
- [ ] Migration is reversible / rollback plan exists
- [ ] Tests added for changed code
- [ ] PR description explains the why

## Notes for Reviewers

Pay special attention to:
- `app/auth/token.py` — the algorithm change affects all token validation
- The migration is non-reversible without a downgrade migration

---
*Generated by [handoff](https://github.com/your-handle/handoff-cli)*
```

---

## 18. Config File Design

**File:** `.handoff.yml` (repo root) or `~/.handoff/config.yml` (global)

```yaml
# .handoff.yml

# Base branch to diff against (default: auto-detect main/master)
base_branch: main

# Override risky path patterns and their severity
risk_paths:
  - pattern: "payments/"
    severity: HIGH
  - pattern: "internal/auth"
    severity: HIGH
  - pattern: "scripts/deploy"
    severity: MEDIUM

# Paths to ignore entirely (glob patterns)
ignore_paths:
  - "docs/**"
  - "*.md"
  - "migrations/seeds/**"

# Additional debug patterns to detect (on top of built-ins)
debug_patterns:
  - "logger.debug"
  - "console.trace"

# Test file mappings (custom source → test path templates)
test_mappings:
  - source: "src/services/**/*.ts"
    test: "src/services/__tests__/*.test.ts"
  - source: "app/api/**/*.py"
    test: "tests/api/test_*.py"

# PR description template (path to custom template file)
pr_template: ".github/pull_request_template.md"

# Minimum readiness score to exit 0 (default: 0 = always pass)
min_score: 70

# LLM config (optional, post-MVP)
llm:
  provider: ollama          # openai | anthropic | ollama | none
  model: llama3             # model name
  base_url: http://localhost:11434
```

**Config loading priority:**
1. CLI flags (highest)
2. `.handoff.yml` in current directory
3. `.handoff.yml` in repo root
4. `~/.handoff/config.yml` (global)
5. Built-in defaults (lowest)

---

## 19. Error Handling

| Error | Message | Exit Code |
|-------|---------|-----------|
| Not a Git repo | `Error: Not inside a git repository. Run handoff from inside a git repo.` | 2 |
| No commits yet | `Error: Repository has no commits yet.` | 2 |
| Base branch not found | `Warning: Could not find branch 'main'. Trying 'master'...` | continue |
| No changes found | `No changes detected between this branch and main.` | 0 |
| Git not installed | `Error: git not found. Please install git.` | 2 |
| File not found (impact) | `Error: File 'path/to/file' does not exist in the repo.` | 1 |
| Config parse error | `Warning: Could not parse .handoff.yml: [error]. Using defaults.` | continue |
| Large diff (>5000 lines) | `Warning: Diff is large (5,847 lines). Analysis may be slow.` | continue |

---

## 20. Security and Privacy Considerations

**Local-first by design:**
- handoff never sends data to any remote server in the base version
- All analysis happens in-process using local file system and git commands
- No telemetry, no analytics, no opt-out required

**Secret detection, not storage:**
- handoff detects patterns that _look like_ secrets in added diff lines
- It never stores, logs, or transmits the detected content
- Output shows line number and truncated context, not the full secret value

**False positive communication:**
- Clearly label secret detection as "possible secret" not "secret found"
- Document the regex patterns so users understand what triggers a warning

**LLM mode (post-MVP):**
- When LLM is configured, clearly warn the user: `This diff will be sent to [provider].`
- Support local Ollama so no data leaves the machine
- Never default to a remote LLM; it must be explicitly configured

---

## 21. Testing Strategy

### Unit Tests

- `test_diff_parser.py` — parse sample `.patch` files, verify FileChange extraction
- `test_risk_detector.py` — test each regex pattern against positive and negative cases
- `test_test_mapper.py` — given source paths, verify mapped test path candidates
- `test_repo_scanner.py` — given fake directory tree, verify stack detection
- `test_score.py` — verify score calculation given known inputs
- `test_pr_template.py` — verify PR Markdown output structure

**Use `tmp_path` fixtures** (pytest built-in) to create real temp directories with fake files — avoids complex mocking.

### Git Mocking Strategy

Option A (recommended for unit tests): Create a real temp git repo in `tmp_path` fixture, run actual git commands inside it. This is more reliable than mocking subprocess.

```python
@pytest.fixture
def git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=tmp_path)
    return tmp_path
```

Option B: Use `pytest-mock` to mock `subprocess.run` — useful for fast unit tests that don't need real git.

### Integration Tests

Create a `tests/fixtures/sample_repo/` directory that is itself a real git repo. Run `handoff pr`, `handoff risks`, etc. against it and assert on output structure. Use JSON output mode for assertions.

```python
def test_pr_command_json(sample_repo):
    result = runner.invoke(app, ["pr", "--json"], obj={"cwd": sample_repo})
    data = json.loads(result.output)
    assert "changed_files" in data
    assert "risks" in data
    assert "score" in data
```

### CLI Tests

Use `typer.testing.CliRunner` for all command tests. Verify:
- Exit codes
- Output contains expected sections
- `--json` output is valid JSON with expected keys
- `--output` writes a file

---

## 22. Success Metrics

For a portfolio project, success metrics are proxies for quality and impact:

| Metric | Target |
|--------|--------|
| GitHub stars | 100+ in first month |
| README demo quality | Terminal recording that reads clearly in 30s |
| Test coverage | >80% on core modules |
| PyPI installs | Publicly visible |
| Zero external API dependencies for base use | Achieved at launch |
| Works on Python 3.11, 3.12 | CI verified |
| `pip install handoff-cli && handoff pr` works in < 10 seconds | Verified |
| Passes mypy with strict mode on core modules | CI enforced |

---

## 23. 2–4 Week Build Roadmap

### Week 1: Foundation

**Goal:** `handoff pr --json` outputs a real diff analysis.

| Day | Task |
|-----|------|
| 1 | Project setup: pyproject.toml, Makefile, CI, ruff, mypy, pytest |
| 1 | Create module structure, empty files with docstrings |
| 2 | `git/models.py` — FileChange, DiffResult, Commit dataclasses |
| 2 | `git/analyzer.py` — branch, diff, commits via subprocess |
| 3 | `git/diff_parser.py` — parse unified diff into FileChange list |
| 3 | Tests: `test_git_analyzer.py`, `test_diff_parser.py` with fixture .patch files |
| 4 | `analysis/risk.py` — category classification + pattern detection |
| 4 | Tests: `test_risk_detector.py` with all pattern positive/negative cases |
| 5 | `analysis/tests.py` — source→test mapping, command generation |
| 5 | Tests: `test_test_mapper.py` |

### Week 2: Core Commands

**Goal:** All primary commands work end-to-end in the terminal.

| Day | Task |
|-----|------|
| 6  | `analysis/repo.py` — stack detection from manifest files |
| 6  | `analysis/score.py` — readiness score calculator |
| 7  | `output/terminal.py` — Rich-based formatter for all analysis output |
| 7  | Wire up `handoff pr` command end-to-end, test manually |
| 8  | `handoff overview` command: repo scan + terminal output |
| 8  | `handoff tests` command: test mapping + terminal output |
| 9  | `handoff risks` command: risk detection + terminal output |
| 9  | `handoff impact <file>` command: grep-based import analysis |
| 10 | `output/pr_template.py` — PR description generator |
| 10 | `handoff write-pr` command |

### Week 3: Polish and Output Formats

**Goal:** All output formats work, edge cases handled, CLI feels polished.

| Day | Task |
|-----|------|
| 11 | `handoff before-push` command — composite command |
| 11 | Exit codes for CI integration (0/1/2) |
| 12 | `output/markdown.py` — `--output` flag writes Markdown to file |
| 12 | `output/json_emitter.py` — `--json` flag emits structured JSON |
| 13 | Config file loading (`config.py`) — `.handoff.yml` support |
| 13 | `handoff install-hook` — install pre-push Git hook |
| 14 | Error handling audit: every error path tested and messaged |
| 14 | Large diff handling (warn + truncate if >5000 lines) |
| 15 | Manual testing on 3 different real repos |

### Week 4: Release Prep

**Goal:** Clean, documented, released to PyPI.

| Day | Task |
|-----|------|
| 16 | `tests/fixtures/sample_repo/` — build realistic fake test repo |
| 16 | Integration test suite with CliRunner |
| 17 | README — install, quickstart, command reference, demo recording |
| 17 | Terminal demo recording with `vhs` or `asciinema` |
| 18 | mypy strict mode pass on all core modules |
| 18 | Coverage check — 80%+ on analysis/ and git/ |
| 19 | PyPI packaging — `build`, `twine upload` |
| 19 | GitHub Releases — tag v0.1.0, release notes |
| 20 | Optional: GitHub Actions workflow for CI |
| 20 | Optional: Test on macOS + Linux (GitHub Actions matrix) |

---

## 24. Open Questions

Before you start building, answer these:

### Product
1. **Should `handoff pr` use branch diff or staged diff by default?** Recommendation: branch diff (vs main/master). Staged diff is a different workflow — keep it as `--staged` flag.

2. **What should happen if there are 0 commits on the branch?** Should warn "No commits on this branch yet" and exit cleanly.

3. **Should the readiness score block the user?** Recommendation: never block by default. Exit code 1 on warnings, exit code 2 on HIGH risks — but only fail CI if user sets `min_score` in config.

4. **Should `handoff before-push` be opinionated or informational?** Recommendation: informational for MVP. Never refuse to let the user push. Present findings, let the user decide.

### Technical
5. **Will you use GitPython or raw subprocess for git?** Recommendation: raw subprocess via a thin wrapper. Fewer dependencies, easier to understand, easier to mock. GitPython adds value only for parsing — but the unified diff format is easy enough to parse manually.

6. **Should the config file live at `.handoff.yml` or `.handoff/config.yml`?** Recommendation: `.handoff.yml` at repo root (simpler, one file, visible, committable). Global user config at `~/.config/handoff/config.yml`.

7. **Will you support Windows for MVP?** Recommendation: macOS + Linux for MVP. Windows needs `git.exe` path handling, different shell, different terminal colors. Log it as a known limitation.

8. **What Python version minimum will you target?** Recommendation: Python 3.11+. Use `tomllib` from stdlib. Target 3.11 and 3.12.

---

## 25. Q&A

### Product Questions

**Q1: Is this idea differentiated enough from existing repo summarizers?**

Yes — the differentiation is the *Git diff / PR workflow* focus. Tools like repomix, gpt-repository-loader, or GitHub Copilot's PR summaries are either full-repo packers for LLM input, or cloud-only AI features. handoff is:
- Local-first, no API key needed
- Workflow-oriented (before-push, write-pr, not just "summarize this repo")
- Opinionated about engineering quality signals (risks, tests, debug patterns)
- Composable (JSON output, exit codes, hookable into CI)

The closest competitor is a pre-commit hook + a shell script. handoff is that, but structured and usable.

**Q2: What should the exact target user be?**

Mid-to-senior Python, JavaScript, or Go engineers at companies with pull request workflows. Specifically engineers who:
- Work on a team with code review
- Have been burned by forgetting to remove a debug log or TODO
- Write PR descriptions reluctantly

**Q3: What is the strongest positioning statement?**

*"handoff turns your git diff into a PR description, risk checklist, and test recommendations — before you open the PR."*

**Q4: What is the smallest useful MVP?**

`handoff before-push` working correctly:
1. List changed files with risk categories
2. Detect TODOs, console.log, possible secrets in added lines
3. Map changed source files to test files and suggest pytest/npm test commands
4. Print a draft PR description to stdout

That's it. Everything else is polish.

**Q5: What feature would make this feel impressive in interviews?**

The **readiness score (0–100)** with a breakdown. It shows you can think about metrics, thresholds, and scoring heuristics — a product-minded engineering signal. Combined with JSON output and CI exit codes, it demonstrates systems thinking: "I built this to be composable, not just a pretty printer."

**Q6: What should I avoid building?**

- Auto-fixing code (scope creep, different product)
- Cloud sync / team dashboards (different business)
- LLM integration in the MVP (adds a paid dependency, reduces audience, complicates the project)
- A GUI or web interface
- Comprehensive AST parsing (rabbit hole, not needed for 80% of the value)

**Q7: What should the tool be named?**

**handoff** is good — clear, memorable, slightly unexpected for a CLI tool. It implies both "handing off code to reviewers" and "handing off unfinished work to teammates." The PyPI name `handoff-cli` is likely available. Check with `pip install handoff-cli` — if it's taken, consider `git-handoff` or `prcheck`.

---

### Technical Questions

**Q8: Should I build it in Python, Go, Rust, or Node?**

**Python.** Fastest to build, best library ecosystem (Rich for output, Typer for CLI, pytest for tests), widely understood in interviews. The perception that "Python is slow" doesn't matter for a CLI that runs in under 2 seconds. PyPI distribution with pipx is clean. Go would be second choice (single binary, fast startup) but the Rich/Typer equivalents in Go are less ergonomic.

**Q9: What libraries should I use?**

```
typer[all]   — CLI: commands, help, auto-completion
rich         — Output: colors, tables, panels, syntax highlighting
pyyaml       — Config: .handoff.yml parsing
pytest       — Tests
pytest-mock  — Git call mocking
mypy         — Type checking
ruff         — Linting + formatting (replaces black + flake8)
```

Avoid: GitPython (heavier than needed), click (typer wraps it, use typer directly), questionary (interactive prompts not needed for MVP).

**Q10: How should I read Git diffs?**

Shell out to git and parse the output:

```python
import subprocess

def get_diff(base: str, head: str = "HEAD") -> str:
    result = subprocess.run(
        ["git", "diff", f"{base}...{head}"],
        capture_output=True, text=True, check=True
    )
    return result.stdout
```

Parse the unified diff format yourself — it's a simple state machine. Lines starting with `+` are added, `-` are removed, `@@` are hunk headers, `diff --git` starts a new file section. Writing your own parser teaches you the format and is easy to unit test with fixture `.patch` files.

**Q11: Should I shell out to git commands or use a Git library?**

**Shell out.** `subprocess.run(["git", ...])` is simpler, more transparent, and easier to mock. GitPython adds value for complex operations (walking trees, object databases) that you don't need. Your `git/analyzer.py` module becomes a clean collection of functions that each call one git command.

**Q12: How should I detect the default branch?**

```python
def detect_default_branch(cwd: Path) -> str:
    # Try to read from remote HEAD reference
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True, cwd=cwd
    )
    if result.returncode == 0:
        # Returns "refs/remotes/origin/main" → extract "main"
        return result.stdout.strip().split("/")[-1]

    # Fall back: check if main or master exist as local branches
    for branch in ("main", "master", "develop"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True, cwd=cwd
        )
        if r.returncode == 0:
            return branch

    raise ValueError("Could not detect default branch")
```

**Q13: How should I handle staged vs unstaged changes?**

```python
class DiffMode(Enum):
    BRANCH = "branch"    # git diff main...HEAD (default)
    STAGED = "staged"    # git diff --cached
    UNSTAGED = "unstaged"  # git diff (no flags)

GIT_DIFF_COMMANDS = {
    DiffMode.BRANCH:   lambda base: ["git", "diff", f"{base}...HEAD"],
    DiffMode.STAGED:   lambda _:    ["git", "diff", "--cached"],
    DiffMode.UNSTAGED: lambda _:    ["git", "diff"],
}
```

Default to `BRANCH` mode. Let the user pass `--staged` or `--unstaged` to override.

**Q14: How should I map source files to tests?**

See Section 16. The key insight: try multiple candidate paths and return the ones that actually exist on disk. The mapping is heuristic, not perfect — that's fine, it'll be right 80% of the time and the user can correct it.

**Q15: How should I detect risky files?**

Keyword matching against the file path (not content). Split the path into segments and check each segment against keyword lists. This is intentionally simple and fast:

```python
def classify_file(path: str) -> tuple[str | None, str | None]:
    path_lower = path.lower()
    for category, (keywords, severity) in RISK_CATEGORIES.items():
        if any(kw in path_lower for kw in keywords):
            return category, severity
    return None, None
```

**Q16: How should I detect secrets without false positives?**

Three filters to reduce noise:
1. Only scan **added lines** in the diff (lines starting with `+`)
2. Skip lines that contain obvious placeholder strings: `example`, `placeholder`, `your_`, `changeme`, `<`, `{`, `test`
3. Require a minimum length on the value (>8 chars) to skip empty assignments

```python
PLACEHOLDER_PATTERNS = [
    r"example", r"placeholder", r"your[_-]",
    r"changeme", r"<.*>", r"\{.*\}", r"test", r"fake", r"dummy"
]

def is_placeholder(value: str) -> bool:
    return any(re.search(p, value, re.IGNORECASE) for p in PLACEHOLDER_PATTERNS)
```

Still label findings as "possible secret" not "secret confirmed" — you're a heuristic tool, not a security scanner.

**Q17: How should I parse package.json, pyproject.toml, Makefile, Dockerfile, and go.mod?**

```python
# pyproject.toml — use stdlib tomllib (Python 3.11+)
import tomllib
with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

# package.json — use stdlib json
import json
with open("package.json") as f:
    pkg = json.load(f)
scripts = pkg.get("scripts", {})

# go.mod — simple line parsing, no library needed
def parse_go_mod(content: str) -> dict:
    module = ""
    go_version = ""
    for line in content.splitlines():
        if line.startswith("module "):
            module = line.split()[1]
        elif line.startswith("go "):
            go_version = line.split()[1]
    return {"module": module, "go_version": go_version}

# Makefile — regex to find targets
import re
def parse_makefile_targets(content: str) -> list[str]:
    return re.findall(r'^([a-zA-Z][a-zA-Z0-9_-]*):', content, re.MULTILINE)

# requirements.txt — split and parse package names
def parse_requirements(content: str) -> list[str]:
    return [
        line.split("==")[0].split(">=")[0].split("[")[0].strip()
        for line in content.splitlines()
        if line and not line.startswith("#")
    ]
```

**Q18: How should I design the config file?**

See Section 18. Key decisions:
- YAML (not TOML) — more familiar to engineers for config files with lists and maps
- Flat structure for common settings, nested only where unavoidable
- Every key is optional — config augments defaults, never replaces them entirely
- Support both repo-level (`.handoff.yml`) and user-level (`~/.config/handoff/config.yml`)

**Q19: Should I include LLM support in the MVP?**

**No.** Reasons:
- It adds a paid API dependency that reduces the tool's audience
- The static analysis in the MVP is already genuinely useful
- Adding LLM later is straightforward (pipe the diff to an API call)
- The MVP should prove value without AI — that's a stronger engineering story

Design the output layer so that adding an LLM summarization pass later is additive, not structural. The analysis data goes to a formatter — swap the formatter for an LLM-enhanced version optionally.

**Q20: How can I support local LLMs like Ollama or LM Studio later?**

Design a `summarizer` protocol:

```python
class Summarizer(Protocol):
    def summarize_diff(self, diff: str, context: dict) -> str: ...

class NoOpSummarizer:
    def summarize_diff(self, diff: str, context: dict) -> str:
        return ""  # Static analysis only

class OllamaSummarizer:
    def summarize_diff(self, diff: str, context: dict) -> str:
        # POST to http://localhost:11434/api/generate
        ...
```

Register the summarizer based on config: `llm.provider: ollama`. This way you add the feature without touching the core analysis code.

---

### Implementation Questions

**Q21: What should the folder structure look like?**

See Section 14. The key decision: keep `git/`, `analysis/`, `output/` as clearly separated layers. Don't let output code call git, and don't let analysis code format strings for display.

**Q22: What are the core modules/classes/functions?**

```
GitAnalyzer.get_diff(base, mode) → DiffResult
DiffParser.parse(raw_diff) → list[FileChange]
RiskDetector.analyze(diff_result) → list[Risk]
TestMapper.map(changed_files, repo_root) → list[TestMapping]
RepoScanner.scan(repo_root) → RepoInfo
ScoreCalculator.score(diff_result, risks, test_mappings) → Score
PRDescriptionBuilder.build(analysis_result) → str
TerminalFormatter.render(analysis_result) → None  (prints to stdout)
```

**Q23: What should the first version of each command do?**

- `handoff pr` — read branch diff, print file list with risk categories and pattern warnings
- `handoff overview` — detect stack from manifests, print language + key files
- `handoff tests` — map changed files to test paths, print commands
- `handoff risks` — print pattern and category risks, nothing else
- `handoff write-pr` — print the PR description template filled with diff data

**Q24: What commands should I build first?**

Order: `handoff risks` → `handoff tests` → `handoff pr` → `handoff overview` → `handoff write-pr` → `handoff before-push` → `handoff impact`.

Start with `risks` because it has no dependencies on other modules (just diff + regex) and is immediately testable and demoable.

**Q25: What should I test first?**

`test_risk_detector.py` — it's pure function testing (regex patterns against strings), runs instantly, and forces you to think about false positives. This is also the most likely place for regressions.

**Q26: What fake sample repo should I create for testing?**

```
tests/fixtures/sample_repo/
├── app/
│   ├── auth/
│   │   ├── token.py          (contains some TODO, debug print)
│   │   └── middleware.py
│   ├── api/
│   │   └── routes/
│   │       └── users.py
│   ├── models/
│   │   └── user.py
│   └── config.py             (contains possible secret pattern)
├── migrations/
│   └── versions/
│       └── 001_add_users.py
├── tests/
│   ├── test_token.py
│   └── test_user.py
├── package.json              (for JS detection)
├── pyproject.toml
├── requirements.txt
├── Makefile
└── Dockerfile
```

Make it a real git repo with commits so you can run actual `git diff` commands in tests.

**Q27: How should I write unit tests for Git diff behavior?**

Store real `.patch` files in `tests/fixtures/diffs/`. Generate them from real repos:

```bash
git diff main...feature-branch > tests/fixtures/diffs/auth_refactor.patch
```

Then load them in tests:

```python
@pytest.fixture
def auth_refactor_diff():
    return (Path(__file__).parent / "fixtures/diffs/auth_refactor.patch").read_text()

def test_diff_parser_extracts_changed_files(auth_refactor_diff):
    result = DiffParser().parse(auth_refactor_diff)
    assert any(f.path == "app/auth/token.py" for f in result.changed_files)
```

**Q28: How should I test the CLI?**

Use `typer.testing.CliRunner`:

```python
from typer.testing import CliRunner
from handoff.main import app

runner = CliRunner()

def test_pr_command_exits_zero(git_repo):
    result = runner.invoke(app, ["pr", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "changed_files" in data
```

For the `git_repo` fixture, use a real temp git repo with staged commits. Test both the happy path and edge cases (no commits, no changes, large diff).

**Q29: How should I handle large repos?**

- For `handoff overview`: limit the directory walk to 3 levels deep, sample rather than walk everything
- For `handoff pr`: limit the diff to the first 10,000 lines, warn if truncated
- For `handoff impact`: grep is fast enough for most repos, but add a `--max-results` cap
- Document: "Works well for repos up to ~500k LOC. Very large monorepos may be slow."

**Q30: How should I make the output look polished?**

Use Rich's built-in components:
- `rich.panel.Panel` for section headers
- `rich.table.Table` for file lists
- `rich.console.Console` with markup for colored inline text
- `rich.rule.Rule` for dividers
- `rich.syntax.Syntax` for showing diff snippets with syntax highlighting

Assign consistent colors: red = HIGH risk, yellow = MEDIUM, green = OK, cyan = informational. Use a single `console = Console()` instance. Never use `print()` directly.

---

### Portfolio / Interview Questions

**Q31: How should I explain this project on my resume?**

```
handoff-cli  |  Python, Typer, Rich, Git  |  github.com/your-handle/handoff-cli
• Built a local-first Git CLI that analyzes PR diffs to surface risks, recommend tests, and generate PR descriptions
• Designed a composable analysis pipeline (risk detection, test mapping, score calculation) with JSON output and CI integration
• Published to PyPI; supports Python 3.11+, macOS/Linux
```

**Q32: What technical tradeoffs should I be ready to discuss?**

- **subprocess vs GitPython**: chose subprocess for transparency and testability over a higher-level API
- **Regex vs AST for secret detection**: regex is fast and portable but produces false positives; AST would be more accurate but language-specific and complex
- **Static analysis vs LLM**: chose static analysis for MVP to keep the tool local-first and dependency-free
- **Python vs Go**: Python for developer velocity and ecosystem; Go would give a single binary but slower iteration
- **Heuristic test mapping vs config-driven**: heuristic works for common patterns; config override available for non-standard layouts

**Q33: What system design talking points does this project create?**

- **Pipeline design**: the analysis pipeline (git → parse → analyze → score → format) shows understanding of separation of concerns
- **Plugin architecture**: the Summarizer protocol shows how to design for extension without coupling
- **Output abstraction**: same data rendered three ways (terminal, JSON, Markdown) demonstrates interface design
- **CLI design**: exit codes, composable commands, machine-readable output — production CLI design patterns
- **Testability**: the git boundary is behind a single class with a well-defined interface, making it mockable

**Q34: What would make this project stand out on GitHub?**

- High-quality README with a terminal recording (use `vhs` or `asciinema` — renders in GitHub)
- A `CHANGELOG.md` with real version history
- CI badge (GitHub Actions: tests passing, coverage %)
- PyPI badge (version, downloads)
- A `--json` flag and documented JSON schema (shows API-first thinking)
- Contributing guide
- Example `.handoff.yml` in the repo itself

**Q35: What README sections should I include?**

1. One-line description + terminal GIF
2. Install (`pip install handoff-cli` or `pipx install handoff-cli`)
3. Quick start (4 commands with expected output)
4. Command reference (table of all commands with descriptions)
5. Config file example
6. How it works (3-bullet architecture summary)
7. Contributing
8. License

**Q36: What screenshots or terminal demos should I include?**

Record these specific scenarios with `vhs` or `asciinema`:
1. `handoff pr` on a realistic branch with auth changes — shows full output
2. `handoff before-push` catching a debug log and TODO — shows the "aha moment"
3. `handoff write-pr --output pr.md` + `cat pr.md` — shows the generated PR description

Keep each demo under 45 seconds.

**Q37: How can I make this look production-quality?**

- Consistent Rich styling with a defined color palette
- `--version` shows the version from pyproject.toml
- `--help` on every command is complete and accurate
- No stack traces on expected errors (catch exceptions at the CLI boundary, print clean messages)
- Works from any subdirectory of the repo (traverse up to find `.git`)
- `handoff` with no args shows help, not an error

**Q38: What should the first GitHub release include?**

**v0.1.0:**
- `handoff pr` — full analysis output
- `handoff risks` — risk-only output
- `handoff tests` — test recommendations
- `handoff overview` — repo scan
- `handoff write-pr` — PR description
- `--json` and `--output` flags on `handoff pr`
- PyPI package
- README with terminal demo
- Works on Python 3.11+, macOS/Linux

Tag with `v0.1.0`, write a release note that lists what's included and what's coming in `v0.2.0` (config file, `handoff before-push`, pre-push hook).

---

*This document should be treated as a living spec. Update it as decisions are made during implementation.*
