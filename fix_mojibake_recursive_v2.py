#!/usr/bin/env python3
# Fix mojibake like "vÃ¦rdier", "TÃ¦rskel", "â–¾" in HTML/CSV/JS/CSS/TXT files.
# Compatible with older Python versions where Path.write_text(newline=...) is unsupported.
#
# Usage:
#   python fix_mojibake_recursive_v2.py
#   python fix_mojibake_recursive_v2.py "C:\Users\Bruger\Desktop\HTML\Den Blinde Vinkel"
#   python fix_mojibake_recursive_v2.py --no-backup

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

EXTENSIONS = {".html", ".htm", ".css", ".js", ".csv", ".txt", ".md", ".json"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}
MOJIBAKE_MARKERS = ("Ã", "Â", "â")

REPLACEMENTS = {
    "Ã¦": "æ",
    "Ã†": "Æ",
    "Ã¸": "ø",
    "Ã˜": "Ø",
    "Ã¥": "å",
    "Ã…": "Å",
    "Ã©": "é",
    "Ã¨": "è",
    "Ã¡": "á",
    "Ã ": "à",
    "Ã¶": "ö",
    "Ã–": "Ö",
    "Ã¼": "ü",
    "Ãœ": "Ü",
    "Ã¤": "ä",
    "Ã„": "Ä",
    "Â ": " ",
    "Â\xa0": " ",
    "Â·": "·",
    "Â©": "©",
    "Â®": "®",
    "Â±": "±",
    "Â°": "°",
    "â€“": "–",
    "â€”": "—",
    "â€˜": "‘",
    "â€™": "’",
    "â€œ": "“",
    "â€�": "”",
    "â€": "”",
    "â€¦": "…",
    "â€¢": "•",
    "â†’": "→",
    "â†": "←",
    "â†‘": "↑",
    "â†“": "↓",
    "â‡’": "⇒",
    "â‰¤": "≤",
    "â‰¥": "≥",
    "â‰ ": "≠",
    "â‰": "≠",
    "âˆ’": "−",
    "â„¢": "™",
    "â–¾": "▾",
    "â–¼": "▼",
    "â–¸": "▸",
    "â–¶": "▶",
    "âœ“": "✓",
    "âœ”": "✔",
    "âœ•": "✕",
    "âœ–": "✖",
}

MOJI_CHUNK_RE = re.compile(r'[^<>\s"\']*(?:Ã|Â|â)[^<>\s"\']*')


def decode_mojibake_chunk(match: re.Match) -> str:
    chunk = match.group(0)

    try:
        fixed = chunk.encode("cp1252").decode("utf-8")
        if fixed != chunk:
            return fixed
    except UnicodeError:
        pass

    fixed = chunk
    for bad, good in REPLACEMENTS.items():
        fixed = fixed.replace(bad, good)
    return fixed


def fix_text(text: str) -> str:
    fixed = text

    for _ in range(4):
        before = fixed
        fixed = MOJI_CHUNK_RE.sub(decode_mojibake_chunk, fixed)
        for bad, good in REPLACEMENTS.items():
            fixed = fixed.replace(bad, good)
        if fixed == before:
            break

    return fixed


def read_text_lossless(path: Path) -> str:
    raw = path.read_bytes()

    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")


def write_utf8(path: Path, text: str) -> None:
    # Do not use Path.write_text(..., newline=""), because older Python versions reject it.
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Folder to scan recursively")
    parser.add_argument("--no-backup", action="store_true", help="Overwrite without backup")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Folder not found: {root}")
        return 1

    backup_root = root / f"_encoding_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    changed = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue

        original = read_text_lossless(path)

        if not any(marker in original for marker in MOJIBAKE_MARKERS):
            continue

        fixed = fix_text(original)

        if fixed != original:
            if not args.no_backup:
                rel = path.relative_to(root)
                backup_path = backup_root / rel
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_path)

            write_utf8(path, fixed)
            changed.append(path.relative_to(root))

    if changed:
        print("Fixed encoding in:")
        for rel in changed:
            print(f"  {rel}")
        if not args.no_backup:
            print(f"\nBackup saved in: {backup_root}")
    else:
        print("No mojibake found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
