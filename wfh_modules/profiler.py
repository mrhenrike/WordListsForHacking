"""
profiler.py — Interactive personal target profiling for wordlist generation.

Each variation is emitted as a separate line (one entry per line).
Generates: case variants, leet variants, reversed strings, name initials/fragments,
token combinations (up to depth 5), date fragment tokens, old password mutations,
social handles, location patterns, corporate keywords, religious patterns,
behavioral patterns from data/behavior_patterns.json, and multi-char special suffixes.

Inspired by CUPP, elpscrk, and BEWGor — absorbs their best mutation strategies.

Author: André Henrique (@mrhenrike)
Version: 2.4.0
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, date
from itertools import permutations as _permutations
from pathlib import Path
from typing import Generator, Optional

_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parent
_BEHAVIOR_DB: Optional[dict] = None


def _find_data_file(filename: str) -> Path:
    """Resolve data file path, checking wfh_modules/data/ first then repo root data/."""
    pkg_path = _MODULE_DIR / "data" / filename
    if pkg_path.exists():
        return pkg_path
    return _REPO_ROOT / "data" / filename

logger = logging.getLogger(__name__)


def _load_behavior_db() -> dict:
    """Load behavior_patterns.json once and cache it in memory."""
    global _BEHAVIOR_DB
    if _BEHAVIOR_DB is None:
        path = _find_data_file("behavior_patterns.json")
        try:
            with open(path, encoding="utf-8") as f:
                _BEHAVIOR_DB = json.load(f)
        except FileNotFoundError:
            logger.warning("behavior_patterns.json not found at %s", path)
            _BEHAVIOR_DB = {}
    return _BEHAVIOR_DB


def load_profile_yaml(filepath: str) -> dict:
    """
    Load a personal profile from a YAML file.

    This allows non-interactive, scripted use of the profiler.
    The YAML structure mirrors the keys returned by interactive_profile().

    Example YAML::

        full_name: "John Doe"
        short_name: "John"
        nicknames:
          - "johnny"
          - "jdoe"
        birth_day: 15
        birth_month: 3
        birth_year: 1990
        pets:
          - "Rex"
        keywords:
          - "soccer"
          - "hacker"
        leet_mode: "basic"
        min_len: 6
        max_len: 32
        year_start: 2000
        year_end: 2026
        suffix_range_start: 0
        suffix_range_end: 99
        suffix_range_zero_pad: 2

    Args:
        filepath: Path to the YAML profile file.

    Returns:
        Profile dict, same structure as interactive_profile() output.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for --profile-file. Install: pip install pyyaml"
        ) from exc

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {filepath}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Normalize list fields that might be given as strings
    for list_field in ("nicknames", "phones", "social_handles", "keywords",
                       "special_dates", "pets", "children"):
        val = data.get(list_field)
        if isinstance(val, str):
            data[list_field] = [v.strip() for v in val.split(",") if v.strip()]
        elif val is None:
            data[list_field] = []

    return data


def generate_year_range_tokens(
    year_start: int,
    year_end: int,
) -> list[str]:
    """
    Generate year string tokens for a range of years.

    Produces 4-digit and 2-digit representations.

    Args:
        year_start: First year (inclusive).
        year_end: Last year (inclusive).

    Returns:
        List of year strings (e.g., ["2020", "20", "2021", "21", ...]).
    """
    tokens: list[str] = []
    for y in range(year_start, year_end + 1):
        ys = str(y)
        tokens.append(ys)
        tokens.append(ys[-2:])
    return list(dict.fromkeys(tokens))


def generate_suffix_range_tokens(
    start: int,
    end: int,
    zero_pad: int = 0,
) -> list[str]:
    """
    Generate numeric suffix tokens for a number range.

    Args:
        start: First number (inclusive).
        end: Last number (inclusive).
        zero_pad: Minimum width for zero-padding (0 = no padding).

    Returns:
        List of formatted number strings.

    Examples:
        generate_suffix_range_tokens(0, 99, 2) → ["00", "01", ..., "99"]
        generate_suffix_range_tokens(1, 9, 0)  → ["1", "2", ..., "9"]
    """
    fmt = f"0{zero_pad}d" if zero_pad > 0 else "d"
    return [format(n, fmt) for n in range(start, end + 1)]


def list_religions() -> list[tuple[str, str]]:
    """
    Return sorted list of (key, display_name) for all religions in the DB.

    Returns:
        List of (key, display) tuples.
    """
    db = _load_behavior_db()
    religions = db.get("religions", {})
    return sorted(
        [(k, v.get("display", k)) for k, v in religions.items()],
        key=lambda x: x[1],
    )


# ── Constants ─────────────────────────────────────────────────────────────────

COMMON_SUFFIXES = [
    "1", "12", "123", "1234", "12345",
    "!", "@", "#", ".", "_", "-",
    "01", "007", "69", "99", "100", "00",
]

COMMON_PREFIXES = ["", "my", "the", "mr", "ms", "dr", "sr", "jr"]

