#!/usr/bin/env python3
"""
wfh.py — WordList For Hacking v1.2.0

Unified wordlist generation tool for pentest and red team operations.
Supports: charset, pattern, profile, corp, phone, scrape, ocr, extract,
leet, xor, analyze, merge, dns, pharma, sanitize, reverse.

Usage:
  python wfh.py                              # interactive menu
  python wfh.py charset 6 8 abc123           # charset + length
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile                      # interactive personal profiling
  python wfh.py corp                         # interactive corporate profiling
  python wfh.py phone --country brazil --state SP
  python wfh.py phone --ddi 55 --ddd 11 --type mobile
  python wfh.py scrape https://site.com      # web scraping
  python wfh.py ocr image.png               # OCR text extraction
  python wfh.py extract file1.pdf file2.xlsx
  python wfh.py leet word -m medium         # leet speak variants
  python wfh.py xor --brute HEXSTRING       # XOR brute-force
  python wfh.py analyze list.lst            # statistical analysis
  python wfh.py merge l1.lst l2.lst         # merge and deduplication
  python wfh.py dns -w words.lst -d company.com
  python wfh.py pharma                      # Brazilian pharmacy patterns
  python wfh.py charset --create-charset my_charset.cfg
  python wfh.py sanitize list.lst           # clean and normalize wordlist
  python wfh.py reverse list.lst            # reverse line order (tac)

Author: André Henrique (@mrhenrike)
Version: 1.2.0
"""

import argparse
import logging
import os
import sys
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

VERSION = "1.2.0"

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
    + "  Author: Andre Henrique (@mrhenrike)\n"
    + "  Unified wordlist generation for pentest & red team\n"
    + f"{Style.RESET_ALL}"
)

