"""
mangler.py — Hashcat/John-style mangling rules for wordlists.

Applies transformation rules to each word generating multiple variants.
Inspired by hashcat rule engine, pipal mangling, and BEWGor permutations.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""

import logging
from typing import Generator

logger = logging.getLogger(__name__)

BUILTIN_RULES: dict[str, str] = {
    "capitalize":     "Capitalize first letter (e.g. password -> Password)",
    "upper":          "Uppercase entire word (e.g. password -> PASSWORD)",
    "lower":          "Lowercase entire word (e.g. Password -> password)",
    "reverse":        "Reverse the word (e.g. password -> drowssap)",
    "toggle":         "Toggle case of all characters (e.g. Password -> pASSWORD)",
    "append_num":     "Append 0-99, common years 2020-2026 (e.g. pass -> pass1, pass2024)",
    "prepend_num":    "Prepend 0-9 (e.g. pass -> 1pass)",
    "append_special": "Append common specials: ! @ # $ % & * (e.g. pass -> pass!)",
    "leet_basic":     "Basic leet substitutions (a->@, e->3, o->0, s->$, i->1)",
    "duplicate":      "Duplicate the word (e.g. pass -> passpass)",
    "strip_vowels":   "Remove all vowels (e.g. password -> psswrd)",
}

_LEET_MAP: dict[str, str] = {
    "a": "@", "A": "@",
    "e": "3", "E": "3",
    "i": "1", "I": "1",
    "o": "0", "O": "0",
    "s": "$", "S": "$",
}

_COMMON_SPECIALS = ["!", "@", "#", "$", "%", "&", "*", "?", ".", "+"]
_COMMON_YEARS = [str(y) for y in range(2020, 2027)]
_VOWELS = set("aeiouAEIOU")


def _apply_capitalize(word: str) -> list[str]:
    """Capitalize first letter."""
    cap = word.capitalize()
    return [cap] if cap != word else []


def _apply_upper(word: str) -> list[str]:
    """Uppercase the entire word."""
    up = word.upper()
    return [up] if up != word else []


def _apply_lower(word: str) -> list[str]:
    """Lowercase the entire word."""
    lo = word.lower()
    return [lo] if lo != word else []


def _apply_reverse(word: str) -> list[str]:
    """Reverse the word."""
    rev = word[::-1]
    return [rev] if rev != word else []


def _apply_toggle(word: str) -> list[str]:
    """Toggle case of each character."""
    toggled = word.swapcase()
    return [toggled] if toggled != word else []


def _apply_append_num(word: str) -> list[str]:
    """Append numbers 0-99 and common years."""
    results = []
    for n in range(100):
        results.append(f"{word}{n}")
    for year in _COMMON_YEARS:
        results.append(f"{word}{year}")
    return results


def _apply_prepend_num(word: str) -> list[str]:
    """Prepend digits 0-9."""
    return [f"{n}{word}" for n in range(10)]


def _apply_append_special(word: str) -> list[str]:
    """Append common special characters."""
    return [f"{word}{s}" for s in _COMMON_SPECIALS]


def _apply_leet_basic(word: str) -> list[str]:
    """Apply basic leet substitutions."""
    result = []
    for ch in word:
        result.append(_LEET_MAP.get(ch, ch))
    leeted = "".join(result)
    return [leeted] if leeted != word else []


def _apply_duplicate(word: str) -> list[str]:
    """Duplicate the word."""
    return [word + word]


def _apply_strip_vowels(word: str) -> list[str]:
    """Remove all vowels."""
    stripped = "".join(ch for ch in word if ch not in _VOWELS)
    return [stripped] if stripped and stripped != word else []


_RULE_FUNCS: dict[str, callable] = {
    "capitalize":     _apply_capitalize,
    "upper":          _apply_upper,
    "lower":          _apply_lower,
    "reverse":        _apply_reverse,
    "toggle":         _apply_toggle,
    "append_num":     _apply_append_num,
    "prepend_num":    _apply_prepend_num,
    "append_special": _apply_append_special,
    "leet_basic":     _apply_leet_basic,
    "duplicate":      _apply_duplicate,
    "strip_vowels":   _apply_strip_vowels,
}


def apply_rules(
    words: list[str],
    rules: list[str],
) -> Generator[str, None, None]:
    """
    Apply mangling rules to a list of words, yielding unique results.

    Args:
        words: Base words to mangle.
        rules: List of rule names to apply (keys from BUILTIN_RULES).

    Yields:
        Mangled word variants (original word + all rule outputs, deduplicated).
    """
    seen: set[str] = set()

    active_funcs = []
    for rule_name in rules:
        fn = _RULE_FUNCS.get(rule_name)
        if fn:
            active_funcs.append(fn)
        else:
            logger.warning("Unknown rule: %s — skipping.", rule_name)

    for word in words:
        if not word:
            continue

        if word not in seen:
            seen.add(word)
            yield word

        for fn in active_funcs:
            variants = fn(word)
            for v in variants:
                if v and v not in seen:
                    seen.add(v)
                    yield v
