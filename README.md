# Random Coffee MVP

A repository-native MVP for weekly random coffee chats.

The app keeps a YAML list of participants, generates history-aware random 1:1 pairings, assigns each pair to one of several configured coffee slots, writes mock Google Calendar event payloads, updates YAML history, and is designed to run from GitHub Actions.

## MVP behaviour

- 50 active participants become 25 separate 15-minute coffee invites.
- Pairings avoid historical repeats where possible.
- Meetings are spread across configured Tue/Wed/Thu/Fri slots rather than one global time.
- If a slot does not work, participants reschedule via Google Calendar's “propose a new time” flow or by messaging each other.
- Calendar integration is mocked for now; no Google API credentials are needed.
- `data/history.yaml` is the source of truth for already-created weeks, making default runs idempotent.

## Production Google Calendar strategy

The production-grade strategy is documented in:

```text
docs/GOOGLE_CALENDAR_PRODUCTION.md
```

Recommended approach:

- Dedicated organiser account, e.g. `random-coffee@example.com`.
- Google Workspace service account with domain-wide delegation.
- GitHub Actions secrets for credentials.
- A real `GoogleCalendarClient` adapter behind the existing mock calendar boundary.
- Deterministic Google event IDs to make retries safe and avoid duplicate invites.

## Repository layout

```text
.github/workflows/weekly-random-coffee.yml  # weekly/manual scheduler
config/participants.yaml                    # mock list of 50 emails
config/schedule.yaml                        # slots and meeting settings
data/history.yaml                           # scheduler-updated history
docs/                                      # spec, decisions, production setup
openspec/specs/random-coffee-mvp/spec.md    # OpenSpec-style acceptance criteria
src/random_coffee/                          # Python scheduler package
tests/test_random_coffee.py                 # pytest suite
```

Generated mock event output is written to:

```text
output/mock-calendar-events/<week>.json
```

## Local usage

Install dependencies and run tests:

```bash
uv run pytest -q
```

Run linting:

```bash
uv run ruff check .
```

Generate a specific week locally:

```bash
uv run python -m random_coffee.cli --week-start 2026-06-08 --seed 12345
```

Run again without `--force` and it will skip because the week already exists in `data/history.yaml`:

```bash
uv run python -m random_coffee.cli --week-start 2026-06-08 --seed 99999
```

Regenerate a week during development:

```bash
uv run python -m random_coffee.cli --week-start 2026-06-08 --seed 99999 --force
```

## GitHub Actions

The workflow runs every Monday morning UTC and can also be triggered manually.

Manual inputs:

- `week_start`: target Monday, e.g. `2026-06-08`; empty means current week.
- `seed`: deterministic pairing seed; empty means derived from the week.
- `force`: replace an existing week in history.

The workflow:

1. Checks out the repo.
2. Installs Python dependencies with `uv`.
3. Runs the tests.
4. Runs the scheduler.
5. Commits changes to `data/history.yaml` and `output/mock-calendar-events/*.json` if there are any.

## Current limitation

The scheduler currently uses `MockCalendarClient`; it does not yet send real Google Calendar invites. See `docs/GOOGLE_CALENDAR_PRODUCTION.md` for the exact implementation and operational steps required to make this production-ready.
