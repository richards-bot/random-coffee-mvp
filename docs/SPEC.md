# Random Coffee Scheduler MVP Specification

> Status: Draft | Updated: 2026-06-07

## Summary

Random Coffee Scheduler is a GitHub Actions driven utility that pairs roughly 50 participants into weekly 15-minute 1:1 coffee meetings. The MVP uses YAML files in the repository for participants, scheduling configuration, and pairing history, and writes mock Google Calendar invite payloads instead of calling the real Google Calendar API.

## Problem & Success Criteria

**Current state:** A group wants recurring random 1:1 coffee chats, but manually pairing people and sending 25 calendar invites each week is tedious and error-prone.

**Desired state:** A weekly GitHub Action generates history-aware pairings, creates one mock calendar invite per pair, and commits the updated history/output back to GitHub.

- [x] ~50 active participants can be represented in version-controlled YAML.
- [x] A weekly scheduler can produce 25 1:1 pairings for 50 participants.
- [x] Pairings avoid historical repeats where possible.
- [x] Pairings are assigned to configured coffee slots spread across Tue/Wed/Thu.
- [x] Output is idempotent for a given week unless explicitly forced.
- [x] Calendar integration is mocked behind an adapter so the real Google API can be added later.

## Scope

**In:**
- YAML participant list with 50 mock email addresses.
- YAML schedule configuration.
- YAML history updated by the scheduler.
- Mock calendar invite JSON artifacts.
- GitHub Actions workflow with cron and manual dispatch.
- Tests for pairing, idempotency, history, slot assignment, and mock invite generation.

**Out:**
- Real Google Calendar API calls or credentials.
- Admin web UI.
- Reading participant availability/free-busy calendars.
- User authentication.
- Automatic reschedule workflow beyond Google Calendar attendee behaviour.

## Requirements

### FR1: Participant source
**Priority:** High
- [x] Participants are loaded from `config/participants.yaml`.
- [x] Inactive participants are ignored.
- [x] Duplicate active emails are rejected after lowercasing/trimming.
- [x] Invalid participant data fails fast.

### FR2: Weekly pairing generation
**Priority:** High
- [x] Even participant counts produce only 1:1 pairings.
- [x] For 50 active participants, exactly 25 pairings are generated.
- [x] No participant appears in more than one pairing in the same week.
- [x] Historical pairings are avoided where possible.
- [x] Odd participant counts produce one group of three rather than excluding someone.

### FR3: Scheduling slots
**Priority:** High
- [x] Slots are loaded from `config/schedule.yaml`.
- [x] Slots are spread across the configured days/times.
- [x] Each generated invite has a 15-minute duration.
- [x] Slot dates are calculated for the target ISO week in `Europe/London` by default.

### FR4: Calendar invite mock adapter
**Priority:** High
- [x] The scheduler creates one mock calendar invite per pairing.
- [x] Each invite contains exactly the paired participants, except the odd-number group-of-three case.
- [x] Each invite includes title, start/end, attendees, description, reschedule note, and mock event ID.
- [x] Mock events are written to `output/mock-calendar-events/<week>.json`.

### FR5: History and idempotency
**Priority:** High
- [x] A completed weekly run is appended to `data/history.yaml`.
- [x] If the same week already exists, the scheduler exits without creating duplicate events.
- [x] Manual `--force` can regenerate a week for development/testing.
- [x] The history records the deterministic random seed and generated event IDs.

### FR6: GitHub Actions operation
**Priority:** High
- [x] Workflow runs weekly on Monday morning.
- [x] Workflow can be run manually with `week_start`, `seed`, and `force` inputs.
- [x] Workflow commits changed history and mock outputs back to the repository.
- [x] Workflow runs tests before scheduling.

## Non-Functional Requirements

- **Simplicity:** No database or hosted app for MVP; repository files are the source of truth.
- **Auditability:** Participant config, history, and generated mock artifacts are version-controlled.
- **Safety:** The Google Calendar boundary is an adapter; real API credentials are not required for MVP.
- **Idempotency:** Default weekly runs must never double-book or duplicate history.
- **Maintainability:** Business logic is unit-tested and separated from CLI/file IO.

## Technical Architecture

- **Language:** Python 3.11.
- **Package management:** `uv` with `pyproject.toml`.
- **Config/history format:** YAML via PyYAML.
- **Scheduler:** GitHub Actions cron invoking `python -m random_coffee.cli`.
- **Calendar integration:** `MockCalendarClient` writes JSON fixtures now; later a `GoogleCalendarClient` can implement the same interface.

### Key Components

**CLI (`random_coffee.cli`):** Parses paths, week/seed/force options, runs the scheduler, and writes files.

**Config loader (`random_coffee.config`):** Loads and validates participants and scheduling configuration.

**Pairing engine (`random_coffee.pairing`):** Generates history-aware pairings using deterministic seeded retries.

**Scheduler (`random_coffee.scheduler`):** Orchestrates loading config, idempotency checks, pair generation, invite generation, and history update.

**Calendar adapter (`random_coffee.calendar_mock`):** Produces mock event payloads with stable event IDs.

**History store (`random_coffee.history`):** Reads/writes `data/history.yaml`, normalises pair keys, and exposes previous pairings.

## Data Model

### Participant

```yaml
email: person01@example.com
name: Person 01
active: true
```

### Schedule config

```yaml
timezone: Europe/London
meeting:
  duration_minutes: 15
  title_template: "Random Coffee: {names}"
  create_google_meet: true
slots:
  - day: Tuesday
    time: "10:00"
```

### History week

```yaml
weeks:
  - week_start: "2026-06-08"
    seed: 12345
    status: completed
    pairings:
      - participants: [person01@example.com, person02@example.com]
        calendar_event_id: mock_...
        scheduled_for: "2026-06-09T10:00:00+01:00"
```

## Rescheduling policy

The app schedules a default 15-minute slot for each pair. If the slot does not work, participants should use Google Calendar's “propose a new time” flow or message each other and move the coffee chat. The invite description explicitly says this.

## Open Questions for later

- Whether to switch from mock adapter to OAuth user account or Workspace service account.
- Whether a review-before-send mode is needed before real calendar writes.
- Whether participants should be synced from Google Groups/Workspace directory rather than YAML.
