# Google Calendar production integration

This document describes the production-grade strategy for turning the current mock calendar MVP into a real Google Calendar invite sender.

The recommended production approach is **Google Workspace service account authentication with domain-wide delegation**, impersonating a dedicated organiser account such as `random-coffee@example.com`.

Do **not** commit Google credentials to this repository. Store credentials only in GitHub Actions secrets or a protected GitHub Actions environment.

---

## Current MVP status

The application already does the non-Google scheduling work:

- Loads participants from `config/participants.yaml`.
- Loads coffee slots from `config/schedule.yaml`.
- Generates 1:1 pairings for even participant counts.
- Creates one group of three for odd participant counts.
- Avoids historical repeat pairings where possible.
- Skips already-completed weeks unless forced.
- Writes pairing history to `data/history.yaml`.
- Writes mock event JSON to `output/mock-calendar-events/<week>.json`.
- Runs weekly through GitHub Actions.

The missing production piece is replacing `MockCalendarClient` with a real Google Calendar adapter.

---

## Production architecture

### Recommended identity model

Use a dedicated Google Workspace organiser account:

```text
random-coffee@example.com
```

The scheduler should create all calendar events while impersonating this account.

Benefits:

- Events are not owned by an individual employee.
- Credential rotation does not require changing human accounts.
- Calendar history is auditable in one place.
- The app can keep working if the maintainer changes.

### Recommended auth model

Use:

```text
Service account + domain-wide delegation + organiser account impersonation
```

Avoid OAuth refresh tokens for production. They work for prototypes but are easier to revoke accidentally and are less suitable for unattended GitHub Actions automation.

### Runtime flow

1. GitHub Action runs on Monday morning or manual dispatch.
2. Tests run first.
3. Scheduler loads YAML config/history.
4. Scheduler generates pairings and slots.
5. `GoogleCalendarClient` authenticates using the service account JSON from GitHub Secrets.
6. Client impersonates `random-coffee@example.com`.
7. Client creates one Google Calendar event per pairing.
8. Google sends invites to attendees via `sendUpdates=all`.
9. Scheduler records real event IDs and links in `data/history.yaml`.
10. GitHub Action commits updated history back to the repository.

---

## Google Workspace setup

These steps usually require a Google Workspace admin.

### 1. Create the organiser account

Create or nominate an account such as:

```text
random-coffee@example.com
```

This account should have Calendar enabled. If Google Meet links are required, it must also be allowed to create Meet conferences under your Workspace policy.

### 2. Create/select a Google Cloud project

Use Google Cloud Console:

```text
https://console.cloud.google.com/
```

Suggested project name:

```text
random-coffee-scheduler
```

### 3. Enable the Calendar API

In the project, enable:

```text
Google Calendar API
```

API Library:

```text
https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
```

### 4. Create a service account

Create a service account, for example:

```text
random-coffee-scheduler
```

Suggested service account ID:

```text
random-coffee-scheduler@<project-id>.iam.gserviceaccount.com
```

No broad project IAM role should be required for Calendar API impersonation beyond the service account existing and having domain-wide delegation authorised.

### 5. Enable domain-wide delegation

In the service account settings:

1. Open the service account.
2. Enable **Domain-wide delegation**.
3. Record the service account **OAuth 2 Client ID**.

The Client ID is required in the Workspace Admin Console.

### 6. Authorise the service account in Workspace Admin

In Google Admin Console:

```text
Security → Access and data control → API controls → Domain-wide delegation
```

Add a new API client:

- **Client ID:** the service account OAuth 2 Client ID.
- **OAuth scopes:**

```text
https://www.googleapis.com/auth/calendar.events
```

Start with the narrow `calendar.events` scope. Use the broader Calendar scope only if a later feature truly needs it:

```text
https://www.googleapis.com/auth/calendar
```

### 7. Create a service account key

Create a JSON key for the service account. Download it once, then store it as a GitHub secret. Do not commit it.

If your organisation blocks service account keys, use Workload Identity Federation instead. That is more secure but more setup-heavy. The application design should still use the same `GoogleCalendarClient` boundary.

---

## GitHub setup

Use GitHub repository or environment secrets. For production, prefer a protected environment such as:

```text
production-calendar
```

