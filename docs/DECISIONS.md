# Architecture Decisions

## 2026-06-07: Repository-native MVP

**Decision:** Use a GitHub repository as the source of truth for MVP state: YAML participant config, YAML scheduling config, YAML history, and JSON mock calendar output.

**Rationale:** Ricky asked for a GitHub Action scheduler, YAML email list, GitHub-hosted history, and no real Google API key yet. This avoids databases/hosting while preserving auditability and easy review.

**Consequences:**
- GitHub Actions needs write permissions to commit history/output.
- YAML history will eventually become awkward if the tool grows, but is appropriate for MVP.

## 2026-06-07: Spread meetings across configured slots

**Decision:** Assign pairings to a small configured set of Tue/Wed/Thu coffee slots rather than one global meeting time.

**Rationale:** Spreading slots reduces clashes. Participants can reschedule the calendar invite if their assigned slot does not work.

**Consequences:**
- The app does not need invasive free/busy calendar permissions.
- Some people may still need to use Google Calendar's “propose new time” flow.

## 2026-06-07: Mock calendar adapter first

**Decision:** Implement calendar creation behind a mock adapter that writes event payloads to JSON files.

**Rationale:** The MVP should prove scheduling, pair generation, idempotency, and GitHub Actions behaviour without requiring Google credentials.

**Consequences:**
- Real Google Calendar integration can be added later by implementing the same adapter boundary.

## 2026-06-07: Production Google Calendar auth strategy

**Decision:** Use a Google Workspace service account with domain-wide delegation, impersonating a dedicated organiser account such as `random-coffee@example.com`, for production Calendar event creation.

**Rationale:** This is the best fit for unattended GitHub Actions automation in a Workspace organisation. It avoids long-lived user refresh tokens, avoids tying event ownership to a human account, and lets Workspace admins constrain the app to Calendar event scopes.

**Consequences:**
- Workspace admin setup is required.
- Credentials must be stored in GitHub Secrets or a protected GitHub Actions environment, never in git.
- The real Google adapter must use deterministic event IDs and conflict recovery to make reruns safe after partial failures.
