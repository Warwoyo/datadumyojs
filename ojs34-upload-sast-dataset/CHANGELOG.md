# Changelog

All notable changes to this OJS 3.4.0-7 dataset are documented here.
Format follows Keep a Changelog; dataset is versioned via `dataset_id`.

## [v1] - 2026-06-21
### Added
- Initial OJS **3.4.0-7** realistic instance seed (`ojs34-realistic-instance-v1`),
  ported from the OJS 3.3 realistic-instance seed. Injects believable dummy data
  into a fresh OJS 3.4.0-7 install: 1 journal (`jist`), 5 issues, 5 sections,
  15 users, 12 submissions (9 published / 2 under review / 1 draft), 44 benign
  uploaded files, and 9 PDF galleys.
- Benign uploads only (PDF, DOCX, XLSX, CSV, JSON, PNG, BibTeX, RIS, LaTeX, TXT).

### Changed — adapted to the OJS 3.4 schema
Verified against the official PKP dataset for `stable-3_4_0`. Differences from
the 3.3 seed that are now handled by `scripts/lib/generate.py`:
- **Short locale codes**: `en_US` → `en` (column type `varchar(14)`).
- **JSON array settings**: `supportedLocales` / `supportedFormLocales` /
  `supportedSubmissionLocales` and `users.locales` are now JSON (`["en"]`),
  not PHP `serialize()`.
- **Current issue**: set on `journals.current_issue_id`; the `issues` table no
  longer has a `current` column.
- **`submissions`**: now carries its own `status`, and `submission_progress` is
  a `varchar` workflow step (`''` = completed wizard), not an integer.
- **`publications.date_published`** is a `DATE` (`YYYY-MM-DD`), not a datetime.
- **Genres**: the seed now inserts the 12 default submission-file genres for the
  journal context (OJS only auto-creates them when a journal is made via the UI;
  this seed inserts the journal row directly).

### Security
- No executable uploads, no web shells, no payloads, no obfuscation, and no real
  credentials. Nothing simulates a hacked instance.