Required secrets:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_IMPERSONATE_USER
GOOGLE_CALENDAR_ID
```

Recommended values:

```text
GOOGLE_SERVICE_ACCOUNT_JSON = full service account JSON key
GOOGLE_IMPERSONATE_USER = random-coffee@example.com
GOOGLE_CALENDAR_ID = primary
```

Optional variables/secrets:

```text
GOOGLE_SEND_UPDATES = all
GOOGLE_CREATE_MEET = true
RANDOM_COFFEE_CALENDAR_PROVIDER = google
```

For the first few live runs, configure the GitHub environment to require manual approval. Once trusted, remove manual approval if fully automatic operation is desired.

---

## Code changes required

### 1. Add Google dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
  "PyYAML>=6.0.2",
  "google-api-python-client>=2.150.0",
  "google-auth>=2.35.0",
]
```

Then update the lockfile:

```bash
uv lock
```

### 2. Add a provider option

The CLI should support:

```bash
uv run python -m random_coffee.cli --calendar-provider mock
uv run python -m random_coffee.cli --calendar-provider google
```

Recommended default:

```text
mock
```

That keeps local development and PR checks safe.

### 3. Introduce a common calendar adapter boundary

Define a common return type with fields such as:

```python
@dataclass(frozen=True)
class CalendarEventResult:
    event_id: str
    html_link: str | None
    summary: str
    start: datetime
    end: datetime
    attendees: tuple[str, ...]
```

Both `MockCalendarClient` and `GoogleCalendarClient` should return this shape.

### 4. Implement `GoogleCalendarClient`

Create:

```text
src/random_coffee/calendar_google.py
```

Responsibilities:

- Read credentials from environment.
- Parse `GOOGLE_SERVICE_ACCOUNT_JSON` as JSON.
- Build delegated credentials with the Calendar scope.
- Impersonate `GOOGLE_IMPERSONATE_USER`.
- Create Calendar API service.
- Insert events into `GOOGLE_CALENDAR_ID`.
- Send invite updates.
- Return real `event.id` and `event.htmlLink`.

Expected auth shape:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES,
).with_subject(impersonated_user)

service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
```

### 5. Build real event payloads

Each pairing should create one event body:

```python
event_body = {
    "id": stable_google_event_id,
    "summary": summary,
    "description": description,
    "start": {
        "dateTime": slot.start.isoformat(),
        "timeZone": schedule.timezone,
    },
    "end": {
        "dateTime": slot.end.isoformat(),
        "timeZone": schedule.timezone,
    },
    "attendees": [{"email": email} for email in pairing.participants],
}
```

If Google Meet links are enabled:

```python
event_body["conferenceData"] = {
    "createRequest": {
        "requestId": stable_conference_request_id,
    }
}
```

Insert using:

```python
service.events().insert(
    calendarId=calendar_id,
    body=event_body,
    sendUpdates="all",
    conferenceDataVersion=1,
).execute()
```

Use `conferenceDataVersion=1` only when Meet creation is enabled, or always pass it harmlessly if the adapter centralises event creation.

### 6. Use deterministic Google event IDs

To make retries safe, generate stable event IDs from:

```text
week_start + sorted participant emails
```

Google Calendar event IDs have constraints. They must use allowed lowercase characters, digits, underscores, and hyphens, and must be unique in a calendar. A safe strategy:

```text
rc-<week-start-without-dashes>-<sha256-of-participants>[:20]
```

Example:

```text
rc-20260608-a1b2c3d4e5f6a7b8c9d0
```

This prevents duplicate event creation if GitHub Actions retries after a partial failure.

### 7. Handle duplicate/conflict responses

If Google returns a conflict because the deterministic event ID already exists:

1. Fetch the existing event by ID.
2. Treat it as success.
3. Record its ID/link in history.

This is essential for safe reruns after partial failures.

### 8. Record real event metadata in history

Extend history entries from:

```yaml
calendar_event_id: mock_...
scheduled_for: "2026-06-09T10:00:00+01:00"
```

to:

```yaml
calendar_event_id: rc-20260608-a1b2...
calendar_event_link: https://www.google.com/calendar/event?eid=...
scheduled_for: "2026-06-09T10:00:00+01:00"
status: created
provider: google
```

For failures:

```yaml
status: failed
error: "Google Calendar API error details"
```

### 9. Handle partial failures deliberately

Production behaviour should be:

- Try to create all events.
- Record success/failure per pairing.
- Exit non-zero if any event failed.
- Preserve enough metadata for a rerun to continue safely.
- Never create duplicates on rerun.

The combination of deterministic event IDs and conflict recovery is what makes this safe.

---

## GitHub Actions changes required

Add environment/secrets to the live scheduling job:

```yaml
environment: production-calendar

