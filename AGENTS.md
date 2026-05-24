# Agent Instructions

See [CLAUDE.md](CLAUDE.md) for all agent instructions.
See [.claude/rules/](./claude/rules/) for coding style, security, testing, and behavior rules.

This file exists for compatibility with tools that look for AGENTS.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. If a remote branch is part of the workflow, do not call the work complete while it only exists locally.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - Required when a remote/branch workflow exists:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- If a remote exists for the branch, work is not complete until local changes are published or there is an explicit reason not to publish them yet
- Do not leave important work stranded locally without saying so clearly
- Avoid "ready to push when you are" handoffs when the workflow expects the agent to publish changes
- If push fails in a repo that expects remote publication, resolve and retry or explain the blocker explicitly
