"""
wfh_modules/osint_perm.py - OSINT Permutation Engine.

Generates target-aware password candidates from OSINT profile data:
  - Name, nickname, pet name permutations (lowercase, capitalized, reversed)
  - Dates: birth, anniversary, important events (dd-mm-yyyy, ddmmyyyy, etc.)
  - Phone numbers: extracted pattern from BR DDD prefix
  - Old passwords: leet transform variants
  - Combinations at multiple complexity levels

Native Python reimplementation of:
  - submodules/Wordlists/elpscrk/perm_classes.py (names_perm, dates_perm)
  - submodules/Wordlists/elpscrk/elpscrk.py (main_ganerator logic)

No external dependencies beyond Python stdlib.

Author: Andre Henrique (@mrhenrike) | Uniao Geek - https://github.com/Uniao-Geek
Version: 1.0.0
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Optional

__version__ = "1.0.0"

# Leet substitution map
_LEET: Dict[str, str] = {
    "a": "4", "i": "1", "e": "3", "t": "7",
    "o": "0", "s": "5", "g": "9", "z": "2", "l": "1",
}

# Common password suffixes added to word stems
_COMMON_SUFFIXES = [
    "", "1", "12", "123", "1234", "12345",
    "!", "@", "#", "01", "02",
    "2020", "2021", "2022", "2023", "2024", "2025",
]

# Special chars appended to indicate common patterns
_SPECIAL_CHARS = ["!", "@", "#", "$", "*", ".", "_", "-"]


def _make_leet(word: str) -> List[str]:
    """Generate leet variations of a word (single-substitution only for speed)."""
    variants = [word]
    for orig, replacement in _LEET.items():
        if orig in word.lower():
            variants.append(word.lower().replace(orig, replacement))
    return variants


def _word_variants(word: str, level: int = 1) -> List[str]:
    """Generate case/leet variants of a word.

    Level 1: lower + capitalized
    Level 2: + upper + reversed + leet
    """
    variants = [word.lower(), word.capitalize()]
    if level >= 2:
        variants += [word.upper(), word[::-1].lower()]
        variants += _make_leet(word)
    return list(dict.fromkeys(variants))  # preserve order, deduplicate


def _date_variants(date_str: str) -> List[str]:
    """Generate common date format permutations from 'dd-mm-yyyy'."""
    try:
        parts = date_str.strip().split("-")
        if len(parts) != 3:
            return []
        day, month, year = parts[0], parts[1], parts[2]
        year2 = year[-2:]
        month2 = month.zfill(2)
        day2 = day.zfill(2)
    except Exception:
        return []

    return [
        f"{day}{month}{year}",
        f"{day2}{month2}{year}",
        f"{year}{month2}{day2}",
        f"{day2}{month2}{year2}",
        f"{year2}{month2}{day2}",
        day, month, year, year2,
        f"{month}{year}",
        f"{year}{month}",
    ]


@dataclass
class OsintProfile:
    """Target profile for OSINT-based password generation."""
    first_name: str = ""
    last_name: str = ""
    nickname: str = ""
    pet_name: str = ""
    partner_name: str = ""
    birth_date: str = ""          # Format: dd-mm-yyyy
    anniversary_date: str = ""    # Format: dd-mm-yyyy
    phone: str = ""               # Digits only
    old_passwords: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    complexity: int = 1           # 1=basic, 2=full


class OsintPermGenerator:
    """Generate password candidates from OSINT profile data.

    Usage:
        profile = OsintProfile(first_name="Andre", birth_date="01-01-1990")
        gen = OsintPermGenerator()
        passwords = gen.generate(profile)
    """

    def generate(self, profile: OsintProfile) -> List[str]:
        """Generate all password candidates from profile.

        Args:
            profile: OSINT profile data.

        Returns:
            Deduplicated list of password candidates.
        """
        candidates = []
        level = profile.complexity

        # Collect base words from profile fields
        base_words = []
        for field_val in [
            profile.first_name, profile.last_name,
            profile.nickname, profile.pet_name, profile.partner_name,
        ]:
            if field_val.strip():
                base_words.append(field_val.strip())

        # Add keywords
        base_words.extend(k.strip() for k in profile.keywords if k.strip())

        # Generate word variants
        all_word_variants = []
        for word in base_words:
            all_word_variants.extend(_word_variants(word, level))

        # Standalone words
        candidates.extend(all_word_variants)

        # Words + common suffixes
        for word in all_word_variants:
            for suf in _COMMON_SUFFIXES:
                candidates.append(word + suf)

        # Date variants
        for date_str in [profile.birth_date, profile.anniversary_date]:
            if date_str.strip():
                date_vars = _date_variants(date_str)
                candidates.extend(date_vars)
                # Words + dates
                for word in all_word_variants:
                    for dv in date_vars:
                        candidates.append(word + dv)
                        if level >= 2:
                            candidates.append(dv + word)

        # Phone patterns
        if profile.phone:
            phone_digits = "".join(c for c in profile.phone if c.isdigit())
            if phone_digits:
                candidates.extend([
                    phone_digits,
                    phone_digits[-8:],   # last 8 digits
                    phone_digits[-9:],   # last 9 digits
                    phone_digits[:4],    # area code
                ])
                for word in all_word_variants[:5]:
                    candidates.append(word + phone_digits[-4:])

        # Old password variants
        for old_pwd in profile.old_passwords:
            if old_pwd.strip():
                candidates.extend(_make_leet(old_pwd))
                for suf in ["1", "2", "!", "2024", "2025"]:
                    candidates.append(old_pwd + suf)

        # Word pairs (level 2)
        if level >= 2 and len(all_word_variants) > 1:
            for w1, w2 in itertools.combinations(all_word_variants[:6], 2):
                candidates.append(w1 + w2)
                candidates.append(w1 + "_" + w2)

        # Filter: min length 4, max length 32
        result = []
        seen = set()
        for c in candidates:
            c = c.strip()
            if 4 <= len(c) <= 32 and c not in seen:
                seen.add(c)
                result.append(c)

        return result

    def generate_lazy(self, profile: OsintProfile) -> Generator[str, None, None]:
        """Lazy generator version for large profiles."""
        for pwd in self.generate(profile):
            yield pwd
