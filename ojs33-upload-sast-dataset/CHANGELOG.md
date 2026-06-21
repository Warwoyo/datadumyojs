# Changelog

All notable changes to this OJS 3.3.0-13 dataset are documented here.
Format follows Keep a Changelog; dataset is versioned via `dataset_id`.

## [v2] - 2026-06-21
### Changed (purpose pivot)
- Repurposed the package from a **SAST upload-directory detection** corpus into a
  **realistic, normally-operating OJS instance seed**
  (`ojs33-realistic-instance-v2`). The goal is now to inject believable dummy
  data into OJS, not to plant detectable artifacts.
- Rewrote `fixtures/fixture-spec.json` as a journal + issues + sections + users +
  submissions model, where each submission owns **multiple uploaded files**.
- Rewrote `scripts/lib/generate.py` (builder 2.0) to render benign, non-empty,
  varied uploads (PDF, DOCX, XLSX, CSV, JSON, PNG, BibTeX, RIS, LaTeX, TXT) with
  filled, topical content, and to emit an FK-consistent OJS data-only seed.
- New content: 1 journal, 5 issues, 5 sections, 15 users, 12 submissions
  (9 published / 2 under review / 1 draft), 44 uploaded files, 9 PDF galleys.

### Removed
- All executable / "compromise" uploads (`.php`, `.phtml`, `.php5`, `.phar`,
  double-extension `.php`, `.inc`) and the PHP-token edge cases.
- SAST scoring machinery: `oracle/expected-scan-policy.v1.yaml`,
  `scripts/collect-scan-evidence.sh`, and the
  clean-baseline / mixed-primary / edge-secondary profiles.

### Added
- Profiles `full-instance` (everything) and `core-published` (published only).
- `oracle/upload-ground-truth.v1.json` and `oracle/scenario-matrix.v1.csv` are
  now a **benign file inventory** (no scan/detection labels).

### Security
- The instance contains **no executable uploads**, no web shells, no payloads,
  no obfuscation, and no real credentials. Nothing simulates a hacked instance.

## [v1] - 2026-06-21
### Added
- Initial dataset `ojs33-upload-sast-lab-v1` for OJS 3.3.0-13 uploaded-directory
  SAST evaluation: 6 benign controls, 6 inert executable-extension markers, and
  5 edge cases, with detection-scoring profiles and an evaluation policy.
  (Superseded by v2.)
