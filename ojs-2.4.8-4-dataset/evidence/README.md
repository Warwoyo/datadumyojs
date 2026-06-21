# evidence/

Runtime scan evidence only. **Not** an input to the oracle (panduan 9.1, 16).

Each scan run gets its own timestamped directory created by
`scripts/collect-evidence.sh`, e.g.:

```
evidence/2026-06-21T120000Z-compromised-run/
├── environment.txt        # OS, scanner host, target files_dir
├── profile.txt            # clean | controller | compromised
├── hash-before.txt        # sha256 of the scanned tree before the run
├── scanner-command.txt    # exact command used
├── scanner-result.json    # raw scanner output (store as-is, never edited)
├── scanner-stdout.log
├── scanner-stderr.log
├── oracle-snapshot.csv    # copy of upload-oracle.csv used for this run
└── comparison-result.csv  # TP/FN/FP/TN per oracle row (built after the scan)
```

Rules:
- Store scanner output verbatim. Never edit results to fit the oracle.
- The unit of evaluation is **one labelled artifact in `upload-oracle.csv`**, not
  one scan or one folder (panduan 14.1).
- If you must revise the oracle, create a new version and record why; do not
  mutate labels after seeing results (panduan 14.2).
