# Architecture notes — OJS 2.4.8-4

OJS 2.4 is the legacy line; its schema and file layout differ fundamentally
from OJS 3.x. This dataset targets 2.4.8-4 exclusively.

## Database (relevant tables)
- `journals`, `journal_settings`
- `roles` — role assignment is `(journal_id, user_id, role_id)`; there is **no**
  `user_user_groups`/`user_groups` (that is OJS 3.x).
- `users`, `user_settings` — names live on the `users` row (`first_name`,
  `last_name`), not in settings.
- `sections`, `section_settings`
- `issues` (has a `current` column), `issue_settings`, `issue_files` (covers)
- `articles` (a submission = an article) + `article_settings`
- `published_articles` — links a published article to an issue
- `article_files` — PK is `(file_id, revision)`; `file_stage` is an integer
- `article_galleys`, `article_supplementary_files`

Role IDs (bitmask constants): site admin `0x1`, manager `0x10`, editor `0x100`,
section editor `0x200`, reviewer `0x1000`, author `0x10000`, reader `0x100000`.

`article.status`: 1=queued, 3=published, 4=declined, 0=archived.

## File layout (classes/file/ArticleFileManager.inc.php)
```
files_dir/journals/<journal_id>/articles/<article_id>/
  submission/original/   (SM, file_stage 1)
  submission/review/     (RV, 2)
  submission/editor/     (ED, 3)
  submission/copyedit/   (CE, 4)
  submission/layout/     (LE, 5)
  public/                (PB, 6)
  supp/                  (SP, 7)
  note/                  (NT, 8)
  attachment/            (AT, 9)
files_dir/journals/<journal_id>/issues/<issue_id>/public/   (issue covers)
public_files_dir/journals/<journal_id>/                     (logo, web assets)
```
Physical filename: `<article_id>-<file_id>-<revision>-<STAGECODE>.<ext>`, and
`article_files.file_name` stores exactly that generated basename.

## Reference schema for testing
`scripts/lib/schema_to_mysql.py` converts the source-tag ADODB XMLSchema
(`ojs_schema.xml`, pkp-lib `common.xml`, both vendored under `scripts/lib/`)
into MySQL `CREATE TABLE` DDL for the subset of tables the seed populates. It is
used to import/verify the seed in a lab DB and is **not** a substitute for the
real OJS installer.
