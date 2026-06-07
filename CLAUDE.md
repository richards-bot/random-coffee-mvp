# CLAUDE.md

## Project Overview

**What:** GitHub Actions driven random coffee scheduler MVP.
**Stack:** Python 3.11, `uv`, PyYAML, pytest, ruff, GitHub Actions.
**Status:** MVP with mock calendar output. Real Google Calendar integration is documented but not implemented.

## Commands

```bash
uv run pytest -q          # Run tests
uv run ruff check .       # Lint
uv run python -m random_coffee.cli --week-start 2026-06-08 --seed 12345
```

## Structure

```text
.github/workflows/weekly-random-coffee.yml  # weekly/manual scheduler
config/participants.yaml                    # participant registry
data/history.yaml                           # generated weekly pairing history
docs/SPEC.md                               # product/technical spec
docs/DECISIONS.md                          # architecture decisions
docs/GOOGLE_CALENDAR_PRODUCTION.md          # real Calendar rollout guide
openspec/specs/random-coffee-mvp/spec.md    # acceptance criteria
src/random_coffee/                          # scheduler package
tests/test_random_coffee.py                 # test suite
```

## Operating Model

- OpenSpec defines requirements and acceptance criteria.
- Beads tracks execution work.
- Use TDD for production code changes.
- Keep Google credentials out of git; use GitHub Secrets only.

## Beads — mandatory

Before code or documentation changes:

1. Run `bd list --json` or `bd ready --json`.
2. Create or claim an issue.
3. Mark it active with `bd update <id> --status in_progress --json`.
4. Include the bead ID in commits.
5. Close the bead when complete.
6. If `bd sync` is unavailable, use `bd vc commit -m "..."` for local Beads state.

## Quality gates

Before handoff:

```bash
uv run ruff check .
uv run pytest -q
git status --short --branch
```

Push completed work to the remote when a remote exists.
