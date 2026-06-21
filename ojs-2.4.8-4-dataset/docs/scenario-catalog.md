# Scenario catalog

Unit of evaluation = one labelled artifact in `ground-truth/upload-oracle.csv`
(panduan 14.1). All "compromised" artifacts are **inert** (plain text; risky
name/extension/location only — no code, no server-side tags, no payloads).

## clean
Baseline only; empty overlay. Measures false positives on a normal corpus.
Expected positive objects: 0 (16 baseline negatives).

## controller (negatives that look risky)
| oracle_id | path | why it must NOT alert |
|---|---|---|
| OR-201 | articles/3/submission/editor/php-coding-guidelines.txt | name contains `php`, extension `.txt` |
| OR-202 | articles/5/submission/layout/figure-final.pdf | benign PDF, correct type, not DB-linked |
| OR-203 | articles/7/supp/measurements-2.csv | extra benign CSV beside a real supp file |

## compromised (positives that must alert)
| oracle_id | path | rule family | severity | indicator |
|---|---|---|---|---|
| OR-101 | articles/6/public/6-901-1-PB.phtml | dangerous_extension | high | server-parsed `.phtml` in upload dir |
| OR-102 | articles/1/submission/original/manuscript.pdf.exe | dangerous_extension | high | double extension `.pdf.exe` |
| OR-103 | articles/7/supp/dataset-helper.jsp | dangerous_extension | medium | orphan `.jsp`, no DB metadata |
| OR-104 | articles/2/submission/review/notes.phar | dangerous_extension | medium | `.phar` archive ext, not DB-linked |

Detection must rest on name/extension/location, not on the inert marker string
(the marker only exists for hashing/audit). See `expected-findings-*.json`.

## Adding artifacts
Edit `POSITIVES` / `CONTROLLERS` in `scripts/lib/generate.py`, rebuild, then
re-hash with `scripts/generate-manifest.py`. Keep every artifact inert.