env:
  RANDOM_COFFEE_CALENDAR_PROVIDER: google
  GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
  GOOGLE_IMPERSONATE_USER: ${{ secrets.GOOGLE_IMPERSONATE_USER }}
  GOOGLE_CALENDAR_ID: ${{ secrets.GOOGLE_CALENDAR_ID }}
```

Change scheduler command to:

```bash
uv run python -m random_coffee.cli --calendar-provider google "${ARGS[@]}"
```

Keep tests running before the real calendar step.

For first rollout, use manual `workflow_dispatch` and a protected environment requiring approval. After successful test runs, enable the cron path for real sends.

---

## Rollout plan

### Phase 1: Unit-tested adapter, no live sends

- Add Google adapter code.
- Test with fake Google service objects.
- Keep GitHub Action in mock mode.

### Phase 2: Test calendar and test users

- Create a separate test calendar or use a staging organiser account.
- Replace participant list with 4-6 internal test accounts.
- Run manual workflow dispatch with provider `google`.
- Verify invites arrive.
- Verify event links and Meet links.
- Verify proposed-time rescheduling is available.
- Rerun the same week and verify no duplicate events.

### Phase 3: Production dry run

- Use production organiser account.
- Use real participant list.
- Keep environment manual approval enabled.
- Run with a future test week if needed.
- Confirm all expected events were created.

### Phase 4: Automatic weekly operation

- Enable/keep cron.
- Remove manual environment approval if desired.
- Monitor first 2-3 automatic runs.

---

## Operational runbook

### Normal weekly run

The GitHub Action runs every Monday. It should:

1. Pass tests.
2. Create events.
3. Commit updated `data/history.yaml`.
4. Exit successfully.

### Manual run

Use GitHub Actions → Weekly Random Coffee → Run workflow.

Inputs:

- `week_start`: Monday date, e.g. `2026-06-08`.
- `seed`: optional deterministic seed.
- `force`: only for deliberate regeneration.

### If a run partially fails

1. Inspect GitHub Actions logs.
2. Inspect `data/history.yaml` if it was committed.
3. Fix the root cause, such as invalid email or Workspace permission.
4. Rerun the workflow for the same `week_start`.
5. Deterministic event IDs should prevent duplicate event creation.

### If wrong invites are created

1. Disable the workflow temporarily.
2. Use the organiser calendar to inspect created events.
3. If needed, delete the affected Google Calendar events manually.
4. Remove or correct the affected week in `data/history.yaml` through a reviewed PR.
5. Rerun with a known seed.

### Credential rotation

1. Create a new service account key or switch to Workload Identity Federation.
2. Update `GOOGLE_SERVICE_ACCOUNT_JSON` in GitHub Secrets.
3. Run a staging/test dispatch.
4. Delete the old key in Google Cloud.

---

## Security checklist

- [ ] No service account JSON committed to git.
- [ ] GitHub repo uses secrets/environment secrets for credentials.
- [ ] Service account uses only the required Calendar scope.
- [ ] Domain-wide delegation is limited to Calendar events unless broader scope is justified.
- [ ] Organiser account is dedicated to this automation.
- [ ] Real calendar workflow uses a protected GitHub environment during rollout.
- [ ] Logs do not print service account JSON, access tokens, or full credential payloads.
- [ ] Public repository remains safe because secrets live only in GitHub Secrets.

---

## Acceptance criteria for “production ready”

- [ ] `GoogleCalendarClient` creates real events with attendees.
- [ ] Invites are emailed with `sendUpdates=all`.
- [ ] Meet links are created when enabled.
- [ ] History records real event IDs and links.
- [ ] Reruns do not duplicate events.
- [ ] Partial failures are visible and recoverable.
- [ ] Tests cover event body construction and duplicate/conflict handling.
- [ ] GitHub Actions can run in mock and google modes.
- [ ] Production credentials are stored only in GitHub Secrets.
- [ ] First live run with test users has been verified.
