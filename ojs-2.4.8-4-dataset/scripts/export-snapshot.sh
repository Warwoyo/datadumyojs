#!/usr/bin/env bash
# Export a baseline snapshot FROM a live, UI-built OJS 2.4.8-4 lab install into
# this dataset layout (panduan section 8). Use this when you build the baseline
# the canonical way (through the OJS UI) instead of the synthetic generator.
#
# Required env:
#   APP_ROOT      OJS application root (source; NOT copied into the dataset)
#   FILES_DIR     live private files_dir
#   DB_NAME       database to dump
# Optional:
#   DB_USER, MYSQLDUMP_CMD (default mysqldump)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASET_ROOT="$(cd "$HERE/.." && pwd)"

: "${APP_ROOT:?Set APP_ROOT}"
: "${FILES_DIR:?Set FILES_DIR}"
: "${DB_NAME:?Set DB_NAME}"
: "${MYSQLDUMP_CMD:=mysqldump}"

mkdir -p "$DATASET_ROOT"/mysql/{files,public}

echo "[1/4] dumping database $DB_NAME ..."
"$MYSQLDUMP_CMD" --single-transaction --routines --triggers --events \
  --default-character-set=utf8 ${DB_USER:+-u "$DB_USER"} "$DB_NAME" \
  > "$DATASET_ROOT/mysql/database.sql"
test -s "$DATASET_ROOT/mysql/database.sql"
grep -q "CREATE TABLE" "$DATASET_ROOT/mysql/database.sql"

echo "[2/4] copying private files_dir ..."
rsync -aHAX --delete "$FILES_DIR/" "$DATASET_ROOT/mysql/files/"

echo "[3/4] copying public assets ..."
rsync -aHAX --delete "$APP_ROOT/public/" "$DATASET_ROOT/mysql/public/"

echo "[4/4] sanitizing config + manifests ..."
if [ -f "$APP_ROOT/config.inc.php" ]; then
  sed -E 's#^(files_dir = ).*#\1"__DATASET_FILES_DIR__"#' \
      "$APP_ROOT/config.inc.php" > "$DATASET_ROOT/mysql/config.inc.php"
fi
python3 "$HERE/generate-manifest.py"
echo "Snapshot exported to $DATASET_ROOT/mysql (remember: review config.inc.php for secrets)."
