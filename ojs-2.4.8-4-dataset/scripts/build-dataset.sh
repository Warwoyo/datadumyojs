#!/usr/bin/env bash
# Regenerate the synthetic baseline (files + database.sql), ground-truth, and
# scenario overlays from scripts/lib/generate.py.
#
# This is the agent-built equivalent of the panduan's "build via OJS UI then
# export-snapshot" flow, for labs that cannot run the legacy OJS 2.4.8-4 UI.
# Deterministic: same OJS_LAB_PASSWORD => identical files (the bcrypt hash in
# database.sql is salted and therefore varies).
#
# Usage:  OJS_LAB_PASSWORD='lab-pw' scripts/build-dataset.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${OJS_LAB_PASSWORD:=ojs248-lab-CHANGE-ME}"
export OJS_LAB_PASSWORD
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 1; }
command -v php >/dev/null || echo "WARN: php not found; password hash will be a sha1 placeholder" >&2
python3 "$HERE/lib/generate.py"
echo "[build] done. See ground-truth/ and scenarios/."
