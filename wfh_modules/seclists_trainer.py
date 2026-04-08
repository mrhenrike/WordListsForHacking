"""
seclists_trainer.py — Auto-discovery and batch training from SecLists corpus.

Locates a SecLists installation (local submodule or custom path),
reads the corpus index (data/seclists_corpus.json), and feeds
relevant files into the PatternModel via train_from_wordlist.

Only structural patterns are extracted — no raw data is stored.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CORPUS_INDEX = Path(__file__).parent.parent / "data" / "seclists_corpus.json"

_KNOWN_SECLISTS_RELATIVES = [
    Path(__file__).parent.parent.parent / "SecLists",
    Path(__file__).parent.parent / "SecLists",
]


def find_seclists_root(hint: Optional[str] = None) -> Optional[Path]:
    """Locate SecLists root directory.

    Args:
        hint: Explicit path provided by the user (--seclists flag).

    Returns:
        Path to SecLists root or None if not found.
    """
    if hint:
        p = Path(hint)
        if p.is_dir() and (p / "Passwords").is_dir():
            return p
        logger.warning("Provided SecLists path not valid: %s", hint)
        return None

    for candidate in _KNOWN_SECLISTS_RELATIVES:
        resolved = candidate.resolve()
        if resolved.is_dir() and (resolved / "Passwords").is_dir():
            logger.info("SecLists auto-discovered at: %s", resolved)
            return resolved

    return None


def load_corpus_index() -> dict:
    """Load the SecLists corpus index JSON."""
    if not _CORPUS_INDEX.exists():
        logger.error("Corpus index not found: %s", _CORPUS_INDEX)
        return {}
    with open(_CORPUS_INDEX, encoding="utf-8") as f:
        return json.load(f)


def train_from_seclists(
    model,
    seclists_root: Path,
    categories: Optional[list[str]] = None,
    max_password_sources: int = 0,
    max_username_sources: int = 0,
) -> dict:
    """Batch-train a PatternModel from SecLists corpus.

    Args:
        model: PatternModel instance.
        seclists_root: Root path of SecLists.
        categories: Filter to specific categories ('password', 'username', 'frequency').
                    None means all.
        max_password_sources: Limit number of password sources (0 = all).
        max_username_sources: Limit number of username sources (0 = all).

    Returns:
        Summary dict with counts per category.
    """
    corpus = load_corpus_index()
    if not corpus:
        return {"error": "corpus index not loaded"}

    cats = categories or ["password", "username", "frequency"]
    summary: dict = {
        "password_files": 0, "password_samples": 0,
        "username_files": 0, "username_samples": 0,
        "frequency_files": 0, "frequency_samples": 0,
        "skipped": [],
    }

    if "password" in cats:
        sources = sorted(corpus.get("password_sources", []), key=lambda s: s.get("priority", 99))
        if max_password_sources > 0:
            sources = sources[:max_password_sources]

        for src in sources:
            fpath = seclists_root / src["path"]
            if not fpath.exists():
                summary["skipped"].append(src["label"])
                logger.debug("Skipped (not found): %s", fpath)
                continue

            max_lines = src.get("max_lines", 500_000)
            label = src.get("label", fpath.name)
            logger.info("Training passwords from: %s (%s)", label, fpath.name)

            stats = model.train_from_wordlist(
                str(fpath), mode="password",
                max_lines=max_lines,
                source_label=f"SecLists/{label}",
            )
            summary["password_files"] += 1
            summary["password_samples"] += stats.get("processed", 0)

    if "username" in cats:
        sources = sorted(corpus.get("username_sources", []), key=lambda s: s.get("priority", 99))
        if max_username_sources > 0:
            sources = sources[:max_username_sources]

        for src in sources:
            fpath = seclists_root / src["path"]
            if not fpath.exists():
                summary["skipped"].append(src["label"])
                logger.debug("Skipped (not found): %s", fpath)
                continue

            max_lines = src.get("max_lines", 200_000)
            label = src.get("label", fpath.name)
            logger.info("Training usernames from: %s (%s)", label, fpath.name)

            stats = model.train_from_wordlist(
                str(fpath), mode="username",
                max_lines=max_lines,
                source_label=f"SecLists/{label}",
            )
            summary["username_files"] += 1
            summary["username_samples"] += stats.get("processed", 0)

    if "frequency" in cats:
        for src in corpus.get("frequency_sources", []):
            fpath = seclists_root / src["path"]
            if not fpath.exists():
                summary["skipped"].append(src["label"])
                continue

            fmt = src.get("format", "space_withcount")
            max_lines = src.get("max_lines", 100_000)
            label = src.get("label", fpath.name)
            logger.info("Training frequency from: %s (%s)", label, fpath.name)

            processed = _train_withcount(model, fpath, fmt, max_lines)
            summary["frequency_files"] += 1
            summary["frequency_samples"] += processed

    return summary


def _train_withcount(model, fpath: Path, fmt: str, max_lines: int) -> int:
    """Train from files where each line has a count and a password.

    Formats:
        space_withcount: 'COUNT PASSWORD' (space separated)
        csv_withcount: 'PASSWORD,COUNT' (CSV)
    """
    processed = 0
    try:
        with open(fpath, encoding="utf-8", errors="replace") as f:
            for line in f:
                if processed >= max_lines:
                    break
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                password = ""
                if fmt == "space_withcount":
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        password = parts[1]
                elif fmt == "csv_withcount":
                    parts = line.split(",", 1)
                    if len(parts) >= 1:
                        password = parts[0]
                else:
                    password = line

                if password and len(password) >= 3:
                    from wfh_modules.ml_patterns import abstract_password
                    shape = abstract_password(password)
                    model._pwd_shape_counts[shape] += 1
                    model._pwd_lengths.append(min(len(password), 64))
                    model._total_pwd_samples += 1
                    processed += 1

    except Exception as exc:
        logger.warning("Error reading %s: %s", fpath, exc)

    if processed > 0:
        model._sources.append(
            f"SecLists frequency: {fpath.name} — {processed} samples [patterns only]"
        )
    return processed
