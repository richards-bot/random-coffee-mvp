# Agent Instructions

See `CLAUDE.md` for project commands, structure, and workflow rules.

This repository uses **bd / Beads** for issue tracking. Do not create separate markdown TODO lists for work tracking.

## Required workflow

1. Check existing work:

   ```bash
   bd list --json
   bd ready --json
   ```

2. Create or claim a bead before changing files:

   ```bash
   bd create "Short task title" --description "Context" -p 1 --type task --json
   bd update <id> --status in_progress --json
   ```

3. Commit meaningful slices with the bead ID in the message:

   ```bash
   git commit -m "docs: update setup guide (<bead-id>)"
   ```

4. Run quality gates before handoff:

   ```bash
   uv run ruff check .
   uv run pytest -q
   ```

5. Close the bead and commit Beads state:

   ```bash
   bd close <id> --reason "Completed" --json
   bd vc commit -m "Close <task> bead"
   ```

6. Push completed work when a remote exists:

   ```bash
   git push
   git status --short --branch
   ```

## Security

Never commit Google credentials, service account JSON, OAuth refresh tokens, or real API keys. Use GitHub Secrets / protected environments for production credentials.
