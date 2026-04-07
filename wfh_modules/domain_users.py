"""
domain_users.py — Corporate domain username and password generation.

Generates realistic corporate username/password combinations from employee
name lists, applying globally used naming conventions plus Brazilian patterns.

Features:
  - 25+ corporate username patterns (firstname.lastname, f.lastname, etc.)
  - Employee name collection from any file (txt/csv/xlsx/pdf/docx)
  - Online name search via Google dorks (no mandatory API)
  - Optional LinkedIn API via LINKEDIN_RAPIDAPI_KEY env var (graceful fallback)
  - Subdomain-admin pattern generation (a1t3ngrt → a1t3ngrtadmin)
  - Password generation from behavioral + corporate context
  - Accent normalization for Brazilian/Portuguese names
  - Custom pattern support

Usage:
  wfh.py corp-users --domain empresa.com.br --file employees.txt
  wfh.py corp-users --domain empresa.com.br --search "Empresa XPTO"
  wfh.py corp-users --domain empresa.com.br --subdomain a1t3ngrt
  wfh.py corp-users --domain empresa.com.br --file names.txt --passwords --out combo.lst
  wfh.py corp-users --domain empresa.com.br --interactive

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""

import logging
import os
import re
import time
from itertools import product
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# ── Accent normalization table ─────────────────────────────────────────────────

_ACCENT_MAP: dict[str, str] = str.maketrans(
    "áàãâäéèêëíìîïóòõôöúùûüçñÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇÑ",
    "aaaaaaeeeeiiiiooooouuuucnAAAAEEEEIIIIOOOOOUUUUCN",
)


def _norm(text: str) -> str:
    """Normalize: strip accents, lowercase, keep only word chars."""
    return text.translate(_ACCENT_MAP).lower().strip()


def _clean(text: str) -> str:
    """Normalize and strip non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", _norm(text))


# ── Name parsing ───────────────────────────────────────────────────────────────

def parse_full_name(full_name: str) -> dict:
    """
    Parse a full name string into structured components.

    Handles compound last names (da Silva, de Oliveira, etc.) and
    Brazilian naming conventions.

    Args:
        full_name: Full name string (e.g., "João da Silva Oliveira").

    Returns:
        Dict with keys:
          - first: First name
          - middle: List of middle names (may be empty)
          - last: Last name (last token, may include particles)
          - all_parts: All name parts as list
          - initials: String of first letters of each part
          - fi: First letter of first name
          - li: First letter of last name
    """
    # Portuguese/Brazilian name particles (prepositions) — not counted as names
    particles = {"da", "de", "do", "das", "dos", "di", "du", "van", "von", "del", "el", "la", "le"}

    raw_parts = [p.strip() for p in full_name.split() if p.strip()]
    if not raw_parts:
        return {
            "first": "", "middle": [], "last": "",
            "all_parts": [], "initials": "", "fi": "", "li": "",
        }

    # Filter out pure particles for building name parts
    name_parts = [p for p in raw_parts if p.lower() not in particles]

    if not name_parts:
        name_parts = raw_parts

    first = name_parts[0]
    last = name_parts[-1] if len(name_parts) > 1 else ""
    middle = name_parts[1:-1] if len(name_parts) > 2 else []

    # Build initials from all parts (including particles skipped)
    initials = "".join(p[0] for p in raw_parts if p)

    return {
        "first": first,
        "middle": middle,
        "last": last,
        "all_parts": name_parts,
        "raw_parts": raw_parts,
        "initials": initials,
        "fi": first[0] if first else "",
        "li": last[0] if last else "",
        "mi": middle[0][0] if middle else "",
    }


# ── Corporate username patterns ────────────────────────────────────────────────

