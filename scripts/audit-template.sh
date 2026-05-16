#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== identity / stale tracker audit =="
if grep -RIn "richard.pryce@guardian.co.uk\|Richard Pryce\|project-template-" . \
  --exclude-dir=.git \
  --exclude=template-workflow.md \
  --exclude=audit-template.sh; then
  echo
  echo "Audit failed: found stale template tracker or identity data."
  exit 1
else
  echo "OK: no stale tracker history or leaked identity markers found."
fi

echo
echo "== placeholder state check =="
if [ -d ./.beads ]; then
  echo "WARNING: template repo contains a .beads directory. Make sure that is intentional."
else
  echo "OK: template repo does not ship a live .beads directory."
fi

echo
echo "== openspec scaffold reminder =="
echo "OpenSpec in the template is scaffold-only until a real artifact is created under openspec/changes/ or openspec/specs/."
