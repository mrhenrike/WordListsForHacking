"""
combiner.py — Keyword combiner for intelligent wordlist generation.

Generates permutations of keywords joined by connectors, with optional
abbreviation, reversal, leet, and numeric tail variations.

Inspired by intelligence-wordlist-generator (iwlgen).

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
import re
from itertools import permutations
from typing import Generator, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONNECTORS = ["", "-", "_", ".", "@", "#"]

DEFAULT_NUM_TAILS = [
    "", "1", "2", "3", "12", "123", "1234",
    "01", "00", "69", "99", "007",
    "!", "@", "#", "!!", "!@#",
    "2024", "2025", "2026",
]

LEET_MAP = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}


def combine_keywords(
    keywords: list[str],
    connectors: Optional[list[str]] = None,
    num_tails: Optional[list[str]] = None,
    max_depth: int = 0,
    use_abbreviation: bool = False,
    use_reverse: bool = False,
    use_leet: bool = False,
    use_lowercase: bool = False,
    min_length: int = 1,
    max_length: int = 64,
) -> Generator[str, None, None]:
    """Generate keyword combination wordlist.

    Args:
        keywords: List of base keywords.
        connectors: Separator strings between keywords.
        num_tails: Numeric/special suffixes to append.
        max_depth: Max permutation depth (0 = all up to len(keywords)).
        use_abbreviation: Generate abbreviation variants.
        use_reverse: Generate reversed variants.
        use_leet: Generate leet speak variants.
        use_lowercase: Add lowercase duplicates.
        min_length: Minimum output length.
        max_length: Maximum output length.

    Yields:
        Combined keyword strings.
    """
    conns = connectors if connectors is not None else DEFAULT_CONNECTORS
    tails = num_tails if num_tails is not None else DEFAULT_NUM_TAILS
    seen: set[str] = set()
    n = len(keywords)
    depth = max_depth if max_depth > 0 else n

    def emit(s: str) -> Optional[str]:
        if s and s not in seen and min_length <= len(s) <= max_length:
            seen.add(s)
            return s
        return None

    base_combos: list[str] = []

    for size in range(1, min(depth, n) + 1):
        for perm in permutations(keywords, size):
            for conn in conns:
                combo = conn.join(perm)
                base_combos.append(combo)
                r = emit(combo)
                if r:
                    yield r

    for combo in list(base_combos):
        for tail in tails:
            if not tail:
                continue
            r = emit(combo + tail)
            if r:
                yield r

    if use_abbreviation:
        for abbr in _abbreviation_variants(keywords):
            r = emit(abbr)
            if r:
                yield r
            for tail in tails:
                if tail:
                    r = emit(abbr + tail)
                    if r:
                        yield r

    if use_reverse:
        for combo in list(base_combos)[:500]:
            rev = combo[::-1]
            r = emit(rev)
            if r:
                yield r

    if use_leet:
        for combo in list(base_combos)[:500]:
            leet = _leetify(combo)
            if leet != combo:
                r = emit(leet)
                if r:
                    yield r

    if use_lowercase:
        for combo in list(base_combos)[:500]:
            low = combo.lower()
            r = emit(low)
            if r:
                yield r


def _abbreviation_variants(keywords: list[str]) -> list[str]:
    """Generate abbreviation variants from keywords.

    Three families:
    1. Single position abbreviated (only i-th word as first letter)
    2. Cumulative forward (first N words as first letters)
    3. Cumulative backward (last N words as first letters)
    """
    abbrs: list[str] = []
    n = len(keywords)

    for i in range(n):
        parts = list(keywords)
        if parts[i]:
            parts[i] = parts[i][0]
        abbrs.append("".join(parts))

    for cutoff in range(1, n):
        parts = [kw[0] if j < cutoff and kw else kw for j, kw in enumerate(keywords)]
        abbrs.append("".join(parts))

    for cutoff in range(1, n):
        parts = [kw[0] if j >= n - cutoff and kw else kw for j, kw in enumerate(keywords)]
        abbrs.append("".join(parts))

    return list(dict.fromkeys(abbrs))


def _leetify(text: str) -> str:
    """Apply leet substitutions."""
    return "".join(LEET_MAP.get(c.lower(), c) if c.isalpha() else c for c in text)


def handle_combiner(args, ctx: dict) -> None:
    """CLI handler for the combiner subcommand."""
    keywords = list(args.keywords) if args.keywords else []

    if getattr(args, "keywords_file", None):
        try:
            with open(args.keywords_file, encoding="utf-8") as f:
                for line in f:
                    kw = line.strip()
                    if kw and not kw.startswith("#"):
                        keywords.append(kw)
        except FileNotFoundError:
            logger.error("Keywords file not found: %s", args.keywords_file)
            return

    if not keywords:
        logger.error("No keywords provided. Use positional args or --keywords-file.")
        return

    connectors = None
    if getattr(args, "connectors", None):
        connectors = [c if c != "EMPTY" else "" for c in args.connectors.split(",")]

    num_tails = None
    if getattr(args, "tails", None):
        num_tails = [""] + [t.strip() for t in args.tails.split(",")]

    gen = combine_keywords(
        keywords,
        connectors=connectors,
        num_tails=num_tails,
        max_depth=getattr(args, "depth", 0),
        use_abbreviation=getattr(args, "abbreviation", False),
        use_reverse=getattr(args, "reverse", False),
        use_leet=getattr(args, "leet", False),
        use_lowercase=getattr(args, "lowercase", False),
        min_length=getattr(args, "min_len", 1),
        max_length=getattr(args, "max_len", 64),
    )

    return gen
