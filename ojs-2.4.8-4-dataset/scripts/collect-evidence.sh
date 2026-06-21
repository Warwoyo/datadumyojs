#!/usr/bin/env bash
# Create a timestamped evidence directory for one scan run (panduan 13.3) and
# capture environment, profile, pre-scan hashes, and the scanner command.
# The scanner itself is run by the operator; this script wires the evidence
# folder and (optionally) records the raw result you pass in.
#
# Usage:
#   PROFILE=compromised TARGET_FILES_DIR=/var/lib/ojs-248-files \
#   [SCAN_RESULT=/path/to/scanner-result.json] [SCANNER_CMD="mytool ..."] \
#   scripts/collect-evidence.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

: "${PROFILE:?Set PROFILE=clean|controller|compromised}"
: "${TARGET_FILES_DIR:?Set TARGET_FILES_DIR}"

RUN="$ROOT/evidence/$(date -u +%Y-%m-%dT%H%M%SZ)-${PROFILE}-run"
mkdir -p "$RUN"

{
  echo "date_utc=$(date -u +%FT%TZ)"
  echo "uname=$(uname -a)"
  echo "target_files_dir=$(readlink -f "$TARGET_FILES_DIR")"
} > "$RUN/environment.txt"
echo "$PROFILE" > "$RUN/profile.txt"
( cd "$TARGET_FILES_DIR" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) \
  > "$RUN/hash-before.txt" 2>/dev/null || true
echo "${SCANNER_CMD:-<record the exact scanner command here>}" > "$RUN/scanner-command.txt"
cp "$ROOT/ground-truth/upload-oracle.csv" "$RUN/oracle-snapshot.csv"
if [ -n "${SCAN_RESULT:-}" ] && [ -f "$SCAN_RESULT" ]; then
  cp "$SCAN_RESULT" "$RUN/scanner-result.json"
fi
echo "Evidence dir ready: $RUN"
echo "Next: run scanner -> save scanner-result.json/stdout/stderr here -> build comparison-result.csv (do NOT edit the oracle)."
