# OJS 2.4.8-4 Upload-Directory SAST Dataset (`ojs-2.4.8-4-upload-lab-v1`)

A deterministic, resettable **baseline + overlay** dataset for evaluating an
SAST *uploaded-directory scanner* against legacy **OJS 2.4.8-4**. It follows
`pkp/datasets` layout (`database.sql` + `files/` + `public/` + `config.inc.php`)
and adds a research layer (ground-truth oracle, scenario overlays, scripts,
evidence) per `panduan_dataset_dummy_ojs_2_4_8_4_sast_upload.md`.

> ⚠️ **Inert by design.** Every "compromised" artifact is plain text with only a
> risky **name / extension / location**. No PHP, no server-side tags, no
> executable code, no payloads, no real credentials (panduan §1, §3.2, §10.6).

## Profiles
| Profile | Overlay | Expected positives |
|---|---|---|
| `clean` | none (baseline only) | 0 — measures false positives |
| `controller` | benign lookalikes | 0 — must not alert |
| `compromised` | inert risky artifacts | 4 — must alert (dangerous extension/location) |

## Layout (panduan §4)
```
ojs-2.4.8-4-dataset/
├── README.md, VERSION
├── mysql/
│   ├── database.sql            # data-only OJS 2.4 seed (FK-free; see below)
│   ├── config.inc.php          # SANITIZED template (placeholders, no secrets)
│   ├── files/journals/1/       # private files_dir: articles/<id>/<stage>/, issues/1/public/
│   └── public/journals/1/      # public assets (journal logo)
├── ground-truth/
│   ├── dataset-manifest.yaml
│   ├── entity-inventory.csv    # journal/sections/issues/articles
│   ├── file-inventory.csv      # baseline files: path↔article_id/file_id/stage/sha256
│   ├── upload-oracle.csv       # THE oracle (per-artifact labels, authored pre-scan)
│   ├── expected-findings-{clean,compromised}.json
│   └── sha256sums*.txt         # per-profile hash manifests
├── scenarios/{clean,controller,compromised}/{overlay-files,profile.yaml}
├── scripts/
│   ├── build-dataset.sh        # regenerate synthetic baseline
│   ├── export-snapshot.sh      # export a UI-built baseline (canonical flow)
│   ├── restore-baseline.sh     # restore DB+files to a lab target (destructive)
│   ├── apply-profile.sh        # overlay a profile onto the restored baseline
│   ├── verify-dataset.sh       # consistency + hashes (+optional DB checks)
│   ├── generate-manifest.py    # (re)compute sha256sums
│   ├── collect-evidence.sh     # per-run evidence dir
│   └── lib/                    # generator + vendored ADODB schema + DDL converter
├── evidence/                   # runtime scan output (never feeds the oracle)
└── docs/                       # architecture, build-log, scenario catalog
```

## Baseline content (8 articles, panduan §5.3)
A-001 submission · A-002 in review · A-003 editor decision · A-004 copyedit ·
A-005 layout · A-006 **published** (issue + public galley) · A-007 supplementary
(CSV) · A-008 revision (file_id 14 at revision 1 **and** 2). 11 dummy users with
OJS 2.4 `roles`, 2 sections, 1 published + 1 future issue, an issue cover, and a
public logo. 16 baseline files across stages (≥15 required).

## Quick start
```bash
# regenerate the package deterministically
OJS_LAB_PASSWORD='your-lab-pw' scripts/build-dataset.sh

# offline verification (structure, hashes, oracle↔files, inertness)
scripts/verify-dataset.sh

# on a lab OJS 2.4.8-4 host: reset → overlay → scan
DATASET_ROOT=$PWD TARGET_FILES_DIR=/var/lib/ojs-248-files \
TARGET_PUBLIC_DIR=/var/www/ojs-248/public DB_NAME=ojs248_dataset \
  scripts/restore-baseline.sh
DATASET_ROOT=$PWD TARGET_FILES_DIR=/var/lib/ojs-248-files \
  scripts/apply-profile.sh compromised
PROFILE=compromised TARGET_FILES_DIR=/var/lib/ojs-248-files \
  scripts/collect-evidence.sh
```

## About `mysql/database.sql`
The panduan's canonical baseline is built through the OJS UI and then exported
with `export-snapshot.sh`. Because that requires a running legacy OJS 2.4.8-4
instance, this package also ships a **deterministic synthetic seed**
(`scripts/lib/generate.py`) that writes the same file layout and an FK-consistent
**data-only** seed. The seed targets the table set the data touches; apply it to
a freshly installed OJS 2.4.8-4 schema (the installer owns `site`/`versions`/
default data) **or** to the reference schema produced by
`scripts/lib/schema_to_mysql.py` for offline import/verification.

The column definitions for that reference schema are taken verbatim from the
source tag `ojs-2_4_8-4` (ADODB XMLSchema, vendored under `scripts/lib/`), so the
seed is validated against the true 2.4.8-4 column set.

### Verified
The seed was imported into the real 2.4.8-4 reference schema in MariaDB with **no
errors**; the panduan §12.3 file↔DB check passes (every `article_files` and
`issue_files` row exists on disk; zero baseline orphans), the published→issue→
galley chain resolves, and the A-008 revision pair (file_id 14 rev 1 & 2) is
present.

## Evaluation
Unit = one labelled artifact in `upload-oracle.csv` (not one scan/folder).
Matching is by `relative_path` (normalize absolute scanner paths to be relative
to `files_dir`). Report TP/FN/FP/TN, detection coverage, miss rate, and control
false-positive rate per profile. Never derive or edit the oracle from scan
output (panduan §14).

## Safety / scope
Lab-only, isolated network. No source-code changes, no web-root placement, no
execution of any artifact. All "compromised" artifacts are inert.
