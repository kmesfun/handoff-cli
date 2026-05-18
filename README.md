# handoff-cli

A local-first CLI that turns your Git diff into a PR description, risk checklist, and test recommendations — before you open the PR.

No cloud account. No API key. Runs entirely on your machine.

---

## Install

**Recommended — pipx (isolated install):**
```bash
pipx install handoff-cli
```

**pip:**
```bash
pip install handoff-cli
```

**From source:**
```bash
git clone https://github.com/kmesfun/handoff-cli.git
cd handoff-cli
pip install -e .
```

Requires Python 3.11+. Verify your installation:
```bash
handoff --version
```

---

## Quick start

Run these from inside any Git repository:

```bash
# See what stack and commands this repo uses
handoff overview

# Full PR readiness report for the current branch
handoff pr

# Catch debug logs, TODOs, and possible secrets in your diff
handoff risks

# Find out which tests to run after your changes
handoff tests

# Generate a Markdown PR description
handoff write-pr

# Run everything before pushing
handoff before-push
```

---

## Commands

### `handoff overview`
Scan the repo and report detected languages, frameworks, key files, and run/test commands.

```
handoff overview
handoff overview --output overview.md
handoff overview --json
```

### `handoff pr`
Full PR readiness analysis of the current branch vs base. Shows changed files (with risk categories), pattern warnings, test recommendations, and a 0–100 readiness score.

```
handoff pr
handoff pr --base develop
handoff pr --staged
handoff pr --output report.md
handoff pr --json
```

### `handoff risks`
Scan changed files for:
- **Category risks** — files touching auth, payments, migrations, security, config, deployment
- **Pattern warnings** — debug statements (`console.log`, `print()`, `debugger`, `pdb`), `TODO`/`FIXME`, possible hardcoded secrets

```
handoff risks
handoff risks --base main
handoff risks --staged
```

### `handoff tests`
Map changed source files to their test counterparts and suggest the exact commands to run. Supports Python (pytest), JavaScript/TypeScript (Jest), Go, and Rust.

```
handoff tests
handoff tests --staged
handoff tests --json
```

### `handoff impact <file>`
Find all files in the repo that import or reference a given file. Useful before modifying a shared utility.

```
handoff impact app/utils/http.py
handoff impact src/lib/auth.ts
```

### `handoff write-pr`
Generate a structured Markdown PR description from the current diff, including a changes table, risk areas, testing checklist, and reviewer notes.

```
handoff write-pr
handoff write-pr --output pr.md
```

### `handoff before-push`
Combines risks + tests + PR description into a single pre-push report. Returns exit code 1 if debug statements or possible secrets are found — useful as a CI gate.

```
handoff before-push
handoff before-push --output checklist.md
handoff before-push --json
```

### `handoff install-hook`
Install a Git pre-push hook so `handoff before-push` runs automatically before every `git push`.

```
handoff install-hook
```

---

## Global options

All commands accept these flags:

| Flag | Description |
|------|-------------|
| `--base <branch>` | Base branch to diff against (default: auto-detect `main`/`master`) |
| `--staged` | Only analyze staged changes |
| `--unstaged` | Only analyze unstaged changes |
| `--output <file>` | Write output to a Markdown file |
| `--json` | Emit structured JSON (useful for scripts and CI) |
| `--no-color` | Disable ANSI colors |
| `--version` | Show version |

---

## Config file

Create `.handoff.yml` in your repo root to customize behavior:

```yaml
# .handoff.yml
base_branch: main

# Extra risky paths
risk_paths:
  - pattern: "internal/payments"
    severity: HIGH

# Paths to skip entirely
ignore_paths:
  - "docs/**"
  - "*.md"

# Minimum score to exit 0 (useful for CI)
min_score: 70
```

See [`.handoff.yml.example`](.handoff.yml.example) for the full reference.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Clean — no blocking issues |
| `1` | Warnings — debug statements or possible secrets found |
| `2` | Error — not a git repo, git not found, etc. |

This makes `handoff before-push` usable as a CI step:

```yaml
# .github/workflows/ci.yml
- name: PR readiness check
  run: handoff before-push --base main
```

---

## Development

```bash
git clone https://github.com/kmesfun/handoff-cli.git
cd handoff-cli
pip install -e .
pip install pytest pytest-mock

# Run tests
make test          # or: pytest tests/ -v

# Lint
make lint          # ruff check

# Type check
make typecheck     # mypy handoff/
```

---

## License

MIT
