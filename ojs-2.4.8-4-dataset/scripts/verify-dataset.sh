#!/usr/bin/env bash
# Verify dataset consistency (panduan section 12).
# Two modes:
#   (a) offline (default): verify file tree, hashes, and oracle vs files/.
#   (b) with DB checks: set DB_NAME (+ MYSQL_CMD) to also run DB count/linkage
#       queries against a restored target.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

PASS=0; FAIL=0
ok(){ PASS=$((PASS+1)); echo "PASS: $*"; }
bad(){ FAIL=$((FAIL+1)); echo "FAIL: $*"; }

# 12.1 structure
for d in mysql/files/journals/1/articles mysql/files/journals/1/issues mysql/public/journals/1; do
  [ -d "$d" ] && ok "structure $d" || bad "missing $d"
done

# 13.1 baseline hashes match recorded manifest
if [ -f ground-truth/sha256sums-baseline.txt ]; then
  if ( cd mysql/files && sha256sum -c --quiet "$ROOT/ground-truth/sha256sums-baseline.txt" ) 2>/dev/null; then
    ok "baseline sha256sums verified"
  else bad "baseline hash mismatch (sha256sums-baseline.txt)"; fi
fi

# oracle baseline negatives must exist on disk with matching hash
python3 - <<'PY' && ok "oracle baseline files present & hashes match" || bad "oracle/file mismatch"
import csv, hashlib, sys, os
bad=0
for r in csv.DictReader(open("ground-truth/file-inventory.csv")):
    p=os.path.join("mysql/files", r["relative_path"])
    if not os.path.isfile(p): print("  missing",p); bad+=1; continue
    if hashlib.sha256(open(p,'rb').read()).hexdigest()!=r["sha256"]:
        print("  hash mismatch",p); bad+=1
sys.exit(1 if bad else 0)
PY

# baseline must NOT contain any scenario positive artifact
if find mysql/files -name '*.phtml' -o -name '*.phar' -o -name '*.jsp' -o -name '*.exe' 2>/dev/null | grep -q .; then
  bad "baseline contains a risky-extension artifact (should only be in compromised overlay)"
else ok "baseline free of scenario positive artifacts"; fi

# overlay artifacts inert
if grep -rIlE '<\?php|<\?=|<script|eval\(|shell_exec|passthru' scenarios/*/overlay-files 2>/dev/null | grep -q .; then
  bad "overlay artifact contains active content"
else ok "all overlay artifacts inert"; fi

# optional DB checks
if [ -n "${DB_NAME:-}" ]; then
  MYSQL_CMD="${MYSQL_CMD:-mysql}"
  c(){ $MYSQL_CMD -N -B "$DB_NAME" -e "$1" 2>/dev/null; }
  [ "$(c "SELECT COUNT(*) FROM journals WHERE path='jdis'")" = "1" ] && ok "one jdis journal" || bad "journal jdis != 1"
  [ "$(c "SELECT COUNT(*) FROM articles")" -ge 8 ] && ok ">=8 articles" || bad "articles < 8"
  [ "$(c "SELECT COUNT(*) FROM published_articles")" -ge 1 ] && ok "published article present" || bad "no published article"
  # every article_files row exists on disk
  python3 - "$MYSQL_CMD" "$DB_NAME" <<'PY' && ok "DB article_files all present on disk" || bad "DB/file mismatch"
import subprocess,sys,os
cmd,db=sys.argv[1],sys.argv[2]
ST={"1":"submission/original","2":"submission/review","3":"submission/editor","4":"submission/copyedit","5":"submission/layout","6":"public","7":"supp","8":"note","9":"attachment"}
rows=subprocess.run(cmd.split()+["-N","-B",db,"-e","SELECT article_id,file_name,file_stage FROM article_files"],capture_output=True,text=True).stdout.strip().splitlines()
bad=0
for r in rows:
    aid,fn,st=r.split("\t")
    p=f"mysql/files/journals/1/articles/{aid}/{ST[st]}/{fn}"
    if not os.path.isfile(p): print("  missing",p); bad+=1
sys.exit(1 if bad else 0)
PY
fi

echo "---- verify: pass=$PASS fail=$FAIL ----"
[ "$FAIL" -eq 0 ]
