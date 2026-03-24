#!/usr/bin/env python3
"""
Verify that every file in the 'duplicates' subfolder has a matching
original (same MD5) in the parent Screenshots folder.

READ-ONLY: does not modify any files.
"""

import hashlib
import re
import sys
from pathlib import Path

SCREENSHOTS_DIR = Path.home() / "Library/CloudStorage/GoogleDrive-borekb@gmail.com/My Drive/Archive/Screenshots"
DUPES_DIR = SCREENSHOTS_DIR / "duplicates"


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_numeric_suffix(stem):
    """Remove trailing ' N' suffix: 'Screenshot ... 2' → 'Screenshot ...'"""
    return re.sub(r" \d+$", "", stem)


def main():
    if not DUPES_DIR.exists():
        print(f"Duplicates folder not found: {DUPES_DIR}", file=sys.stderr)
        sys.exit(1)

    dupes = sorted(f for f in DUPES_DIR.iterdir() if f.is_file() and f.name != ".DS_Store")
    print(f"Files in duplicates folder: {len(dupes)}\n")

    ok = []
    problems = []

    for dupe in dupes:
        md5_dupe = md5_file(dupe)
        ext = dupe.suffix
        base_stem = strip_numeric_suffix(dupe.stem)

        # Find all candidates in parent folder with same base name
        found_match = False
        for candidate in SCREENSHOTS_DIR.iterdir():
            if not candidate.is_file():
                continue
            if candidate.suffix != ext:
                continue
            if candidate.parent == DUPES_DIR:
                continue
            if not candidate.stem.startswith(base_stem):
                continue

            md5_cand = md5_file(candidate)
            if md5_dupe == md5_cand:
                found_match = True
                break

        if found_match:
            ok.append(dupe.name)
        else:
            problems.append(dupe.name)

    print("=" * 60)
    print(f"Confirmed duplicates (matching original exists): {len(ok)}")
    print(f"Problems (NO matching original found):           {len(problems)}")
    print("=" * 60)

    if problems:
        print("\nFiles WITHOUT a matching original:")
        for name in problems:
            print(f"  {name}")

    if not problems:
        print("\nAll files in 'duplicates' are confirmed duplicates. Safe to delete.")


if __name__ == "__main__":
    main()