WORD_SEPARATORS = ["", ".", "-", "_", "@", "#", "!", "$"]

LEET_BASIC: dict[str, str] = {
    "a": "@", "A": "4",
    "e": "3", "E": "3",
    "i": "1", "I": "!",
    "o": "0", "O": "0",
    "s": "$", "S": "$",
    "t": "7", "T": "7",
    "l": "1", "L": "1",
    "b": "6", "B": "8",
    "g": "9", "G": "9",
    "z": "2", "Z": "2",
}

ACCENT_MAP: dict[str, str] = {
    "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
    "é": "e", "ê": "e", "ë": "e",
    "í": "i", "î": "i", "ï": "i",
    "ó": "o", "ô": "o", "õ": "o", "ö": "o",
    "ú": "u", "û": "u", "ü": "u",
    "ç": "c", "ñ": "n",
    "Á": "A", "À": "A", "Â": "A", "Ã": "A",
    "É": "E", "Ê": "E",
    "Í": "I",
    "Ó": "O", "Ô": "O", "Õ": "O",
    "Ú": "U",
    "Ç": "C", "Ñ": "N",
}

ZODIAC = [
    ((3, 21), (4, 19), "aries"),
    ((4, 20), (5, 20), "taurus"),
    ((5, 21), (6, 20), "gemini"),
    ((6, 21), (7, 22), "cancer"),
    ((7, 23), (8, 22), "leo"),
    ((8, 23), (9, 22), "virgo"),
    ((9, 23), (10, 22), "libra"),
    ((10, 23), (11, 21), "scorpio"),
    ((11, 22), (12, 21), "sagittarius"),
    ((12, 22), (1, 19), "capricorn"),
    ((1, 20), (2, 18), "aquarius"),
    ((2, 19), (3, 20), "pisces"),
]

CHINESE_ZODIAC = [
    "rat", "ox", "tiger", "rabbit", "dragon", "snake",
    "horse", "goat", "monkey", "rooster", "dog", "pig",
]


# ── Utilities ─────────────────────────────────────────────────────────────────

def strip_accents(text: str) -> str:
    """Remove accented characters using PT/ES/FR/DE map."""
    for accented, plain in ACCENT_MAP.items():
        text = text.replace(accented, plain)
    return text


def normalize(word: str) -> str:
    """Strip accents and remove non-alphanumeric chars except dashes/underscores."""
    return strip_accents(word.strip())


def get_zodiac(day: int, month: int) -> str:
    """Return zodiac sign name for a given day and month."""
    for (sm, sd), (em, ed), name in ZODIAC:
        if sm <= em:
            if (month == sm and day >= sd) or (month == em and day <= ed):
                return name
            if sm < month < em:
                return name
        else:
            if (month == sm and day >= sd) or month > sm or (month == em and day <= ed) or month < em:
                return name
    return "unknown"


def get_chinese_zodiac(year: int) -> str:
    """Return Chinese zodiac animal for a given year."""
    return CHINESE_ZODIAC[(year - 4) % 12]


def estimate_birth_year(age: int) -> int:
    """Estimate birth year from approximate age."""
    return datetime.now().year - age


def parse_date_input(raw: str) -> Optional[tuple[int, int, int]]:
    """
    Parse a date from user input in multiple formats.

    Supports: dd/mm/yyyy, dd-mm-yyyy, ddmmyyyy, yyyy, dd/mm, dd-mm, mm/yyyy.

    Args:
        raw: Raw date string from user.

    Returns:
        Tuple (day, month, year) with 0 for unknown components, or None.
    """
    raw = raw.strip()
    if not raw:
        return None

    # yyyy only
    if re.fullmatch(r"\d{4}", raw):
        return (0, 0, int(raw))

    # ddmmyyyy
    if re.fullmatch(r"\d{8}", raw):
        return (int(raw[:2]), int(raw[2:4]), int(raw[4:]))

    # dd/mm/yyyy or dd-mm-yyyy or dd.mm.yyyy
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", raw)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # dd/mm or dd-mm
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})", raw)
    if m:
        return (int(m.group(1)), int(m.group(2)), 0)

    # mm/yyyy
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{4})", raw)
    if m:
        return (0, int(m.group(1)), int(m.group(2)))

    return None


def _split_words(text: str) -> list[str]:
    """Split text on whitespace, returning non-empty tokens."""
    return [t for t in text.replace(",", " ").split() if t]


def _word_variants(word: str, leet: bool = True) -> list[str]:
    """
    Generate case and leet variants of a single word.

    Each variant is a clean single-word token (no spaces).

    Args:
        word: Single word to vary.
        leet: Include leet substitutions.

    Returns:
        Ordered unique list of variants.
    """
    clean = normalize(word)
    if not clean:
        return []

    base = list(dict.fromkeys([
        clean,
        clean.lower(),
        clean.upper(),
        clean.capitalize(),
        clean[0].upper() + clean[1:].lower() if len(clean) > 1 else clean.upper(),
    ]))

    if leet:
        for w in list(base):
            leet_w = ""
            for ch in w:
                leet_w += LEET_BASIC.get(ch, ch)
            if leet_w not in base and leet_w != w:
                base.append(leet_w)

    return base


