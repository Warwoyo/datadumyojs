#!/usr/bin/env bash
# Restore the target from a backup created by apply-profile.sh (spesifikasi 9.4).
#
# Usage:
#   APP_DIR=... FILES_DIR=... DB_NAME=... DB_USER=... DB_PASS=... \
#   scripts/rollback.sh <backup_id>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib/common.sh"
require_env

BID="${1:?backup_id required (e.g. 20260621T101500Z)}"
MAN="$PKG_DIR/evidence/backup-manifest-$BID.json"
BK="$PKG_DIR/evidence/backup-$BID"
[[ -f "$MAN" ]] || die "no backup manifest for id $BID"
[[ -f "$BK/database.sql" && -f "$BK/files.tar.gz" ]] || die "backup artifacts missing for $BID"

# integrity check before restoring
want_db="$(python3 -c "import json;print(json.load(open('$MAN'))['db_backup_sha256'])")"
got_db="$(sha256sum "$BK/database.sql" | cut -d' ' -f1)"
[[ "$want_db" == "$got_db" ]] || die "db backup checksum mismatch; aborting rollback"

log "restoring database from backup $BID"
mysql_cli "$DB_NAME" < "$BK/database.sql" || die "db rollback failed"

log "restoring FILES_DIR from backup $BID"
assert_containment
safe_clear_dir "$FILES_DIR"
tar -C "$FILES_DIR" -xzf "$BK/files.tar.gz"

RES="$PKG_DIR/evidence/rollback-$BID-$(date -u +%Y%m%dT%H%M%SZ).json"
cat > "$RES" <<JSON
{ "backup_id": "$BID", "result": "success",
  "restored_at_utc": "$(date -u +%FT%TZ)" }
JSON
log "rollback OK; report: $RES"
