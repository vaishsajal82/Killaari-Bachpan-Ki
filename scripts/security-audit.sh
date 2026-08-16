#!/usr/bin/env bash
# scripts/security-audit.sh — runs a dependency vulnerability scan against
# requirements.txt using pip-audit (queries the PyPA Advisory DB / OSV).
#
# Local usage (from the repo root):
#   ./scripts/security-audit.sh
#
# CI usage: see .github/workflows/security-audit.yml alongside this script
# — runs on every push/PR and fails the build (non-zero exit) if any
# vulnerability is found, so a newly-disclosed CVE in a pinned dependency
# blocks merges until reviewed/fixed rather than being discovered later.
#
# There's no frontend package.json in this project (the public site and
# admin portal are plain HTML/CSS/JS with no npm dependencies), so there's
# nothing for `npm audit` to scan — if that ever changes, add the
# equivalent `npm audit --audit-level=high` step here too.

set -uo pipefail
cd "$(dirname "$0")/.."

# Uses a throwaway local venv rather than installing pip-audit into
# whatever Python is already active — keeps this safe to run on machines
# where the system Python is externally-managed (PEP 668, e.g. modern
# Debian/Ubuntu) without needing --break-system-packages, and avoids
# polluting a developer's existing environment.
VENV_DIR=".security-audit-venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip "pip-audit==2.10.1"

echo "== Auditing kilkaari-backend/requirements.txt =="
# --ignore-vuln entries below are documented, deliberate exceptions, not
# blanket suppression — see the long comment in requirements.txt next to
# the `slowapi==0.1.9` line for the full reasoning. Summary: these are
# transitive deps of python-jose with no fix version compatible with
# python-jose's own pin (forcing one breaks `pip install -r
# requirements.txt` outright — verified), and this app's HS256-only JWT
# usage never exercises the vulnerable code path (RSA/EC key parsing).
# Every other finding still fails this script/CI normally — only these
# specific, reviewed IDs are excluded.
"$VENV_DIR/bin/pip-audit" -r kilkaari-backend/requirements.txt \
  --ignore-vuln PYSEC-2026-2263 \
  --ignore-vuln PYSEC-2026-3455 \
  --ignore-vuln PYSEC-2026-3456 \
  --ignore-vuln PYSEC-2026-3457 \
  --ignore-vuln PYSEC-2026-1325
STATUS=$?

rm -rf "$VENV_DIR"

if [ "$STATUS" -eq 0 ]; then
  echo "== No known vulnerabilities found =="
fi
exit "$STATUS"