def _date_tokens(day: int, month: int, year: int) -> list[str]:
    """
    Generate date string tokens from date components.

    Produces: ddmmyyyy, dd/mm/yyyy, dd-mm-yyyy, yyyy, ddmm, mmyyyy,
    and reversed variants (yyyymmdd).

    Args:
        day: Day (0 = unknown).
        month: Month (0 = unknown).
        year: Year (0 = unknown).

    Returns:
        List of date token strings.
    """
    tokens: list[str] = []
    if year:
        tokens.append(str(year))
        tokens.append(str(year)[-2:])  # 2-digit year
    if day and month:
        dd = str(day).zfill(2)
        mm = str(month).zfill(2)
        tokens.extend([
            f"{dd}{mm}",
            f"{mm}{dd}",
        ])
        if year:
            yy = str(year)
            y2 = yy[-2:]
            tokens.extend([
                f"{dd}{mm}{yy}",
                f"{dd}{mm}{y2}",
                f"{yy}{mm}{dd}",
                f"{y2}{mm}{dd}",
                f"{dd}/{mm}/{yy}",
                f"{dd}-{mm}-{yy}",
                f"{dd}.{mm}.{yy}",
                f"{dd}/{mm}/{y2}",
                f"{dd}-{mm}-{y2}",
            ])
    elif month and year:
        mm = str(month).zfill(2)
        tokens.extend([f"{mm}{year}", f"{year}{mm}"])
    return list(dict.fromkeys(tokens))


def _clean_phone(phone: str) -> list[str]:
    """
    Return phone number in multiple formats: E.164, local (no +), bare digits.

    Args:
        phone: Raw phone string (e.g., '+5511912345678', '11912345678').

    Returns:
        List of phone string variants.
    """
    digits = re.sub(r"\D", "", phone)
    variants = [digits]
    if phone.startswith("+"):
        variants.append("+" + digits)
    return list(dict.fromkeys(v for v in variants if len(v) >= 7))


def _social_handle_variants(handle: str) -> list[str]:
    """
    Return social media handle with and without @ prefix.

    Args:
        handle: Handle string, optionally prefixed with @.

    Returns:
        List with/without @ variant.
    """
    clean = handle.lstrip("@").strip()
    if not clean:
        return []
    return list(dict.fromkeys([clean, f"@{clean}"]))


# ── CUPP/elpscrk/BEWGor enhancements ─────────────────────────────────────────

def _reversed_tokens(tokens: list[str]) -> list[str]:
    """Generate reversed versions of all tokens (CUPP/elpscrk/BEWGor parity)."""
    reversed_list: list[str] = []
    for tok in tokens:
        rev = tok[::-1]
        if rev != tok and len(rev) >= 3:
            reversed_list.append(rev)
    return reversed_list


def _name_initials(full_name: str) -> list[str]:
    """Extract name fragments: initials, first letter, first 2 letters (BEWGor/elpscrk parity)."""
    parts = _split_words(full_name)
    if not parts:
        return []

    fragments: list[str] = []
    initials = "".join(p[0] for p in parts if p).upper()
    if len(initials) >= 2:
        fragments.append(initials)
        fragments.append(initials.lower())

    for part in parts:
        clean = normalize(part)
        if not clean:
            continue
        fragments.append(clean[0].lower())
        fragments.append(clean[0].upper())
        if len(clean) >= 2:
            fragments.append(clean[:2].lower())
            fragments.append(clean[:2].upper())
            fragments.append(clean[:2].capitalize())

    return list(dict.fromkeys(fragments))


def _extra_date_fragments(day: int, month: int, year: int) -> list[str]:
    """Generate granular date fragments (CUPP-style: isolated day, month, year digits)."""
    frags: list[str] = []
    if day:
        frags.append(str(day))
        frags.append(str(day).zfill(2))
        if day >= 10:
            frags.append(str(day % 10))
    if month:
        frags.append(str(month))
        frags.append(str(month).zfill(2))
        if month >= 10:
            frags.append(str(month % 10))
    if year:
        ys = str(year)
        frags.append(ys)
        frags.append(ys[-2:])
        if len(ys) >= 3:
            frags.append(ys[-3:])
    return list(dict.fromkeys(frags))


def _phone_fragments(phone: str) -> list[str]:
    """Decompose phone into fragments: last 4, first 4, national format (elpscrk parity)."""
    digits = re.sub(r"\D", "", phone)
    frags: list[str] = []
    if len(digits) >= 4:
        frags.append(digits[-4:])
        frags.append(digits[:4])
    if len(digits) >= 7:
        frags.append(digits[-7:])
    if digits.startswith("55") and len(digits) > 4:
        frags.append("0" + digits[2:])
    return list(dict.fromkeys(f for f in frags if f))


