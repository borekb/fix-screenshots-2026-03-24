#!/usr/bin/env python3
"""
Classify " 2" files in the Screenshots folder:
- gdrive-duplicate:        byte-for-byte identical (MD5 match) → safe to delete
- same-pixels:             different file bytes but identical pixel data → metadata/compression difference only
- shottr-annotation:       different pixels, same dimensions → small annotation (arrow, rectangle, text)
- shottr-annotation-resized: different pixels, different dimensions → annotation that changed the canvas
- orphan:                  " 2" file without a matching original

READ-ONLY: this script does not modify any files.
"""

import hashlib
import json
import os
import struct
import sys
import zlib
from pathlib import Path

SCREENSHOTS_DIR = Path.home() / "Library/CloudStorage/GoogleDrive-borekb@gmail.com/My Drive/Archive/Screenshots"


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def png_dimensions(path):
    """Read dimensions from PNG IHDR chunk (first 24 bytes of file)."""
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            return None, None
        length = struct.unpack(">I", f.read(4))[0]
        chunk_type = f.read(4)
        if chunk_type != b"IHDR":
            return None, None
        w, h = struct.unpack(">II", f.read(8))
        return w, h


def decode_png_pixels(path):
    """Decode PNG to raw pixel data for comparison.

    Returns raw decompressed pixel data (including filter bytes) or None on error.
    This is sufficient for equality comparison: if the decompressed data is identical,
    the images are pixel-identical.
    """
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None

            idat_chunks = []
            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                length = struct.unpack(">I", header[:4])[0]
                chunk_type = header[4:8]
                data = f.read(length)
                f.read(4)  # CRC

                if chunk_type == b"IDAT":
                    idat_chunks.append(data)
                elif chunk_type == b"IEND":
                    break

            compressed = b"".join(idat_chunks)
            return zlib.decompress(compressed)
    except Exception:
        return None


def is_suffix_2_file(name):
    """Check if filename has a ' 2' suffix before the extension.

    Matches: 'Screenshot 2026-01-02 at 21.46.59 2.png' (suffix ' 2' before .png)
    Does NOT match: 'Screenshot 2026-02-22 at 2.06.56.png' (the '2.' is part of the time)

    The key distinction: a genuine ' 2' suffix is preceded by a non-digit character
    (the original filename), while a time component like 'at 2.06' has ' 2' preceded
    by 'at' and followed by digits that form a time.
    """
    # Find the last occurrence of " 2." in the filename
    idx = name.rfind(" 2.")
    if idx == -1:
        return False

    # The part after " 2." should be just the extension (png, jpg, etc.),
    # not more digits (which would indicate a time like "2.06.56")
    after = name[idx + 3:]  # after " 2."
    ext_part = after.split(".")[0] if "." in after else after
    if ext_part.isdigit():
        # This is something like " 2.06.56.png" — the "2" is part of the time
        return False

    return True


def find_pairs(base_dir):
    """Find all ' 2' files and their potential originals."""
    pairs = []
    for f in sorted(base_dir.iterdir()):
        name = f.name
        if not is_suffix_2_file(name):
            continue
        ext = f.suffix
        stem_without_2 = name.rsplit(" 2.", 1)[0]
        original = base_dir / f"{stem_without_2}{ext}"
        pairs.append((original, f))
    return pairs


def classify_pair(original, copy):
    if not original.exists():
        return "orphan", {}

    size_orig = original.stat().st_size
    size_copy = copy.stat().st_size

    md5_orig = md5_file(original)
    md5_copy = md5_file(copy)

    info = {
        "original": original.name,
        "copy": copy.name,
        "size_original": size_orig,
        "size_copy": size_copy,
        "size_diff_pct": round((size_copy - size_orig) / size_orig * 100, 1) if size_orig else 0,
    }

    if md5_orig == md5_copy:
        return "gdrive-duplicate", info

    # MD5 differs — compare dimensions
    w1, h1 = png_dimensions(original)
    w2, h2 = png_dimensions(copy)
    info["dim_original"] = f"{w1}x{h1}" if w1 else "?"
    info["dim_copy"] = f"{w2}x{h2}" if w2 else "?"

    if w1 != w2 or h1 != h2:
        return "shottr-annotation-resized", info

    # Same dimensions, different bytes — compare actual pixel data
    pixels_orig = decode_png_pixels(original)
    pixels_copy = decode_png_pixels(copy)

    if pixels_orig is None or pixels_copy is None:
        info["note"] = "could not decode PNG pixels"
        return "shottr-annotation", info

    if pixels_orig == pixels_copy:
        return "same-pixels", info
    else:
        return "shottr-annotation", info


CATEGORIES = [
    "gdrive-duplicate",
    "same-pixels",
    "shottr-annotation",
    "shottr-annotation-resized",
    "orphan",
]

STATUS_CHARS = {
    "gdrive-duplicate": "=",
    "same-pixels": "~",
    "shottr-annotation": "A",
    "shottr-annotation-resized": "A",
    "orphan": "?",
}


def main():
    if not SCREENSHOTS_DIR.exists():
        print(f"Directory not found: {SCREENSHOTS_DIR}", file=sys.stderr)
        sys.exit(1)

    pairs = find_pairs(SCREENSHOTS_DIR)
    results = {cat: [] for cat in CATEGORIES}

    print(f"Found {len(pairs)} ' 2' files to classify...\n")

    for original, copy in pairs:
        category, info = classify_pair(original, copy)
        results[category].append(info)
        print(f"  [{STATUS_CHARS[category]}] {copy.name}")

    # Summary
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)

    print(f"\n[=] GDrive duplicate (byte-for-byte identical, safe to delete): {len(results['gdrive-duplicate'])}")

    if results["same-pixels"]:
        print(f"\n[~] Same pixels, different file bytes (metadata/compression difference only): {len(results['same-pixels'])}")
        for r in results["same-pixels"]:
            print(f"    {r['copy']}  ({r['size_diff_pct']:+}% size)")

    if results["shottr-annotation"]:
        print(f"\n[A] Shottr annotation, same dimensions (different pixels): {len(results['shottr-annotation'])}")
        for r in results["shottr-annotation"]:
            print(f"    {r['copy']}  ({r['size_diff_pct']:+}% size, {r['dim_copy']})")

    if results["shottr-annotation-resized"]:
        print(f"\n[A] Shottr annotation, different dimensions: {len(results['shottr-annotation-resized'])}")
        for r in results["shottr-annotation-resized"]:
            print(f"    {r['copy']}  (original {r['dim_original']} → annotated {r['dim_copy']})")

    if results["orphan"]:
        print(f"\n[?] Orphan (no matching original found): {len(results['orphan'])}")

    # Write JSON report
    report_path = Path(__file__).parent / "classification-report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()