MENU = f"""
{Fore.CYAN}=== MAIN MENU ==={Style.RESET_ALL}

  {Fore.GREEN}[1]{Style.RESET_ALL}  charset   — Generate by charset and length
  {Fore.GREEN}[2]{Style.RESET_ALL}  pattern   — Generate by template with variables
  {Fore.GREEN}[3]{Style.RESET_ALL}  profile   — Interactive personal target profiling
  {Fore.GREEN}[4]{Style.RESET_ALL}  corp      — Interactive corporate target profiling
  {Fore.GREEN}[5]{Style.RESET_ALL}  phone     — Generate phone number wordlists
  {Fore.GREEN}[6]{Style.RESET_ALL}  scrape    — Web scraping wordlist extraction
  {Fore.GREEN}[7]{Style.RESET_ALL}  ocr       — Extract text from image via OCR
  {Fore.GREEN}[8]{Style.RESET_ALL}  extract   — Extract wordlist from files (pdf/xlsx/docx/img)
  {Fore.GREEN}[9]{Style.RESET_ALL}  leet      — Leet speak variants (basic/medium/aggressive/custom)
  {Fore.GREEN}[10]{Style.RESET_ALL} xor       — XOR encryption / brute-force
  {Fore.GREEN}[11]{Style.RESET_ALL} analyze   — Statistical analysis of wordlist
  {Fore.GREEN}[12]{Style.RESET_ALL} merge     — Merge and deduplicate wordlists
  {Fore.GREEN}[13]{Style.RESET_ALL} dns       — DNS/subdomain fuzzing wordlist
  {Fore.GREEN}[14]{Style.RESET_ALL} pharma    — Brazilian pharmacy and health plan patterns
  {Fore.GREEN}[15]{Style.RESET_ALL} sanitize  — Clean wordlist (dedupe, sort, filter, remove blanks/#)
  {Fore.GREEN}[16]{Style.RESET_ALL} reverse   — Reverse line order (tac)
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
) -> int:
    """
    Write generator output to file or stdout with optional progress bar.

    Args:
        generator: String generator.
        output: Output file path or None for stdout.
        estimate: Entry count estimate for progress bar.
        min_len: Minimum length filter.
        max_len: Maximum length filter.

    Returns:
        Total entries written.
    """
    count = 0

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        f = out_path.open("w", encoding="utf-8")
        _info(f"Writing to: {output}")
    else:
        f = None  # type: ignore

    try:
        if _TQDM and estimate and estimate > 0:
            pbar = _tqdm(total=estimate, unit="words", ncols=80)
        else:
            pbar = None

        for word in generator:
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
    )

    if args.create_charset:
        create_charset_wizard(args.create_charset)
        return

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

    if hasattr(args, "name") and args.name:
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
    from wfh_modules.web_scraper import WebScraper

    auth = None
    if args.auth:
        parts = args.auth.split(":", 1)
        auth = (parts[0], parts[1]) if len(parts) == 2 else None

    scraper = WebScraper(
        start_url=args.url,
        depth=args.depth,
        min_word_len=args.min_word,
        max_word_len=args.max_word,
        extract_emails=args.emails,
        extract_meta=args.meta,
        auth=auth,
        delay=args.delay,
    )
    _info(f"Crawling: {args.url} [depth={args.depth}]")
    count = _write_output(scraper.crawl(), args.output)
    _ok(f"Extracted: {count:,} words")


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
    from wfh_modules.analyzer import analyze_wordlist, format_report

    _info(f"Analyzing: {args.wordlist}")
    try:
        metrics = analyze_wordlist(args.wordlist, top_n=args.top)
    except FileNotFoundError as e:
        _err(str(e))
        return

    report = format_report(metrics, args.wordlist)
    print(report)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        _ok(f"Report saved to: {args.output}")


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
    )

    words: list[str] = []
    if args.wordlist:
        words = load_words_from_file(args.wordlist)
    if args.words:
        words.extend(args.words)

    if not words:
        _err("Provide words with --wordlist or --words")
        return

    if args.template:
        gen = generate_from_template(args.template, words, args.domain)
    else:
        gen = generate_subdomain_permutations(
            words, args.domain,
            use_prefixes=not args.no_prefixes,
            use_suffixes=not args.no_suffixes,
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
        ns.country = input("  Country (e.g. brazil, usa, uk): ").strip() or None
        ns.state = input("  State/region (e.g. SP, NY): ").strip() or None
        ns.ddi = input("  DDI override (or Enter): ").strip() or None
        ns.ddd = input("  DDD/area code override (or Enter): ").strip() or None
        ns.type = input("  Type [mobile/landline/both]: ").strip() or "both"
        ns.pattern = input("  Custom pattern (X=digit, or Enter): ").strip() or None
        ns.formats = input("  Formats (e164,local,bare — comma-sep): ").strip() or "e164,local"
        cmd_phone(ns)

    elif choice == "6":
        ns.url = input("  URL to crawl: ").strip()
        ns.depth = int(input("  Depth (default 2): ").strip() or "2")
        ns.min_word = int(input("  Min word length (6): ").strip() or "6")
        ns.max_word = int(input("  Max word length (32): ").strip() or "32")
        ns.emails = input("  Extract emails? [y/N]: ").strip().lower() in ("y", "yes")
        ns.meta = input("  Extract metadata? [y/N]: ").strip().lower() in ("y", "yes")
        ns.auth = None
        ns.delay = 0.5
        cmd_scrape(ns)

    elif choice == "7":
        ns.image = input("  Image path: ").strip()
        ns.lang = input("  OCR languages (default: pt,en): ").strip() or "pt,en"
        cmd_ocr(ns)

    elif choice == "8":
        files_raw = input("  Files (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (4): ").strip() or "4")
        ns.max_len = int(input("  Max length (64): ").strip() or "64")
        cmd_extract(ns)

    elif choice == "9":
        ns.word = input("  Base word: ").strip()
        ns.mode = input("  Mode (basic/medium/aggressive/custom): ").strip() or "basic"
        ns.custom_map = ""
        if ns.mode == "custom":
            ns.custom_map = input("  Mapping (e.g. a=@,4;t=7;s=$): ").strip()
        ns.max_results = int(input("  Max results (10000): ").strip() or "10000")
        cmd_leet(ns)

    elif choice == "10":
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

    elif choice == "11":
        ns.wordlist = input("  Wordlist to analyze: ").strip()
        ns.top = int(input("  Top N (20): ").strip() or "20")
        cmd_analyze(ns)

    elif choice == "12":
        files_raw = input("  Files to merge (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (6): ").strip() or "6")
        ns.max_len = int(input("  Max length (128): ").strip() or "128")
        ns.no_numeric = input("  Remove purely numeric? [y/N]: ").strip().lower() in ("y", "yes")
        ns.filter = None
        ns.no_dedupe = False
        ns.sort = input("  Sort (alpha/length/random or Enter to skip): ").strip() or None
        cmd_merge(ns)

    elif choice == "13":
        ns.domain = input("  Target domain: ").strip()
        ns.wordlist = input("  Words file (or Enter): ").strip() or None
        ns.words = []
        ns.template = None
        ns.no_prefixes = False
        ns.no_suffixes = False
        cmd_dns(ns)

    elif choice == "14":
        ns.codes = input("  Store codes (e.g. 1200-1300 or 1200,1201, Enter for default): ").strip() or None
        cmd_pharma(ns)

    elif choice == "15":
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

    elif choice == "16":
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
  python wfh.py charset 6 8 -f charsets.cfg mixalpha-numeric
  python wfh.py charset --create-charset my_charsets.cfg
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile
  python wfh.py profile --name "John Doe" --nick "johnny" --birth 15/03/1990
  python wfh.py corp
  python wfh.py phone --country brazil --state SP --type mobile -o phones_sp.lst
  python wfh.py phone --country usa --state NY --formats e164,local -o phones_ny.lst
  python wfh.py phone --ddi 55 --ddd 11 --pattern "9XXXX-XXXX" -o custom.lst
  python wfh.py scrape https://site.com -d 2 --emails
  python wfh.py ocr image.png -o wordlist.txt
  python wfh.py extract report.pdf spreadsheet.xlsx -o extracted.txt
  python wfh.py leet admin -m aggressive
  python wfh.py leet password -m custom --custom-map "a=@,4;s=$;e=3"
  python wfh.py xor --brute 1a2b3c4d
  python wfh.py analyze wlist_brasil.lst --top 30
  python wfh.py merge l1.lst l2.lst --no-numeric --sort alpha -o merged.lst
  python wfh.py dns -w words.lst -d company.com
  python wfh.py pharma --codes 1200-1250 -o pharma_passwords.lst
  python wfh.py sanitize wlist_brasil.lst --min-len 8 --sort alpha --inplace
  python wfh.py sanitize list.lst --filter "^[a-zA-Z]" --exclude "\\d{3,}$" -o clean.lst
  python wfh.py sanitize list.lst --min-len 6 --max-len 20 --sort length -o output.lst
  python wfh.py reverse list.lst -o reversed.lst
  python wfh.py reverse list.lst --inplace
""",
    )
    parser.add_argument("--version", action="version", version=f"wfh.py {VERSION}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    sub = parser.add_subparsers(dest="command", help="Operation mode")

    # ── charset ───────────────────────────────────────────────────────────
    p_cs = sub.add_parser("charset", help="Generate by charset and length")
    p_cs.add_argument("min_len", nargs="?", type=int, default=6, help="Minimum length")
    p_cs.add_argument("max_len", nargs="?", type=int, default=8, help="Maximum length")
    p_cs.add_argument("charset", nargs="?", default="lalpha",
                       help="Charset: built-in name or direct character string")
    p_cs.add_argument("-f", "--charset-file", dest="charset_file", help=".cfg charset file")
    p_cs.add_argument("-p", "--pattern", help="Pattern with placeholders (@,%,^,...)")
    p_cs.add_argument("--create-charset", dest="create_charset", metavar="FILE",
                       help="Wizard to create a charset file")
    p_cs.add_argument("-o", "--output", help="Output file")

    # ── pattern ───────────────────────────────────────────────────────────
    p_pt = sub.add_parser("pattern", help="Generate by template with variables")
    p_pt.add_argument("-t", "--template", help="Template (e.g. DS{cod}@rd.com.br)")
    p_pt.add_argument("-f", "--template-file", dest="template_file", help="Template file")
    p_pt.add_argument("--vars", nargs="+", metavar="KEY=VALUE",
                       help="Variables (e.g. cod=1200-1300 company=Drogasil,Hapvida)")
    p_pt.add_argument("-o", "--output", help="Output file")

    # ── profile ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser("profile", help="Interactive personal target profiling")
    p_pr.add_argument("--name", help="Target full name")
    p_pr.add_argument("--nick", help="Nickname or alias")
    p_pr.add_argument("--birth", help="Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or age)")
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
    p_sc.add_argument("-d", "--depth", type=int, default=2, help="Crawl depth")
    p_sc.add_argument("--min-word", type=int, default=6, dest="min_word")
    p_sc.add_argument("--max-word", type=int, default=32, dest="max_word")
    p_sc.add_argument("--emails", action="store_true", help="Extract emails")
    p_sc.add_argument("--meta", action="store_true", help="Extract metadata")
    p_sc.add_argument("--auth", help="HTTP Basic Auth (user:password)")
    p_sc.add_argument("--delay", type=float, default=0.5)
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
    p_an.add_argument("--top", type=int, default=20, help="Top N most frequent")
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
    p_mg.add_argument("--sort", choices=["alpha", "length", "random"])
    p_mg.add_argument("-o", "--output", help="Output file")

    # ── dns ───────────────────────────────────────────────────────────────
    p_dn = sub.add_parser("dns", help="DNS/subdomain fuzzing wordlist")
    p_dn.add_argument("-d", "--domain", required=True, help="Target domain")
    p_dn.add_argument("-w", "--wordlist", help="Words file")
    p_dn.add_argument("--words", nargs="+", help="Direct word list")
    p_dn.add_argument("-t", "--template", help="Template (e.g. dev-{word}.{domain})")
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
                       choices=["alpha", "alpha-rev", "length", "length-rev", "random"],
                       help="Sort mode for output")
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

    return parser


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    """Main entry point for wfh.py."""
    print(BANNER)

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose if hasattr(args, "verbose") else False:
        logging.getLogger().setLevel(logging.DEBUG)

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
        "charset":  cmd_charset,
        "pattern":  cmd_pattern,
        "profile":  cmd_profile,
        "corp":     cmd_corp,
        "phone":    cmd_phone,
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
