"""
num2text.py — Digit-to-text wordlist generator (PT-BR + EN).

Converts a number (up to 12 digits) into its digit-by-digit text representation
and produces case/leet/separator variations for password wordlist generation.

Examples:
  123       → umdoistres, UMDOISTRES, UmDoisTres, uMdOiStReS, um-dois-tres, ...
  2025      → doiszerodoiscinco, DOISZERODOISCINCO, ...
  1206      → umdoiszeroseis, ...

Usage:
  wfh num2text --number 123
  wfh num2text --number 2025 --lang en
  wfh num2text --number 123456 --separators -,_,@
  wfh num2text --range 0-9999 -o labs/labs_number2text.lst

Author: André Henrique (@mrhenrike)
"""
from __future__ import annotations

import itertools
import unicodedata
from typing import Generator

MAX_DIGITS = 12

# ---------------------------------------------------------------------------
# Digit name tables
# ---------------------------------------------------------------------------

DIGIT_PT: dict[str, str] = {
    "0": "zero",
    "1": "um",
    "2": "dois",
    "3": "tres",   # accent-free for ascii-safe variants
    "4": "quatro",
    "5": "cinco",
    "6": "seis",
    "7": "sete",
    "8": "oito",
    "9": "nove",
}

DIGIT_PT_ACCENTED: dict[str, str] = {
    **DIGIT_PT,
    "3": "três",
}

DIGIT_EN: dict[str, str] = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

LEET_MAP: dict[str, str] = {
    "a": "4", "e": "3", "i": "1", "o": "0",
    "s": "$", "t": "7", "z": "2", "g": "9",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _digits(number: str | int) -> list[str]:
    """Validates and returns individual digit characters."""
    s = str(number).lstrip("0") or "0"
    s = str(number) if str(number).startswith("0") else s
    # keep leading zeros if the original had them
    s = str(number)
    if not s.isdigit():
        raise ValueError(f"Not a valid number: {number!r}")
    if len(s) > MAX_DIGITS:
        raise ValueError(f"Number exceeds {MAX_DIGITS} digits: {s!r}")
    return list(s)


def _word_list(number: str | int, lang: str = "pt") -> list[str]:
    """Returns the list of digit words for a number."""
    table = DIGIT_PT if lang == "pt" else DIGIT_EN
    return [table[d] for d in _digits(number)]


def _word_list_accented(number: str | int) -> list[str]:
    table = DIGIT_PT_ACCENTED
    return [table[d] for d in _digits(number)]


# ---------------------------------------------------------------------------
# Case variants
# ---------------------------------------------------------------------------

def _case_variants(words: list[str]) -> list[str]:
    """
    Returns multiple case styles for a list of words.

    Styles produced (concatenated):
      all_lower         umdoistres
      ALL_UPPER         UMDOISTRES
      title             UmDoisTres  (each word capitalised)
      camel             umDoisTres  (first lowercase, rest capitalised)
      alternating_char  uMdOiStReS  (char-level alternating)
      alternating_word  umDOIStres  (word-level alternating upper/lower)
      block2            UMdoiSTres  (alternating blocks of 2 chars)
    """
    joined  = "".join(words)
    titled  = "".join(w.capitalize() for w in words)
    camel   = words[0].lower() + "".join(w.capitalize() for w in words[1:]) if len(words) > 1 else words[0].lower()

    # char-level alternating
    alt_chars = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(joined))

    # word-level alternating
    alt_words = "".join(w.upper() if i % 2 else w.lower() for i, w in enumerate(words))

    # block-of-2 chars alternating upper/lower
    block2_chars = []
    for i, c in enumerate(joined):
        block2_chars.append(c.upper() if (i // 2) % 2 == 0 else c.lower())
    block2 = "".join(block2_chars)

    seen: set[str] = set()
    result: list[str] = []
    for v in [joined.lower(), joined.upper(), titled, camel, alt_chars, alt_words, block2]:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


# ---------------------------------------------------------------------------
# Separator variants
# ---------------------------------------------------------------------------

def _sep_variants(words: list[str], separators: list[str]) -> list[str]:
    """Joins words with each separator in both lower and upper."""
    result: list[str] = []
    seen: set[str] = set()
    for sep in separators:
        if sep == "":
            continue  # handled by case_variants
        for variant in [sep.join(w.lower() for w in words),
                        sep.join(w.upper() for w in words),
                        sep.join(w.capitalize() for w in words)]:
            if variant not in seen:
                seen.add(variant)
                result.append(variant)
    return result


# ---------------------------------------------------------------------------
# Leet variant
# ---------------------------------------------------------------------------

def _leet(s: str) -> str:
    return "".join(LEET_MAP.get(c.lower(), c) for c in s)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def num2text_variants(
    number: str | int,
    lang: str = "pt",
    separators: list[str] | None = None,
    with_leet: bool = True,
    with_accented: bool = True,
    min_len: int = 0,
    max_len: int = 0,
) -> Generator[str, None, None]:
    """
    Generates all text variants for a number.

    Args:
        number:       The number to convert (up to 12 digits).
        lang:         Language for digit names — 'pt' (default) or 'en'.
        separators:   List of separators between digit words (default: [], -, _, ., @, #).
        with_leet:    Include leet substitutions.
        with_accented: Include accented PT-BR variants (três instead of tres).
        min_len:      Minimum length filter (0 = no filter).
        max_len:      Maximum length filter (0 = no filter).

    Yields:
        Password variant strings.
    """
    seps = separators if separators is not None else ["", "-", "_", ".", "@", "#", "!"]
    words = _word_list(number, lang)

    seen: set[str] = set()

    def emit(s: str) -> bool:
        if s in seen:
            return False
        seen.add(s)
        if min_len and len(s) < min_len:
            return False
        if max_len and len(s) > max_len:
            return False
        return True

    # Case variants (concatenated, no separator)
    for v in _case_variants(words):
        if emit(v):
            yield v
        # leet on each case variant
        if with_leet:
            lv = _leet(v)
            if emit(lv):
                yield lv

    # Separator variants
    for v in _sep_variants(words, seps):
        if emit(v):
            yield v

    # Accented PT-BR variants (três instead of tres)
    if with_accented and lang == "pt":
        acc_words = _word_list_accented(number)
        for v in _case_variants(acc_words):
            ascii_v = _strip_accents(v)
            # yield the accented version
            if emit(v):
                yield v
            # also yield ascii-stripped version
            if emit(ascii_v):
                yield ascii_v
        for v in _sep_variants(acc_words, seps):
            if emit(v):
                yield v

    # Original digits appended to text (e.g. umdoistres123)
    base = "".join(words)
    num_str = str(number)
    for suffix in [num_str, num_str[::-1]]:
        for case_base in [base.lower(), base.upper(), "".join(w.capitalize() for w in words)]:
            for sep in ["", "_", "@", "#"]:
                v = f"{case_base}{sep}{suffix}"
                if emit(v):
                    yield v


def num2text_range(
    start: int,
    end: int,
    lang: str = "pt",
    separators: list[str] | None = None,
    with_leet: bool = True,
    with_accented: bool = True,
    min_len: int = 0,
    max_len: int = 0,
) -> Generator[str, None, None]:
    """Generates variants for every number in [start, end]."""
    seen: set[str] = set()
    for n in range(start, end + 1):
        for v in num2text_variants(n, lang, separators, with_leet, with_accented, min_len, max_len):
            if v not in seen:
                seen.add(v)
                yield v