MULTI_CHAR_SPECIALS = [
    "!!", "!@", "!#", "@!", "@#", "#!", "#@",
    "123", "1!", "!1", "12", "01", "!@#", "@!#",
    "$$", "**", "##", "!", "@", "#", "$", "*",
]


# ── Main generator ────────────────────────────────────────────────────────────

def _emit_all(
    tokens: list[str],
    date_tokens: list[str],
    separators: list[str],
    min_len: int,
    max_len: int,
    with_spaces: bool,
    seen: set[str],
    depth: int = 3,
) -> Generator[str, None, None]:
    """Yield all combinations of tokens, dates, separators.

    Args:
        tokens: Base word tokens.
        date_tokens: Date-derived tokens.
        separators: Separators to use between tokens.
        min_len: Minimum entry length.
        max_len: Maximum entry length.
        with_spaces: Include space as a separator option.
        seen: Mutable set of already-emitted entries.
        depth: Max permutation depth (3=default, 4=enhanced, 5=max BEWGor).
    """
    seps = list(separators)
    if with_spaces and " " not in seps:
        seps.append(" ")

    def _try_emit(s: str) -> Optional[str]:
        if s and s not in seen and min_len <= len(s) <= max_len:
            seen.add(s)
            return s
        return None

    # Single tokens
    for tok in tokens:
        r = _try_emit(tok)
        if r:
            yield r

    # Token + suffix
    for tok in tokens:
        for suf in COMMON_SUFFIXES:
            r = _try_emit(tok + suf)
            if r:
                yield r

    # Token + date token
    for tok in tokens:
        for dt in date_tokens:
            for sep in seps:
                for combo in [tok + sep + dt, dt + sep + tok]:
                    r = _try_emit(combo)
                    if r:
                        yield r

    # Token pair combinations (2-token permutations)
    limit = min(len(tokens), 15)  # Cap to avoid combinatorial explosion
    token_subset = tokens[:limit]
    for t1, t2 in _permutations(token_subset, 2):
        for sep in seps:
            r = _try_emit(t1 + sep + t2)
            if r:
                yield r

    # 3-token combinations — use first 8 tokens only to limit volume
    limit3 = min(len(tokens), 8)
    token3_subset = tokens[:limit3]
    for t1, t2, t3 in _permutations(token3_subset, 3):
        r = _try_emit(t1 + t2 + t3)
        if r:
            yield r
        non_empty_seps = [s for s in seps if s]
        if non_empty_seps:
            sep = non_empty_seps[0]
            r = _try_emit(t1 + sep + t2 + sep + t3)
            if r:
                yield r

    # 4-token combinations (depth 4, BEWGor parity) — first 6 tokens
    if depth >= 4:
        limit4 = min(len(tokens), 6)
        for t1, t2, t3, t4 in _permutations(tokens[:limit4], 4):
            r = _try_emit(t1 + t2 + t3 + t4)
            if r:
                yield r

    # 5-token combinations (depth 5, BEWGor max parity) — first 5 tokens
    if depth >= 5:
        limit5 = min(len(tokens), 5)
        for combo in _permutations(tokens[:limit5], 5):
            r = _try_emit("".join(combo))
            if r:
                yield r

    # Prefix + token
    for pref in COMMON_PREFIXES:
        if not pref:
            continue
        for tok in tokens[:10]:
            r = _try_emit(pref + tok)
            if r:
                yield r

    # Reversed tokens (CUPP/elpscrk/BEWGor parity)
    rev_tokens = _reversed_tokens(tokens[:15])
    for rev in rev_tokens:
        r = _try_emit(rev)
        if r:
            yield r
        for dt in date_tokens[:10]:
            r = _try_emit(rev + dt)
            if r:
                yield r
            r = _try_emit(dt + rev)
            if r:
                yield r

    # Multi-char special suffixes (CUPP parity)
    for tok in tokens[:12]:
        for spec in MULTI_CHAR_SPECIALS:
            r = _try_emit(tok + spec)
            if r:
                yield r


# ── Interactive wizard ────────────────────────────────────────────────────────

