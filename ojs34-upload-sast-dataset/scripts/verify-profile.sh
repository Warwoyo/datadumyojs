#!/usr/bin/env bash
# Verify a profile after apply (spesifikasi section 10).
# Filesystem + database + safety checks. Writes evidence/verify-<profile>-<ts>.json.
#
# Usage: APP_DIR=... FILES_DIR=... DB_NAME=... DB_USER=... DB_PASS=... \
#        scripts/verify-profile.sh <profile>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib/common.sh"
PROFILE="${1:?profile required}"
require_env

PASS=0 FAIL=0
ok()   { PASS=$((PASS+1)); log "PASS: $*"; }
bad()  { FAIL=$((FAIL+1)); log "FAIL: $*"; }

ORACLE="$PKG_DIR/oracle/upload-ground-truth.v1.json"

log "== 10.1 filesystem verification =="
# membership filter
mapfile -t IN_PROFILE < <(python3 -c "
import json,sys
o=json.load(open('$ORACLE'))
for f in o['fixtures']:
    if '$PROFILE' in f['profile_membership']:
        print(f['relative_path']+'|'+f['sha256'])
")
for line in "${IN_PROFILE[@]}"; do
  rel="${line%%|*}"; want="${line##*|}"
  fpath="$FILES_DIR/$rel"
  if [[ ! -f "$fpath" ]]; then bad "missing $rel"; continue; fi
  [[ -L "$fpath" ]] && bad "symlink fixture $rel"
  got="$(sha256sum "$fpath" | cut -d' ' -f1)"
  [[ "$got" == "$want" ]] && ok "hash $rel" || bad "hash mismatch $rel"
done

# uploads must never carry an executable extension (a normal instance has none)
if find "$FILES_DIR" -type f \( -name '*.php' -o -name '*.phtml' -o -name '*.php5' \
        -o -name '*.phar' -o -name '*.inc' -o -name '*.cgi' -o -name '*.pl' \
        -o -name '*.sh' -o -name '*.jsp' -o -iname '*.asp' \) 2>/dev/null | grep -q .; then
  bad "an executable-extension file is present under FILES_DIR"
else ok "no executable-extension uploads under FILES_DIR"; fi

# no +x on uploaded files
if find "$FILES_DIR" -type f -perm -u+x 2>/dev/null | grep -q .; then
  bad "executable bit set on an uploaded file"; else ok "no executable bit on uploads"; fi

log "== 10.2 database verification =="
if command -v mysql >/dev/null; then
  c() { mysql_cli -N -B "$DB_NAME" -e "$1" 2>/dev/null; }
  [[ "$(c "SELECT COUNT(*) FROM journals WHERE path='jist'")" == "1" ]] && ok "one jist journal" || bad "journal jist count != 1"
  [[ "$(c "SELECT COUNT(*) FROM issues WHERE published=1")" -ge 5 ]] && ok "published issues present" || bad "published issues < 5"
  [[ "$(c "SELECT COUNT(*) FROM submission_files")" -ge 40 ]] && ok "submission_files present" || bad "submission_files < 40"
  [[ "$(c "SELECT COUNT(*) FROM user_user_groups")" -ge 16 ]] && ok "users mapped to groups" || bad "user_user_groups < 16"
  # every galley must reference a real submission file (sane published catalogue)
  bad_galleys="$(c "SELECT COUNT(*) FROM publication_galleys g LEFT JOIN submission_files sf ON g.submission_file_id=sf.submission_file_id WHERE sf.submission_file_id IS NULL")"
  [[ "$bad_galleys" == "0" ]] && ok "all galleys reference real submission files" || bad "galley references a missing submission file"
else
  log "SKIP db checks (mysql client not available)"
fi

OUT="$PKG_DIR/evidence/verify-$PROFILE-$(date -u +%Y%m%dT%H%M%SZ).json"
cat > "$OUT" <<JSON
{ "profile": "$PROFILE", "pass": $PASS, "fail": $FAIL,
  "verdict": "$([[ $FAIL -eq 0 ]] && echo OK || echo FAILED)",
  "checked_at_utc": "$(date -u +%FT%TZ)" }
JSON
log "verification report: $OUT  (pass=$PASS fail=$FAIL)"
[[ $FAIL -eq 0 ]]
