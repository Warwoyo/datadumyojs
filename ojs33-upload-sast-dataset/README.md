# OJS 3.3.0-13 Realistic Instance Seed (`ojs33-realistic-instance-v2`)

A deterministic, resettable seed that injects **realistic dummy data** into an
OJS 3.3.0-13 install so the instance looks like a journal that is **running
normally**. It wires a journal, issues, sections, a pool of editors / authors /
reviewers, and submissions into real OJS database relations (journal, issue,
section, users, publication, authors, submission_files, files, galleys), and
lays down the matching uploaded files under the OJS `files_dir`.

Each submission carries **several uploaded files** — manuscript, typeset PDF
galley, figures, supplementary data, cover letters, datasets, references —
exactly as a real submission accumulates them across the editorial workflow.

> ✅ **Benign by construction.** Every uploaded file is a non-empty, real-looking
> document (PDF, DOCX, XLSX, CSV, JSON, PNG, BibTeX, RIS, LaTeX, TXT). There are
> **no executable uploads** (`.php`/`.phtml`/`.php5`/`.phar`/`.inc`/…), no web
> shells, no command execution, no obfuscation, no real credentials, and
> nothing that simulates a compromised or hacked instance.

---

## What gets injected

| Item | Count | Notes |
|---|---:|---|
| Journal | 1 | *Journal of Information Systems and Technology* (`jist`) |
| Issues | 5 | Vol 1–3, all published; the 2025 issue is **current** |
| Sections | 5 | Articles, Review Articles, Case Studies, Short Communications, Editorials |
| Users | 15 | admin, journal manager/editors, section editors, authors, reviewers, a reader |
| Submissions | 12 | 9 published, 2 under review, 1 draft |
| Uploaded files | 44 | 2–6 per submission, varied types and stages |
| Public PDF galleys | 9 | one per published submission |

Upload types present: `pdf docx xlsx csv json png bib ris tex txt`.

## Package layout

```
ojs33-upload-sast-dataset/
├── README.md, CHANGELOG.md, dataset-manifest.yaml
├── fixtures/fixture-spec.json        # SINGLE SOURCE OF TRUTH (journal + submissions + files)
├── files/journals/1/articles/<sid>/  # rendered uploads (FILES_DIR layout)
│   └── CHECKSUMS.sha256
├── mysql/database.sql                # OJS data-only seed (FK-consistent with the inventory)
│   └── config.overlay.example.ini    # safe overlay reference (never copied raw)
├── oracle/
│   ├── upload-ground-truth.v1.json   # benign file inventory (paths, hashes, IDs, genres, stages)
│   └── scenario-matrix.v1.csv        # flat per-file inventory
├── profiles/{full-instance,core-published}.yaml
├── scripts/{build-dataset,apply-profile,verify-profile,rollback}.sh
│   └── lib/{generate.py,common.sh}
└── evidence/                         # backups + verify reports (runtime outputs)
```

## Profiles

| Profile | Scope |
|---|---|
| `full-instance` | Every submission and file — published, under review, and draft. |
| `core-published` | Only published submissions and their files (the live catalogue). |

`apply-profile.sh` always restores the full `files/` tree on disk; the profile
name selects which subset `verify-profile.sh` checks.

---

## Quick start

### 1. Build / rebuild the package (deterministic)
```bash
OJS_LAB_PASSWORD='your-lab-pw' scripts/build-dataset.sh
```
Re-running with the same spec reproduces identical `files/` hashes and
`files_tree_sha256`. (The bcrypt hash in `database.sql` is salted, so it varies;
it is intentionally excluded from `files_tree_sha256`.)

### 2. Apply to a lab OJS target (DESTRUCTIVE; backs up first)
```bash
APP_DIR=/var/www/ojs-330 FILES_DIR=/var/ojs-files \
DB_NAME=ojs DB_HOST=localhost DB_USER=ojs DB_PASS=secret \
scripts/apply-profile.sh full-instance
```
Apply runs a **fail-closed safety gate**: it refuses unless `FILES_DIR` is
outside `APP_DIR` and outside the web root, then backs up the DB and files to
`evidence/backup-<id>` before restoring the snapshot.

### 3. Verify
```bash
APP_DIR=... FILES_DIR=... DB_NAME=... DB_USER=... DB_PASS=... \
scripts/verify-profile.sh full-instance
```
Checks every in-profile file hash, absence of symlinks, that **no** upload
carries an executable extension, no executable bit, and core OJS relations
(journal, published issues, submission_files, user/group mappings, galleys).

### 4. Rollback
```bash
APP_DIR=... FILES_DIR=... DB_NAME=... DB_USER=... DB_PASS=... \
scripts/rollback.sh <backup_id>
```

---

## Applying the database

`mysql/database.sql` is a **data-only seed** (INSERTs) for OJS 3.3.0-13. It does
**not** create tables and does **not** touch OJS source code. Apply it on top of
a freshly installed OJS 3.3.0-13 schema (the installer creates the tables, the
default `site` row, and the default `genres`, including `genre_id=1` referenced
by the uploads). The seed is regenerated from the same `fixture-spec.json` so the
database IDs always match the file inventory.

Foreign-key-relevant defaults assumed present on a fresh install: `site`,
`genres` (Article Text = `genre_id 1`).

## Realism notes

- Submissions span 2022–2026 with plausible submitted / published dates.
- Published submissions sit in issues and expose a single approved PDF galley;
  submissions under review and the draft have no issue and no galley.
- Authors carry names, affiliations, and countries across several institutions;
  many submissions are multi-author.
- File contents are filled and topical (e.g. the manuscript PDF embeds the
  title, author list, abstract, and section headings; CSV/XLSX hold small
  realistic tables; BibTeX/RIS hold matching citations).

## Reproducibility & integrity

- `dataset-manifest.yaml > integrity` carries `oracle_sha256`,
  `database_sql_sha256`, and `files_tree_sha256`.
- `files/CHECKSUMS.sha256` lists every uploaded-file hash; the inventory stores
  the same `sha256` per file.
- Applying the same profile twice yields the same files, hashes, and DB IDs,
  with no leftover files and no OJS source changes.

## What this dataset is **not**

Not a malware or attack corpus. It contains no executable uploads and nothing
that points to a hacked instance. Its purpose is the opposite: to make an OJS
3.3.0-13 install look like a healthy, normally-operating journal populated with
realistic submissions and their files.
