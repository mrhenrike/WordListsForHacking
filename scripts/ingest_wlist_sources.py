#!/usr/bin/env python3
"""
Merge local lab/drogarias password sources into passwords/wlist_brasil.lst.

Run from repo root:

    python3 scripts/ingest_wlist_sources.py

Rules:
  - labs/*.lst + drogarias/passwords_farmacias.lst only (no usernames)
  - drops purely-numeric lines (any length)
  - deduplicates case-sensitively
"""
from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WLIST = BASE / "passwords" / "wlist_brasil.lst"
LAB_FILES = (
    BASE / "labs" / "labs_passwords.lst",
    BASE / "labs" / "labs_mikrotik_pass.lst",
)
DROG_PW = BASE / "labs" / "drogarias" / "passwords_farmacias.lst"


def is_purely_numeric(s: str) -> bool:
    return bool(s) and s.isdigit()


def eligible(w: str) -> bool:
    return bool(w) and not is_purely_numeric(w) and len(w) >= 6


def sanitize(entries: set[str]) -> set[str]:
    """Remove purely-numeric entries from the working set."""
    return {w for w in entries if w and not is_purely_numeric(w)}


def main() -> None:
    entries: set[str] = set()
    if WLIST.is_file():
        with WLIST.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                w = line.rstrip("\n\r")
                if eligible(w):
                    entries.add(w)
    before = len(entries)
    added = 0

    for path in (*LAB_FILES, DROG_PW):
        if not path.is_file():
            print(f"skip (missing): {path}")
            continue
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                w = line.strip()
                if not eligible(w):
                    continue
                if w not in entries:
                    added += 1
                entries.add(w)
        print(f"ingested: {path.name}")

    entries = sanitize(entries)

    WLIST.parent.mkdir(parents=True, exist_ok=True)
    with WLIST.open("w", encoding="utf-8") as f:
        for entry in sorted(entries, key=lambda x: x.lower()):
            f.write(entry + "\n")

    size_mb = WLIST.stat().st_size / (1024 * 1024)
    print(f"done: {before:,} → {len(entries):,} (+{added:,} new) | {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
