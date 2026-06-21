#!/usr/bin/env bash
# Restore the canonical baseline snapshot to a lab OJS 2.4.8-4 target.
# DESTRUCTIVE: drops/recreates DB_NAME and rsync --delete on TARGET_FILES_DIR.
# (panduan section 11.2)
set -euo pipefail

: "${DATASET_ROOT:?Set DATASET_ROOT}"
: "${TARGET_FILES_DIR:?Set TARGET_FILES_DIR}"
: "${TARGET_PUBLIC_DIR:?Set TARGET_PUBLIC_DIR}"
: "${DB_NAME:?Set DB_NAME}"
: "${MYSQL_CMD:=mysql}"

BASE="$DATASET_ROOT/mysql"

test -f "$BASE/database.sql"
test -d "$BASE/files"
test -d "$BASE/public"

# Guardrail: never rsync --delete onto '/', a home, or an empty path.
case "$(readlink -f "$TARGET_FILES_DIR")" in
  ""|"/"|"$HOME") echo "Refusing unsafe TARGET_FILES_DIR" >&2; exit 1 ;;
esac

printf 'Restoring database into %s ...\n' "$DB_NAME"
"$MYSQL_CMD" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8 COLLATE utf8_general_ci;"
"$MYSQL_CMD" "$DB_NAME" < "$BASE/database.sql"

printf 'Restoring private files_dir...\n'
mkdir -p "$TARGET_FILES_DIR"
rsync -aHAX --delete "$BASE/files/" "$TARGET_FILES_DIR/"

printf 'Restoring public files...\n'
mkdir -p "$TARGET_PUBLIC_DIR"
rsync -aHAX --delete "$BASE/public/" "$TARGET_PUBLIC_DIR/"

printf 'Baseline restore complete.\n'