# Each entry: (pattern_id, description, generator_key)
# Tokens:
#   {fn}  = first name (normalized, no accents)
#   {ln}  = last name
#   {mn}  = first middle name (empty if none)
#   {fi}  = first initial
#   {li}  = last initial
#   {mi}  = middle initial
#   {ini} = all initials
#   {all} = first + last (no sep)
#   SEP   = separator (., -, _, or "" — iterated per pattern)
CORPORATE_PATTERNS: list[dict] = [
    # ── Most common globally ───────────────────────────────────────────
    {"id": "fn_sep_ln",       "desc": "firstname.lastname",          "fmt": "{fn}{sep}{ln}"},
    {"id": "ln_sep_fn",       "desc": "lastname.firstname",          "fmt": "{ln}{sep}{fn}"},
    {"id": "fi_sep_ln",       "desc": "f.lastname (initial+last)",   "fmt": "{fi}{sep}{ln}"},
    {"id": "fn_sep_li",       "desc": "firstname.l (name+initial)",  "fmt": "{fn}{sep}{li}"},
    {"id": "fi_ln",           "desc": "flastname (no sep)",          "fmt": "{fi}{ln}"},
    {"id": "fn_li",           "desc": "firstnamel (name+initial)",   "fmt": "{fn}{li}"},
    {"id": "fn_only",         "desc": "firstname",                   "fmt": "{fn}"},
    {"id": "ln_only",         "desc": "lastname",                    "fmt": "{ln}"},
    {"id": "fn_ln",           "desc": "firstnamelastname (no sep)",  "fmt": "{fn}{ln}"},
    {"id": "ln_fn",           "desc": "lastnamefirstname (no sep)",  "fmt": "{ln}{fn}"},
    # ── With middle name (when available) ─────────────────────────────
    {"id": "fn_sep_mn_sep_ln","desc": "first.middle.last",           "fmt": "{fn}{sep}{mn}{sep}{ln}", "needs_middle": True},
    {"id": "fi_mi_ln",        "desc": "fml (first+mid+last initials)","fmt": "{fi}{mi}{ln}",           "needs_middle": True},
    {"id": "fi_sep_mi_sep_li","desc": "f.m.l (all initials)",        "fmt": "{fi}{sep}{mi}{sep}{li}", "needs_middle": True},
    # ── Initials only ────────────────────────────────────────────────
    {"id": "fi_li",           "desc": "initials (fl)",               "fmt": "{fi}{li}"},
    {"id": "ini",             "desc": "all initials (fml...)",       "fmt": "{ini}"},
    # ── Reversed / alternative ───────────────────────────────────────
    {"id": "ln_sep_fi",       "desc": "lastname.f",                  "fmt": "{ln}{sep}{fi}"},
    {"id": "ln_fi",           "desc": "lastnamef",                   "fmt": "{ln}{fi}"},
    # ── BR-specific patterns ─────────────────────────────────────────
    {"id": "fn_sep_ln_br",    "desc": "nome.sobrenome",              "fmt": "{fn}{sep}{ln}"},  # alias for PT-BR
    {"id": "fi_sep_ln_br",    "desc": "nsobrenome (initial+sobrenome)","fmt": "{fi}{ln}"},
    # ── With numeric suffix (service/generic accounts) ────────────────
    {"id": "fn_sep_ln_num",   "desc": "firstname.lastname + 2-digit suffix", "fmt": "{fn}{sep}{ln}{num}"},
    {"id": "fi_ln_num",       "desc": "flastname + 2-digit suffix",  "fmt": "{fi}{ln}{num}"},
    # ── Dept/role-based (admin variants) ─────────────────────────────
    {"id": "fn_sep_ln_adm",   "desc": "firstname.lastname.admin",    "fmt": "{fn}{sep}{ln}{sep}admin"},
    {"id": "adm_fn_sep_ln",   "desc": "admin.firstname.lastname",    "fmt": "admin{sep}{fn}{sep}{ln}"},
    # ── Subdomain/service account ────────────────────────────────────
    {"id": "sub_admin",       "desc": "subdomain+admin",             "fmt": "{sub}admin",     "subdomain": True},
    {"id": "sub_sep_admin",   "desc": "subdomain.admin",             "fmt": "{sub}{sep}admin","subdomain": True},
    {"id": "admin_sep_sub",   "desc": "admin.subdomain",             "fmt": "admin{sep}{sub}","subdomain": True},
]

