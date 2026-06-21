#!/usr/bin/env bash
# Build the dataset package from fixtures/fixture-spec.json (single source of truth).
# Renders benign uploaded files, computes SHA-256 hashes, and emits oracle/,
# mysql/database.sql, files/CHECKSUMS.sha256, and the manifest integrity block.
#
# Reproducible: same spec + same OJS_LAB_PASSWORD => identical files/ hashes.
# (The bcrypt password hash in database.sql is salted and therefore varies; it
#  is excluded from files_tree_sha256.)
#
# Usage:  OJS_LAB_PASSWORD='your-lab-pw' scripts/build-dataset.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$(cd "$HERE/.." && pwd)"

: "${OJS_LAB_PASSWORD:=ojs-lab-CHANGE-ME}"
export OJS_LAB_PASSWORD

command -v python3 >/dev/null || { echo "python3 required" >&2; exit 1; }
command -v php >/dev/null || echo "WARN: php not found; user password hash will be a placeholder" >&2

echo "[build] rendering dataset from spec ..."
python3 "$HERE/lib/generate.py"

# Stitch the generated integrity block into dataset-manifest.yaml.
MANIFEST="$PKG/dataset-manifest.yaml"
GEN="$HERE/lib/_integrity.generated.yaml"
if [[ -f "$MANIFEST" && -f "$GEN" ]]; then
  python3 - "$MANIFEST" "$GEN" <<'PY'
import sys, re, pathlib
manifest, gen = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
text = manifest.read_text()
block = gen.read_text()
# Replace everything from the first "# AUTO-GENERATED" marker to EOF.
marker = "# AUTO-GENERATED integrity block"
idx = text.find(marker)
if idx != -1:
    text = text[:idx]
text = text.rstrip() + "\n" + block
manifest.write_text(text)
print("[build] manifest integrity block updated")
PY
fi

echo "[build] done."
