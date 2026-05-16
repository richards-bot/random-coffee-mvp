# Template Workflow

This template is meant to bootstrap a **fresh** project workflow, not to ship an already-live tracker or spec history.

## What setup is expected to do

`./setup.sh <project-name>` should:

1. copy the template into a new directory
2. remove template-local `.git/`, `.beads/`, and `setup.sh`
3. initialize a brand new git repository
4. initialize a brand new Beads database and hooks
5. leave OpenSpec scaffold in place, ready for real artifacts

That distinction matters:

- **Beads in the template repo is not canonical project state**
- **OpenSpec in the template repo is scaffold, not a finished spec system**

## Intended delivery loop

### 1. Bootstrap

Run:

```bash
./setup.sh my-project
cd ~/my-project
```

Or manual setup:

```bash
git clone https://github.com/richpryce/claude-code-project-template.git my-project
cd my-project
rm -rf .git .beads setup.sh
git init
bd init
bd hooks install
```

### 2. Turn the idea into real artifacts

Inside Claude Code:

```text
/brain-dump
```

Expected outputs:

- `docs/SPEC.md` gets project-specific scope and acceptance criteria
- `docs/DECISIONS.md` records the first real decisions
- `openspec/project.md` gets project identity/context
- at least one real OpenSpec artifact appears under `openspec/changes/` or `openspec/specs/`
- beads issues are created with spec references in their notes

Until that happens, OpenSpec is only scaffold.

### 3. Execute work

Recommended loop:

1. `bd ready --json`
2. `/start-bead`
3. `/plan` for non-trivial work
4. implement one thin slice
5. `/checkpoint` at meaningful approval boundaries
6. `/complete-bead`

## Template self-audit checks

Before publishing changes to the template itself, run a quick leak/staleness audit.

Preferred:

```bash
./scripts/audit-template.sh
```

### Identity / stale tracker audit

```bash
grep -R "richard.pryce@guardian.co.uk\|Richard Pryce\|project-template-" -n . \
  --exclude-dir=.git \
  --exclude=template-workflow.md \
  --exclude=audit-template.sh
```

This should not return template-internal Beads history or personal identity leaks.

### Fresh setup smoke test

```bash
./setup.sh template-smoke-test
cd ~/template-smoke-test
bd list --json
```

Expected result: setup succeeds and `bd list --json` reports an empty fresh tracker.

### OpenSpec expectation check

After creating a sample artifact, validate the OpenSpec tree:

```bash
openspec validate --all
```

If there are no real specs/changes yet, that is normal for the template itself—but document that reality clearly.

## Publishing rule of thumb

If the template can leak prior issue history, personal metadata, or imply that placeholder scaffolding is already operational, it is not ready.
