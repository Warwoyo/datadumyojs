#!/usr/bin/env bash
# Overlay a scenario profile onto an already-restored baseline (panduan 11.3).
# MUST be run only after restore-baseline.sh succeeded.
set -euo pipefail

: "${DATASET_ROOT:?Set DATASET_ROOT}"
: "${TARGET_FILES_DIR:?Set TARGET_FILES_DIR}"
: "${1:?Usage: apply-profile.sh <clean|controller|compromised>}"

PROFILE="$1"
OVERLAY="$DATASET_ROOT/scenarios/$PROFILE/overlay-files"
PROFILE_META="$DATASET_ROOT/scenarios/$PROFILE/profile.yaml"

test -f "$PROFILE_META"

# Safety: overlay must stay within TARGET_FILES_DIR (no path escape).
if [ -d "$OVERLAY" ]; then
  rsync -aHAX "$OVERLAY/" "$TARGET_FILES_DIR/"
fi

printf 'Profile applied: %s\n' "$PROFILE"
