"""
profiler.py — Interactive personal target profiling for wordlist generation.

Each variation is emitted as a separate line (one entry per line).
Generates: case variants, leet variants, token combinations, date variations,
social handles, location patterns, corporate keywords, and more.

Usage:
  wfh.py profile                       # full interactive wizard
  wfh.py profile --name "John" --nick "johnny" --birth 1990

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""

import logging
import re
from datetime import datetime, date
from typing import Generator, Optional

logger = logging.getLogger(__name__)

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


# ── Main generator ────────────────────────────────────────────────────────────

def _emit_all(
    tokens: list[str],
    date_tokens: list[str],
    separators: list[str],
    min_len: int,
    max_len: int,
    with_spaces: bool,
    seen: set[str],
) -> Generator[str, None, None]:
    """
    Yield all combinations of tokens, dates, separators.

    Yields each unique, length-filtered entry exactly once.

    Args:
        tokens: Base word tokens.
        date_tokens: Date-derived tokens.
        separators: Separators to use between tokens.
        min_len: Minimum entry length.
        max_len: Maximum entry length.
        with_spaces: Include space as a separator option.
        seen: Mutable set of already-emitted entries.

    Yields:
        Individual wordlist entries (one per line).
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

    # Token pair combinations
    limit = min(len(tokens), 15)  # Cap to avoid combinatorial explosion
    for i in range(limit):
        for j in range(limit):
            if i == j:
                continue
            for sep in seps:
                r = _try_emit(tokens[i] + sep + tokens[j])
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

    # ── Keywords & special dates ──────────────────────────────
    print("\n[ KEYWORDS & SPECIAL DATES ]")
    profile["keywords"] = _ask_multi("Keywords / topics of interest (hobbies, teams, idols...)")
    profile["special_dates"] = _ask_multi("Special dates (anniversaries, events — any format)")

    # ── Generation options ────────────────────────────────────
    print("\n[ GENERATION OPTIONS ]")
    profile["leet_mode"] = _ask("Leet mode [none/basic/medium/aggressive] (default: basic)") or "basic"
    profile["with_spaces"] = _ask("Include spaces between words? [y/N]").lower() in ("y", "yes")
    min_raw = _ask("Minimum password length (default: 6)")
    max_raw = _ask("Maximum password length (default: 32, 0 = unlimited)")
    profile["min_len"] = int(min_raw) if min_raw.isdigit() else 6
    profile["max_len"] = int(max_raw) if max_raw.isdigit() and int(max_raw) > 0 else 32
    profile["include_specials"] = _ask("Add special characters to combinations? [y/N]").lower() in ("y", "yes")

    return profile


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

    # ── Collect tokens ────────────────────────────────────────

    # Full name words
    add_words(profile.get("full_name", ""))
    add_words(profile.get("short_name", ""))

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

    # Phones
    for phone in profile.get("phones", []):
        for pv in _clean_phone(phone):
            if pv not in word_tokens:
                word_tokens.append(pv)

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

    # Special dates
    for sd in profile.get("special_dates", []):
        parsed = parse_date_input(sd)
        if parsed:
            add_dates(*parsed)
        else:
            clean_sd = re.sub(r"\D", "", sd)
            if clean_sd and clean_sd not in all_date_tokens:
                all_date_tokens.append(clean_sd)

    # Special characters override
    seps = list(WORD_SEPARATORS)
    if include_specials:
        seps.extend(["&", "*", "(", ")", "+", "=", "~"])

    # ── Emit all combinations ─────────────────────────────────
    yield from _emit_all(
        word_tokens, all_date_tokens,
        seps, effective_min, effective_max,
        with_spaces, seen,
    )