# Separators used when generating with SEP token
DOMAIN_SEPARATORS = [".", "_", "-", ""]

# Numeric suffixes for generic/service accounts
NUMERIC_SUFFIXES = ["01", "02", "1", "2", "00", "10", "99"]


# ── Username generation ────────────────────────────────────────────────────────

def generate_usernames_from_name(
    full_name: str,
    domain: str,
    separators: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
    with_at_domain: bool = True,
    subdomain: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Generate all corporate username variations for a single person's name.

    Args:
        full_name: Full name of the employee.
        domain: Company domain (e.g., 'empresa.com.br').
        separators: Separator characters to use (default: ['.', '_', '-', '']).
        patterns: List of pattern IDs to include (default: all).
        with_at_domain: If True, appends '@domain' to each username.
        subdomain: Subdomain prefix for subdomain-admin patterns.

    Yields:
        Username strings (with or without @domain).
    """
    parsed = parse_full_name(full_name)
    fn = _clean(parsed["first"])
    ln = _clean(parsed["last"])
    fi = fn[0] if fn else ""
    li = ln[0] if ln else ""
    mn = _clean(parsed["middle"][0]) if parsed["middle"] else ""
    mi = mn[0] if mn else ""
    ini = _clean(parsed["initials"])

    if not fn and not ln:
        return

    seps = separators if separators is not None else DOMAIN_SEPARATORS
    filter_ids = set(patterns) if patterns else None
    seen: set[str] = set()
    sub = _clean(subdomain) if subdomain else ""

    suffix = "@" + domain if with_at_domain else ""

    def _emit(user: str) -> Optional[str]:
        # Skip entries that are empty, start/end with separator, or have no alphanumeric chars
        if not user or user in seen:
            return None
        if not re.search(r"[a-z0-9]", user):
            return None
        # Skip if user contains double-separator sequences (bad names)
        if re.search(r"[._\-]{2,}", user):
            return None
        # Skip if user starts or ends with a separator char
        if user[0] in "._-" or user[-1] in "._-":
            return None
        seen.add(user)
        return user + suffix

    for pat in CORPORATE_PATTERNS:
        pid = pat["id"]
        if filter_ids and pid not in filter_ids:
            continue
        if pat.get("needs_middle") and not mn:
            continue
        if pat.get("subdomain") and not sub:
            continue
        # Skip patterns requiring a last name if last name is empty
        if not ln and any(tok in pat["fmt"] for tok in ("{ln}", "{li}")):
            continue
        # Skip patterns requiring a first name if first name is empty
        if not fn and any(tok in pat["fmt"] for tok in ("{fn}", "{fi}")):
            continue

        fmt = pat["fmt"]

        if "{sep}" in fmt:
            for sep in seps:
                for num in (NUMERIC_SUFFIXES if "{num}" in fmt else [""]):
                    try:
                        user = fmt.format(
                            fn=fn, ln=ln, fi=fi, li=li,
                            mn=mn, mi=mi, ini=ini, sep=sep,
                            num=num, sub=sub,
                        )
                    except KeyError:
                        continue
                    r = _emit(user)
                    if r:
                        yield r
        else:
            for num in (NUMERIC_SUFFIXES if "{num}" in fmt else [""]):
                try:
                    user = fmt.format(
                        fn=fn, ln=ln, fi=fi, li=li,
                        mn=mn, mi=mi, ini=ini, num=num, sub=sub,
                    )
                except KeyError:
                    continue
                r = _emit(user)
                if r:
                    yield r


def generate_usernames_from_list(
    names: list[str],
    domain: str,
    separators: Optional[list[str]] = None,
    patterns: Optional[list[str]] = None,
    with_at_domain: bool = True,
    subdomain: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Generate username variations for a list of employee names.

    Args:
        names: List of full name strings.
        domain: Company domain.
        separators: Separator chars (default: ['.', '_', '-', '']).
        patterns: List of pattern IDs to include.
        with_at_domain: Append '@domain' suffix.
        subdomain: Subdomain prefix for admin patterns.

    Yields:
        Username strings.
    """
    global_seen: set[str] = set()
    for name in names:
        name = name.strip()
        if not name or name.startswith("#"):
            continue
        for user in generate_usernames_from_name(
            name, domain, separators, patterns, with_at_domain, subdomain
        ):
            if user not in global_seen:
                global_seen.add(user)
                yield user


def generate_subdomain_admin_users(
    subdomains: list[str],
    domain: str,
    with_at_domain: bool = False,
) -> Generator[str, None, None]:
    """
    Generate admin/service account usernames from subdomain prefixes.

    Pattern: a1t3ngrt.securonix.net → a1t3ngrtadmin, a1t3ngrt_admin, etc.

    Args:
        subdomains: List of subdomain prefixes (e.g., ['a1t3ngrt', 'webmail']).
        domain: Company domain for context.
        with_at_domain: Append '@domain' to results.

    Yields:
        Admin username strings.
    """
    seen: set[str] = set()
    suffix = "@" + domain if with_at_domain else ""

    for sub in subdomains:
        sub = _clean(sub)
        if not sub:
            continue
        candidates = [
            sub + "admin",
            sub + "_admin",
            sub + ".admin",
            "admin_" + sub,
            "admin." + sub,
            "admin" + sub,
            sub + "-admin",
            "admin-" + sub,
            sub,                # bare subdomain as user
        ]
        for c in candidates:
            if c not in seen:
                seen.add(c)
                yield c + suffix


# ── Name collection from file ──────────────────────────────────────────────────

def collect_names_from_file(filepath: str) -> list[str]:
    """
    Extract person names from any supported file type.

    Supported formats: .txt, .csv, .tsv, .xlsx, .xls, .pdf, .docx, .doc, .md

    The function reads lines/cells and returns values that look like person names
    (at least 2 words, non-numeric, no URLs/emails).

    Args:
        filepath: Path to the input file.

    Returns:
        List of candidate full name strings.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = path.suffix.lower()
    raw_values: list[str] = []

    if ext in (".txt", ".md", ".lst", ".csv", ".tsv"):
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # CSV: take first non-numeric column
                    parts = re.split(r"[,;\t]", line)
                    for p in parts:
                        p = p.strip().strip('"').strip("'")
                        if p:
                            raw_values.append(p)

    elif ext in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    for cell in row:
                        if cell:
                            raw_values.append(str(cell).strip())
        except ImportError:
            logger.warning("openpyxl not installed. Install: pip install openpyxl")

    elif ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    raw_values.extend(text.splitlines())
        except ImportError:
            logger.warning("pdfplumber not installed. Install: pip install pdfplumber")

    elif ext in (".docx",):
        try:
            import docx
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                if para.text.strip():
                    raw_values.append(para.text.strip())
        except ImportError:
            logger.warning("python-docx not installed. Install: pip install python-docx")

    else:
        # Fallback: read as plain text
        with path.open(encoding="utf-8", errors="replace") as f:
            raw_values = [line.strip() for line in f if line.strip()]

    return _filter_names(raw_values)


def _filter_names(candidates: list[str]) -> list[str]:
    """
    Filter a list of raw strings to retain only plausible person names.

    Rejects: URLs, emails, pure numbers, very short strings, strings with
    typical non-name patterns (CPF, CNPJ, phone numbers).

    Args:
        candidates: Raw strings to filter.

    Returns:
        List of plausible name strings.
    """
    _email_re = re.compile(r"@|https?://|www\.|\.com")
    _numeric_re = re.compile(r"^\d+[\d\.\-\/]*$")
    _cpf_re = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
    _phone_re = re.compile(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}")

    names: list[str] = []
    seen: set[str] = set()

    for raw in candidates:
        s = raw.strip()
        if not s or len(s) < 4:
            continue
        if _email_re.search(s):
            continue
        if _numeric_re.match(s):
            continue
        if _cpf_re.search(s):
            continue
        if _phone_re.search(s):
            continue
        # Must have at least one letter
        if not re.search(r"[a-zA-ZÀ-ÿ]", s):
            continue
        # Normalize spacing
        s = re.sub(r"\s+", " ", s).strip()
        if s.lower() not in seen:
            seen.add(s.lower())
            names.append(s)

    return names


# ── Online name search (no mandatory API) ─────────────────────────────────────

def search_names_google_dorks(
    company_name: str,
    domain: Optional[str] = None,
    max_results: int = 50,
    delay: float = 2.0,
) -> list[str]:
    """
    Search for employee names via Google dorks (no API required).

    Uses search queries like:
      site:linkedin.com/in "at CompanyName"
      "CompanyName" "LinkedIn" people employees

    Note: Google may rate-limit or block. The function applies delays
    and respects response codes. Results are parsed from snippets.

    Args:
        company_name: Company name to search for.
        domain: Optional company domain for extra context.
        max_results: Maximum names to collect.
        delay: Delay between requests in seconds.

    Returns:
        List of candidate name strings found.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("requests and beautifulsoup4 required. Install: pip install requests beautifulsoup4")
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    queries = [
        f'site:linkedin.com/in "{company_name}"',
        f'site:linkedin.com "at {company_name}"',
    ]
    if domain:
        queries.append(f'site:linkedin.com "{domain}"')

    _name_re = re.compile(r"\b([A-ZÁÀÃÉÊÍÓÔÕÚ][a-záàãéêíóôõúç]+(?:\s+[A-ZÁÀÃÉÊÍÓÔÕÚ][a-záàãéêíóôõúç]+){1,4})\b")

    collected: list[str] = []
    seen: set[str] = set()

    for query in queries:
        if len(collected) >= max_results:
            break
        try:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=20&hl=pt-BR"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 429:
                logger.warning("Google rate-limited. Try again later or use --file.")
                break
            if resp.status_code != 200:
                logger.debug("Google returned %d for query: %s", resp.status_code, query)
                continue

            soup = BeautifulSoup(resp.content.decode("utf-8", errors="replace"), "lxml")

            # Parse h3 titles and snippet divs
            for el in soup.find_all(["h3", "div"], class_=lambda c: c and ("BNeawe" in c or "VwiC3b" in c)):
                text = el.get_text(" ", strip=True)
                for match in _name_re.finditer(text):
                    name = match.group(1).strip()
                    if len(name.split()) >= 2 and name.lower() not in seen:
                        seen.add(name.lower())
                        collected.append(name)
                        if len(collected) >= max_results:
                            break

            time.sleep(delay)

        except Exception as exc:
            logger.debug("Error during Google dork search: %s", exc)
            continue

    return collected


def search_names_linkedin_api(
    company_name: str,
    max_results: int = 50,
) -> list[str]:
    """
    Search for employee names via LinkedIn API (RapidAPI).

    Requires LINKEDIN_RAPIDAPI_KEY environment variable.
    If not set, returns an empty list with a warning — no exception raised.

    Args:
        company_name: Company name to search for.
        max_results: Maximum results to fetch.

    Returns:
        List of candidate name strings, or [] if API key is not set.
    """
    api_key = os.environ.get("LINKEDIN_RAPIDAPI_KEY", "").strip()
    if not api_key:
        logger.warning(
            "LINKEDIN_RAPIDAPI_KEY not set. LinkedIn API search skipped. "
            "Set the env var or use --search (Google dorks) or --file instead."
        )
        return []

    try:
        import requests
    except ImportError:
        logger.error("requests required. Install: pip install requests")
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-profiles-and-company-data.p.rapidapi.com",
    }

    names: list[str] = []
    try:
        resp = requests.get(
            "https://linkedin-profiles-and-company-data.p.rapidapi.com/search-people",
            headers=headers,
            params={"keywords": company_name, "count": str(min(max_results, 50))},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("people", data.get("results", [])):
                full_name = item.get("name") or item.get("fullName") or ""
                if full_name.strip():
                    names.append(full_name.strip())
        else:
            logger.warning("LinkedIn API returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error("LinkedIn API error: %s", exc)

    return names


def collect_names_online(
    company_name: str,
    domain: Optional[str] = None,
    max_results: int = 50,
    use_linkedin_api: bool = True,
    delay: float = 2.0,
) -> list[str]:
    """
    Collect employee names using all available online methods.

    Priority order:
      1. LinkedIn API (if LINKEDIN_RAPIDAPI_KEY is set and use_linkedin_api=True)
      2. Google dorks (no API required, may be rate-limited)

    Args:
        company_name: Company name to search for.
        domain: Optional company domain for extra context.
        max_results: Maximum names to collect.
        use_linkedin_api: Attempt LinkedIn API if key is available.
        delay: Delay between requests in seconds.

    Returns:
        Deduplicated list of candidate name strings.
    """
    names: list[str] = []
    seen: set[str] = set()

    if use_linkedin_api:
        api_names = search_names_linkedin_api(company_name, max_results)
        for n in api_names:
            if n.lower() not in seen:
                seen.add(n.lower())
                names.append(n)

    if len(names) < max_results:
        remaining = max_results - len(names)
        dork_names = search_names_google_dorks(company_name, domain, remaining, delay)
        for n in dork_names:
            if n.lower() not in seen:
                seen.add(n.lower())
                names.append(n)

    return names


# ── Password generation ────────────────────────────────────────────────────────

# Common corporate password patterns (global + Brazilian)
# Tokens: {fn} first name, {ln} last name, {fi} first initial, {domain} domain name,
#         {year} current year, {company} company short name
CORPORATE_PASSWORD_PATTERNS: list[str] = [
    # ── Global standards ──────────────────────────────────────
    "{fn}@{year}",
    "{fn}{year}!",
    "{fn}{year}@",
    "{fn}{year}#",
    "{fn}.{ln}@{year}",
    "{fn}{ln}{year}",
    "{fn}{ln}!",
    "{fn}{ln}@",
    "{ln}{fn}{year}",
    "{ln}@{year}",
    "{company}{year}",
    "{company}@{year}",
    "{company}#{year}",
    "{company}!",
    "{company}123",
    "{company}1234",
    "{company}@123",
    "{company}_{year}",
    "Welcome{year}!",
    "Welcome@{year}",
    "Welcome1!",
    "{company}2024",
    "{company}2025",
    "{company}2026",
    # ── Brazilian patterns ────────────────────────────────────
    "{fn}@safelabs",
    "{fn}123456",
    "{fn}12345",
    "{fn}1234",
    "{fn}123",
    "{company}@{year}!",
    "{company}Mudar{year}",
    "{company}mudar{year}",
    "Mudar{year}!",
    "Mudar@{year}",
    "mudar{year}",
    "{fn}Mudar{year}",
    "{fn}mudar{year}",
    "{fn}@mudar",
    "P@ssw0rd{year}",
    "S3nh@{year}",
    "Senha{year}!",
    "senha{year}",
    "{fn}_{ln}@{year}",
    "{fn}.{ln}@{company}",
    "{fn}.{ln}{year}",
    # ── IT-role patterns ──────────────────────────────────────
    "Admin{year}!",
    "admin{year}@",
    "root{year}!",
    "{company}vpn{year}",
    "{company}VPN{year}",
    "{company}local{year}",
    "{company}corp{year}",
    "{company}adm{year}",
    "{company}admin!",
    "{company}admin{year}",
]


def generate_passwords_for_person(
    full_name: str,
    company_name: str,
    domain: str,
    year_range: Optional[range] = None,
) -> Generator[str, None, None]:
    """
    Generate password candidates for a person in a company context.

    Args:
        full_name: Employee full name.
        company_name: Company short name or trade name.
        domain: Company domain (e.g., 'empresa.com.br').
        year_range: Years to use in patterns (default: 2020-2026).

    Yields:
        Password strings.
    """
    parsed = parse_full_name(full_name)
    fn = _clean(parsed["first"])
    ln = _clean(parsed["last"])
    fi = fn[0] if fn else ""
    company = _clean(company_name.split()[0] if company_name else domain.split(".")[0])
    domain_short = _clean(domain.split(".")[0])
    years = year_range or range(2020, 2027)

    seen: set[str] = set()

    def _emit(s: str) -> Optional[str]:
        if s and s not in seen and len(s) >= 6:
            seen.add(s)
            return s
        return None

    for year in years:
        y = str(year)
        y2 = y[-2:]
        for pat in CORPORATE_PASSWORD_PATTERNS:
            for comp_token in [company, company.capitalize(), company.upper(), domain_short]:
                try:
                    pw = pat.format(
                        fn=fn, ln=ln, fi=fi, company=comp_token,
                        domain=domain_short, year=y,
                    )
                except KeyError:
                    continue
                r = _emit(pw)
                if r:
                    yield r
                # Capitalize first name variant
                r = _emit(pw.replace(fn, fn.capitalize(), 1))
                if r:
                    yield r


def generate_combo_list(
    names: list[str],
    company_name: str,
    domain: str,
    separators: Optional[list[str]] = None,
    year_range: Optional[range] = None,
    with_passwords: bool = True,
) -> Generator[str, None, None]:
    """
    Generate a combined user:password combo list for a set of names.

    Output format: username@domain:password

    Args:
        names: List of employee full names.
        company_name: Company name.
        domain: Company domain.
        separators: Separator chars for username generation.
        year_range: Year range for password patterns.
        with_passwords: If True, generate user:password pairs; else usernames only.

    Yields:
        Strings in format 'username@domain:password' or just 'username@domain'.
    """
    for name in names:
        name = name.strip()
        if not name or name.startswith("#"):
            continue

        users = list(generate_usernames_from_name(
            name, domain, separators, with_at_domain=True,
        ))

        if not with_passwords:
            yield from users
            continue

        passwords = list(generate_passwords_for_person(
            name, company_name, domain, year_range,
        ))

        for user in users:
            for pw in passwords:
                yield f"{user}:{pw}"


# ── Interactive wizard ─────────────────────────────────────────────────────────

def interactive_domain_users_wizard() -> dict:
    """
    Interactive wizard to collect parameters for domain username generation.

    Returns:
        Dict with all parameters needed for generation.
    """
    print("\n[ CORPORATE DOMAIN USER GENERATOR ]")
    print("Generates usernames and passwords for corporate domain accounts.\n")

    domain = input("  Company domain (e.g. empresa.com.br): ").strip()
    company_name = input("  Company trade name (short, e.g. Acme): ").strip()

    print("\n  Name source:")
    print("  [1] Load from file")
    print("  [2] Search online (Google dorks, no API needed)")
    print("  [3] Search via LinkedIn API (requires LINKEDIN_RAPIDAPI_KEY env var)")
    print("  [4] Enter names manually")
    source = input("  Choose [1-4]: ").strip()

    names: list[str] = []
    filepath = None

    if source == "1":
        filepath = input("  File path (txt/csv/xlsx/pdf): ").strip()
        try:
            names = collect_names_from_file(filepath)
            print(f"  Found {len(names)} candidate name(s) in file.")
        except FileNotFoundError as exc:
            print(f"  ERROR: {exc}")
    elif source == "2":
        max_r = input("  Max results [50]: ").strip() or "50"
        print(f"  Searching Google for '{company_name}'... (may take a moment)")
        names = search_names_google_dorks(company_name, domain, int(max_r))
        print(f"  Found {len(names)} name(s) via Google dorks.")
    elif source == "3":
        api_key = os.environ.get("LINKEDIN_RAPIDAPI_KEY", "")
        if not api_key:
            print("  WARNING: LINKEDIN_RAPIDAPI_KEY not set in environment.")
            print("  Set it with: $env:LINKEDIN_RAPIDAPI_KEY='your-key'  (PowerShell)")
            print("  Falling back to Google dorks...")
            names = search_names_google_dorks(company_name, domain, 50)
        else:
            names = search_names_linkedin_api(company_name, 100)
        print(f"  Found {len(names)} name(s).")
    elif source == "4":
        print("  Enter full names (one per line, empty line to stop):")
        while True:
            n = input("    > ").strip()
            if not n:
                break
            names.append(n)
    else:
        print("  Invalid option, using manual entry.")

    if names:
        print(f"\n  Preview (first 5): {names[:5]}")
        ok = input("  Use these names? [Y/n]: ").strip().lower()
        if ok in ("n", "no"):
            names = []

    # Custom separators
    sep_input = input("\n  Username separators [. _ - '' / all]: ").strip().lower()
    if sep_input == "all" or not sep_input:
        separators = DOMAIN_SEPARATORS
    else:
        separators = [s.strip() for s in sep_input.replace("''", "").split(",") if s.strip() or s == "''"]
        if "''" in sep_input or '""' in sep_input:
            separators.append("")

    # Subdomain admin
    sub_input = input("\n  Subdomain prefix for admin patterns (e.g. a1t3ngrt, or Enter to skip): ").strip()
    subdomains = [s.strip() for s in sub_input.split(",") if s.strip()] if sub_input else []

    # Output options
    gen_users = input("\n  Generate usernames? [Y/n]: ").strip().lower() not in ("n", "no")
    gen_passwords = input("  Generate passwords? [Y/n]: ").strip().lower() not in ("n", "no")
    gen_combo = input("  Generate user:password combo? [Y/n]: ").strip().lower() not in ("n", "no")

    year_start = int(input("  Year range start [2020]: ").strip() or "2020")
    year_end = int(input("  Year range end [2026]: ").strip() or "2026")

    with_at = input("  Include @domain in usernames? [Y/n]: ").strip().lower() not in ("n", "no")

    return {
        "domain": domain,
        "company_name": company_name,
        "names": names,
        "filepath": filepath,
        "separators": separators,
        "subdomains": subdomains,
        "gen_users": gen_users,
        "gen_passwords": gen_passwords,
        "gen_combo": gen_combo,
        "year_start": year_start,
        "year_end": year_end,
        "with_at_domain": with_at,
    }


def run_domain_users(params: dict) -> Generator[str, None, None]:
    """
    Execute domain user generation based on wizard parameters.

    Args:
        params: Dict returned by interactive_domain_users_wizard() or built manually.

    Yields:
        Username, password, or combo strings.
    """
    domain = params.get("domain", "")
    company_name = params.get("company_name", domain.split(".")[0] if domain else "")
    names = params.get("names", [])
    separators = params.get("separators", DOMAIN_SEPARATORS)
    subdomains = params.get("subdomains", [])
    gen_users = params.get("gen_users", True)
    gen_passwords = params.get("gen_passwords", False)
    gen_combo = params.get("gen_combo", False)
    year_start = int(params.get("year_start", 2020))
    year_end = int(params.get("year_end", 2026))
    with_at = params.get("with_at_domain", True)
    year_range = range(year_start, year_end + 1)

    # ── Usernames from names ───────────────────────────────────
    if gen_users and names:
        yield from generate_usernames_from_list(
            names, domain, separators, with_at_domain=with_at,
        )

    # ── Subdomain-admin users ──────────────────────────────────
    if subdomains:
        yield from generate_subdomain_admin_users(subdomains, domain, with_at_domain=with_at)

    # ── Passwords only ─────────────────────────────────────────
    if gen_passwords and not gen_combo and names:
        seen: set[str] = set()
        for name in names:
            for pw in generate_passwords_for_person(name, company_name, domain, year_range):
                if pw not in seen:
                    seen.add(pw)
                    yield pw

    # ── Combo user:pass ────────────────────────────────────────
    if gen_combo and names:
        yield from generate_combo_list(names, company_name, domain, separators, year_range)
