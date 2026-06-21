#!/usr/bin/env bash
# Apply a dataset profile to a lab OJS 3.3.0-13 target.
# DESTRUCTIVE to the target DB and FILES_DIR. Always backs up first, runs the
# preflight safety gate, and is idempotent (re-running yields the same state).
#
# Usage:
#   APP_DIR=/var/www/ojs-330 FILES_DIR=/var/ojs-files DB_NAME=ojs \
#   DB_USER=ojs DB_PASS=secret scripts/apply-profile.sh <full-instance|core-published>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/lib/common.sh"

PROFILE="${1:?profile required: full-instance|core-published}"
[[ -f "$PKG_DIR/profiles/$PROFILE.yaml" ]] || die "unknown profile: $PROFILE"

require_env
assert_containment                                   # spesifikasi 2.3 fail-closed gate

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BK="$PKG_DIR/evidence/backup-$TS"
mkdir -p "$BK"

log "== Phase 0: backup current target state =="
mysqldump --no-tablespaces -h "$DB_HOST" -u "$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" > "$BK/database.sql" \
  || die "db backup failed"
tar -C "$FILES_DIR" -czf "$BK/files.tar.gz" . || die "files backup failed"
cat > "$PKG_DIR/evidence/backup-manifest-$TS.json" <<JSON
{
  "backup_id": "$TS",
  "profile_applied": "$PROFILE",
  "db_name": "$DB_NAME",
  "files_dir": "$(canon "$FILES_DIR")",
  "db_backup": "$(canon "$BK/database.sql")",
  "files_backup": "$(canon "$BK/files.tar.gz")",
  "db_backup_sha256": "$(sha256sum "$BK/database.sql" | cut -d' ' -f1)",
  "files_backup_sha256": "$(sha256sum "$BK/files.tar.gz" | cut -d' ' -f1)",
  "created_at_utc": "$(date -u +%FT%TZ)"
}
JSON
log "backup written: $BK (backup_id=$TS)"

log "== Phase 1: restore database snapshot =="
mysql_cli "$DB_NAME" < "$PKG_DIR/mysql/database.sql" || die "db restore failed"

log "== Phase 2: clear FILES_DIR and sync snapshot files =="
safe_clear_dir "$FILES_DIR"
# Copy the full files/ tree (the inventory covers every file; profile selection
# is logical and applied at verify time). The full instance is always restored.
tar -C "$PKG_DIR/files" --exclude=CHECKSUMS.sha256 -cf - journals \
  | tar -C "$FILES_DIR" -xf -

# Optional ownership fix-up for the PHP-FPM/OJS user (spesifikasi 9.2 step 8).
if [[ -n "${OJS_OWNER:-}" ]]; then
  chown -R "$OJS_OWNER" "$FILES_DIR"
  log "ownership set to $OJS_OWNER"
fi
find "$FILES_DIR" -type d -exec chmod 750 {} +
find "$FILES_DIR" -type f -exec chmod 640 {} +   # readable, never +x

# Clear rebuildable OJS cache if present (never touches source).
[[ -d "$APP_DIR/cache" ]] && find "$APP_DIR/cache" -maxdepth 1 -name '*.php' -delete 2>/dev/null || true

log "applied profile '$PROFILE'. backup_id=$TS"
log "next: scripts/verify-profile.sh $PROFILE"