def _ask(prompt: str, required: bool = False) -> str:
    """Prompt user for input, repeating if required and empty."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if val or not required:
            return val


def _ask_multi(prompt: str) -> list[str]:
    """Collect multiple values, stopping on empty input."""
    print(f"  {prompt} (one per line, empty to stop):")
    values: list[str] = []
    while True:
        val = input("    > ").strip()
        if not val:
            break
        values.append(val)
    return values


def interactive_profile() -> dict:
    """
    Full interactive personal profiling wizard.

    Returns:
        Dict with all collected profile data.
    """
    print("\n" + "=" * 58)
    print("  Personal Target Profiler — Wordlist Generator")
    print("=" * 58)
    print("  Press Enter to skip any field.\n")

    profile: dict = {}

    # ── Personal ─────────────────────────────────────────────
    print("[ PERSONAL INFORMATION ]")
    profile["full_name"] = _ask("Full name")
    profile["short_name"] = _ask("Short name or part of name")
    profile["nicknames"] = _ask_multi("Nicknames/aliases")

    birth_raw = _ask("Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or approximate age)")
    if birth_raw.isdigit() and int(birth_raw) < 120:
        profile["birth_year"] = estimate_birth_year(int(birth_raw))
        profile["birth_day"] = 0
        profile["birth_month"] = 0
    else:
        parsed = parse_date_input(birth_raw)
        if parsed:
            profile["birth_day"], profile["birth_month"], profile["birth_year"] = parsed
        else:
            profile["birth_day"] = profile["birth_month"] = profile["birth_year"] = 0

    profile["national_id"] = _ask("National ID / SSN / CPF (or leave blank)")
    profile["phones"] = _ask_multi("Phone numbers (DDI+DDD+number, e.g. +5511912345678)")
    profile["location_city"] = _ask("City / hometown")
    profile["location_state"] = _ask("State / province / region")
    profile["location_country"] = _ask("Country")

    # ── Partner ───────────────────────────────────────────────
    print("\n[ PARTNER / SPOUSE ]")
    has_partner = _ask("Add partner data? [y/N]").lower() in ("y", "yes")
    if has_partner:
        profile["partner_name"] = _ask("Partner full name")
        profile["partner_nick"] = _ask("Partner nickname")
        partner_birth = _ask("Partner date of birth")
        parsed = parse_date_input(partner_birth)
        if parsed:
            profile["partner_birth_day"], profile["partner_birth_month"], profile["partner_birth_year"] = parsed
        else:
            profile["partner_birth_day"] = profile["partner_birth_month"] = profile["partner_birth_year"] = 0

    # ── Children ──────────────────────────────────────────────
    print("\n[ CHILDREN ]")
    has_children = _ask("Add children data? [y/N]").lower() in ("y", "yes")
    if has_children:
        profile["children"] = []
        while True:
            child_name = _ask("Child name (or Enter to stop)")
            if not child_name:
                break
            child_birth = _ask(f"  {child_name} date of birth")
            parsed = parse_date_input(child_birth)
            bd, bm, by = parsed if parsed else (0, 0, 0)
            profile["children"].append({
                "name": child_name,
                "birth_day": bd,
                "birth_month": bm,
                "birth_year": by,
            })

    # ── Pets ──────────────────────────────────────────────────
    print("\n[ PETS ]")
    has_pets = _ask("Add pet data? [y/N]").lower() in ("y", "yes")
    if has_pets:
        profile["pets"] = _ask_multi("Pet names")

    # ── Corporate ─────────────────────────────────────────────
    print("\n[ CORPORATE DATA ]")
    has_corp = _ask("Add corporate data? [y/N]").lower() in ("y", "yes")
    if has_corp:
        profile["company_name"] = _ask("Company name / trade name")
        profile["company_legal"] = _ask("Legal company name (razão social)")
        profile["company_email"] = _ask("Corporate email")
        profile["company_domain"] = _ask("Company domain (e.g. company.com)")

    # ── Social media ──────────────────────────────────────────
    print("\n[ SOCIAL MEDIA ]")
    profile["social_handles"] = _ask_multi(
        "Social media handles (with or without @, e.g. @mrhenrike or mrhenrike)"
    )

    # ── Religion ──────────────────────────────────────────────
    print("\n[ RELIGION & FAITH ]")
    profile["religion_key"] = None
    profile["religion_custom"] = None
    profile["church_name"] = None
    profile["church_group"] = None

    has_religion = _ask("Add religion data? [y/N]").lower() in ("y", "yes")
    if has_religion:
        religions = list_religions()
        print("\n  Available religions (enter number or press Enter to type custom):")
        for idx, (key, display) in enumerate(religions, 1):
            print(f"    {idx:>2}. {display}")
        print(f"    {len(religions)+1:>2}. Other / not listed")

        choice_raw = _ask(f"  Select [1-{len(religions)+1}]").strip()
        if choice_raw.isdigit():
            choice = int(choice_raw)
            if 1 <= choice <= len(religions):
                profile["religion_key"] = religions[choice - 1][0]
                print(f"  Selected: {religions[choice - 1][1]}")
            else:
                profile["religion_custom"] = _ask("  Enter your religion name")
        else:
            profile["religion_custom"] = choice_raw if choice_raw else None

        # Church / congregation (only if religion was filled)
        if profile["religion_key"] or profile["religion_custom"]:
            print()
            has_church = _ask("Add church / congregation / group data? [y/N]").lower() in ("y", "yes")
            if has_church:
                profile["church_name"] = _ask("  Church or congregation name (e.g. Assembleia de Deus SP)")
                profile["church_group"] = _ask("  Small group / cell / ministry name (or Enter to skip)")

    # ── Keywords & special dates ──────────────────────────────
    print("\n[ KEYWORDS & SPECIAL DATES ]")
    profile["keywords"] = _ask_multi("Keywords / topics of interest (hobbies, teams, idols...)")
    profile["special_dates"] = _ask_multi("Special dates (anniversaries, events — any format)")

    # ── Generation options ────────────────────────────────────
    print("\n[ GENERATION OPTIONS ]")
    profile["leet_mode"] = _ask("Leet mode [none/basic/medium/aggressive] (default: basic)") or "basic"
    profile["with_spaces"] = _ask("Include spaces between words? [y/N]").lower() in ("y", "yes")
    profile["use_behavior_patterns"] = _ask(
        "Include behavioral/religious patterns from knowledge base? [Y/n]"
    ).lower() not in ("n", "no")
    min_raw = _ask("Minimum password length (default: 6)")
    max_raw = _ask("Maximum password length (default: 32, 0 = unlimited)")
    profile["min_len"] = int(min_raw) if min_raw.isdigit() else 6
    profile["max_len"] = int(max_raw) if max_raw.isdigit() and int(max_raw) > 0 else 32
    profile["include_specials"] = _ask("Add special characters to combinations? [y/N]").lower() in ("y", "yes")

    return profile


# ── Behavioral pattern generator ──────────────────────────────────────────────

def _generate_from_behavior(
    profile: dict,
    seen: set[str],
    min_len: int,
    max_len: int,
) -> Generator[str, None, None]:
    """
    Yield wordlist entries derived from religion and behavioral patterns in the JSON DB.

    Uses data/behavior_patterns.json loaded offline.

    Args:
        profile: Profiler dict with religion_key, keywords, location_city, etc.
        seen: Mutable dedup set.
        min_len: Minimum entry length.
        max_len: Maximum entry length.

    Yields:
        Individual wordlist entries.
    """
    db = _load_behavior_db()
    if not db:
        return

    def _try(s: str) -> Optional[str]:
        s = s.strip()
        if s and s not in seen and min_len <= len(s) <= max_len:
            seen.add(s)
            return s
        return None

    anos = [str(y) for y in range(2016, 2027)]
    seps = ["@", "#", "_", "-", "!", ".", ""]

    # ── Religion patterns ──────────────────────────────────────
    rel_key = profile.get("religion_key")
    rel_custom = profile.get("religion_custom", "")
    church = (profile.get("church_name") or "").strip()
    group = (profile.get("church_group") or "").strip()

    rel_data: dict = {}
    if rel_key:
        rel_data = db.get("religions", {}).get(rel_key, {})

    # Keywords from religion
    for kw in rel_data.get("keywords", []):
        kw_clean = normalize(kw)
        if not kw_clean:
            continue
        r = _try(kw_clean)
        if r:
            yield r
        r = _try(kw_clean.capitalize())
        if r:
            yield r
        # kw + year
        for ano in anos:
            for sep in ["@", "#", "_", ""]:
                r = _try(f"{kw_clean}{sep}{ano}")
                if r:
                    yield r
                r = _try(f"{kw_clean.capitalize()}{sep}{ano}")
                if r:
                    yield r

    # Common phrases from religion
    for phrase in rel_data.get("phrases", []):
        p = phrase.strip()
        if not p:
            continue
        r = _try(p)
        if r:
            yield r
        r = _try(p.lower())
        if r:
            yield r
        for ano in anos:
            for sep in ["@", "#", ""]:
                r = _try(f"{p}{sep}{ano}")
                if r:
                    yield r

    # Verse references
    for ref in rel_data.get("verse_refs", []):
        r = _try(ref)
        if r:
            yield r
        for ano in anos:
            r = _try(f"{ref}{ano}")
            if r:
                yield r

    # Holy names
    for name in rel_data.get("holy_names", []):
        n = normalize(name)
        if not n:
            continue
        r = _try(n)
        if r:
            yield r
        for ano in anos:
            for sep in ["@", "#", ""]:
                r = _try(f"{n}{sep}{ano}")
                if r:
                    yield r
                r = _try(f"{n.lower()}{sep}{ano}")
                if r:
                    yield r

    # Common titles from religion
    for title in rel_data.get("common_titles", []):
        t = normalize(title).replace(" ", "")
        if not t:
            continue
        r = _try(t)
        if r:
            yield r

    # Prebuilt common passwords
    for pw in rel_data.get("common_passwords", []):
        r = _try(pw)
        if r:
            yield r

    # Church name patterns
    if church:
        ch_clean = normalize(church).replace(" ", "")
        for sep in seps:
            for ano in anos:
                r = _try(f"{ch_clean}{sep}{ano}")
                if r:
                    yield r
        r = _try(ch_clean)
        if r:
            yield r
        r = _try(ch_clean.lower())
        if r:
            yield r
        r = _try(ch_clean.upper())
        if r:
            yield r

    # Church + group
    if group:
        gr_clean = normalize(group).replace(" ", "")
        r = _try(gr_clean)
        if r:
            yield r
        if ch_clean if church else "":
            r = _try(f"{ch_clean}{gr_clean}")
            if r:
                yield r
            for sep in ["@", "#", "_", ""]:
                for ano in anos:
                    r = _try(f"{gr_clean}{sep}{ano}")
                    if r:
                        yield r

    # Custom religion name
    if rel_custom:
        rc = normalize(rel_custom).replace(" ", "")
        for sep in seps:
            for ano in anos:
                r = _try(f"{rc}{sep}{ano}")
                if r:
                    yield r
        r = _try(rc)
        if r:
            yield r

    # ── BR cultural phrases ────────────────────────────────────
    for phrase in db.get("cultural_phrases_br", {}).get("popular", []):
        r = _try(phrase)
        if r:
            yield r
    for phrase in db.get("cultural_phrases_br", {}).get("religious_phrases_br", []):
        r = _try(phrase)
        if r:
            yield r

    # ── Keyword-based behavioral patterns ─────────────────────
    profile_keywords = [normalize(kw).replace(" ", "") for kw in profile.get("keywords", [])]
    for kw in profile_keywords:
        if not kw:
            continue
        for bp_key, bp_data in db.get("behavioral_patterns", {}).items():
            # Check if keyword matches sports/music/gaming
            bp_kws = [k.lower() for k in bp_data.get("keywords", [])]
            if any(kw.lower() in bk or bk in kw.lower() for bk in bp_kws):
                for pat in bp_data.get("patterns", [])[:5]:
                    candidate = pat.replace("{clube}", kw).replace("{artista}", kw).replace("{game}", kw).replace("{nick}", kw).replace("{ano}", anos[-1])
                    r = _try(candidate)
                    if r:
                        yield r

    # ── Sports fan: city/club combos ─────────────────────────
    city = normalize(profile.get("location_city", "")).replace(" ", "")
    if city:
        for club in db.get("behavioral_patterns", {}).get("sports_fan", {}).get("br_clubs", []):
            cl = normalize(club)
            for ano in anos[-3:]:  # last 3 years only to limit volume
                r = _try(f"{cl}@{ano}")
                if r:
                    yield r



# ── Generation ────────────────────────────────────────────────────────────────

def generate_from_profile(
    profile: dict,
    leet_mode: Optional[str] = None,
    min_len: int = 6,
    max_len: int = 32,
    with_spaces: bool = False,
    include_specials: bool = False,
) -> Generator[str, None, None]:
    """
    Generate wordlist from personal profile data.

    Each variation is yielded as a single separate string (one per line).

    Args:
        profile: Dict returned by interactive_profile() or manually built.
        leet_mode: Override leet mode ('none', 'basic', 'medium', 'aggressive').
        min_len: Minimum entry length.
        max_len: Maximum entry length (0 = unlimited).
        with_spaces: Include space as separator in combinations.
        include_specials: Include special char variants.

    Yields:
        Individual wordlist entries, one per yield.
    """
    use_leet = leet_mode or profile.get("leet_mode", "basic")
    do_leet = use_leet not in ("none", "")
    effective_max = max_len if max_len > 0 else 9999
    effective_min = min_len

    # Override from profile if present
    if profile.get("min_len"):
        effective_min = profile["min_len"]
    if profile.get("max_len"):
        effective_max = profile["max_len"]
    if profile.get("with_spaces"):
        with_spaces = profile["with_spaces"]
    if profile.get("include_specials"):
        include_specials = profile["include_specials"]

    seen: set[str] = set()
    word_tokens: list[str] = []
    all_date_tokens: list[str] = []

    def add_words(text: str) -> None:
        """Add all word variants from a text string."""
        for word in _split_words(text):
            for variant in _word_variants(word, leet=do_leet):
                if variant and variant not in word_tokens:
                    word_tokens.append(variant)

    def add_dates(day: int, month: int, year: int) -> None:
        """Add date tokens from date components."""
        for dt in _date_tokens(day, month, year):
            if dt not in all_date_tokens:
                all_date_tokens.append(dt)

    depth = profile.get("depth", 3) or 3

    # ── Collect tokens ────────────────────────────────────────

    # Full name words
    add_words(profile.get("full_name", ""))
    add_words(profile.get("short_name", ""))

    # Name initials and fragments (BEWGor/elpscrk parity)
    for name_field in ("full_name", "short_name"):
        for frag in _name_initials(profile.get(name_field, "")):
            if frag and frag not in word_tokens:
                word_tokens.append(frag)

    # Surname as separate field (CUPP parity)
    surname = profile.get("surname", "")
    if surname:
        add_words(surname)

    # Nicknames
    for nick in profile.get("nicknames", []):
        add_words(nick)

    # Birth date
    day = profile.get("birth_day", 0) or 0
    month = profile.get("birth_month", 0) or 0
    year = profile.get("birth_year", 0) or 0
    add_dates(day, month, year)

    # Zodiac
    if day and month:
        zodiac = get_zodiac(day, month)
        add_words(zodiac)
        if year:
            add_words(get_chinese_zodiac(year))

    # National ID as token
    nid = profile.get("national_id", "").strip()
    if nid:
        clean_nid = re.sub(r"\D", "", nid)
        for v in [nid, clean_nid]:
            if v and v not in word_tokens:
                word_tokens.append(v)

    # Old passwords (elpscrk parity)
    for oldpwd in profile.get("old_passwords", []):
        if oldpwd and oldpwd not in word_tokens:
            word_tokens.append(oldpwd)
        rev = oldpwd[::-1]
        if rev and rev != oldpwd and rev not in word_tokens:
            word_tokens.append(rev)

    # Phones + fragments (elpscrk parity)
    for phone in profile.get("phones", []):
        for pv in _clean_phone(phone):
            if pv not in word_tokens:
                word_tokens.append(pv)
        for frag in _phone_fragments(phone):
            if frag not in word_tokens:
                word_tokens.append(frag)

    # Location
    add_words(profile.get("location_city", ""))
    add_words(profile.get("location_state", ""))
    add_words(profile.get("location_country", ""))

    # Partner
    add_words(profile.get("partner_name", ""))
    add_words(profile.get("partner_nick", ""))
    add_dates(
        profile.get("partner_birth_day", 0) or 0,
        profile.get("partner_birth_month", 0) or 0,
        profile.get("partner_birth_year", 0) or 0,
    )

    # Children
    for child in profile.get("children", []):
        add_words(child.get("name", ""))
        add_dates(
            child.get("birth_day", 0) or 0,
            child.get("birth_month", 0) or 0,
            child.get("birth_year", 0) or 0,
        )

    # Pets
    for pet in profile.get("pets", []):
        add_words(pet)

    # Corporate
    add_words(profile.get("company_name", ""))
    add_words(profile.get("company_legal", ""))
    email = profile.get("company_email", "")
    if email:
        word_tokens.append(email)
        local = email.split("@")[0]
        if local:
            add_words(local)
    domain = profile.get("company_domain", "").replace("https://", "").replace("http://", "")
    if domain:
        add_words(domain.split(".")[0])

    # Social handles
    for handle in profile.get("social_handles", []):
        for hv in _social_handle_variants(handle):
            if hv not in word_tokens:
                word_tokens.append(hv)

    # Keywords
    for kw in profile.get("keywords", []):
        add_words(kw)

    # Religion tokens (church/group names as word tokens)
    church = (profile.get("church_name") or "").strip()
    if church:
        add_words(church)
    church_group = (profile.get("church_group") or "").strip()
    if church_group:
        add_words(church_group)
    rel_custom = (profile.get("religion_custom") or "").strip()
    if rel_custom:
        add_words(rel_custom)

    # Special dates
    for sd in profile.get("special_dates", []):
        parsed = parse_date_input(sd)
        if parsed:
            add_dates(*parsed)
        else:
            clean_sd = re.sub(r"\D", "", sd)
            if clean_sd and clean_sd not in all_date_tokens:
                all_date_tokens.append(clean_sd)

    # ── Year range tokens (--year-start / --year-end) ─────────
    y_start = profile.get("year_start")
    y_end = profile.get("year_end")
    if y_start and y_end:
        for yt in generate_year_range_tokens(int(y_start), int(y_end)):
            if yt not in all_date_tokens:
                all_date_tokens.append(yt)

    # ── Suffix range tokens (--suffix-range) ──────────────────
    sr_start = profile.get("suffix_range_start")
    sr_end = profile.get("suffix_range_end")
    if sr_start is not None and sr_end is not None:
        zero_pad = int(profile.get("suffix_range_zero_pad", 0))
        for st in generate_suffix_range_tokens(int(sr_start), int(sr_end), zero_pad):
            # Add as date-like suffixes to combine with word_tokens
            if st not in all_date_tokens:
                all_date_tokens.append(st)

    # Extra date fragments (CUPP-style granular: isolated day, month, year digits)
    for date_src in [
        (day, month, year),
        (profile.get("partner_birth_day", 0) or 0,
         profile.get("partner_birth_month", 0) or 0,
         profile.get("partner_birth_year", 0) or 0),
    ]:
        for frag in _extra_date_fragments(*date_src):
            if frag not in all_date_tokens:
                all_date_tokens.append(frag)

    # Parents and siblings (BEWGor parity)
    for parent in profile.get("parents", []):
        if isinstance(parent, dict):
            add_words(parent.get("name", ""))
        elif isinstance(parent, str):
            add_words(parent)
    for sibling in profile.get("siblings", []):
        if isinstance(sibling, dict):
            add_words(sibling.get("name", ""))
        elif isinstance(sibling, str):
            add_words(sibling)

    # Special characters override
    seps = list(WORD_SEPARATORS)
    if include_specials:
        seps.extend(["&", "*", "(", ")", "+", "=", "~"])

    # ── Emit all token combinations ───────────────────────────
    yield from _emit_all(
        word_tokens, all_date_tokens,
        seps, effective_min, effective_max,
        with_spaces, seen, depth=depth,
    )

    # ── Behavioral/religious patterns from JSON DB ────────────
    if profile.get("use_behavior_patterns", True):
        yield from _generate_from_behavior(
            profile, seen, effective_min, effective_max,
        )
