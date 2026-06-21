#!/usr/bin/env bash
# Shared helpers for apply/verify/collect/rollback. Sourced, not executed.
# Reads the lab environment contract from spesifikasi section 2.1.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()  { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
die()  { printf 'FATAL: %s\n' "$*" >&2; exit 1; }

# ---- required environment (see spesifikasi 2.1) ----------------------------
require_env() {
  : "${APP_DIR:?APP_DIR required}"
  : "${FILES_DIR:?FILES_DIR required}"
  : "${DB_NAME:?DB_NAME required}"
  : "${DB_HOST:=localhost}"
  : "${DB_USER:?DB_USER required}"
  : "${DB_PASS:=}"
  export APP_DIR FILES_DIR DB_NAME DB_HOST DB_USER DB_PASS
}

mysql_cli() { mysql -h "$DB_HOST" -u "$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$@"; }

canon() { realpath -m "$1"; }

# ---- non-negotiable safety gate (spesifikasi 2.3) --------------------------
# FILES_DIR must be OUTSIDE APP_DIR, not a symlink into web root, and APP_DIR/public
# must not be the fixture store. Fail closed.
assert_containment() {
  require_env
  local app files pub
  app="$(canon "$APP_DIR")"
  files="$(canon "$FILES_DIR")"
  pub="$(canon "$APP_DIR/public")"

  case "$files/" in
    "$app"/*) die "FILES_DIR ($files) is INSIDE APP_DIR ($app). Refusing (fail closed)." ;;
  esac
  if [[ -L "$FILES_DIR" ]]; then
    local tgt; tgt="$(canon "$(readlink "$FILES_DIR")")"
    case "$tgt/" in "$app"/*) die "FILES_DIR is a symlink into APP_DIR. Refusing." ;; esac
  fi
  case "$files/" in
    "$pub"/*) die "FILES_DIR is under APP_DIR/public (web root). Refusing." ;;
  esac
  log "containment OK: FILES_DIR is outside APP_DIR and web root."
}

# Refuse rm on un-normalized / suspicious paths.
safe_clear_dir() {
  local target; target="$(canon "$1")"
  [[ -n "$target" && "$target" != "/" ]] || die "refusing to clear '$target'"
  case "$target" in /|/usr|/etc|/var|/home|/root|"$HOME") die "refusing to clear protected path '$target'";; esac
  [[ -d "$target" ]] || die "not a directory: $target"
  log "clearing contents of $target"
  find "$target" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
}
