#!/usr/bin/env python3
"""
wfh.py — WordList For Hacking v2.0.0

Unified wordlist generation tool for pentest and red team operations.
Supports: charset, pattern, profile, corp, phone, scrape, ocr, extract,
leet, xor, analyze, merge, dns, pharma, sanitize, reverse, mangle.

Usage:
  python wfh.py                              # interactive menu
  python wfh.py charset 6 8 abc123           # charset + length
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile                      # interactive personal profiling
  python wfh.py corp                         # interactive corporate profiling
  python wfh.py phone --country brazil --state SP
  python wfh.py phone --ddi 55 --ddd 11 --type mobile
  python wfh.py scrape https://site.com      # web scraping
  python wfh.py scrape https://site.com --with-numbers --with-spaces
  python wfh.py scrape --urls-file urls.txt  # multi-URL scraping
  python wfh.py ocr image.png               # OCR text extraction
  python wfh.py extract file1.pdf file2.xlsx
  python wfh.py leet word -m medium         # leet speak variants
  python wfh.py xor --brute HEXSTRING       # XOR brute-force
  python wfh.py analyze list.lst            # statistical analysis
  python wfh.py analyze list.lst --format markdown
  python wfh.py merge l1.lst l2.lst --sort frequency
  python wfh.py mangle wordlist.lst         # hashcat-style mangling rules
  python wfh.py dns -w words.lst -d company.com
  python wfh.py pharma                      # Brazilian pharmacy patterns
  python wfh.py charset --create-charset my_charset.cfg
  python wfh.py sanitize list.lst           # clean and normalize wordlist
  python wfh.py sanitize list.lst --strip-control --sort frequency
  python wfh.py reverse list.lst            # reverse line order (tac)

Author: André Henrique (@mrhenrike)
Version: 1.8.0
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Generator, Optional

# Forçar UTF-8 no stdout/stderr para Windows (evita UnicodeEncodeError com acentos)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

# ── Colorama ─────────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    _COLOR = True
except ImportError:
    _COLOR = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

# ── tqdm ──────────────────────────────────────────────────────────────────────
try:
    from tqdm import tqdm as _tqdm
    _TQDM = True
except ImportError:
    _TQDM = False

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("wfh")

VERSION = "2.1.2"

# ── Graceful shutdown ──────────────────────────────────────────────────────────
_SHUTDOWN_REQUESTED = False

def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True
    print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Shutdown requested — finishing current batch...")

signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, _signal_handler)


def is_shutdown() -> bool:
    """Check if a graceful shutdown has been requested."""
    return _SHUTDOWN_REQUESTED


# ── Global execution context ───────────────────────────────────────────────────
# Set once in main() from global CLI args; consumed by all handlers.
_GLOBAL_CTX: dict = {
    "threads":      5,      # thread count (1-300)
    "compute_mode": "auto", # cpu | gpu | cuda | rocm | mps | auto | hybrid
    "use_ml":       True,   # ML enabled globally
    "limit":        0,      # global line limit (0=unlimited)
    "timeout":      0,      # global timeout in seconds (0=unlimited)
    "start_time":   0.0,    # epoch when execution started
}

_BANNER_ART = (
    " __          _______ _    _         \n"
    r" \ \        / /  ____| |  | |        " + "\n"
    r"  \ \  /\  / /| |__  | |__| |       " + "\n"
    r"   \ \/  \/ / |  __| |  __  |       " + "\n"
    r"    \  /\  /  | |    | |  | |       " + "\n"
    r"     \/  \/   |_|    |_|  |_|       " + "\n"
)
BANNER = (
    f"\n{Fore.CYAN}{Style.BRIGHT}\n"
    + _BANNER_ART
    + f"\n  WordList For Hacking  v{VERSION}\n"
    + "  Author: André Henrique (@mrhenrike)\n"
    + "  Unified wordlist generation for pentest & red team\n"
    + f"{Style.RESET_ALL}"
)

MENU = f"""
{Fore.CYAN}=== MAIN MENU ==={Style.RESET_ALL}

  {Fore.GREEN}[1]{Style.RESET_ALL}  charset     — Generate by charset and length
  {Fore.GREEN}[2]{Style.RESET_ALL}  pattern     — Generate by template with variables
  {Fore.GREEN}[3]{Style.RESET_ALL}  profile     — Interactive personal target profiling
  {Fore.GREEN}[4]{Style.RESET_ALL}  corp        — Interactive corporate target profiling
  {Fore.GREEN}[5]{Style.RESET_ALL}  corp-users  — Corporate domain user/password generation
  {Fore.GREEN}[6]{Style.RESET_ALL}  phone       — Generate phone number wordlists
  {Fore.GREEN}[7]{Style.RESET_ALL}  scrape      — Web scraping wordlist extraction
  {Fore.GREEN}[8]{Style.RESET_ALL}  ocr         — Extract text from image via OCR
  {Fore.GREEN}[9]{Style.RESET_ALL}  extract     — Extract wordlist from files (pdf/xlsx/docx/img)
  {Fore.GREEN}[10]{Style.RESET_ALL} leet        — Leet speak variants (basic/medium/aggressive/custom)
  {Fore.GREEN}[11]{Style.RESET_ALL} xor         — XOR encryption / brute-force
  {Fore.GREEN}[12]{Style.RESET_ALL} analyze     — Statistical analysis of wordlist
  {Fore.GREEN}[13]{Style.RESET_ALL} merge       — Merge and deduplicate wordlists
  {Fore.GREEN}[14]{Style.RESET_ALL} dns         — DNS/subdomain fuzzing wordlist
  {Fore.GREEN}[15]{Style.RESET_ALL} pharma      — Brazilian pharmacy and health plan patterns
  {Fore.GREEN}[16]{Style.RESET_ALL} sanitize    — Clean wordlist (dedupe, sort, filter, remove blanks/#)
  {Fore.GREEN}[17]{Style.RESET_ALL} reverse     — Reverse line order (tac)
  {Fore.GREEN}[18]{Style.RESET_ALL} corp-prefixes — Corporate prefix username generation
  {Fore.GREEN}[19]{Style.RESET_ALL} train       — Train ML pattern model
  {Fore.GREEN}[20]{Style.RESET_ALL} sysinfo     — Show hardware profile and compute backend
  {Fore.GREEN}[21]{Style.RESET_ALL} mangle      — Apply hashcat-style mangling rules
  {Fore.GREEN}[0]{Style.RESET_ALL}  Exit
"""


# ── Utilitários de output ────────────────────────────────────────────────────

def _info(msg: str) -> None:
    print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {msg}")


def _ok(msg: str) -> None:
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}")


def _warn(msg: str) -> None:
    print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {msg}")


def _err(msg: str) -> None:
    print(f"{Fore.RED}[-]{Style.RESET_ALL} {msg}", file=sys.stderr)


def _write_output(
    generator: Generator[str, None, None],
    output: Optional[str],
    estimate: Optional[int] = None,
    min_len: int = 0,
    max_len: int = 9999,
    append: bool = False,
) -> int:
    """
    Write generator output to file or stdout with optional progress bar.

    Respects global --limit (max entries), --timeout (max seconds),
    and graceful Ctrl+C shutdown.

    Args:
        generator: String generator.
        output: Output file path or None for stdout.
        estimate: Entry count estimate for progress bar.
        min_len: Minimum length filter.
        max_len: Maximum length filter.
        append: If True, open file in append mode (for --resume).

    Returns:
        Total entries written.
    """
    count = 0
    limit = _GLOBAL_CTX.get("limit", 0)
    timeout = _GLOBAL_CTX.get("timeout", 0)
    start = _GLOBAL_CTX.get("start_time", 0.0) or time.time()

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        f = out_path.open(mode, encoding="utf-8")
        _info(f"Writing to: {output}" + (" (append)" if append else ""))
    else:
        f = None  # type: ignore

    try:
        if _TQDM and estimate and estimate > 0:
            pbar = _tqdm(total=estimate, unit="words", ncols=80)
        else:
            pbar = None

        for word in generator:
            if _SHUTDOWN_REQUESTED:
                _warn(f"Graceful shutdown — wrote {count:,} entries before stopping.")
                break

            if limit and count >= limit:
                _warn(f"Reached --limit {limit:,}. Stopping.")
                break

            if timeout and (time.time() - start) > timeout:
                _warn(f"Reached --timeout {timeout}s. Stopping at {count:,} entries.")
                break

            if not word:
                continue
            if min_len and len(word) < min_len:
                continue
            if max_len and len(word) > max_len:
                continue
            line = word + "\n"
            if f:
                f.write(line)
            else:
                sys.stdout.write(line)
            count += 1
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

    finally:
        if f:
            f.close()

    return count


def _confirm_large(estimate: int, threshold: int = 10_000_000) -> bool:
    """
    Prompt user for confirmation before generating very large lists.

    Args:
        estimate: Estimated number of entries to generate.
        threshold: Threshold above which to ask for confirmation.

    Returns:
        True if user confirms.
    """
    if estimate <= threshold:
        return True
    _warn(f"Estimated: {estimate:,} entries. This may take a long time.")
    try:
        resp = input("  Continue? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


# ── Command handlers ─────────────────────────────────────────────────────────

def cmd_charset(args: argparse.Namespace) -> None:
    """Handler for charset mode."""
    from wfh_modules.charset_gen import (
        get_charset, generate_by_charset, generate_by_pattern,
        estimate_size, create_charset_wizard, PLACEHOLDER_MAP,
        generate_by_mask, estimate_mask_size,
        generate_constrained, estimate_constrained_size,
    )

    if args.create_charset:
        create_charset_wizard(args.create_charset)
        return

    # ── Hashcat-style mask (?u?l?d?s?a) ──────────────────────
    if getattr(args, "mask", None):
        total, size = estimate_mask_size(args.mask, getattr(args, "custom_charset1", None))
        _info(f"Mask: {args.mask} | Estimated: {total:,} entries ~ {size}")
        if not _confirm_large(total):
            _warn("Operation cancelled.")
            return
        gen = generate_by_mask(args.mask, getattr(args, "custom_charset1", None))
        count = _write_output(gen, args.output, estimate=total)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Constrained composition (--digits N --lower M --upper K --special P) ─
    n_digits = getattr(args, "n_digits", 0) or 0
    n_lower = getattr(args, "n_lower", 0) or 0
    n_upper = getattr(args, "n_upper", 0) or 0
    n_special = getattr(args, "n_special", 0) or 0
    if any([n_digits, n_lower, n_upper, n_special]):
        length = args.min_len  # for constrained mode use min_len as fixed length
        total, size = estimate_constrained_size(length, n_digits, n_lower, n_upper, n_special)
        _info(
            f"Constrained: len={length} | digits={n_digits} lower={n_lower} "
            f"upper={n_upper} special={n_special} | Est: {total:,} ~ {size}"
        )
        if not _confirm_large(total):
            _warn("Operation cancelled.")
            return
        try:
            gen = generate_constrained(length, n_digits, n_lower, n_upper, n_special)
        except ValueError as exc:
            _err(str(exc))
            return
        count = _write_output(gen, args.output, estimate=total)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Crunch-style pattern (@,%,^) ──────────────────────────
    if args.pattern:
        _info(f"Generating by pattern: {args.pattern}")
        gen = generate_by_pattern(
            args.pattern,
            charset_file=args.charset_file,
            extra_charset=args.charset if args.charset else None,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Standard charset generation ───────────────────────────
    charset_str = get_charset(args.charset or "lalpha", args.charset_file)
    total, size = estimate_size(len(charset_str), args.min_len, args.max_len)
    _info(f"Charset: {len(charset_str)} chars | {args.min_len}..{args.max_len} | "
          f"Estimated: {total:,} entries ~ {size}")

    if not _confirm_large(total):
        _warn("Operation cancelled.")
        return

    gen = generate_by_charset(charset_str, args.min_len, args.max_len)
    count = _write_output(gen, args.output, estimate=total)
    _ok(f"Generated: {count:,} entries")


def cmd_pattern(args: argparse.Namespace) -> None:
    """Handler for pattern mode."""
    from wfh_modules.pattern_engine import (
        render_template, generate_from_template_file, expand_variable,
        generate_company_patterns,
    )

    variables: dict[str, list[str]] = {}
    for var_spec in (args.vars or []):
        if "=" in var_spec:
            name, val = var_spec.split("=", 1)
            variables[name.strip()] = expand_variable(name.strip(), val.strip())

    if args.template_file:
        gen = generate_from_template_file(args.template_file, variables)
    elif args.template:
        gen = render_template(args.template, variables)
    else:
        _err("Provide --template or --template-file")
        return

    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")


def cmd_profile(args: argparse.Namespace) -> None:
    """Handler for personal profiling mode."""
    from wfh_modules.profiler import interactive_profile, generate_from_profile

    # ── Load from YAML file ──────────────────────────────────────────────────
    if getattr(args, "profile_file", None):
        from wfh_modules.profiler import load_profile_yaml
        try:
            profile = load_profile_yaml(args.profile_file)
            _info(f"Profile loaded from: {args.profile_file}")
        except (FileNotFoundError, ImportError) as exc:
            _err(str(exc))
            return
    elif hasattr(args, "name") and args.name:
        from wfh_modules.profiler import parse_date_input
        birth_parsed = parse_date_input(getattr(args, "birth", "") or "") or (0, 0, 0)
        profile = {
            "full_name": args.name,
            "short_name": "",
            "nicknames": [],
            "birth_day": birth_parsed[0],
            "birth_month": birth_parsed[1],
            "birth_year": birth_parsed[2],
            "national_id": "",
            "phones": [],
            "location_city": "",
            "location_state": "",
            "location_country": "",
            "children": [],
            "pets": [],
            "social_handles": [],
            "keywords": [],
            "special_dates": [],
            "leet_mode": getattr(args, "leet", "basic") or "basic",
            "with_spaces": False,
            "min_len": 6,
            "max_len": 32,
            "include_specials": False,
        }
        if getattr(args, "nick", ""):
            profile["nicknames"] = [args.nick]
    else:
        profile = interactive_profile()

    # ── Inject year-range / suffix-range from CLI ────────────────────────────
    if getattr(args, "year_start", None) and getattr(args, "year_end", None):
        profile["year_start"] = args.year_start
        profile["year_end"] = args.year_end
    if getattr(args, "suffix_range", None):
        try:
            parts = args.suffix_range.split("-")
            profile["suffix_range_start"] = int(parts[0])
            profile["suffix_range_end"] = int(parts[1])
            # Auto-detect zero-pad from format (e.g. "00-99" → pad 2)
            profile["suffix_range_zero_pad"] = len(parts[0]) if parts[0].startswith("0") else 0
        except (ValueError, IndexError):
            _warn(f"Invalid --suffix-range format '{args.suffix_range}', expected START-END (e.g. 00-99)")

    leet_mode = getattr(args, "leet", "basic") or profile.get("leet_mode", "basic")
    _info(f"Generating wordlist from profile [leet={leet_mode}]...")
    gen = generate_from_profile(profile, leet_mode=leet_mode)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")


def cmd_corp(args: argparse.Namespace) -> None:
    """Handler for corporate profiling mode."""
    from wfh_modules.corp_profiler import interactive_corp_profile, generate_from_corp_profile

    profile = interactive_corp_profile()
    leet_mode = getattr(args, "leet", "basic") or profile.get("leet_mode", "basic")
    _info(f"Generating corporate wordlist [leet={leet_mode}]...")
    gen = generate_from_corp_profile(profile, leet_mode=leet_mode)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")


def cmd_corp_users(args: argparse.Namespace) -> None:
    """Handler for corporate domain user/password generation."""
    from wfh_modules.domain_users import (
        interactive_domain_users_wizard,
        run_domain_users,
        collect_names_from_file,
        collect_names_online,
        generate_subdomain_admin_users,
        DOMAIN_SEPARATORS,
        ALL_DOMAIN_SEPARATORS,
    )

    params: dict = {}

    # ── Interactive mode (no --domain provided) ────────────────────────────
    if not getattr(args, "domain", None):
        params = interactive_domain_users_wizard()
    else:
        domain = args.domain
        company_name = getattr(args, "company", None) or domain.split(".")[0]
        names: list[str] = []

        # Collect names from file
        if getattr(args, "file", None):
            _info(f"Loading names from: {args.file}")
            try:
                names = collect_names_from_file(args.file)
                _ok(f"Loaded {len(names)} name(s) from file")
            except FileNotFoundError as exc:
                _err(str(exc))
                return

        # Collect names online (Google dorks + optional LinkedIn API)
        if getattr(args, "search", None):
            _info(f"Searching online for employees of '{args.search}'...")
            online = collect_names_online(
                args.search,
                domain=domain,
                max_results=getattr(args, "max_results", 50),
                use_linkedin_api=not getattr(args, "no_api", False),
            )
            _ok(f"Found {len(online)} name(s) online")
            names.extend(online)

        # Manual name list (args.names is a single string)
        if getattr(args, "names", None):
            raw_names = args.names if isinstance(args.names, str) else ",".join(args.names)
            names.extend([n.strip() for n in raw_names.split(",") if n.strip()])

        # Parse separators — default is "." only; user can supply custom list or "all"
        sep_raw = getattr(args, "separators", None)
        if sep_raw:
            if sep_raw.strip().lower() == "all":
                separators = ALL_DOMAIN_SEPARATORS
            elif sep_raw.strip().lower() == "none":
                separators = [""]
            else:
                separators = []
                for token in sep_raw.split(","):
                    t = token.strip()
                    if t.lower() in ("none", "empty", "''", '""'):
                        if "" not in separators:
                            separators.append("")
                    elif t:
                        if t not in separators:
                            separators.append(t)
                if not separators:
                    separators = DOMAIN_SEPARATORS
        else:
            separators = DOMAIN_SEPARATORS  # default: ["."]

        subdomains = []
        if getattr(args, "subdomain", None):
            subdomains = [s.strip() for s in args.subdomain.split(",") if s.strip()]

        year_start = int(getattr(args, "year_start", None) or 2020)
        year_end = int(getattr(args, "year_end", None) or 2026)

        params = {
            "domain": domain,
            "company_name": company_name,
            "names": names,
            "separators": separators,
            "subdomains": subdomains,
            "gen_users": not getattr(args, "no_users", False),
            "gen_passwords": getattr(args, "passwords", False),
            "gen_combo": getattr(args, "combo", False),
            "year_start": year_start,
            "year_end": year_end,
            "with_at_domain": not getattr(args, "no_at", False),
        }

    if not params.get("names") and not params.get("subdomains"):
        _warn("No names or subdomains provided. Use --file, --search, --names, or --subdomain.")
        return

    _info(
        f"Generating for domain: {params.get('domain')} | "
        f"names: {len(params.get('names', []))} | "
        f"subdomains: {len(params.get('subdomains', []))}"
    )

    # ── Threads ────────────────────────────────────────────────────────────────
    threads = _GLOBAL_CTX.get("threads", 5)

    # ── ML ranking ─────────────────────────────────────────────────────────────
    # Respects both per-command --no-ml and global --no-ml
    cmd_use_ml = getattr(args, "use_ml", True)
    global_ml  = _GLOBAL_CTX.get("use_ml", True)
    use_ml     = cmd_use_ml and global_ml

    ml_model = None
    if use_ml:
        try:
            from wfh_modules.ml_patterns import get_model, DEFAULT_MODEL_FILE
            if DEFAULT_MODEL_FILE.exists():
                ml_model = get_model()
                if ml_model.is_trained():
                    _info(f"ML model loaded ({ml_model._total_uid_samples:,} samples) — ranking by probability")
                else:
                    ml_model = None
        except Exception:
            ml_model = None

    # ── Parallel generation across multiple names ──────────────────────────────
    names_list = params.get("names", [])
    if threads > 1 and len(names_list) > 1:
        from wfh_modules.thread_pool import parallel_generate

        _info(f"Parallel generation: {threads} threads × {len(names_list)} names")

        single_name_params = []
        for name in names_list:
            p = dict(params)
            p["names"] = [name]
            single_name_params.append(p)

        def _gen_for_params(p: dict):
            return run_domain_users(p)

        gen = parallel_generate(_gen_for_params, single_name_params, threads=threads)
    else:
        gen = run_domain_users(params)

    if ml_model:
        domain = params.get("domain", "")
        candidates = list(gen)
        ranked     = ml_model.rank_and_yield(candidates, domain)
        count      = _write_output(ranked, args.output)
    else:
        count = _write_output(gen, args.output)

    _ok(f"Generated: {count:,} entries")


def cmd_phone(args: argparse.Namespace) -> None:
    """Handler for phone number wordlist generation."""
    from wfh_modules.phone_gen import (
        generate_phones, interactive_phone_wizard, estimate_count, COUNTRIES,
    )

    interactive = not any([
        getattr(args, "country", None),
        getattr(args, "ddi", None),
        getattr(args, "ddd", None),
    ])

    if interactive:
        params = interactive_phone_wizard()
    else:
        formats_raw = getattr(args, "formats", None) or "e164,local"
        params = {
            "country": getattr(args, "country", None),
            "state": getattr(args, "state", None),
            "ddi": getattr(args, "ddi", None),
            "ddd": getattr(args, "ddd", None),
            "phone_type": getattr(args, "type", "both"),
            "custom_pattern": getattr(args, "pattern", None),
            "output_formats": [f.strip() for f in formats_raw.split(",")],
        }

    _info(f"Generating phone numbers [country={params.get('country') or 'custom'}]...")
    gen = generate_phones(**params)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} phone entries")


def cmd_scrape(args: argparse.Namespace) -> None:
    """Handler for web scraping mode."""
    from wfh_modules.web_scraper import WebScraper, DEFAULT_STOPWORDS

    auth = None
    if args.auth:
        parts = args.auth.split(":", 1)
        auth = (parts[0], parts[1]) if len(parts) == 2 else None

    # Parse extra headers (--header "Name: Value")
    extra_headers: dict[str, str] = {}
    for hdr in (getattr(args, "headers", None) or []):
        if ":" in hdr:
            k, v = hdr.split(":", 1)
            extra_headers[k.strip()] = v.strip()

    # Stop-words
    stopwords = frozenset()
    if getattr(args, "no_stopwords", False):
        stopwords = DEFAULT_STOPWORDS
    stopwords_file = getattr(args, "stopwords_file", None)
    if stopwords_file:
        try:
            with open(stopwords_file, encoding="utf-8") as f:
                custom_sw = frozenset(line.strip().lower() for line in f if line.strip())
            stopwords = stopwords | custom_sw
            _info(f"Loaded {len(custom_sw)} custom stop-words from {stopwords_file}")
        except FileNotFoundError:
            _warn(f"Stop-words file not found: {stopwords_file}")

    with_numbers = getattr(args, "with_numbers", False)
    with_spaces = getattr(args, "with_spaces", False)
    capture_paths = getattr(args, "capture_paths", False)
    capture_subdomains = getattr(args, "capture_subdomains", False)

    # Multi-URL mode
    urls_file = getattr(args, "urls_file", None)
    urls_to_crawl: list[str] = []
    if urls_file:
        try:
            with open(urls_file, encoding="utf-8") as uf:
                urls_to_crawl = [u.strip() for u in uf if u.strip() and not u.startswith("#")]
            _info(f"Loaded {len(urls_to_crawl)} URLs from {urls_file}")
        except FileNotFoundError:
            _err(f"URLs file not found: {urls_file}")
            return
    else:
        urls_to_crawl = [args.url]

    total_count = 0
    for url in urls_to_crawl:
        if is_shutdown():
            break
        scraper = WebScraper(
            start_url=url,
            depth=args.depth,
            min_word_len=args.min_word,
            max_word_len=args.max_word,
            extract_emails=args.emails,
            extract_meta=args.meta,
            auth=auth,
            delay=args.delay,
            user_agent=getattr(args, "user_agent", None),
            proxy=getattr(args, "proxy", None),
            extra_headers=extra_headers or None,
            stopwords=stopwords if stopwords else None,
            with_numbers=with_numbers,
            with_spaces=with_spaces,
            capture_paths=capture_paths,
            capture_subdomains=capture_subdomains,
        )
        _info(f"Crawling: {url} [depth={args.depth}]")
        if getattr(args, "proxy", None):
            _info(f"Proxy: {args.proxy}")
        count = _write_output(scraper.crawl(), args.output, append=(total_count > 0))
        total_count += count

    _ok(f"Extracted: {total_count:,} words from {len(urls_to_crawl)} URL(s)")


def cmd_ocr(args: argparse.Namespace) -> None:
    """Handler for OCR mode."""
    from wfh_modules.ocr_extractor import extract_from_image

    _info(f"Processing OCR: {args.image}")
    try:
        result = extract_from_image(args.image, lang=args.lang.split(","))
    except ImportError:
        _err("easyocr not installed. Run: pip install easyocr")
        return

    _ok(f"Extracted: {len(result['usernames'])} users, "
        f"{len(result['passwords'])} passwords, {len(result['words'])} words")

    all_tokens = result["usernames"] + result["passwords"] + result["words"]

    def gen():
        yield from all_tokens

    count = _write_output(gen(), args.output)
    _ok(f"Total written: {count:,}")


def cmd_extract(args: argparse.Namespace) -> None:
    """Handler for file extraction mode."""
    from wfh_modules.file_extractor import extract_wordlist_from_files

    _info(f"Extracting from {len(args.files)} file(s)...")
    gen = extract_wordlist_from_files(
        args.files, min_len=args.min_len, max_len=args.max_len,
    )
    count = _write_output(gen, args.output)
    _ok(f"Extracted: {count:,} words")


def cmd_leet(args: argparse.Namespace) -> None:
    """Handler for leet speak mode."""
    from wfh_modules.leet_permuter import generate_all_variations

    _info(f"Generating leet variants [{args.mode}] for: {args.word}")
    gen = generate_all_variations(
        args.word,
        leet_mode=args.mode,
        custom_mapping=getattr(args, "custom_map", "") or "",
        max_leet=args.max_results,
    )
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} variants")


def cmd_xor(args: argparse.Namespace) -> None:
    """Handler for XOR mode."""
    from wfh_modules.xor_crypto import (
        brute_force_display, xor_encrypt_str, xor_decrypt_str,
    )

    if args.brute:
        brute_force_display(args.brute)
    elif args.encrypt and args.key:
        import binascii
        enc = xor_encrypt_str(args.encrypt, args.key)
        _ok(f"Encrypted (hex): {binascii.hexlify(enc).decode()}")
    elif args.decrypt and args.key:
        import binascii
        data = bytes.fromhex(args.decrypt)
        result = xor_decrypt_str(data, args.key)
        _ok(f"Decrypted: {result!r}")
    else:
        _err("Provide --brute, --encrypt or --decrypt with --key")


def cmd_analyze(args: argparse.Namespace) -> None:
    """Handler for wordlist analysis."""
    from wfh_modules.analyzer import (
        analyze_wordlist, format_report,
        analyze_masks, format_mask_report,
        export_stats_json, export_stats_csv,
        export_stats_markdown,
        extract_base_words,
    )

    _info(f"Analyzing: {args.wordlist}")
    try:
        metrics = analyze_wordlist(args.wordlist, top_n=args.top)
    except FileNotFoundError as e:
        _err(str(e))
        return

    mask_data: Optional[dict] = None
    do_masks = getattr(args, "masks", False)
    if do_masks:
        _info("Running Hashcat mask analysis...")
        try:
            mask_data = analyze_masks(args.wordlist, top_n=args.top)
        except Exception as exc:
            _warn(f"Mask analysis failed: {exc}")

    do_base = getattr(args, "base_words", False)
    base_output = getattr(args, "base_output", None)

    # ── Output format ──────────────────────────────────────────
    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        content = export_stats_json(metrics, args.wordlist, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"JSON report saved to: {args.output}")
    elif fmt == "csv":
        content = export_stats_csv(metrics, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"CSV report saved to: {args.output}")
    elif fmt == "markdown":
        content = export_stats_markdown(metrics, args.wordlist, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"Markdown report saved to: {args.output}")
    else:
        report = format_report(metrics, args.wordlist)
        print(report)
        if mask_data:
            print(format_mask_report(mask_data))
        if args.output:
            out_parts = [report]
            if mask_data:
                out_parts.append(format_mask_report(mask_data))
            Path(args.output).write_text("\n".join(out_parts), encoding="utf-8")
            _ok(f"Report saved to: {args.output}")

    # ── Base word extraction ───────────────────────────────────
    if do_base:
        _info("Extracting base words...")
        try:
            bases = extract_base_words(args.wordlist)
            _ok(f"Unique base words found: {len(bases):,}")
            if base_output:
                Path(base_output).write_text(
                    "\n".join(bases), encoding="utf-8"
                )
                _ok(f"Base words saved to: {base_output}")
            else:
                for b in bases[:50]:
                    print(f"  {b}")
                if len(bases) > 50:
                    print(f"  ... and {len(bases)-50} more")
        except Exception as exc:
            _warn(f"Base word extraction failed: {exc}")


def cmd_merge(args: argparse.Namespace) -> None:
    """Handler for wordlist merge."""
    from wfh_modules.merger import merge_to_file, stream_merged

    if not args.output:
        gen = stream_merged(
            args.files,
            min_len=args.min_len,
            max_len=args.max_len,
            no_numeric=args.no_numeric,
            filter_pattern=args.filter,
            dedupe=not args.no_dedupe,
            sort_mode=args.sort,
        )
        count = _write_output(gen, None)
    else:
        count = merge_to_file(
            args.files,
            args.output,
            min_len=args.min_len,
            max_len=args.max_len,
            no_numeric=args.no_numeric,
            filter_pattern=args.filter,
            dedupe=not args.no_dedupe,
            sort_mode=args.sort,
        )
    _ok(f"Total: {count:,} entries")


def cmd_dns(args: argparse.Namespace) -> None:
    """Handler for DNS wordlist generation."""
    from wfh_modules.dns_wordlist import (
        generate_subdomain_permutations, generate_from_template, load_words_from_file,
        load_templates_from_yaml, generate_from_yaml_templates,
        generate_multi_domain, filter_dns_output,
    )

    match_regex = getattr(args, "match_regex", None)
    filter_regex = getattr(args, "filter_regex", None)
    separator = getattr(args, "separator", None)
    separators = [separator] if separator else None

    # ── Multi-domain mode ──────────────────────────────────────
    domain_list = getattr(args, "domain_list", None)
    if domain_list:
        words: list[str] = []
        if getattr(args, "wordlist", None):
            words = load_words_from_file(args.wordlist)
        if getattr(args, "words", None):
            words.extend(args.words)
        gen = generate_multi_domain(
            domain_list, words, separators,
            use_prefixes=not getattr(args, "no_prefixes", False),
            use_suffixes=not getattr(args, "no_suffixes", False),
            match_regex=match_regex,
            filter_regex=filter_regex,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} DNS entries")
        return

    words = []
    if getattr(args, "wordlist", None):
        words = load_words_from_file(args.wordlist)
    if getattr(args, "words", None):
        words.extend(args.words)

    if not words:
        _err("Provide words with --wordlist or --words")
        return

    # ── YAML template file ─────────────────────────────────────
    template_file = getattr(args, "template_file", None)
    if template_file:
        try:
            templates = load_templates_from_yaml(template_file)
        except (FileNotFoundError, ImportError) as exc:
            _err(str(exc))
            return
        gen = generate_from_yaml_templates(
            templates, words, args.domain,
            match_regex=match_regex,
            filter_regex=filter_regex,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} DNS entries")
        return

    if args.template:
        gen = generate_from_template(args.template, words, args.domain)
        gen = filter_dns_output(gen, match_regex, filter_regex)
    else:
        gen = generate_subdomain_permutations(
            words, args.domain, separators,
            use_prefixes=not args.no_prefixes,
            use_suffixes=not args.no_suffixes,
            match_regex=match_regex,
            filter_regex=filter_regex,
        )

    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} subdomains")


def cmd_pharma(args: argparse.Namespace) -> None:
    """Handler for Brazilian pharmacy patterns."""
    from wfh_modules.pattern_engine import (
        generate_pharma_patterns, generate_company_patterns,
    )

    store_codes_arg = getattr(args, "codes", None)
    if store_codes_arg:
        store_codes = [c.strip() for c in store_codes_arg.split(",")]
    else:
        store_codes = [str(c) for c in range(1200, 1215)]

    _info(f"Generating BR pharmacy patterns [{len(store_codes)} store codes]...")
    gen = generate_pharma_patterns(store_codes=store_codes)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")


def cmd_sanitize(args: argparse.Namespace) -> None:
    """Handler for wordlist sanitization."""
    from wfh_modules.sanitizer import sanitize, format_sanitize_stats

    inplace = getattr(args, "inplace", False)
    output = getattr(args, "output", None)

    try:
        stats = sanitize(
            filepath=args.wordlist,
            output=output,
            no_blank=not getattr(args, "keep_blank", False),
            no_comments=not getattr(args, "keep_comments", False),
            dedupe=not getattr(args, "no_dedupe", False),
            sort_mode=getattr(args, "sort", None),
            min_len=getattr(args, "min_len", None),
            max_len=getattr(args, "max_len", None),
            filter_pattern=getattr(args, "filter", None),
            exclude_pattern=getattr(args, "exclude", None),
            inplace=inplace,
            strip_control=getattr(args, "strip_control", False),
        )
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    _ok(format_sanitize_stats(stats, args.wordlist))
    if output:
        _ok(f"Saved to: {output}")
    elif inplace:
        _ok(f"File updated in-place: {args.wordlist}")


def cmd_reverse(args: argparse.Namespace) -> None:
    """Handler for wordlist line reversal (tac)."""
    from wfh_modules.sanitizer import reverse_file

    inplace = getattr(args, "inplace", False)
    output = getattr(args, "output", None)

    try:
        count = reverse_file(args.wordlist, output=output, inplace=inplace)
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    _ok(f"Reversed: {count:,} lines")
    if output:
        _ok(f"Saved to: {output}")
    elif inplace:
        _ok(f"File updated in-place: {args.wordlist}")


def cmd_mangle(args: argparse.Namespace) -> None:
    """Handler for hashcat-style mangling rules on wordlists."""
    from wfh_modules.mangler import apply_rules, BUILTIN_RULES

    list_rules = getattr(args, "list_rules", False)
    if list_rules:
        _info("Available mangling rules:")
        for name, desc in BUILTIN_RULES.items():
            print(f"  {name:20s} — {desc}")
        return

    wordlist_path = getattr(args, "wordlist", None)
    if not wordlist_path:
        _err("Provide a wordlist to mangle.")
        return

    path = Path(wordlist_path)
    if not path.exists():
        _err(f"File not found: {wordlist_path}")
        return

    rules = getattr(args, "rules", "all") or "all"
    if rules == "all":
        active_rules = list(BUILTIN_RULES.keys())
    else:
        active_rules = [r.strip() for r in rules.split(",") if r.strip()]

    _info(f"Mangling: {wordlist_path} with rules: {', '.join(active_rules)}")

    lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n\r") for ln in f if ln.strip()]

    gen = apply_rules(lines, active_rules)
    count = _write_output(gen, args.output)
    _ok(f"Mangled output: {count:,} entries")


# ── Interactive menu ──────────────────────────────────────────────────────────

def interactive_menu() -> None:
    """Display and process the main interactive menu."""
    print(MENU)
    choice = input(f"{Fore.CYAN}Select an option: {Style.RESET_ALL}").strip()

    output = input("  Output file (Enter for stdout): ").strip() or None

    ns = argparse.Namespace(output=output)

    if choice == "1":
        ns.charset = input("  Charset (built-in name or chars): ").strip() or "lalpha"
        ns.min_len = int(input("  Min length: ").strip() or "6")
        ns.max_len = int(input("  Max length: ").strip() or "8")
        ns.charset_file = None
        ns.pattern = None
        ns.create_charset = None
        cmd_charset(ns)

    elif choice == "2":
        ns.template = input("  Template (e.g. DS{cod}@rd.com.br): ").strip()
        ns.template_file = None
        ns.vars = []
        while True:
            v = input("  Variable (name=value, Enter to stop): ").strip()
            if not v:
                break
            ns.vars.append(v)
        cmd_pattern(ns)

    elif choice == "3":
        ns.name = None
        ns.nick = None
        ns.birth = None
        ns.leet = input("  Leet mode (basic/medium/aggressive/none): ").strip() or "basic"
        cmd_profile(ns)

    elif choice == "4":
        ns.leet = input("  Leet mode (basic/medium/aggressive/none): ").strip() or "basic"
        cmd_corp(ns)

    elif choice == "5":
        # corp-users interactive — delegate entirely to wizard
        ns.domain = None
        cmd_corp_users(ns)

    elif choice == "6":
        ns.country = input("  Country (e.g. brazil, usa, uk): ").strip() or None
        ns.state = input("  State/region (e.g. SP, NY): ").strip() or None
        ns.ddi = input("  DDI override (or Enter): ").strip() or None
        ns.ddd = input("  DDD/area code override (or Enter): ").strip() or None
        ns.type = input("  Type [mobile/landline/both]: ").strip() or "both"
        ns.pattern = input("  Custom pattern (X=digit, or Enter): ").strip() or None
        ns.formats = input("  Formats (e164,local,bare — comma-sep): ").strip() or "e164,local"
        cmd_phone(ns)

    elif choice == "7":
        ns.url = input("  URL to crawl: ").strip()
        ns.depth = int(input("  Depth (default 2): ").strip() or "2")
        ns.min_word = int(input("  Min word length (6): ").strip() or "6")
        ns.max_word = int(input("  Max word length (32): ").strip() or "32")
        ns.emails = input("  Extract emails? [y/N]: ").strip().lower() in ("y", "yes")
        ns.meta = input("  Extract metadata? [y/N]: ").strip().lower() in ("y", "yes")
        ns.auth = None
        ns.delay = 0.5
        ns.proxy = None
        ns.user_agent = None
        ns.headers = None
        ns.no_stopwords = False
        ns.stopwords_file = None
        cmd_scrape(ns)

    elif choice == "8":
        ns.image = input("  Image path: ").strip()
        ns.lang = input("  OCR languages (default: pt,en): ").strip() or "pt,en"
        cmd_ocr(ns)

    elif choice == "9":
        files_raw = input("  Files (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (4): ").strip() or "4")
        ns.max_len = int(input("  Max length (64): ").strip() or "64")
        cmd_extract(ns)

    elif choice == "10":
        ns.word = input("  Base word: ").strip()
        ns.mode = input("  Mode (basic/medium/aggressive/custom): ").strip() or "basic"
        ns.custom_map = ""
        if ns.mode == "custom":
            ns.custom_map = input("  Mapping (e.g. a=@,4;t=7;s=$): ").strip()
        ns.max_results = int(input("  Max results (10000): ").strip() or "10000")
        cmd_leet(ns)

    elif choice == "11":
        sub = input("  [1] Brute-force  [2] Encrypt  [3] Decrypt: ").strip()
        ns.brute = None
        ns.encrypt = None
        ns.decrypt = None
        ns.key = None
        if sub == "1":
            ns.brute = input("  Hex string: ").strip()
        elif sub == "2":
            ns.encrypt = input("  Text to encrypt: ").strip()
            ns.key = input("  Key: ").strip()
        elif sub == "3":
            ns.decrypt = input("  Encrypted hex: ").strip()
            ns.key = input("  Key: ").strip()
        cmd_xor(ns)

    elif choice == "12":
        ns.wordlist = input("  Wordlist to analyze: ").strip()
        ns.top = int(input("  Top N (20): ").strip() or "20")
        ns.masks = input("  Run Hashcat mask analysis? [y/N]: ").strip().lower() in ("y", "yes")
        ns.base_words = False
        ns.base_output = None
        ns.format = "text"
        cmd_analyze(ns)

    elif choice == "13":
        files_raw = input("  Files to merge (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (6): ").strip() or "6")
        ns.max_len = int(input("  Max length (128): ").strip() or "128")
        ns.no_numeric = input("  Remove purely numeric? [y/N]: ").strip().lower() in ("y", "yes")
        ns.filter = None
        ns.no_dedupe = False
        ns.sort = input("  Sort (alpha/length/random or Enter to skip): ").strip() or None
        cmd_merge(ns)

    elif choice == "14":
        ns.domain = input("  Target domain: ").strip()
        ns.wordlist = input("  Words file (or Enter): ").strip() or None
        ns.words = []
        ns.template = None
        ns.template_file = None
        ns.domain_list = None
        ns.separator = None
        ns.match_regex = None
        ns.filter_regex = None
        ns.no_prefixes = False
        ns.no_suffixes = False
        cmd_dns(ns)

    elif choice == "15":
        ns.codes = input("  Store codes (e.g. 1200-1300 or 1200,1201, Enter for default): ").strip() or None
        cmd_pharma(ns)

    elif choice == "16":
        ns.wordlist = input("  Wordlist to sanitize: ").strip()
        ns.sort = input("  Sort (alpha/alpha-rev/length/length-rev/random or Enter): ").strip() or None
        min_raw = input("  Min length (Enter to skip): ").strip()
        max_raw = input("  Max length (Enter to skip): ").strip()
        ns.min_len = int(min_raw) if min_raw else None
        ns.max_len = int(max_raw) if max_raw else None
        ns.filter = input("  Include regex (Enter to skip): ").strip() or None
        ns.exclude = input("  Exclude regex (Enter to skip): ").strip() or None
        ns.keep_blank = False
        ns.keep_comments = False
        ns.no_dedupe = False
        ns.inplace = input("  Overwrite original? [y/N]: ").strip().lower() in ("y", "yes")
        if not ns.inplace:
            ns.output = input("  Output file (Enter for stdout): ").strip() or None
        cmd_sanitize(ns)

    elif choice == "17":
        ns.wordlist = input("  Wordlist to reverse: ").strip()
        ns.inplace = input("  Overwrite original? [y/N]: ").strip().lower() in ("y", "yes")
        if not ns.inplace:
            ns.output = input("  Output file (Enter for stdout): ").strip() or None
        cmd_reverse(ns)

    elif choice == "0":
        _info("Exiting wfh.py.")
        sys.exit(0)

    else:
        _warn("Invalid option.")


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="wfh.py",
        description="WordList For Hacking — Professional wordlist generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python wfh.py charset 6 8 abc123
  python wfh.py charset 8 8 --pattern "Pass@@@%%%"
  python wfh.py charset 8 8 --mask "?u?l?l?l?d?d?s"
  python wfh.py charset 8 8 --digits 2 --lower 4 --upper 1 --special 1
  python wfh.py charset 6 8 -f charsets.cfg mixalpha-numeric
  python wfh.py charset --create-charset my_charsets.cfg
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile
  python wfh.py profile --name "John Doe" --nick "johnny" --birth 15/03/1990
  python wfh.py profile --profile-file target.yaml -o wordlist.lst
  python wfh.py profile --year-start 2000 --year-end 2026 --suffix-range 00-99
  python wfh.py corp
  python wfh.py corp-users --domain empresa.com.br --file employees.txt -o users.lst
  python wfh.py corp-users --domain empresa.com.br --search "Empresa XPTO" --passwords -o combo.lst
  python wfh.py corp-users --domain empresa.com.br --names "João Silva,Maria Souza" --combo -o combo.lst
  python wfh.py corp-users --domain acme.com --subdomain corp-ad -o admins.lst
  python wfh.py phone --country brazil --state SP --type mobile -o phones_sp.lst
  python wfh.py phone --country usa --state NY --formats e164,local -o phones_ny.lst
  python wfh.py phone --ddi 55 --ddd 11 --pattern "9XXXX-XXXX" -o custom.lst
  python wfh.py scrape https://site.com -d 2 --emails --no-stopwords
  python wfh.py scrape https://site.com --proxy http://127.0.0.1:8080
  python wfh.py scrape https://site.com --user-agent "Mozilla/5.0" --header "X-Token: abc"
  python wfh.py ocr image.png -o wordlist.txt
  python wfh.py extract report.pdf spreadsheet.xlsx -o extracted.txt
  python wfh.py leet admin -m aggressive
  python wfh.py leet password -m custom --custom-map "a=@,4;s=$;e=3"
  python wfh.py xor --brute 1a2b3c4d
  python wfh.py analyze wlist_brasil.lst --top 30
  python wfh.py analyze wlist_brasil.lst --masks --format json -o stats.json
  python wfh.py analyze wlist_brasil.lst --base-words --base-output bases.lst
  python wfh.py merge l1.lst l2.lst --no-numeric --sort alpha -o merged.lst
  python wfh.py dns -w words.lst -d company.com
  python wfh.py dns -d company.com --template-file patterns.yaml -w words.lst
  python wfh.py dns --domain-list domains.txt -w words.lst -o subdomains.lst
  python wfh.py dns -d company.com --match-regex "^api" --filter-regex "test"
  python wfh.py pharma --codes 1200-1250 -o pharma_passwords.lst
  python wfh.py sanitize wlist_brasil.lst --min-len 8 --sort alpha --inplace
  python wfh.py sanitize list.lst --filter "^[a-zA-Z]" --exclude "\\d{3,}$" -o clean.lst
  python wfh.py sanitize list.lst --min-len 6 --max-len 20 --sort length -o output.lst
  python wfh.py reverse list.lst -o reversed.lst
  python wfh.py reverse list.lst --inplace
  python wfh.py mangle wordlist.lst --rules capitalize,append_num -o mangled.lst
  python wfh.py mangle wordlist.lst --list-rules
  python wfh.py scrape https://site.com --with-numbers --capture-paths
  python wfh.py scrape --urls-file urls.txt -d 2 -o scraped.lst
  python wfh.py analyze list.lst --format markdown -o report.md
  python wfh.py sanitize list.lst --strip-control --sort frequency -o clean.lst
  python wfh.py --limit 100000 charset 6 8 abc123 -o limited.lst
  python wfh.py --timeout 60 profile -o timed.lst
""",
    )
    parser.add_argument("--version", action="version", version=f"wfh.py {VERSION}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    # ── Global compute / threading / ML args ──────────────────────────────────
    parser.add_argument(
        "--threads", "-T", metavar="N", type=int, default=5,
        help=(
            "Number of worker threads for parallel generation (default: 5, range: 1–300). "
            "Warning at >50, alert at >100, critical at >200."
        ),
    )
    parser.add_argument(
        "--compute", metavar="MODE", default="auto",
        choices=["auto", "cpu", "gpu", "cuda", "rocm", "mps", "hybrid"],
        help=(
            "Compute backend for ML operations: "
            "auto (default) | cpu | gpu | cuda | rocm | mps | hybrid. "
            "'auto' selects the best available GPU, falls back to CPU."
        ),
    )
    parser.add_argument(
        "--no-ml", dest="no_ml_global", action="store_true", default=False,
        help=(
            "Disable ML-based ranking globally for all subcommands. "
            "When set, all modules run in rule-based mode regardless of "
            "per-command --no-ml flags."
        ),
    )
    parser.add_argument(
        "--limit", "-L", metavar="N", type=int, default=0,
        help=(
            "Global limit: stop after writing N entries (default: 0 = unlimited). "
            "Applies to all generation and extraction commands."
        ),
    )
    parser.add_argument(
        "--timeout", metavar="SECS", type=int, default=0,
        help=(
            "Global timeout: stop after SECS seconds of execution (default: 0 = unlimited). "
            "Applies to all generation commands."
        ),
    )

    sub = parser.add_subparsers(dest="command", help="Operation mode")

    # ── charset ───────────────────────────────────────────────────────────
    p_cs = sub.add_parser("charset", help="Generate by charset and length")
    p_cs.add_argument("min_len", nargs="?", type=int, default=6, help="Minimum length (also fixed length for --constrained)")
    p_cs.add_argument("max_len", nargs="?", type=int, default=8, help="Maximum length")
    p_cs.add_argument("charset", nargs="?", default="lalpha",
                       help="Charset: built-in name or direct character string")
    p_cs.add_argument("-f", "--charset-file", dest="charset_file", help=".cfg charset file")
    p_cs.add_argument("-p", "--pattern", help="Pattern with Crunch-style placeholders (@,%,^,...)")
    p_cs.add_argument("--mask", metavar="MASK",
                       help="Hashcat-style mask (e.g. ?u?l?l?d?d?s — ?u=upper ?l=lower ?d=digit ?s=special ?a=all)")
    p_cs.add_argument("--custom-charset1", dest="custom_charset1", metavar="CHARS",
                       help="Custom charset for ?1 placeholder in mask")
    p_cs.add_argument("--digits", dest="n_digits", type=int, default=0,
                       help="Exact digit count (constrained composition mode)")
    p_cs.add_argument("--lower", dest="n_lower", type=int, default=0,
                       help="Exact lowercase count (constrained composition mode)")
    p_cs.add_argument("--upper", dest="n_upper", type=int, default=0,
                       help="Exact uppercase count (constrained composition mode)")
    p_cs.add_argument("--special", dest="n_special", type=int, default=0,
                       help="Exact special char count (constrained composition mode)")
    p_cs.add_argument("--create-charset", dest="create_charset", metavar="FILE",
                       help="Wizard to create a charset file")
    p_cs.add_argument("-o", "--output", help="Output file")

    # ── pattern ───────────────────────────────────────────────────────────
    p_pt = sub.add_parser("pattern", help="Generate by template with variables")
    p_pt.add_argument("-t", "--template", help="Template (e.g. DS{cod}@rd.com.br)")
    p_pt.add_argument("-f", "--template-file", dest="template_file", help="Template file")
    p_pt.add_argument("--vars", nargs="+", metavar="KEY=VALUE",
                       help="Variables (e.g. cod=1200-1300 company=Acme,Globex)")
    p_pt.add_argument("-o", "--output", help="Output file")

    # ── profile ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser("profile", help="Interactive personal target profiling")
    p_pr.add_argument("--name", help="Target full name")
    p_pr.add_argument("--nick", help="Nickname or alias")
    p_pr.add_argument("--birth", help="Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or age)")
    p_pr.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                       help="Load profile from YAML file (non-interactive mode)")
    p_pr.add_argument("--year-start", dest="year_start", type=int, metavar="YYYY",
                       help="Include year range from this year (e.g. 2000)")
    p_pr.add_argument("--year-end", dest="year_end", type=int, metavar="YYYY",
                       help="Include year range to this year (e.g. 2026)")
    p_pr.add_argument("--suffix-range", dest="suffix_range", metavar="START-END",
                       help="Append numeric suffix range (e.g. 00-99 or 1-9999)")
    p_pr.add_argument("--leet", default="basic",
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Leet speak mode")
    p_pr.add_argument("-o", "--output", help="Output file")

    # ── corp ──────────────────────────────────────────────────────────────
    p_co = sub.add_parser("corp", help="Interactive corporate target profiling")
    p_co.add_argument("--leet", default="basic",
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Leet speak mode")
    p_co.add_argument("-o", "--output", help="Output file")

    # ── corp-users ────────────────────────────────────────────────────────
    p_cu = sub.add_parser(
        "corp-users",
        help="Generate corporate domain usernames and passwords",
        description=(
            "Generate corporate username/password lists from employee names.\n\n"
            "Name sources (choose one or combine):\n"
            "  --file       Load names from txt/csv/xlsx/pdf file\n"
            "  --search     Search online via Google dorks (no API needed)\n"
            "  --names      Comma-separated names inline\n\n"
            "LinkedIn API (optional):\n"
            "  Set LINKEDIN_RAPIDAPI_KEY env var to enable API-based search.\n"
            "  Without it, Google dorks are used automatically.\n\n"
            "Username patterns generated (default separator: '.'; use --separators to change):\n"
            "  firstname.lastname  f.lastname  flastname  lastname.firstname\n"
            "  firstname  lastname  firstnamel  initials  and 15+ more\n\n"
            "Examples:\n"
            "  wfh.py corp-users --domain empresa.com.br --file employees.txt\n"
            "  wfh.py corp-users --domain empresa.com.br --search 'Acme Corp'\n"
            "  wfh.py corp-users --domain empresa.com.br --names 'João Silva,Maria Souza'\n"
            "  wfh.py corp-users --domain empresa.com.br --file names.txt --combo -o combo.lst\n"
            "  wfh.py corp-users --domain acme.com --subdomain corp-ad -o admins.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cu.add_argument("--domain", default="",
                       help="Company domain (e.g. empresa.com.br)")
    p_cu.add_argument("--company", default="",
                       help="Company trade name (for passwords). Defaults to domain prefix.")
    # Name sources
    p_cu.add_argument("--file", metavar="FILE",
                       help="File with employee names (txt/csv/xlsx/pdf/docx)")
    p_cu.add_argument("--search", metavar="COMPANY_NAME",
                       help="Search online for employee names (Google dorks)")
    p_cu.add_argument("--names", metavar="NAME1,NAME2,...",
                       help="Comma-separated full names inline")
    p_cu.add_argument("--max-results", dest="max_results", type=int, default=50,
                       help="Max online search results (default: 50)")
    p_cu.add_argument("--no-api", dest="no_api", action="store_true",
                       help="Skip LinkedIn API even if LINKEDIN_RAPIDAPI_KEY is set")
    # Username options
    p_cu.add_argument("--separators", metavar="SEP",
                       help=(
                           "Username separator(s) used between name parts. "
                           "Default: '.' (dot only). "
                           "Examples: --separators _ | --separators .,_ | "
                           "--separators all (uses . _ - and empty) | "
                           "--separators none (no separator)."
                       ))
    p_cu.add_argument("--subdomain", metavar="SUB1,SUB2",
                       help="Subdomain(s) for admin patterns (e.g. a1t3ngrt,webmail)")
    p_cu.add_argument("--no-users", dest="no_users", action="store_true",
                       help="Skip username generation (only passwords or combo)")
    p_cu.add_argument("--no-at", dest="no_at", action="store_true",
                       help="Omit @domain suffix from usernames")
    # Password and combo options
    p_cu.add_argument("--passwords", action="store_true",
                       help="Also generate password list")
    p_cu.add_argument("--combo", action="store_true",
                       help="Generate user:password combo list")
    p_cu.add_argument("--year-start", dest="year_start", type=int, default=2020,
                       help="Password year range start (default: 2020)")
    p_cu.add_argument("--year-end", dest="year_end", type=int, default=2026,
                       help="Password year range end (default: 2026)")
    p_cu.add_argument("-o", "--output", help="Output file")
    p_cu.add_argument(
        "--no-ml", dest="use_ml", action="store_false", default=True,
        help="Disable ML-based ranking (use original rule-based order)",
    )

    # ── phone ─────────────────────────────────────────────────────────────
    p_ph2 = sub.add_parser("phone", help="Generate phone number wordlists")
    p_ph2.add_argument("--country", help="Country name (e.g. brazil, usa, uk)")
    p_ph2.add_argument("--state", help="State/region code (e.g. SP, NY)")
    p_ph2.add_argument("--ddi", help="Manual DDI override (e.g. 55)")
    p_ph2.add_argument("--ddd", help="Manual DDD/area code override (e.g. 11)")
    p_ph2.add_argument("--type", dest="type", default="both",
                        choices=["mobile", "landline", "both"],
                        help="Phone type to generate")
    p_ph2.add_argument("--pattern", dest="pattern",
                        help="Custom digit pattern (X=any digit, e.g. '9XXXX-XXXX')")
    p_ph2.add_argument("--formats", dest="formats", default="e164,local",
                        help="Output formats: e164,local,bare (comma-sep, default: e164,local)")
    p_ph2.add_argument("-o", "--output", help="Output file")

    # ── scrape ────────────────────────────────────────────────────────────
    p_sc = sub.add_parser("scrape", help="Web scraping wordlist extraction")
    p_sc.add_argument("url", help="Target URL")
    p_sc.add_argument("-d", "--depth", type=int, default=2, help="Crawl depth (default: 2)")
    p_sc.add_argument("--min-word", type=int, default=6, dest="min_word",
                       help="Minimum word length to extract (default: 6)")
    p_sc.add_argument("--max-word", type=int, default=32, dest="max_word",
                       help="Maximum word length to extract (default: 32)")
    p_sc.add_argument("--emails", action="store_true", help="Extract email addresses")
    p_sc.add_argument("--meta", action="store_true", help="Extract metadata (Author, Generator)")
    p_sc.add_argument("--auth", help="HTTP Basic Auth (user:password)")
    p_sc.add_argument("--proxy", help="HTTP/SOCKS proxy URL (e.g. http://127.0.0.1:8080)")
    p_sc.add_argument("--user-agent", dest="user_agent",
                       help="Custom User-Agent string")
    p_sc.add_argument("--header", dest="headers", action="append", metavar="NAME:VALUE",
                       help="Extra HTTP header (can be repeated)")
    p_sc.add_argument("--no-stopwords", dest="no_stopwords", action="store_true",
                       help="Exclude common EN/PT-BR stop-words from output")
    p_sc.add_argument("--stopwords-file", dest="stopwords_file", metavar="FILE",
                       help="Custom stop-words file (one word per line)")
    p_sc.add_argument("--delay", type=float, default=0.5,
                       help="Delay between requests in seconds (default: 0.5)")
    p_sc.add_argument("--with-numbers", dest="with_numbers", action="store_true",
                       help="Include words containing digits (normally excluded)")
    p_sc.add_argument("--with-spaces", dest="with_spaces", action="store_true",
                       help="Include multi-word phrases (space-separated tokens)")
    p_sc.add_argument("--urls-file", dest="urls_file", metavar="FILE",
                       help="File with one URL per line (multi-URL scraping mode)")
    p_sc.add_argument("--capture-paths", dest="capture_paths", action="store_true",
                       help="Extract URL path segments as additional words")
    p_sc.add_argument("--capture-subdomains", dest="capture_subdomains", action="store_true",
                       help="Extract subdomain labels as additional words")
    p_sc.add_argument("-o", "--output", help="Output file")

    # ── ocr ───────────────────────────────────────────────────────────────
    p_oc = sub.add_parser("ocr", help="Extract text from image via OCR")
    p_oc.add_argument("image", help="Image path")
    p_oc.add_argument("--lang", default="pt,en", help="OCR languages (default: pt,en)")
    p_oc.add_argument("-o", "--output", help="Output file")

    # ── extract ───────────────────────────────────────────────────────────
    p_ex = sub.add_parser("extract", help="Extract wordlist from files")
    p_ex.add_argument("files", nargs="+", help="Input files (max 50)")
    p_ex.add_argument("--min-len", type=int, default=4, dest="min_len")
    p_ex.add_argument("--max-len", type=int, default=64, dest="max_len")
    p_ex.add_argument("-o", "--output", help="Output file")

    # ── leet ─────────────────────────────────────────────────────────────
    p_lt = sub.add_parser("leet", help="Leet speak variants")
    p_lt.add_argument("word", help="Base word")
    p_lt.add_argument("-m", "--mode", default="basic",
                       choices=["basic", "medium", "aggressive", "custom"],
                       help="Leet substitution mode")
    p_lt.add_argument("--custom-map", dest="custom_map", default="",
                       help="Custom mapping (e.g. a=@,4;t=7;s=$;l=1,|)")
    p_lt.add_argument("--max-results", type=int, default=10000, dest="max_results")
    p_lt.add_argument("-o", "--output", help="Output file")

    # ── xor ───────────────────────────────────────────────────────────────
    p_xr = sub.add_parser("xor", help="XOR encryption / brute-force")
    xr_group = p_xr.add_mutually_exclusive_group(required=True)
    xr_group.add_argument("--brute", metavar="HEX", help="Brute-force single-byte key")
    xr_group.add_argument("--encrypt", metavar="TEXT", help="Encrypt text")
    xr_group.add_argument("--decrypt", metavar="HEX", help="Decrypt hex string")
    p_xr.add_argument("--key", help="Key for encrypt/decrypt")
    p_xr.add_argument("-o", "--output", help="Output file")

    # ── analyze ───────────────────────────────────────────────────────────
    p_an = sub.add_parser("analyze", help="Statistical analysis of wordlist")
    p_an.add_argument("wordlist", help="Wordlist to analyze")
    p_an.add_argument("--top", type=int, default=20, help="Top N most frequent (default: 20)")
    p_an.add_argument("--masks", action="store_true",
                       help="Include Hashcat mask analysis (?u?l?d?s frequency)")
    p_an.add_argument("--base-words", dest="base_words", action="store_true",
                       help="Extract base words (strip trailing digits/specials)")
    p_an.add_argument("--base-output", dest="base_output", metavar="FILE",
                       help="Save base words to file")
    p_an.add_argument("--format", dest="format", choices=["text", "json", "csv", "markdown"],
                       default="text", help="Output format: text, json, csv, markdown (default: text)")
    p_an.add_argument("-o", "--output", help="Save report to file")

    # ── merge ─────────────────────────────────────────────────────────────
    p_mg = sub.add_parser("merge", help="Merge and deduplicate wordlists")
    p_mg.add_argument("files", nargs="+", help="Input wordlists")
    p_mg.add_argument("--min-len", type=int, default=6, dest="min_len")
    p_mg.add_argument("--max-len", type=int, default=128, dest="max_len")
    p_mg.add_argument("--no-numeric", action="store_true", dest="no_numeric",
                       help="Remove purely numeric entries")
    p_mg.add_argument("--filter", help="Include regex filter (only matches pass)")
    p_mg.add_argument("--no-dedupe", action="store_true", dest="no_dedupe")
    p_mg.add_argument("--sort", choices=["alpha", "length", "random", "frequency"],
                       help="Sort mode: alpha, length, random, or frequency (most common first)")
    p_mg.add_argument("-o", "--output", help="Output file")

    # ── dns ───────────────────────────────────────────────────────────────
    p_dn = sub.add_parser("dns", help="DNS/subdomain fuzzing wordlist")
    p_dn.add_argument("-d", "--domain", default="", help="Target domain (required unless --domain-list)")
    p_dn.add_argument("--domain-list", dest="domain_list", metavar="FILE",
                       help="File with one domain per line (multi-domain mode)")
    p_dn.add_argument("-w", "--wordlist", help="Words file")
    p_dn.add_argument("--words", nargs="+", help="Direct word list")
    p_dn.add_argument("-t", "--template", help="Inline template (e.g. dev-{word}.{domain})")
    p_dn.add_argument("--template-file", dest="template_file", metavar="FILE",
                       help="YAML file with permutation templates")
    p_dn.add_argument("--separator", help="Custom separator between tokens (e.g. _ or .)")
    p_dn.add_argument("--match-regex", dest="match_regex", metavar="REGEX",
                       help="Include only output matching this regex")
    p_dn.add_argument("--filter-regex", dest="filter_regex", metavar="REGEX",
                       help="Exclude output matching this regex")
    p_dn.add_argument("--no-prefixes", action="store_true", dest="no_prefixes")
    p_dn.add_argument("--no-suffixes", action="store_true", dest="no_suffixes")
    p_dn.add_argument("-o", "--output", help="Output file")

    # ── pharma ────────────────────────────────────────────────────────────
    p_ph = sub.add_parser("pharma", help="Brazilian pharmacy and health plan patterns")
    p_ph.add_argument("--codes", help="Store codes (e.g. 1200-1300 or 1200,1201)")
    p_ph.add_argument("-o", "--output", help="Output file")

    # ── sanitize ──────────────────────────────────────────────────────────
    p_sa = sub.add_parser(
        "sanitize",
        help="Clean wordlist (dedupe, sort, filter, remove blanks and comments)",
        description=(
            "Sanitize an existing wordlist applying filters in order:\n"
            "  1. Remove comments (#)     2. Remove blank lines\n"
            "  3. Filter by length        4. Filter by regex\n"
            "  5. Deduplicate             6. Sort\n\n"
            "Examples:\n"
            "  wfh.py sanitize list.lst --inplace\n"
            "  wfh.py sanitize list.lst --min-len 8 --sort alpha -o clean.lst\n"
            "  wfh.py sanitize list.lst --filter '^[a-zA-Z]' --exclude '\\d{3,}$' -o out.lst\n"
            "  wfh.py sanitize list.lst --min-len 6 --max-len 20 --sort length-rev -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sa.add_argument("wordlist", help="Wordlist to sanitize")
    p_sa.add_argument("--min-len", type=int, default=None, dest="min_len",
                       help="Minimum length (removes shorter entries)")
    p_sa.add_argument("--max-len", type=int, default=None, dest="max_len",
                       help="Maximum length (removes longer entries)")
    p_sa.add_argument("--sort", dest="sort",
                       choices=["alpha", "alpha-rev", "length", "length-rev", "random", "frequency"],
                       help="Sort mode: alpha, alpha-rev, length, length-rev, random, frequency")
    p_sa.add_argument("--filter", dest="filter", metavar="REGEX",
                       help="Include regex — keep only matching lines")
    p_sa.add_argument("--exclude", dest="exclude", metavar="REGEX",
                       help="Exclude regex — remove matching lines")
    p_sa.add_argument("--no-dedupe", action="store_true", dest="no_dedupe",
                       help="Do not remove duplicates")
    p_sa.add_argument("--keep-blank", action="store_true", dest="keep_blank",
                       help="Keep blank lines")
    p_sa.add_argument("--keep-comments", action="store_true", dest="keep_comments",
                       help="Keep comment lines (#)")
    p_sa.add_argument("--strip-control", dest="strip_control", action="store_true",
                       help="Remove control characters (tabs, null bytes, escape sequences) from lines")
    p_sa.add_argument("--inplace", action="store_true",
                       help="Overwrite original file")
    p_sa.add_argument("-o", "--output", help="Output file (default: stdout)")

    # ── reverse ───────────────────────────────────────────────────────────
    p_rv = sub.add_parser(
        "reverse",
        help="Reverse line order of a wordlist (tac)",
        description=(
            "Reverse the line order of a wordlist (equivalent to 'tac').\n\n"
            "Examples:\n"
            "  wfh.py reverse list.lst -o reversed.lst\n"
            "  wfh.py reverse list.lst --inplace"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rv.add_argument("wordlist", help="Wordlist to reverse")
    p_rv.add_argument("--inplace", action="store_true",
                       help="Overwrite original file")
    p_rv.add_argument("-o", "--output", help="Output file (default: stdout)")

    # ── mangle ────────────────────────────────────────────────────────────────
    p_mn = sub.add_parser(
        "mangle",
        help="Apply hashcat-style mangling rules to a wordlist",
        description=(
            "Apply transformation rules to every word in a wordlist.\n\n"
            "Rules (inspired by Hashcat/John rule engine):\n"
            "  capitalize   — Capitalize first letter\n"
            "  upper        — Uppercase entire word\n"
            "  lower        — Lowercase entire word\n"
            "  reverse      — Reverse the word\n"
            "  toggle       — Toggle case of all chars\n"
            "  append_num   — Append 0-99, common years\n"
            "  prepend_num  — Prepend 0-9\n"
            "  append_special — Append !, @, #, $, %, etc.\n"
            "  leet_basic   — Basic leet substitutions\n"
            "  duplicate    — Duplicate the word (e.g. passpass)\n"
            "  strip_vowels — Remove all vowels\n\n"
            "Examples:\n"
            "  wfh.py mangle wordlist.lst -o mangled.lst\n"
            "  wfh.py mangle wordlist.lst --rules capitalize,leet_basic,append_num\n"
            "  wfh.py mangle wordlist.lst --list-rules"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mn.add_argument("wordlist", nargs="?", default=None, help="Wordlist to mangle")
    p_mn.add_argument("--rules", default="all",
                       help="Comma-separated rule names or 'all' (default: all)")
    p_mn.add_argument("--list-rules", dest="list_rules", action="store_true",
                       help="List available mangling rules and exit")
    p_mn.add_argument("-o", "--output", help="Output file")

    # ── sysinfo ───────────────────────────────────────────────────────────────
    sub.add_parser(
        "sysinfo",
        help="Show hardware profile, compute backend and thread status",
        description=(
            "Display detected CPU, RAM, GPU and compute backend.\n"
            "Shows current --threads and --compute settings.\n\n"
            "Examples:\n"
            "  wfh.py sysinfo\n"
            "  wfh.py --compute gpu sysinfo\n"
            "  wfh.py --threads 20 sysinfo"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── corp-prefixes ─────────────────────────────────────────────────────────
    p_cp = sub.add_parser(
        "corp-prefixes",
        help="Generate username variations with corporate department/role prefixes",
        description=(
            "Generate username variations with department, role, and functional prefixes.\n\n"
            "All patterns loaded from data/corp_prefix_patterns.json — no hardcoded data.\n"
            "No real company names ever stored or generated.\n\n"
            "Prefix categories:\n"
            "  department  — ti, helpdesk, adm, rh, fin, seg, dev, redes, ...\n"
            "  role        — svc, admin, ger, dir, analista, trainee, ...\n"
            "  contractor  — ext, externo, terceiro, vendor, pj, ...\n"
            "  temp        — temp, tmp, provisorio, ...\n"
            "  generic     — user, usr, account, login, ...\n\n"
            "Examples:\n"
            "  wfh.py corp-prefixes --names 'João Silva' --domain empresa.com.br\n"
            "  wfh.py corp-prefixes --names 'João Silva' --prefixes svc,adm --separators .\n"
            "  wfh.py corp-prefixes --names 'João Silva' --categories department,role\n"
            "  wfh.py corp-prefixes --names 'João Silva' --sector judicial\n"
            "  wfh.py corp-prefixes --list-prefixes\n"
            "  wfh.py corp-prefixes --file employees.txt --domain corp.com.br -o prefixed.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cp.add_argument("--names", metavar="NAME1,NAME2", help="Comma-separated full names")
    p_cp.add_argument("--file", metavar="FILE", help="File with employee names")
    p_cp.add_argument("--domain", default="", help="Company domain for @domain suffix")
    p_cp.add_argument("--no-at", dest="no_at", action="store_true",
                       help="Omit @domain suffix from output")
    p_cp.add_argument(
        "--prefixes", metavar="pfx1,pfx2",
        help="Explicit prefix list (e.g. svc,adm,ti). Overrides --categories.",
    )
    p_cp.add_argument(
        "--categories", metavar="cat1,cat2",
        help="Prefix categories to include: department, role, contractor, temp, generic",
    )
    p_cp.add_argument(
        "--sector", metavar="SECTOR",
        help=(
            "Force sector label for prefix selection "
            "(energia_utilities, judicial, financas, saude, governo, generic, ...)"
        ),
    )
    p_cp.add_argument(
        "--separators", metavar="SEP",
        default=".",
        help="Separator(s) between prefix and name parts (default: '.')",
    )
    p_cp.add_argument(
        "--no-numeric", dest="no_numeric", action="store_true",
        help="Skip numeric suffix variants",
    )
    p_cp.add_argument(
        "--list-prefixes", dest="list_prefixes", action="store_true",
        help="List all available prefix groups and exit",
    )
    p_cp.add_argument(
        "--config", metavar="FILE",
        help="Custom prefix patterns JSON file (default: data/corp_prefix_patterns.json)",
    )
    p_cp.add_argument("-o", "--output", help="Output file")

    # ── train ─────────────────────────────────────────────────────────────────
    p_tr = sub.add_parser(
        "train",
        help="Train ML pattern model from AD exports, wordlists, and username lists",
        description=(
            "Train the statistical pattern model for corporate credential generation.\n\n"
            "Privacy: only structural patterns are extracted — no raw usernames,\n"
            "passwords, company names, or personal data are ever stored.\n\n"
            "Examples:\n"
            "  wfh.py train --csv export.csv --auto -o .model/pattern_model.json\n"
            "  wfh.py train --auto\n"
            "  wfh.py train --csv users.csv --wordlist wlist_brasil.lst --usernames username_br.lst\n"
            "  wfh.py train --csv export.csv --uid-col samaccountname --mail-col mail"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_tr.add_argument(
        "--csv", metavar="FILE", action="append", default=[],
        help="AD export CSV file(s) to train from (can repeat for multiple files)",
    )
    p_tr.add_argument(
        "--wordlist", metavar="FILE", action="append", default=[],
        help="Password wordlist file(s) to train from",
    )
    p_tr.add_argument(
        "--usernames", metavar="FILE", action="append", default=[],
        help="Username list file(s) to train from",
    )
    p_tr.add_argument(
        "--auto", action="store_true",
        help="Auto-discover and train from known local wordlists (wlist_brasil.lst, username_br.lst, etc.)",
    )
    p_tr.add_argument(
        "--uid-col", dest="uid_col", default="userid",
        help="CSV column name for username/samaccountname (default: userid)",
    )
    p_tr.add_argument(
        "--eid-col", dest="eid_col", default="employeeid",
        help="CSV column name for employee ID (default: employeeid)",
    )
    p_tr.add_argument(
        "--mail-col", dest="mail_col", default="workemail",
        help="CSV column name for work email (default: workemail)",
    )
    p_tr.add_argument(
        "--max-rows", dest="max_rows", type=int, default=0,
        help="Max CSV rows to process (0 = all)",
    )
    p_tr.add_argument(
        "--max-lines", dest="max_lines", type=int, default=500_000,
        help="Max lines to read from wordlists (default: 500000)",
    )
    p_tr.add_argument(
        "-o", "--output", metavar="FILE",
        help="Output model file (default: .model/pattern_model.json)",
    )

    return parser


# ── Entrypoint ────────────────────────────────────────────────────────────────

def cmd_sysinfo(args: argparse.Namespace) -> None:
    """Show hardware profile and compute backend status."""
    from wfh_modules.hw_profiler import get_hw_profile
    from wfh_modules.compute_backend import auto_select_backend
    from wfh_modules.thread_pool import (
        DEFAULT_THREADS, MIN_THREADS, MAX_THREADS,
        WARN_THRESHOLD, ALERT_THRESHOLD,
    )

    compute_mode = _GLOBAL_CTX.get("compute_mode", "auto")

    _info("Detecting hardware profile...")
    hw = get_hw_profile(force=True)

    print()
    print(f"  CPU   : {hw.cpu_model}")
    print(f"  Cores : {hw.cpu_cores} physical / {hw.cpu_threads} logical")
    print(f"  RAM   : {hw.ram_total_mb:,} MB total / {hw.ram_avail_mb:,} MB available")

    if hw.has_gpu():
        for gpu in hw.gpus:
            print(f"  GPU   : {gpu.one_liner()}")
    else:
        print("  GPU   : None detected (CPU-only mode)")

    print()
    backend = auto_select_backend(compute_mode, hw)
    print(f"  Compute backend : {backend.name.upper()}")
    print(f"  Device info     : {backend.device_info}")
    print(f"  ML enabled      : {_GLOBAL_CTX.get('use_ml', True)}")

    cur_threads = _GLOBAL_CTX.get("threads", DEFAULT_THREADS)
    rec_threads = hw.recommended_threads()
    print()
    print(f"  Threads (active) : {cur_threads}  [range: {MIN_THREADS}–{MAX_THREADS}, recommended: {rec_threads}]")
    if cur_threads >= ALERT_THRESHOLD:
        print(f"  {Fore.RED}[ALERT]{Style.RESET_ALL} Thread count {cur_threads} is very high — monitor system resources.")
    elif cur_threads >= WARN_THRESHOLD:
        print(f"  {Fore.YELLOW}[WARN]{Style.RESET_ALL} Thread count {cur_threads} exceeds recommended limit.")
    print()


def cmd_corp_prefixes(args: argparse.Namespace) -> None:
    """Handler for corporate username prefix generation."""
    from wfh_modules.corp_prefixes import (
        load_prefix_config,
        generate_from_name,
        get_all_prefixes,
        list_all_prefixes,
    )

    try:
        config = load_prefix_config(getattr(args, "config", None))
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    # ── List available prefixes ──────────────────────────────────────────────
    if getattr(args, "list_prefixes", False):
        all_groups = list_all_prefixes(config)
        for group, aliases in all_groups.items():
            print(f"  {group}: {', '.join(aliases)}")
        return

    # ── Collect names ────────────────────────────────────────────────────────
    names: list[str] = []
    if getattr(args, "names", None):
        raw = args.names if isinstance(args.names, str) else ",".join(args.names)
        names = [n.strip() for n in raw.split(",") if n.strip()]

    if getattr(args, "file", None):
        from wfh_modules.domain_users import collect_names_from_file
        try:
            names += collect_names_from_file(args.file)
        except FileNotFoundError as exc:
            _err(str(exc))
            return

    if not names:
        _warn("No names provided. Use --names or --file.")
        return

    # ── Resolve options ──────────────────────────────────────────────────────
    domain     = getattr(args, "domain", "") or ""
    sector     = getattr(args, "sector", None)
    categories = None
    if getattr(args, "categories", None):
        categories = [c.strip() for c in args.categories.split(",")]

    # Explicit prefix list
    prefixes = None
    if getattr(args, "prefixes", None):
        prefixes = [p.strip() for p in args.prefixes.split(",")]

    sep_raw = getattr(args, "separators", None)
    if sep_raw:
        separators = [s if s.lower() not in ("none", "empty") else "" for s in sep_raw.split(",")]
    else:
        separators = ["."]  # default

    with_numeric = not getattr(args, "no_numeric", False)

    # ── Generate ────────────────────────────────────────────────────────────
    def _generate():
        for name in names:
            results = generate_from_name(
                full_name=name,
                domain=domain,
                prefixes=prefixes,
                categories=categories,
                separators=separators,
                sector=sector,
                with_numeric=with_numeric,
                config=config,
            )
            if domain and not getattr(args, "no_at", False):
                for r in results:
                    yield f"{r}@{domain}"
            else:
                yield from results

    count = _write_output(_generate(), args.output)
    _ok(f"Generated: {count:,} prefixed username entries")


def cmd_train(args: argparse.Namespace) -> None:
    """
    Train the ML pattern model from available data sources.

    Privacy: only structural patterns are extracted — no raw usernames,
    passwords, company names, or personal data are ever stored in the model.
    """
    from wfh_modules.ml_patterns import PatternModel, DEFAULT_MODEL_FILE

    model = PatternModel()
    trained_any = False

    # ── CSV sources ────────────────────────────────────────────────────────────
    for csv_path in (getattr(args, "csv", None) or []):
        p = _resolve_path(csv_path)
        if not p or not p.exists():
            _warn(f"CSV not found: {csv_path}")
            continue
        _info(f"Training from CSV: {p.name}")
        stats = model.train_from_csv(
            str(p),
            userid_col     = getattr(args, "uid_col",  "userid"),
            employeeid_col = getattr(args, "eid_col",  "employeeid"),
            workemail_col  = getattr(args, "mail_col", "workemail"),
            max_rows       = getattr(args, "max_rows", 0),
        )
        _info(f"  → {stats['uid_samples']:,} uid samples from {stats['processed_rows']:,} rows")
        trained_any = True

    # ── Password wordlists ────────────────────────────────────────────────────
    for wl_path in (getattr(args, "wordlist", None) or []):
        p = _resolve_path(wl_path)
        if not p or not p.exists():
            _warn(f"Wordlist not found: {wl_path}")
            continue
        _info(f"Training from password wordlist: {p.name}")
        stats = model.train_from_wordlist(
            str(p), mode="password",
            max_lines=getattr(args, "max_lines", 500_000),
            source_label=p.name,
        )
        _info(f"  → {stats['processed']:,} samples")
        trained_any = True

    # ── Username lists ────────────────────────────────────────────────────────
    for ul_path in (getattr(args, "usernames", None) or []):
        p = _resolve_path(ul_path)
        if not p or not p.exists():
            _warn(f"Username list not found: {ul_path}")
            continue
        _info(f"Training from username list: {p.name}")
        stats = model.train_from_wordlist(
            str(p), mode="username",
            max_lines=getattr(args, "max_lines", 200_000),
            source_label=p.name,
        )
        _info(f"  → {stats['processed']:,} samples")
        trained_any = True

    # ── Auto-discover local wordlists if --auto flag is set ───────────────────
    if getattr(args, "auto", False):
        wfh_root = _resolve_path(".")
        auto_sources = [
            ("passwords/wlist_brasil.lst",       "password", 300_000),
            ("passwords/default-creds-combo.lst", "password", 50_000),
            ("usernames/username_br.lst",          "username", 10_000),
        ]
        for rel, mode, limit in auto_sources:
            p = wfh_root / rel if wfh_root else None
            if p and p.exists():
                _info(f"Auto-training from {p.name} (mode={mode})")
                stats = model.train_from_wordlist(
                    str(p), mode=mode,
                    max_lines=limit,
                    source_label=p.name,
                )
                _info(f"  → {stats['processed']:,} samples")
                trained_any = True

    if not trained_any:
        _warn("No training data provided. Use --csv, --wordlist, --usernames, or --auto.")
        return

    # ── Save model ─────────────────────────────────────────────────────────────
    out_path = getattr(args, "output", None) or str(DEFAULT_MODEL_FILE)
    saved = model.save(out_path)
    print()
    _info(f"Model saved: {saved}")
    print(model.describe())


def _resolve_path(p: str):
    """Resolve a path relative to wfh.py location or cwd."""
    from pathlib import Path
    pp = Path(p)
    if pp.exists():
        return pp
    # Try relative to wfh.py location
    wfh_dir = Path(__file__).parent
    alt = wfh_dir / p
    if alt.exists():
        return alt
    return pp  # return as-is (may not exist)


def main() -> None:
    """Main entry point for wfh.py."""
    print(BANNER)

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose if hasattr(args, "verbose") else False:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Apply global execution context ────────────────────────────────────────
    from wfh_modules.thread_pool import validate_thread_count, DEFAULT_THREADS
    from wfh_modules.compute_backend import set_backend

    raw_threads    = getattr(args, "threads", DEFAULT_THREADS) or DEFAULT_THREADS
    compute_mode   = getattr(args, "compute", "auto") or "auto"
    global_use_ml  = not getattr(args, "no_ml_global", False)
    global_limit   = getattr(args, "limit", 0) or 0
    global_timeout = getattr(args, "timeout", 0) or 0

    # Validate and store thread count
    threads = validate_thread_count(raw_threads, clamp=True)
    _GLOBAL_CTX["threads"]      = threads
    _GLOBAL_CTX["compute_mode"] = compute_mode
    _GLOBAL_CTX["use_ml"]       = global_use_ml
    _GLOBAL_CTX["limit"]        = global_limit
    _GLOBAL_CTX["timeout"]      = global_timeout
    _GLOBAL_CTX["start_time"]   = time.time()

    # Initialize compute backend (lazy — only if any module uses it)
    if compute_mode != "auto" or threads > 1:
        try:
            backend = set_backend(compute_mode)
            if compute_mode != "auto":
                _info(f"Compute: {backend.name.upper()} | {backend.device_info}")
        except Exception:
            pass

    # No subcommand → interactive menu
    if not args.command:
        try:
            while True:
                interactive_menu()
                print()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            _info("Exiting.")
        return

    # Dispatch to subcommand handler
    handlers = {
        "charset":    cmd_charset,
        "pattern":    cmd_pattern,
        "profile":    cmd_profile,
        "corp":       cmd_corp,
        "corp-users": cmd_corp_users,
        "phone":      cmd_phone,
        "scrape":   cmd_scrape,
        "ocr":      cmd_ocr,
        "extract":  cmd_extract,
        "leet":     cmd_leet,
        "xor":      cmd_xor,
        "analyze":  cmd_analyze,
        "merge":    cmd_merge,
        "dns":      cmd_dns,
        "pharma":   cmd_pharma,
        "sanitize": cmd_sanitize,
        "reverse":  cmd_reverse,
        "train":         cmd_train,
        "corp-prefixes": cmd_corp_prefixes,
        "sysinfo":       cmd_sysinfo,
        "mangle":        cmd_mangle,
    }

    handler = handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\n")
            _warn("Interrupted by user.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
