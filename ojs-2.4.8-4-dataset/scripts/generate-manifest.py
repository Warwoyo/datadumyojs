#!/usr/bin/env python3
"""
(Re)generate ground-truth/sha256sums*.txt from the current files on disk
(panduan section 13). Does not touch labels in upload-oracle.csv — the oracle is
authored by design, never derived from a scan.

Usage: python3 scripts/generate-manifest.py
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def hash_tree(root: Path, out: Path):
    lines = []
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                lines.append(f"{h}  {p.relative_to(root)}")
    out.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"{out.name}: {len(lines)} files")


def main():
    gt = ROOT / "ground-truth"
    hash_tree(ROOT / "mysql/files", gt / "sha256sums-baseline.txt")
    hash_tree(ROOT / "mysql/files", gt / "sha256sums.txt")
    hash_tree(ROOT / "scenarios/clean/overlay-files", gt / "sha256sums-clean.txt")
    hash_tree(ROOT / "scenarios/controller/overlay-files", gt / "sha256sums-controller.txt")
    hash_tree(ROOT / "scenarios/compromised/overlay-files", gt / "sha256sums-compromised.txt")


if __name__ == "__main__":
    main()
