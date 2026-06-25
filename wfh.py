#!/usr/bin/env python3
"""
wfh.py — WordList For Hacking v2.0.0

Unified wordlist generation tool for pentest and red team operations.
Supports: charset, pattern, profile, corp, phone, scrape, ocr, extract,
leet, xor, analyze, merge, dns, pharma, sanitize, reverse, mangle.

Usage:
  python wfh.py                              # interactive menu
  python wfh.py charset 6 8 abc123           # charset + length
  python wfh.py pattern -t "XX{cod}@corp.example.com" --vars cod=1200-1300
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

VERSION = "2.7.0"

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
    "min_len":      0,      # global minimum entry length (0=no filter)
    "max_len":      0,      # global maximum entry length (0=no filter)
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
  {Fore.GREEN}[22]{Style.RESET_ALL} default-creds — Query default credentials database (IoT/routers/SNMP)
  {Fore.GREEN}[23]{Style.RESET_ALL} isp-keygen    — ISP default WiFi password keyspace generator
  {Fore.GREEN}[24]{Style.RESET_ALL} phrase        — Phrase-initials password generator (@0x90 style)
  {Fore.GREEN}[25]{Style.RESET_ALL} mutate        — Mutate an existing password (case/leet/prefix/suffix)
  {Fore.GREEN}[26]{Style.RESET_ALL} num2text      — Convert digits to text words and generate variations
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
    stream: bool = False,
    avg_entry_len: int = 14,
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
        stream: If True, flush after each write (real-time output).

    Returns:
        Total entries written.
    """
    count = 0
    limit = _GLOBAL_CTX.get("limit", 0)
    timeout = _GLOBAL_CTX.get("timeout", 0)
    start = _GLOBAL_CTX.get("start_time", 0.0) or time.time()

    # Global min/max override: take the most restrictive bound
    g_min = _GLOBAL_CTX.get("min_len", 0) or 0
    g_max = _GLOBAL_CTX.get("max_len", 0) or 0
    if g_min > 0:
        min_len = max(min_len, g_min)
    if g_max > 0:
        max_len = min(max_len, g_max) if max_len > 0 else g_max

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not _check_disk_space(output, estimate=estimate, avg_entry_len=avg_entry_len):
            _warn("Cancelled by user — no file written.")
            return 0
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
                if stream:
                    f.flush()
            else:
                sys.stdout.write(line)
                if stream:
                    sys.stdout.flush()
            count += 1
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

    finally:
        if f:
            f.close()

    return count


def _effective_len_bounds(min_len: int = 0, max_len: int = 9999) -> tuple[int, int]:
    """Merge profile/command bounds with global --min-len / --max-len."""
    g_min = _GLOBAL_CTX.get("min_len", 0) or 0
    g_max = _GLOBAL_CTX.get("max_len", 0) or 0
    if g_min > 0:
        min_len = max(min_len, g_min)
    if g_max > 0:
        max_len = min(max_len, g_max) if max_len > 0 else g_max
    return min_len, max_len


def _count_generator_entries(
    generator: Generator[str, None, None],
    min_len: int = 0,
    max_len: int = 9999,
) -> tuple[int, int, float]:
    """
    Count filtered generator output without writing.

    Returns:
        (entry_count, total_bytes_including_newlines, avg_line_length)
    """
    min_len, max_len = _effective_len_bounds(min_len, max_len)
    count = 0
    total_bytes = 0
    for word in generator:
        if not word:
            continue
        if min_len and len(word) < min_len:
            continue
        if max_len and len(word) > max_len:
            continue
        count += 1
        total_bytes += len(word.encode("utf-8")) + 1
    avg = total_bytes / count if count else 0.0
    return count, total_bytes, avg


def _profile_preview_and_confirm(
    profile: dict,
    leet_mode: str,
    output_path: str,
) -> Optional[tuple[int, float]]:
    """
    Count profile entries, show size summary, optionally ask to proceed.

    Returns:
        (count, avg_line_bytes) if user proceeds, None if cancelled.
    """
    from wfh_modules.profiler import generate_from_profile

    min_len = int(profile.get("min_len", 6) or 0)
    max_len = int(profile.get("max_len", 32) or 0) or 9999

    _info("Estimating wordlist — counting entries (this may take a moment)...")
    gen = generate_from_profile(profile, leet_mode=leet_mode)
    count, total_bytes, avg_len = _count_generator_entries(gen, min_len, max_len)

    print()
    print("  ┌─ Wordlist preview ─────────────────────────")
    print(f"  │  Entries (lines) : {count:,}")
    print(f"  │  Est. file size  : {_format_bytes(total_bytes)}")
    print(f"  │  Avg line length : {avg_len:.1f} chars")
    print(f"  │  Output file     : {output_path}")
    if profile.get("location_country") and not profile.get("include_country_variations", True):
        print("  │  Country mode    : minimal (ISO + name only)")
    elif profile.get("location_country"):
        print("  │  Country mode    : full variations (ISO, names, DDI, leet, combos)")
    print("  └────────────────────────────────────────────")
    print()

    ask = profile.get("interactive_mode", False)
    if ask:
        try:
            resp = input("  Generate and save this wordlist? [Y/n]: ").strip().lower()
            if resp in ("n", "no"):
                _warn("Cancelled by user — no file written.")
                return None
        except (KeyboardInterrupt, EOFError):
            _warn("Cancelled — no file written.")
            return None
    elif count == 0:
        _warn("No entries matched the current filters — nothing to write.")
        return None

    return count, avg_len


def _format_bytes(n: int) -> str:
    """Format byte count as human-readable string (B → KB → MB → GB → TB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n = int(n / 1024)
    return f"{n:.1f} PB"


def _check_disk_space(
    output: str,
    estimate: Optional[int] = None,
    avg_entry_len: int = 14,
) -> bool:
    """
    Check available disk space before writing an output file.

    Warns and requests confirmation when:
    - Estimated file size >= 50 MB, OR
    - Estimated file size > 60 %% of free space, OR
    - Free disk space < 300 MB regardless of estimate.

    Args:
        output: Destination file path.
        estimate: Expected number of entries (None = unknown).
        avg_entry_len: Average bytes per entry (including newline) for size estimation.

    Returns:
        True to proceed, False to cancel.
    """
    import shutil

    try:
        target_dir = Path(output).resolve().parent
        usage = shutil.disk_usage(str(target_dir))
        free_bytes = usage.free
    except Exception:
        return True  # can't check → proceed silently

    warn_parts: list[str] = []
    needs_confirm = False

    est_bytes: Optional[int] = None
    if estimate is not None and estimate > 0:
        est_bytes = estimate * avg_entry_len

    if est_bytes is not None:
        if est_bytes >= 50 * 1024 * 1024:          # >= 50 MB
            warn_parts.append(f"Estimated file size : {_format_bytes(est_bytes)}")
            needs_confirm = True
        if est_bytes > free_bytes * 0.6:            # > 60%% of free space
            warn_parts.append(
                f"File may use {est_bytes / free_bytes * 100:.0f}%% of available disk space"
            )
            needs_confirm = True

    if free_bytes < 300 * 1024 * 1024:             # < 300 MB free (always warn)
        warn_parts.insert(0, "Low disk space!")
        needs_confirm = True

    warn_parts.append(
        f"Free disk space     : {_format_bytes(free_bytes)}  "
        f"[{Path(output).resolve().parent}]"
    )

    if not needs_confirm:
        if est_bytes is not None:
            _info(f"Output size estimate: {_format_bytes(est_bytes)} | "
                  f"Free: {_format_bytes(free_bytes)}")
        return True

    print()
    for line in warn_parts:
        _warn(line)
    print()

    try:
        resp = input("  Continue writing to file? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


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
    from wfh_modules.profiler import interactive_profile, resolve_profile_output

    # ── Resolve locale: CLI --lang > YAML locale > session default ────────────
    from wfh_modules.i18n import set_session_locale as _set_locale
    _cli_lang = getattr(args, "lang", None)
    if _cli_lang:
        _set_locale(_cli_lang)

    # ── Load from YAML file ──────────────────────────────────────────────────
    if getattr(args, "profile_file", None):
        from wfh_modules.profiler import load_profile_yaml
        try:
            profile = load_profile_yaml(args.profile_file)
            if not _cli_lang and profile.get("locale"):
                _set_locale(profile["locale"])
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
            "leet_mode": getattr(args, "leet", None) or "basic",
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
            profile["suffix_range_zero_pad"] = len(parts[0]) if parts[0].startswith("0") else 0
        except (ValueError, IndexError):
            _warn(f"Invalid --suffix-range format '{args.suffix_range}', expected START-END (e.g. 00-99)")

    # ── Inject CUPP/elpscrk/BEWGor fields from CLI ──────────────────────────
    if getattr(args, "surname", None):
        profile["surname"] = args.surname
    if getattr(args, "old_passwords", None):
        profile["old_passwords"] = args.old_passwords
    if getattr(args, "depth", None):
        profile["depth"] = args.depth
    if getattr(args, "parents", None):
        profile["parents"] = args.parents
    if getattr(args, "siblings", None):
        profile["siblings"] = args.siblings

    # ── Inject engine/pipeline flags from CLI ───────────────────────────────
    _cli_engines = getattr(args, "engines", None)
    if _cli_engines:
        profile["engines"] = _cli_engines
    elif profile.get("_engine_ids"):
        # Promote interactive wizard selection to pipeline-compatible format
        profile["engines"] = ",".join(str(i) for i in profile["_engine_ids"])

    _max_cand = getattr(args, "max_candidates", 0)
    if _max_cand:
        profile["max_candidates"] = _max_cand
    _timeout = getattr(args, "timeout_secs", 0.0)
    if _timeout:
        profile["timeout_secs"] = _timeout

    leet_mode = getattr(args, "leet", None) or profile.get("leet_mode", "basic")
    profile["leet_mode"] = leet_mode

    output = resolve_profile_output(getattr(args, "output", None), profile)

    # ── Pipeline execution ───────────────────────────────────────────────────
    try:
        from wfh_modules.pipeline_engine import run_profile_pipeline, ProfilePipeline, PipelineConfig
        _use_pipeline = True
    except ImportError:
        _use_pipeline = False

    if _use_pipeline:
        if output:
            profile["output_path"] = output
            # Quick preview using legacy generator before the heavy pipeline runs
            _preview_ok = True
            if profile.get("interactive_mode"):
                from wfh_modules.profiler import generate_from_profile
                preview = _profile_preview_and_confirm(profile, leet_mode, output)
                if preview is None:
                    return
            _info(f"Running generation pipeline [leet={leet_mode}, engines={profile.get('engines', 'default')}]...")
            try:
                result = run_profile_pipeline(profile, output_path=output)
                count = result.get("lines_written", 0)
                elapsed = result.get("elapsed_secs", 0)
                archive = result.get("archive", {})
                feedback = result.get("feedback", {})
                if count:
                    dest = archive.get("output_path") or output
                    _ok(f"Generated: {count:,} entries → {dest} [{elapsed}s]")
                    if feedback:
                        hit_rate = feedback.get("hit_rate", 0)
                        hits = feedback.get("hits", 0)
                        total = feedback.get("total", 0)
                        _info(f"Feedback: {hits}/{total} known targets found ({hit_rate:.1%} hit rate)")
                else:
                    _warn("No entries written.")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
        else:
            _info(f"Running generation pipeline [leet={leet_mode}] → stdout...")
            try:
                config = PipelineConfig.from_profile(profile)
                pipeline = ProfilePipeline(profile, config)
                count = _write_output(pipeline.run(), None)
                _ok(f"Generated: {count:,} entries (stdout — use -o or interactive output prompt to save)")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
    else:
        # Fallback to legacy generator when pipeline_engine is unavailable
        from wfh_modules.profiler import generate_from_profile
        if output:
            preview = _profile_preview_and_confirm(profile, leet_mode, output)
            if preview is None:
                return
            est_count, avg_len = preview
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(
                gen, output,
                estimate=est_count,
                min_len=int(profile.get("min_len", 0) or 0),
                max_len=int(profile.get("max_len", 0) or 0),
                avg_entry_len=max(1, int(avg_len)),
            )
            if count:
                _ok(f"Generated: {count:,} entries → {output}")
            else:
                _warn("No entries written.")
        else:
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(gen, None)
            _ok(f"Generated: {count:,} entries (stdout — use -o or interactive output prompt to save)")


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

    suffix = getattr(args, "suffix", None) or ""
    prefix_file = getattr(args, "prefix_file", None)
    digit_length = getattr(args, "digit_length", None)

    if prefix_file:
        from wfh_modules.dns_wordlist import load_words_from_file
        prefixes = load_words_from_file(prefix_file)
        _info(f"Loaded {len(prefixes)} prefixes from {prefix_file}")
        pattern = "X" * (digit_length or 7)

        def _multi_prefix_gen():
            for px in prefixes:
                px = px.strip().lstrip("#")
                if not px:
                    continue
                for num in generate_phones(
                    ddi="", ddd="",
                    custom_pattern=pattern,
                    output_formats=["bare"],
                ):
                    entry = px + num + suffix
                    yield entry

        count = _write_output(_multi_prefix_gen(), args.output)
        _ok(f"Generated: {count:,} phone entries (multi-prefix)")
        return

    if digit_length:
        params["custom_pattern"] = "X" * digit_length

    _info(f"Generating phone numbers [country={params.get('country') or 'custom'}]...")

    def _gen_with_suffix():
        for num in generate_phones(**params):
            yield num + suffix if suffix else num

    count = _write_output(_gen_with_suffix(), args.output)
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
    include_js = getattr(args, "include_js", False)
    include_css = getattr(args, "include_css", False)
    include_pdf = getattr(args, "include_pdf", False)
    lowercase = getattr(args, "lowercase", False)
    subdomain_strategy = getattr(args, "subdomain_strategy", "exact")
    output_emails = getattr(args, "output_emails", None)
    output_urls = getattr(args, "output_urls", None)

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

    all_emails: set[str] = set()
    all_urls: list[str] = []

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
            include_js=include_js,
            include_css=include_css,
            include_pdf=include_pdf,
            lowercase=lowercase,
            subdomain_strategy=subdomain_strategy,
        )
        _info(f"Crawling: {url} [depth={args.depth}]")
        if include_js:
            _info("Including JavaScript content")
        if include_css:
            _info("Including CSS content")
        if include_pdf:
            _info("Including PDF content")
        if getattr(args, "proxy", None):
            _info(f"Proxy: {args.proxy}")
        stream_mode = getattr(args, "stream", False)
        if stream_mode and not args.output:
            _warn("--stream requires -o/--output. Ignoring --stream.")
            stream_mode = False
        count = _write_output(scraper.crawl(), args.output, append=(total_count > 0), stream=stream_mode)
        total_count += count
        all_emails |= scraper.emails_found
        all_urls.extend(scraper.urls_visited)

    _ok(f"Extracted: {total_count:,} words from {len(urls_to_crawl)} URL(s)")

    if output_emails and all_emails:
        with open(output_emails, "w", encoding="utf-8", newline="\n") as ef:
            for email in sorted(all_emails):
                ef.write(email + "\n")
        _ok(f"Emails: {len(all_emails)} written to {output_emails}")

    if output_urls and all_urls:
        with open(output_urls, "w", encoding="utf-8", newline="\n") as uf:
            for u in all_urls:
                uf.write(u + "\n")
        _ok(f"URLs visited: {len(all_urls)} written to {output_urls}")


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


def cmd_mutate(args: argparse.Namespace) -> None:
    """Handler for existing-password mutation generator."""
    from wfh_modules.profiler import password_variants

    password = getattr(args, "password", "") or ""
    if not password:
        _err("A password is required.")
        return

    extra_prefixes: Optional[list[str]] = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        extra_prefixes = ["" if p == "EMPTY" else p for p in raw_pfx.split(",")]

    extra_suffixes: Optional[list[str]] = None
    raw_sfx = getattr(args, "suffixes", None)
    if raw_sfx:
        extra_suffixes = ["" if s == "EMPTY" else s for s in raw_sfx.split(",")]

    leet_mode = getattr(args, "leet_mode", "all") or "all"
    min_len = getattr(args, "min_len", 1) or 1
    max_len = getattr(args, "max_len", 128) or 128

    _info(f"Password : {password}")
    _info(f"Leet     : {leet_mode}")

    variants = password_variants(
        password,
        extra_prefixes=extra_prefixes,
        extra_suffixes=extra_suffixes,
        leet_mode=leet_mode,
        min_len=min_len,
        max_len=max_len,
    )

    def _gen():
        yield from variants

    count = _write_output(_gen(), args.output)
    _ok(f"Generated: {count:,} mutation variants")


def cmd_num2text(args: argparse.Namespace) -> None:
    """Convert digits to text words and generate case/leet/separator variations."""
    from wfh_modules.num2text import num2text_variants, num2text_range, _normalise_lang

    lang     = _normalise_lang(getattr(args, "lang", "en") or "en")
    raw_seps = getattr(args, "separators", None)
    seps     = [s for s in raw_seps.split(",")] if raw_seps else None
    no_leet  = getattr(args, "no_leet", False)
    min_len  = getattr(args, "min_len", 0) or 0
    max_len  = getattr(args, "max_len", 0) or 0

    raw_range  = getattr(args, "range", None)
    raw_number = getattr(args, "number", None)

    if raw_range:
        parts = raw_range.split("-", 1)
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            _err("--range must be in format START-END (e.g. 0-9999)")
            return
        start, end = int(parts[0]), int(parts[1])
        if end - start > 1_000_000:
            _err("Range too large (max 1,000,000 numbers at once)")
            return
        _info(f"num2text range {start}-{end}  lang={lang}")
        gen = num2text_range(start, end, lang, seps, not no_leet, min_len, max_len)
    elif raw_number:
        s = str(raw_number)
        if not s.isdigit():
            _err("--number must contain digits only")
            return
        if len(s) > 12:
            _err("--number exceeds 12 digits")
            return
        _info(f"num2text: {s}  lang={lang}")
        gen = num2text_variants(s, lang, seps, not no_leet, min_len, max_len)
    else:
        _err("Provide --number or --range")
        return

    count = _write_output(gen, args.output)
    _ok(f"num2text: {count:,} variants generated")


def cmd_phrase(args: argparse.Namespace) -> None:
    """Handler for phrase-initials password generation."""
    from wfh_modules.profiler import phrase_initials_variants

    phrase = getattr(args, "phrase", "") or ""
    if not phrase:
        _err("A phrase is required.")
        return

    extra_prefixes: Optional[list[str]] = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        parts = raw_pfx.split(",")
        extra_prefixes = ["" if p == "EMPTY" else p for p in parts]

    extra_suffixes: Optional[list[str]] = None
    raw_sfx = getattr(args, "suffixes", None)
    if raw_sfx:
        parts = raw_sfx.split(",")
        extra_suffixes = ["" if s == "EMPTY" else s for s in parts]

    _info(f"Phrase : {phrase}")

    variants = phrase_initials_variants(
        phrase,
        extra_prefixes=extra_prefixes,
        extra_suffixes=extra_suffixes,
    )

    def _gen():
        yield from variants

    count = _write_output(_gen(), args.output)
    _ok(f"Generated: {count:,} phrase-initials variants")


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


def cmd_leet_perm(args: argparse.Namespace) -> None:
    """Handler for cartesian leet permutation over a wordlist (elpscrk-style)."""
    from wfh_modules.leet_permuter import leet_perm_wordlist, parse_custom_mapping, LEET_MEDIUM

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _err("Provide a wordlist file.")
        return
    path = Path(wordlist)
    if not path.exists():
        _err(f"File not found: {wordlist}")
        return

    leet_map = None
    custom = getattr(args, "custom_map", "") or ""
    if custom:
        parsed = parse_custom_mapping(custom)
        leet_map = {
            k: (v[0] if v else k)
            for k, v in parsed.items()
        }
    elif getattr(args, "mode", "medium") == "medium":
        leet_map = {
            k: (v[1] if len(v) > 1 else k)
            for k, v in LEET_MEDIUM.items()
        }

    max_per = getattr(args, "max_per_word", 512) or 512
    max_lines = getattr(args, "max_lines", 0) or 0

    def _gen():
        count = 0
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                word = line.rstrip("\n\r")
                if not word:
                    continue
                count += 1
                if max_lines and count > max_lines:
                    break
                yield from leet_perm_wordlist([word], leet_map=leet_map, max_per_word=max_per)

    _info(f"Applying leet-perm to {wordlist} (max {max_per}/word)...")
    total = _write_output(_gen(), args.output)
    _ok(f"Generated: {total:,} leet-perm variants")


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

    if getattr(args, "mask_optindex", False):
        from wfh_modules.analyzer import (
            maskgen_optindex,
            format_maskgen_report,
            export_masks_csv_pack,
        )
        _info("Running PACK maskgen optindex ranking...")
        try:
            if mask_data is None:
                mask_data = analyze_masks(args.wordlist, top_n=args.top)
            opt_rows = maskgen_optindex(
                mask_data,
                pps=int(getattr(args, "pps", 0) or 0),
                target_time_hrs=float(getattr(args, "time_budget", 1.0) or 1.0),
                use_gpu=bool(getattr(args, "use_gpu", False)),
            )
            print(format_maskgen_report(opt_rows))
            opt_out = getattr(args, "mask_csv", None)
            if opt_out:
                export_masks_csv_pack(opt_rows, opt_out)
                _ok(f"PACK mask CSV saved: {opt_out}")
        except Exception as exc:
            _warn(f"Mask optindex failed: {exc}")

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
    """Handler for DNS wordlist generation (alterx + DNSCewl parity)."""
    from wfh_modules.dns_wordlist import (
        generate_subdomain_permutations, generate_from_template, load_words_from_file,
        load_templates_from_yaml, generate_from_yaml_templates,
        generate_multi_domain, filter_dns_output, clusterbomb_generate,
        parse_fqdn, enrich_payloads, dnscewl_mutations, estimate_output,
        PAYLOAD_WORD, PAYLOAD_NUMBER, PAYLOAD_REGION, DEFAULT_PATTERNS,
    )
    from itertools import chain

    match_regex = getattr(args, "match_regex", None)
    filter_regex = getattr(args, "filter_regex", None)
    separator = getattr(args, "separator", None)
    separators = [separator] if separator else None

    words: list[str] = []
    if getattr(args, "wordlist", None):
        words = load_words_from_file(args.wordlist)
    if getattr(args, "words", None):
        words.extend(args.words)

    custom_payloads: dict[str, list[str]] = {}
    for pp in (getattr(args, "payloads", None) or []):
        if "=" in pp:
            key, fpath = pp.split("=", 1)
            custom_payloads[key.strip()] = load_words_from_file(fpath.strip())

    # ── Multi-domain mode ──────────────────────────────────────
    domain_list = getattr(args, "domain_list", None)
    if domain_list and not getattr(args, "clusterbomb", False):
        gen = generate_multi_domain(
            domain_list, words or PAYLOAD_WORD, separators,
            use_prefixes=not getattr(args, "no_prefixes", False),
            use_suffixes=not getattr(args, "no_suffixes", False),
            match_regex=match_regex, filter_regex=filter_regex,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} DNS entries")
        return

    # ── ClusterBomb mode (alterx-style) ────────────────────────
    if getattr(args, "clusterbomb", False) or getattr(args, "template_file", None):
        payloads = {
            "word": words if words else PAYLOAD_WORD,
            "number": PAYLOAD_NUMBER,
            "region": PAYLOAD_REGION,
        }
        payloads.update(custom_payloads)

        patterns = DEFAULT_PATTERNS
        extra_yaml_payloads: dict = {}

        template_file = getattr(args, "template_file", None)
        if template_file:
            try:
                yaml_templates, yaml_payloads = load_templates_from_yaml(template_file)
                if yaml_templates:
                    patterns = yaml_templates
                if yaml_payloads:
                    extra_yaml_payloads = yaml_payloads
                    payloads.update(yaml_payloads)
            except (FileNotFoundError, ImportError) as exc:
                _err(str(exc))
                return

        input_fqdns = []
        if args.domain:
            input_fqdns = [args.domain]
        elif domain_list:
            input_fqdns = load_words_from_file(domain_list)

        if getattr(args, "enrich", False) and input_fqdns:
            payloads["word"], payloads["number"] = enrich_payloads(
                input_fqdns, payloads["word"], payloads["number"],
            )
            _info(f"Enriched: {len(payloads['word'])} words, {len(payloads['number'])} numbers")

        if getattr(args, "estimate", False):
            est = estimate_output(patterns, payloads, len(input_fqdns) or 1)
            _ok(f"Estimated output: {est:,} lines")
            return

        generators = []
        for fqdn in (input_fqdns or [""]):
            input_vars = parse_fqdn(fqdn) if fqdn else {}
            generators.append(clusterbomb_generate(
                patterns, payloads, input_vars,
                match_regex=match_regex, filter_regex=filter_regex,
            ))

        if getattr(args, "dnscewl", False) and input_fqdns:
            for fqdn in input_fqdns:
                generators.append(dnscewl_mutations(
                    payloads["word"][:50], fqdn,
                    numeric_range=getattr(args, "numeric_range", 10),
                    extension_swap=getattr(args, "extension_swap", None),
                ))

        count = _write_output(chain(*generators), args.output)
        _ok(f"Generated: {count:,} DNS entries (ClusterBomb)")
        return

    if not words:
        words = PAYLOAD_WORD[:30]
        _info(f"No words provided — using {len(words)} built-in payloads")

    generators = []

    if args.template:
        gen = generate_from_template(args.template, words, args.domain)
        generators.append(filter_dns_output(gen, match_regex, filter_regex))
    else:
        generators.append(generate_subdomain_permutations(
            words, args.domain, separators,
            use_prefixes=not args.no_prefixes,
            use_suffixes=not args.no_suffixes,
            match_regex=match_regex, filter_regex=filter_regex,
        ))

    if getattr(args, "dnscewl", False):
        generators.append(dnscewl_mutations(
            words[:50], args.domain,
            numeric_range=getattr(args, "numeric_range", 10),
            extension_swap=getattr(args, "extension_swap", None),
        ))

    count = _write_output(chain(*generators), args.output)
    _ok(f"Generated: {count:,} subdomains")


def cmd_pharma(args: argparse.Namespace) -> None:
    """Generate passwords and usernames for retail/pharmacy chain patterns."""
    from wfh_modules.pharma_gen import (
        gen_passwords, gen_usernames, gen_both, _expand_id_range,
    )

    brand  = getattr(args, "brand", None) or "AcmePharma"
    mode   = getattr(args, "mode", "both") or "both"

    raw_ids = getattr(args, "ids", None)
    if raw_ids:
        store_ids = _expand_id_range(raw_ids)
    else:
        store_ids = list(range(1200, 1215))

    raw_cnpjs  = getattr(args, "cnpj", None)
    cnpjs      = [c.strip() for c in raw_cnpjs.split(",")] if raw_cnpjs else []

    raw_abbrevs = getattr(args, "abbrevs", None)
    abbrevs     = [a.strip() for a in raw_abbrevs.split(",")] if raw_abbrevs else None

    raw_seps = getattr(args, "separators", None)
    seps     = [s for s in raw_seps.split(",")] if raw_seps else None

    raw_partners = getattr(args, "partners", None)
    partners     = [p.strip() for p in raw_partners.split(",")] if raw_partners else None

    raw_domains = getattr(args, "domains", None)
    domains     = [d.strip() for d in raw_domains.split(",")] if raw_domains else None

    padding  = not getattr(args, "no_padding", False)
    min_len  = getattr(args, "min_len", 0) or 0
    max_len  = getattr(args, "max_len", 0) or 0

    _info(f"Brand: {brand}  |  IDs: {len(store_ids)}  |  Tax IDs: {len(cnpjs)}  |  Mode: {mode}")

    if mode == "passwords":
        gen = gen_passwords(brand, store_ids, cnpjs, abbrevs, seps, partners,
                            padding, min_len, max_len)
    elif mode == "usernames":
        gen = gen_usernames(brand, store_ids, domains, abbrevs, padding,
                            True, min_len, max_len)
    else:
        gen = gen_both(brand, store_ids, cnpjs, abbrevs, seps, partners,
                       domains, padding, min_len, max_len)

    count = _write_output(gen, args.output)
    _ok(f"pharma: {count:,} entries generated")


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


def cmd_default_creds(args: argparse.Namespace) -> None:
    """Handler for the default-creds subcommand — query IoT/router default credentials."""
    from wfh_modules.default_creds import handle_default_creds
    handle_default_creds(args, {})


def cmd_isp_keygen(args: argparse.Namespace) -> None:
    """Handler for ISP default WiFi password keyspace generation."""
    from wfh_modules.isp_keygen import handle_isp_keygen
    handle_isp_keygen(args, {})


def cmd_password_dna(args: argparse.Namespace) -> None:
    """Handler for password DNA analysis and variant generation."""
    from wfh_modules.password_dna import handle_password_dna

    dna, gen = handle_password_dna(args, {})
    if not dna or not gen:
        _err("No passwords provided. Pass them as arguments or via --file.")
        return

    _info(f"Analyzing {dna.n} password(s)...")
    if getattr(args, "show_dna", False):
        print()
        print(dna.describe())
        print()

    depth = getattr(args, "depth", "normal")
    _info(f"Generating variants [depth={depth}]...")
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} candidates from {dna.n} password DNA(s)")


def cmd_combiner(args: argparse.Namespace) -> None:
    """Handler for keyword combiner wordlist generation."""
    from wfh_modules.combiner import handle_combiner
    gen = handle_combiner(args, {})
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} combined entries")


def cmd_pcfg(args: argparse.Namespace) -> None:
    """Handler for PCFG grammar training and generation."""
    from wfh_modules.pcfg_engine import handle_pcfg
    gen = handle_pcfg(args, _GLOBAL_CTX)
    if gen:
        action = getattr(args, "pcfg_action", "generate")
        if action == "train":
            for line in gen:
                print(line)
        else:
            count = _write_output(
                gen, args.output,
                min_len=getattr(args, "min_len", 1),
                max_len=getattr(args, "max_len", 64),
            )
            _ok(f"PCFG generated: {count:,} candidates (probability-ordered)")


def cmd_markov(args: argparse.Namespace) -> None:
    """Handler for Markov model training and generation."""
    from wfh_modules.markov_engine import handle_markov
    gen = handle_markov(args, _GLOBAL_CTX)
    if gen:
        action = getattr(args, "markov_action", "generate")
        if action == "train":
            for line in gen:
                print(line)
        else:
            count = _write_output(
                gen, args.output,
                min_len=getattr(args, "min_len", 4),
                max_len=getattr(args, "max_len", 16),
            )
            _ok(f"Markov generated: {count:,} candidates (cost-ordered)")


def cmd_kwalk(args: argparse.Namespace) -> None:
    """Handler for keyboard walk generation."""
    from wfh_modules.kwalk_gen import handle_kwalk
    gen = handle_kwalk(args, _GLOBAL_CTX)
    if gen:
        if getattr(args, "list_layouts", False):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, args.output)
            _ok(f"Keyboard walks generated: {count:,} candidates")


def cmd_rulegen(args: argparse.Namespace) -> None:
    """Handler for hashcat rule auto-generation."""
    from wfh_modules.rulegen_engine import handle_rulegen
    gen = handle_rulegen(args, _GLOBAL_CTX)
    if gen:
        output = getattr(args, "output", None)
        if output and output.endswith(".rule"):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, output)
            _ok(f"Rules generated: {count:,} hashcat-compatible rules")


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Handler for wordlist quality benchmarking."""
    from wfh_modules.benchmark_suite import handle_benchmark
    gen = handle_benchmark(args, _GLOBAL_CTX)
    if gen:
        output = getattr(args, "output", None)
        if output:
            with open(output, "w", encoding="utf-8") as fh:
                for line in gen:
                    fh.write(line + "\n")
            _ok(f"Benchmark report saved: {output}")
        else:
            for line in gen:
                print(line)


def cmd_prince(args: argparse.Namespace) -> None:
    """Handler for PRINCE attack mode."""
    from wfh_modules.prince_engine import handle_prince
    gen = handle_prince(args, _GLOBAL_CTX)
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"PRINCE generated: {count:,} chained candidates")


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

    lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n\r") for ln in f if ln.strip()]

    if getattr(args, "overseer", False):
        from wfh_modules.mangler import overseer_expand, OverseerConfig
        cfg = OverseerConfig(
            pps=int(getattr(args, "pps", 0) or 0),
            target_time_hrs=float(getattr(args, "time_budget", 1.0) or 1.0),
            use_gpu=bool(getattr(args, "use_gpu", False)),
            use_capswap=bool(getattr(args, "capswap", False)),
        )
        masks_raw = getattr(args, "masks", None)
        if masks_raw:
            cfg.masks = [m.strip() for m in masks_raw.split(",") if m.strip()]
        _info(
            f"PyMangler Overseer: {len(lines)} base words, "
            f"budget={cfg.target_time_hrs}h, gpu={cfg.use_gpu}"
        )
        gen = overseer_expand(lines[:50], cfg)
    else:
        rules = getattr(args, "rules", "all") or "all"
        if rules == "all":
            active_rules = list(BUILTIN_RULES.keys())
        else:
            active_rules = [r.strip() for r in rules.split(",") if r.strip()]
        _info(f"Mangling: {wordlist_path} with rules: {', '.join(active_rules)}")
        gen = apply_rules(lines, active_rules)

    count = _write_output(gen, args.output)
    _ok(f"Mangled output: {count:,} entries")


def cmd_improve(args: argparse.Namespace) -> None:
    """Enrich an existing wordlist (CUPP -w parity)."""
    from wfh_modules.profiler import improve_wordlist

    source = getattr(args, "wordlist", None)
    if not source:
        _err("Provide a wordlist to improve.")
        return
    if not Path(source).is_file():
        _err(f"File not found: {source}")
        return

    output = args.output or str(
        Path(source).with_name(Path(source).stem + ".improved.lst")
    )
    count = improve_wordlist(
        source_path=source,
        output_path=output,
        leet_mode=getattr(args, "leet", "basic") or "basic",
        append_years=not getattr(args, "no_years", False),
        append_specials=not getattr(args, "no_specials", False),
        year_start=int(getattr(args, "year_start", 2020)),
        year_end=int(getattr(args, "year_end", 2027)),
        min_len=int(getattr(args, "min_len", 6)),
        max_len=int(getattr(args, "max_len", 32)),
    )
    _ok(f"Improved wordlist: {count:,} entries -> {output}")


def cmd_maya_rank(args: argparse.Namespace) -> None:
    """Rank a wordlist by MAYA-inspired cracking probability."""
    from wfh_modules.maya_ranker import rank_wordlist, format_rank_report

    source = getattr(args, "wordlist", None)
    if not source:
        _err("Provide a wordlist to rank.")
        return
    if not Path(source).is_file():
        _err(f"File not found: {source}")
        return

    output = args.output or str(Path(source).with_suffix(".ranked.lst"))
    backend = getattr(args, "backend", "auto") or "auto"
    result = rank_wordlist(
        input_path=source,
        output_path=output,
        use_gpu=bool(getattr(args, "use_gpu", False)),
        top_n=int(getattr(args, "top", 0) or 0),
        backend=backend,
        min_score=float(getattr(args, "min_score", 0.0) or 0.0),
    )
    print(format_rank_report(result))
    if args.output:
        _ok(f"Ranked wordlist saved: {output}")


def cmd_br_names(args: argparse.Namespace) -> None:
    """Handler for the br-names subcommand.

    Generates a username list from BRWordList Brazilian name files.
    """
    from wfh_modules.brwordlist_loader import BRWordListLoader, generate_usernames_from_br_names
    from pathlib import Path as _Path

    explicit_path: Optional[str] = getattr(args, "brwordlist_path", None)
    base_path = _Path(explicit_path) if explicit_path else None

    category: str = getattr(args, "category", "names") or "names"
    include_leet: bool = bool(getattr(args, "leet", False))

    loader = BRWordListLoader(base_path)
    if not loader.is_available():
        _warn(
            "BRWordList submodule not found. Run:\n"
            "  git submodule update --init submodules/Wordlists/BRWordList"
        )
        return

    _info(f"Loading BRWordList names (category={category})...")
    usernames = generate_usernames_from_br_names(
        category=category,
        base_path=base_path,
        include_leet=include_leet,
    )

    if not usernames:
        _warn("No names loaded from BRWordList.")
        return

    count = _write_output(iter(usernames), args.output)
    _ok(f"br-names: {count:,} username entries generated")


def cmd_iwlgen(args: argparse.Namespace) -> None:
    """Handler for the iwlgen subcommand.

    Generates keyword permutation wordlists using the IwlgenEngine.
    """
    from wfh_modules.iwlgen import IwlgenEngine

    raw_keywords: Optional[str] = getattr(args, "keywords", None)
    if not raw_keywords:
        _err("Provide at least one keyword with --keywords.")
        return

    keywords: list[str] = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    if not keywords:
        _err("No valid keywords found in --keywords input.")
        return

    raw_connectors: str = getattr(args, "connectors", "") or ""
    if raw_connectors:
        connectors = list(raw_connectors)
    else:
        connectors = ["", ".", "_", "-", "@"]

    do_leet: bool = bool(getattr(args, "leet", False))
    do_abbr: bool = bool(getattr(args, "abbreviation", False))
    do_reverse: bool = bool(getattr(args, "reverse", False))

    raw_num_tails: Optional[str] = getattr(args, "num_tails", None)
    num_tails: list[str] = [t.strip() for t in raw_num_tails.split(",") if t.strip()] if raw_num_tails else []

    min_len: int = int(getattr(args, "min_length", 4) or 4)
    max_len: int = int(getattr(args, "max_length", 64) or 64)

    config = {
        "connectors": connectors,
        "leet": do_leet,
        "abbreviation": do_abbr,
        "reverse": do_reverse,
        "num_tails": num_tails,
        "tails": [""],
        "min_length": min_len,
        "max_length": max_len,
        "to_lower": True,
    }

    _info(f"IwlgenEngine: keywords={keywords}, connectors={connectors}, leet={do_leet}")
    engine = IwlgenEngine()
    wordlist = engine.generate(keywords=keywords, config=config)

    count = _write_output(iter(wordlist), args.output)
    _ok(f"iwlgen: {count:,} entries generated")


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
        ns.template = input("  Template (e.g. XX{cod}@corp.example.com): ").strip()
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

    elif choice == "24":
        ns.phrase = input("  Phrase (e.g. 'é mais fácil pedir do que tentar quebrar'): ").strip()
        ns.prefixes = input("  Extra prefixes (comma-sep, EMPTY for '', or Enter): ").strip() or None
        ns.suffixes = input("  Extra suffixes (comma-sep, EMPTY for '', or Enter): ").strip() or None
        cmd_phrase(ns)

    elif choice == "25":
        ns.password = input("  Existing password to mutate: ").strip()
        ns.leet_mode = input("  Leet mode [basic/v2/v3/all/none] (default: all): ").strip() or "all"
        ns.prefixes = input("  Extra prefixes (comma-sep, EMPTY for '', or Enter to use defaults): ").strip() or None
        ns.suffixes = input("  Extra suffixes (comma-sep, EMPTY for '', or Enter to use defaults): ").strip() or None
        min_raw = input("  Min length (default: 1): ").strip()
        max_raw = input("  Max length (default: 128): ").strip()
        ns.min_len = int(min_raw) if min_raw.isdigit() else 1
        ns.max_len = int(max_raw) if max_raw.isdigit() else 128
        cmd_mutate(ns)

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
  python wfh.py pattern -t "XX{cod}@corp.example.com" --vars cod=1200-1300
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
    parser.add_argument(
        "--lang", metavar="LOCALE", default=None,
        help=(
            "Language/locale for generated tokens and interactive prompts: "
            "en (default) | pt-br | pt-pt | es. "
            "Controls month names, zodiac sign names, and UI language in the wizard. "
            "When omitted, defaults to 'en' (or the YAML locale: field if present)."
        ),
    )

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
    parser.add_argument(
        "--min-len", dest="global_min_len", metavar="N", type=int, default=0,
        help=(
            "Global minimum entry length (default: 0 = no filter). "
            "Entries shorter than N are discarded from all output. "
            "Combined with per-command limits: most restrictive bound applies. "
            "Example: --min-len 8 keeps only entries with 8+ characters."
        ),
    )
    parser.add_argument(
        "--max-len", dest="global_max_len", metavar="N", type=int, default=0,
        help=(
            "Global maximum entry length (default: 0 = no filter). "
            "Entries longer than N are discarded from all output. "
            "Combined with per-command limits: most restrictive bound applies. "
            "Example: --max-len 16 discards entries longer than 16 characters."
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
    p_cs.add_argument("-p", "--pattern", help="Pattern with Crunch-style placeholders (@,%%,^,...)")
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
    p_pt.add_argument("-t", "--template", help="Template (e.g. XX{cod}@corp.example.com)")
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
    p_pr.add_argument("--leet", default=None,
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Leet speak mode (default: from profile YAML or basic)")
    p_pr.add_argument("--surname", help="Surname (separate from first name, CUPP parity)")
    p_pr.add_argument("--old-passwords", dest="old_passwords", nargs="+", metavar="PWD",
                       help="Known old passwords to mutate (elpscrk parity)")
    p_pr.add_argument("--depth", type=int, default=3, choices=[3, 4, 5],
                       help="Permutation depth: 3 (default), 4 (enhanced), 5 (max BEWGor)")
    p_pr.add_argument("--parents", nargs="+", metavar="NAME",
                       help="Parent names (BEWGor parity)")
    p_pr.add_argument("--siblings", nargs="+", metavar="NAME",
                       help="Sibling names (BEWGor parity)")
    p_pr.add_argument("--engines", metavar="SPEC",
                       help=(
                           "Engine selection: preset name (light/medium/potent/nuclear), "
                           "numeric IDs (1,3,5), range (1-10), or 'all'. "
                           "Skips interactive engine menu when provided."
                       ))
    p_pr.add_argument("--max-candidates", dest="max_candidates", type=int, default=0, metavar="N",
                       help="Hard limit on generated candidates (0 = unlimited)")
    p_pr.add_argument("--timeout", dest="timeout_secs", type=float, default=0.0, metavar="SECS",
                       help="Pipeline timeout in seconds (0 = no timeout)")
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
    p_ph2.add_argument("--suffix", dest="suffix",
                        help="Append suffix to each generated number (pnwgen parity)")
    p_ph2.add_argument("--prefix-file", dest="prefix_file", metavar="FILE",
                        help="File with one prefix per line (pnwgen multi-prefix mode)")
    p_ph2.add_argument("--digit-length", dest="digit_length", type=int, metavar="N",
                        help="Override digit count for brute-force (4-10, pnwgen parity)")
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
    p_sc.add_argument("--include-js", dest="include_js", action="store_true",
                       help="Include words from JavaScript content (cewler parity)")
    p_sc.add_argument("--include-css", dest="include_css", action="store_true",
                       help="Include words from CSS content (cewler parity)")
    p_sc.add_argument("--include-pdf", dest="include_pdf", action="store_true",
                       help="Extract text from PDF files found during crawl (requires pypdf)")
    p_sc.add_argument("--lowercase", action="store_true",
                       help="Lowercase all extracted words")
    p_sc.add_argument("--subdomain-strategy", dest="subdomain_strategy",
                       choices=["exact", "children", "all"], default="exact",
                       help="Subdomain crawl scope: exact (default), children, all")
    p_sc.add_argument("--output-emails", dest="output_emails", metavar="FILE",
                       help="Write extracted emails to separate file")
    p_sc.add_argument("--output-urls", dest="output_urls", metavar="FILE",
                       help="Write visited URLs to separate file")
    p_sc.add_argument("--stream", action="store_true",
                       help="Flush output after each page (real-time streaming, requires -o)")
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
    p_mut = sub.add_parser(
        "mutate",
        help="Generate mutations from an existing password (case, leet, prefix, suffix)",
        description=(
            "Given an existing password, generate all mutations:\n"
            "case variants, leet substitutions, reversed, duplicated,\n"
            "vowels stripped, and cartesian product with prefixes/suffixes.\n\n"
            "Examples:\n"
            "  wfh.py mutate \"1q2w3e4r\"\n"
            "  wfh.py mutate \"minhasenha\" --leet-mode basic --min-len 8\n"
            "  wfh.py mutate \"abc123\" --prefixes _,! --suffixes @0x90,#0x90,EMPTY\n"
            "  wfh.py mutate \"senha\" --leet-mode none -o mutations.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mut.add_argument("password", help="Existing password to mutate")
    p_mut.add_argument(
        "--leet-mode", dest="leet_mode", default="all",
        choices=["basic", "v2", "v3", "all", "none"],
        help="Leet substitution table (default: all)",
    )
    p_mut.add_argument(
        "--prefixes", metavar="P1,P2,...",
        help="Extra prefixes (comma-separated). Use EMPTY for empty string.",
    )
    p_mut.add_argument(
        "--suffixes", metavar="S1,S2,...",
        help="Extra suffixes (comma-separated). Use EMPTY for empty string.",
    )
    p_mut.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Minimum result length (default: 1)")
    p_mut.add_argument("--max-len", dest="max_len", type=int, default=128,
                       help="Maximum result length (default: 128)")
    p_mut.add_argument("-o", "--output", help="Output file")

    # ── num2text ──────────────────────────────────────────────────────────
    p_n2t = sub.add_parser(
        "num2text",
        help="Convert digits to text words and generate case/leet/separator variants",
        description=(
            "Converts a number (up to 12 digits) into its digit-by-digit word\n"
            "representation and generates multiple case, leet and separator variants.\n\n"
            "Language codes accepted:\n"
            "  en / en-us / en-gb  — English (default)    one, two, three, ...\n"
            "  pt / pt-pt          — European Portuguese   um, dois, tres, ...\n"
            "  br / pt-br          — Brazilian Portuguese  um/uma, dois/duas, tres, ...\n"
            "  es / es-es / es-mx  — Spanish               uno, dos, tres, ...\n\n"
            "Examples:\n"
            "  wfh num2text --number 123\n"
            "  wfh num2text --number 123 --lang pt\n"
            "  wfh num2text --number 123 --lang br\n"
            "  wfh num2text --number 123 --lang es\n"
            "  wfh num2text --number 1206 --lang en --separators -,_,@\n"
            "  wfh num2text --range 0-9999 --lang en -o labs/labs_number2text.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_n2t.add_argument("--number", metavar="N",
                       help="Single number to convert (up to 12 digits)")
    p_n2t.add_argument("--range", metavar="START-END",
                       help="Range of numbers to convert (e.g. 0-9999)")
    p_n2t.add_argument("--lang", metavar="LANG", default="en",
                       help="Digit language: en (default), pt, br, es — also: en-us, pt-br, es-mx, etc.")
    p_n2t.add_argument("--separators", metavar="SEP1,SEP2,...",
                       help="Word separators (default: \"\", -, _, ., @, #, !)")
    p_n2t.add_argument("--no-leet", action="store_true", dest="no_leet",
                       help="Skip leet substitutions")
    p_n2t.add_argument("--min-len", type=int, default=0, dest="min_len",
                       help="Minimum entry length")
    p_n2t.add_argument("--max-len", type=int, default=0, dest="max_len",
                       help="Maximum entry length")
    p_n2t.add_argument("-o", "--output", help="Output file")

    p_phrase = sub.add_parser(
        "phrase",
        help="Generate passwords from phrase initials (acrostic mutations + @0x90 style)",
        description=(
            "Extract the first letter of each word in a phrase and generate\n"
            "password variants with case mutations, leet substitutions, and\n"
            "prefix/suffix combinations, including hacker patterns (@0x90, #0x90).\n\n"
            "PT-BR: 'mais' is replaced by '+' (common informal shorthand).\n\n"
            "Examples:\n"
            "  wfh.py phrase \"é mais fácil pedir do que tentar quebrar\"\n"
            "  wfh.py phrase \"minha empresa segura\" --suffixes @0x90,#0x90\n"
            "  wfh.py phrase \"apenas um teste\" --prefixes _,__ -o out.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_phrase.add_argument("phrase", help="Input phrase")
    p_phrase.add_argument(
        "--prefixes", metavar="P1,P2,...",
        help="Extra prefixes (comma-separated). Use EMPTY for empty string.",
    )
    p_phrase.add_argument(
        "--suffixes", metavar="S1,S2,...",
        help="Extra suffixes (comma-separated). Use EMPTY for empty string.",
    )
    p_phrase.add_argument("-o", "--output", help="Output file")

    p_lt = sub.add_parser("leet", help="Leet speak variants")
    p_lt.add_argument("word", help="Base word")
    p_lt.add_argument("-m", "--mode", default="basic",
                       choices=["basic", "medium", "aggressive", "custom"],
                       help="Leet substitution mode")
    p_lt.add_argument("--custom-map", dest="custom_map", default="",
                       help="Custom mapping (e.g. a=@,4;t=7;s=$;l=1,|)")
    p_lt.add_argument("--max-results", type=int, default=10000, dest="max_results")
    p_lt.add_argument("-o", "--output", help="Output file")

    p_lp = sub.add_parser(
        "leet-perm",
        help="Cartesian leet permutation over a wordlist (elpscrk-style)",
        description=(
            "Apply full cartesian leet substitution to each line of a wordlist.\n"
            "Useful as a post-pass after profile or combiner generation.\n\n"
            "Examples:\n"
            "  wfh.py leet-perm words.lst -o leet_words.lst\n"
            "  wfh.py leet-perm base.lst --max-per-word 256 --max-lines 5000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_lp.add_argument("wordlist", help="Input wordlist (one token per line)")
    p_lp.add_argument("-o", "--output", help="Output file")
    p_lp.add_argument("-m", "--mode", default="medium", choices=["medium", "custom"],
                       help="Leet map preset (default: medium)")
    p_lp.add_argument("--custom-map", dest="custom_map", default="",
                       help="Custom char map (e.g. a=@,4;t=7;s=$)")
    p_lp.add_argument("--max-per-word", dest="max_per_word", type=int, default=512,
                       help="Max variants per input word (default: 512)")
    p_lp.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max input lines to process (0 = all)")

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
    p_an.add_argument("--base-ranked", dest="base_ranked", action="store_true",
                       help="Show base words with frequency ranking (pipal parity)")
    p_an.add_argument("--position-freq", dest="position_freq", action="store_true",
                       help="Show character frequency by position (pipal Frequency_Checker)")
    p_an.add_argument("--all-masks", dest="all_masks", action="store_true",
                       help="Show ALL masks (not just top N)")
    p_an.add_argument("--mask-optindex", dest="mask_optindex", action="store_true",
                       help="PACK maskgen optindex ranking with time budget")
    p_an.add_argument("--mask-csv", dest="mask_csv", metavar="FILE",
                       help="Export PACK-compatible mask CSV (requires --mask-optindex)")
    p_an.add_argument("--time-budget", dest="time_budget", type=float, default=1.0,
                       help="Crack time budget hours for --mask-optindex")
    p_an.add_argument("--pps", type=int, default=0,
                       help="Passwords/sec for --mask-optindex (0=auto)")
    p_an.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="GPU PPS for --mask-optindex (optional)")
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
    p_dn = sub.add_parser("dns", help="DNS/subdomain fuzzing (alterx + DNSCewl style)")
    p_dn.add_argument("-d", "--domain", default="", help="Target domain (required unless --domain-list)")
    p_dn.add_argument("--domain-list", dest="domain_list", metavar="FILE",
                       help="File with one domain per line (multi-domain mode)")
    p_dn.add_argument("-w", "--wordlist", help="Words file")
    p_dn.add_argument("--words", nargs="+", help="Direct word list")
    p_dn.add_argument("-t", "--template", help="Inline template (e.g. dev-{word}.{domain})")
    p_dn.add_argument("--template-file", dest="template_file", metavar="FILE",
                       help="YAML file with permutation templates (alterx-compatible)")
    p_dn.add_argument("--separator", help="Custom separator between tokens (e.g. _ or .)")
    p_dn.add_argument("--match-regex", dest="match_regex", metavar="REGEX",
                       help="Include only output matching this regex")
    p_dn.add_argument("--filter-regex", dest="filter_regex", metavar="REGEX",
                       help="Exclude output matching this regex")
    p_dn.add_argument("--no-prefixes", action="store_true", dest="no_prefixes")
    p_dn.add_argument("--no-suffixes", action="store_true", dest="no_suffixes")
    p_dn.add_argument("--enrich", action="store_true",
                       help="Extract tokens from input FQDNs to enrich payloads (alterx -enrich)")
    p_dn.add_argument("--clusterbomb", action="store_true",
                       help="Use ClusterBomb mode with built-in alterx patterns and payloads")
    p_dn.add_argument("--payload", dest="payloads", action="append", metavar="KEY=FILE",
                       help="Custom payload file (key=file, can repeat). Keys: word, number, region")
    p_dn.add_argument("--dnscewl", action="store_true",
                       help="Add DNSCewl-style mutations (append/prepend/numeric-range)")
    p_dn.add_argument("--numeric-range", dest="numeric_range", type=int, default=10,
                       help="Numeric range for DNSCewl mutations (default: 10)")
    p_dn.add_argument("--extension-swap", dest="extension_swap", nargs="+", metavar="TLD",
                       help="Swap TLD extensions (e.g. com.au co.uk org)")
    p_dn.add_argument("--estimate", action="store_true",
                       help="Estimate output size without generating")
    p_dn.add_argument("-o", "--output", help="Output file")

    # ── pharma ────────────────────────────────────────────────────────────
    p_ph = sub.add_parser(
        "pharma",
        help="Generate passwords and usernames for retail/pharmacy chain patterns",
        description=(
            "Generates wordlists based on common credential patterns in retail chain environments.\n\n"
            "Password patterns:\n"
            "  abbrev+sep+id       Brand#1206  ABBREV_1206  abbrev1206\n"
            "  partner+cnpj        system01234567890123\n"
            "  abbrev+sep+cnpj     AB-01234567890123\n\n"
            "Username patterns:\n"
            "  abbrev+id@domain    XX1206@corp.com  xx0100@corp.com\n"
            "  IJ/LJ/TC+id         IJ1206  IJ120601  IJ120602  LJ0100\n\n"
            "Examples:\n"
            "  wfh pharma --brand AcmePharma --ids 1200-1210 -o out.lst\n"
            "  wfh pharma --brand RetailCo --abbrevs RC,RET --cnpj 01234567890123 --mode passwords\n"
            "  wfh pharma --brand BrandX --ids 5,6,7,8 --domains corp.com.br --mode usernames\n"
            "  wfh pharma --brand AcmePharma --ids 1206 --partners system,partner --separators @,#\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ph.add_argument("--brand", "-b", default="AcmePharma",
                      help="Brand/company name (default: AcmePharma)")
    p_ph.add_argument("--ids",
                      help="Store ID range '1200-1210' or list '1206,1207,1208'")
    p_ph.add_argument("--cnpj",
                      help="Tax ID(s) comma-separated (e.g. 01234567890123)")
    p_ph.add_argument("--abbrevs",
                      help="Extra abbreviations comma-separated (e.g. AB,ABBRV,ABR)")
    p_ph.add_argument("--separators",
                      help="Separators comma-separated (default: @,#,!,&,_,-,.,*,'')")
    p_ph.add_argument("--partners",
                      help="System/partner prefixes comma-separated (default: system,portal,erp,...)")
    p_ph.add_argument("--domains",
                      help="Email domains for usernames comma-separated (e.g. corp.com.br)")
    p_ph.add_argument("--mode", choices=["passwords", "usernames", "both"], default="both",
                      help="Generation mode: passwords | usernames | both (default: both)")
    p_ph.add_argument("--no-padding", action="store_true", dest="no_padding",
                      help="Skip zero-padded ID variants (0100, 01206...)")
    p_ph.add_argument("--min-len", type=int, default=0, dest="min_len",
                      help="Minimum length of generated entries")
    p_ph.add_argument("--max-len", type=int, default=0, dest="max_len",
                      help="Maximum length of generated entries")
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
    p_mn.add_argument("--overseer", action="store_true",
                       help="PyMangler Overseer mask mode with time budget")
    p_mn.add_argument("--masks", metavar="LIST",
                       help="Comma-separated masks for Overseer (w,wd,wds,...)")
    p_mn.add_argument("--time-budget", dest="time_budget", type=float, default=1.0,
                       help="Crack time budget in hours for Overseer (default: 1.0)")
    p_mn.add_argument("--pps", type=int, default=0,
                       help="Passwords/sec for Overseer budget (0=auto CPU/GPU)")
    p_mn.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="Use GPU PPS defaults in Overseer mode (optional)")
    p_mn.add_argument("--capswap", action="store_true",
                       help="Enable positional capswap in Overseer mode")
    p_mn.add_argument("-o", "--output", help="Output file")

    # ── improve (CUPP -w parity) ─────────────────────────────────────────────
    p_imp = sub.add_parser(
        "improve",
        help="Enrich an existing wordlist with leet, years, and specials",
    )
    p_imp.add_argument("wordlist", help="Source wordlist")
    p_imp.add_argument("-o", "--output", help="Output file")
    p_imp.add_argument("--leet", default="basic", choices=["basic", "medium", "aggressive"])
    p_imp.add_argument("--no-years", dest="no_years", action="store_true")
    p_imp.add_argument("--no-specials", dest="no_specials", action="store_true")
    p_imp.add_argument("--year-start", dest="year_start", type=int, default=2020)
    p_imp.add_argument("--year-end", dest="year_end", type=int, default=2027)
    p_imp.add_argument("--min-len", dest="min_len", type=int, default=6)
    p_imp.add_argument("--max-len", dest="max_len", type=int, default=32)

    # ── maya-rank ─────────────────────────────────────────────────────────────
    p_mr = sub.add_parser(
        "maya-rank",
        help="Rank wordlist candidates by MAYA cracking probability",
    )
    p_mr.add_argument("wordlist", help="Wordlist to rank")
    p_mr.add_argument("-o", "--output", help="Ranked output file")
    p_mr.add_argument("--top", type=int, default=0, help="Keep top N candidates (0=all)")
    p_mr.add_argument("--backend", choices=["auto", "torch", "fallback"], default="auto")
    p_mr.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="Use GPU for torch backend (optional)")
    p_mr.add_argument("--min-score", dest="min_score", type=float, default=0.0)

    # ── osint-perm ────────────────────────────────────────────────────────────
    p_op = sub.add_parser(
        "osint-perm",
        help="OSINT-based password permutations from target profile",
        description=(
            "Generate password candidates from OSINT profile fields\n"
            "(name, nickname, birth date, pet, phone, keywords).\n\n"
            "Examples:\n"
            "  wfh.py osint-perm --first-name Melissa --last-name Andrade -o out.lst\n"
            "  wfh.py osint-perm --nick mel --birth 01/1990 --complexity 2 -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_op.add_argument("--first-name", dest="first_name", help="Target first name")
    p_op.add_argument("--last-name", dest="last_name", help="Target last name")
    p_op.add_argument("--nick", help="Nickname or handle")
    p_op.add_argument("--birth", help="Birth date (DD/MM/YYYY or MM/YYYY)")
    p_op.add_argument("--pet", help="Pet name")
    p_op.add_argument("--phone", help="Phone number")
    p_op.add_argument("--complexity", type=int, default=1, choices=range(6),
                       metavar="0-5", help="Permutation depth (default: 1)")
    p_op.add_argument("--keywords", nargs="+", metavar="WORD", help="Extra keywords")
    p_op.add_argument("-o", "--output", help="Output file")

    # ── cupp ──────────────────────────────────────────────────────────────────
    p_cupp = sub.add_parser(
        "cupp",
        help="CUPP-style target-specific password generation",
        description=(
            "Generate password candidates from a personal profile\n"
            "(names, dates, pets, company, custom words).\n\n"
            "Examples:\n"
            "  wfh.py cupp --first-name Melissa --last-name Andrade --company Daryus -o out.lst\n"
            "  wfh.py cupp --nick mel --birth 01/1990 --words Ozzy Pitty --max-output 50000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cupp.add_argument("--first-name", dest="first_name", help="Target first name")
    p_cupp.add_argument("--last-name", dest="last_name", help="Target last name")
    p_cupp.add_argument("--nick", help="Nickname or handle")
    p_cupp.add_argument("--birth", help="Birth date")
    p_cupp.add_argument("--pet", help="Pet name")
    p_cupp.add_argument("--company", help="Company name")
    p_cupp.add_argument("--words", nargs="+", metavar="WORD", help="Extra words")
    p_cupp.add_argument("--max-output", dest="max_output", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_cupp.add_argument("-o", "--output", help="Output file")

    # ── pattern-rank ────────────────────────────────────────────────────────
    p_prk = sub.add_parser(
        "pattern-rank",
        help="Analyze wordlist patterns: keyboard walks, Hashcat masks",
        description=(
            "Analyze a password wordlist for structural patterns:\n"
            "keyboard walks, PT-BR month names, top Hashcat masks.\n\n"
            "Examples:\n"
            "  wfh.py pattern-rank passwords.lst\n"
            "  wfh.py pattern-rank leaked.txt --layout qwerty --max-lines 100000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_prk.add_argument("wordlist", help="Wordlist to analyze")
    p_prk.add_argument("--layout", default="qwerty",
                       help="Keyboard layout for walk detection (default: qwerty)")
    p_prk.add_argument("--max-lines", dest="max_lines", type=int, default=500_000,
                       help="Max lines to analyze (default: 500000)")

    # ── scrape-target ───────────────────────────────────────────────────────
    p_st = sub.add_parser(
        "scrape-target",
        help="Crawl a target URL and extract words for wordlists",
        description=(
            "Lightweight target spider: crawl a URL and extract\n"
            "unique words suitable for wordlist generation.\n\n"
            "Examples:\n"
            "  wfh.py scrape-target --url https://example.com -o words.lst\n"
            "  wfh.py scrape-target --url https://corp.com --depth 3 --max-pages 50"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_st.add_argument("--url", required=True, help="Target URL to crawl")
    p_st.add_argument("--depth", type=int, default=2, help="Crawl depth (default: 2)")
    p_st.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min word length (default: 4)")
    p_st.add_argument("--max-pages", dest="max_pages", type=int, default=20,
                       help="Max pages to fetch (default: 20)")
    p_st.add_argument("-o", "--output", help="Output file")

    # ── default-creds ─────────────────────────────────────────────────────────
    p_dc = sub.add_parser(
        "default-creds",
        help="Query default credentials database for IoT, routers, printers, ICS/SCADA",
        description=(
            "Query the consolidated default credentials database.\n\n"
            "Contains factory-default user:password pairs from 25+ vendors,\n"
            "SNMP community strings and SNMPv3 defaults.\n\n"
            "Sources: RouterXPL-Forge, routersploit, MikrotikAPI-BF.\n\n"
            "Examples:\n"
            "  wfh.py default-creds -o all_defaults.lst\n"
            "  wfh.py default-creds --vendor mikrotik -o mikrotik.lst\n"
            "  wfh.py default-creds --vendor huawei --format json\n"
            "  wfh.py default-creds --snmp -o snmp_communities.lst\n"
            "  wfh.py default-creds --snmp --snmp-version v3 -o snmpv3.lst\n"
            "  wfh.py default-creds --format user -o usernames.lst\n"
            "  wfh.py default-creds --list-vendors"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dc.add_argument("--vendor", help="Filter by vendor name (partial match)")
    p_dc.add_argument("--protocol", help="Filter by protocol (api, ssh, telnet, http)")
    p_dc.add_argument("--category", help="Filter by category (router, printer, ics)")
    p_dc.add_argument(
        "--format", choices=["combo", "user", "pass", "json"],
        default="combo", help="Output format (default: combo = user:pass)",
    )
    p_dc.add_argument("--snmp", action="store_true",
                       help="Output SNMP community strings instead of credentials")
    p_dc.add_argument("--snmp-version", dest="snmp_version",
                       choices=["v2", "v3"], default="v2",
                       help="SNMP version (default: v2)")
    p_dc.add_argument("--list-vendors", dest="list_vendors", action="store_true",
                       help="List all vendors in the database and exit")
    p_dc.add_argument("--list-protocols", dest="list_protocols", action="store_true",
                       help="List all protocols in the database and exit")
    p_dc.add_argument("-o", "--output", help="Output file")

    # ── isp-keygen ─────────────────────────────────────────────────────────────
    p_isp = sub.add_parser(
        "isp-keygen",
        help="ISP default WiFi password keyspace generator",
        description=(
            "Generate vendor-specific WiFi password wordlists based on known\n"
            "ISP default password patterns.\n\n"
            "Xfinity/Comcast pattern: word5 + 4digit + word6\n"
            "  e.g., fever7538harbor (15 chars, lowercase + digits)\n\n"
            "Keyspace: 686 × 10,000 × 685 = ~4.7 billion per direction.\n\n"
            "Examples:\n"
            "  wfh.py isp-keygen --list-isps\n"
            "  wfh.py isp-keygen --isp xfinity_comcast --estimate\n"
            "  wfh.py isp-keygen --isp xfinity_comcast --limit 1000 -o sample.lst\n"
            "  wfh.py isp-keygen --isp xfinity_comcast --direction both -o full.lst\n"
            "  wfh.py isp-keygen --isp xfinity_comcast --direction reverse --limit 500000 -o rev.lst\n"
            "  wfh.py isp-keygen --isp xfinity_comcast --word5-file custom5.txt -o custom.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_isp.add_argument("--isp", default="xfinity_comcast",
                        help="ISP pattern name (default: xfinity_comcast)")
    p_isp.add_argument("--direction", choices=["forward", "reverse", "both"],
                        default="forward",
                        help="Generation direction (default: forward)")
    p_isp.add_argument("--limit", type=int, default=0,
                        help="Max entries to generate (0 = all)")
    p_isp.add_argument("--estimate", action="store_true",
                        help="Show keyspace estimate only, don't generate")
    p_isp.add_argument("--word5-file", dest="word5_file",
                        help="Custom 5-letter word file (overrides built-in)")
    p_isp.add_argument("--word6-file", dest="word6_file",
                        help="Custom 6-letter word file (overrides built-in)")
    p_isp.add_argument("--list-isps", dest="list_isps", action="store_true",
                        help="List available ISP patterns and exit")
    p_isp.add_argument("-o", "--output", help="Output file")

    # ── sysinfo ───────────────────────────────────────────────────────────────
    p_si = sub.add_parser(
        "sysinfo",
        help="Show hardware profile, compute backend and thread status",
        description=(
            "Display detected CPU, RAM, GPU and compute backend.\n"
            "Shows current --threads and --compute settings.\n\n"
            "Examples:\n"
            "  wfh.py sysinfo\n"
            "  wfh.py sysinfo --crc32-stress 150000\n"
            "  wfh.py --compute gpu sysinfo\n"
            "  wfh.py --threads 20 sysinfo"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_si.add_argument("--crc32-stress", dest="crc32_stress", type=int, default=0, metavar="N",
                       help="Run CRC32 dedup stress test with N synthetic lines")

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
            "  wfh.py train --seclists\n"
            "  wfh.py train --seclists /path/to/SecLists --seclists-categories password frequency\n"
            "  wfh.py train --auto --seclists\n"
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
        "--seclists", metavar="PATH", nargs="?", const="auto",
        help="Train from SecLists corpus (auto-discover or specify path)",
    )
    p_tr.add_argument(
        "--seclists-categories", dest="seclists_categories",
        metavar="CAT", nargs="+", default=None,
        choices=["password", "username", "frequency"],
        help="SecLists categories to train: password username frequency (default: all)",
    )
    p_tr.add_argument(
        "-o", "--output", metavar="FILE",
        help="Output model file (default: .model/pattern_model.json)",
    )

    # ── password-dna ───────────────────────────────────────────────────────
    p_dna = sub.add_parser(
        "password-dna",
        help="Analyze password patterns and generate behavioral variants",
        description=(
            "Analyze 1-10 known passwords from a target to extract behavioral DNA:\n"
            "structural patterns, word banks, separator habits, number placement,\n"
            "capitalization style, and leet preferences. Then generate a wordlist\n"
            "of candidates matching the same behavioral profile.\n\n"
            "Minimum: 1 password. Ideal: 3+ passwords. Maximum: 10.\n\n"
            "Examples:\n"
            '  wfh.py password-dna "Empresa@2024" "empresa#2025" "Empresa!123"\n'
            '  wfh.py password-dna --file known_passwords.txt --depth deep -o candidates.lst\n'
            '  wfh.py password-dna "P@ssw0rd1" --depth quick --show-dna\n'
            '  wfh.py password-dna "JoaoSilva99" "joao.silva@2024" "Silva#joao1"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dna.add_argument("passwords", nargs="*",
                        help="Known target passwords (1-10)")
    p_dna.add_argument("--file", metavar="FILE",
                        help="File with known passwords (one per line, max 10)")
    p_dna.add_argument("--depth", choices=["quick", "normal", "deep"],
                        default="normal",
                        help="Generation depth: quick (~2K), normal (~15K), deep (~100K+)")
    p_dna.add_argument("--show-dna", dest="show_dna", action="store_true",
                        help="Print the extracted DNA profile before generating")
    p_dna.add_argument("-o", "--output", help="Output file")

    # ── combiner ──────────────────────────────────────────────────────────
    p_cb = sub.add_parser(
        "combiner",
        help="Keyword combiner (intelligence-wordlist-generator style)",
        description=(
            "Generate wordlists from keyword permutations with connectors.\n\n"
            "Examples:\n"
            "  wfh.py combiner admin password secret\n"
            "  wfh.py combiner admin test --connectors ',-,_,.,EMPTY' --leet --reverse\n"
            "  wfh.py combiner --keywords-file keywords.txt --depth 3 --abbreviation\n"
            "  wfh.py combiner acme corp 2026 --tails '!,@,#,123' -o wordlist.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cb.add_argument("keywords", nargs="*", help="Keywords to combine")
    p_cb.add_argument("--keywords-file", dest="keywords_file", metavar="FILE",
                       help="File with one keyword per line")
    p_cb.add_argument("--connectors", metavar="LIST",
                       help="Comma-separated connectors (use EMPTY for no separator, default: EMPTY,-,_,.,@,#)")
    p_cb.add_argument("--tails", metavar="LIST",
                       help="Comma-separated numeric/special tails to append")
    p_cb.add_argument("--depth", type=int, default=0,
                       help="Max permutation depth (0 = all, default: 0)")
    p_cb.add_argument("--abbreviation", action="store_true",
                       help="Generate abbreviation variants")
    p_cb.add_argument("--reverse", action="store_true",
                       help="Generate reversed variants")
    p_cb.add_argument("--leet", action="store_true",
                       help="Generate leet speak variants")
    p_cb.add_argument("--lowercase", action="store_true",
                       help="Add lowercase duplicates")
    p_cb.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Minimum output length (default: 1)")
    p_cb.add_argument("--max-len", dest="max_len", type=int, default=64,
                       help="Maximum output length (default: 64)")
    p_cb.add_argument("-o", "--output", help="Output file")

    # ── pcfg ─────────────────────────────────────────────────────────────
    p_pcfg = sub.add_parser(
        "pcfg",
        help="PCFG probabilistic grammar — train or generate",
        description=(
            "Probabilistic Context-Free Grammar engine (Weir et al.).\n"
            "Train a grammar from password corpora, then generate candidates\n"
            "in approximate probability order (most likely first).\n\n"
            "Examples:\n"
            "  wfh.py pcfg train --wordlist rockyou.txt\n"
            "  wfh.py pcfg generate -o candidates.lst\n"
            "  wfh.py pcfg generate --top-structures 50 --top-terminals 100 --limit 1000000\n"
            "  wfh.py pcfg generate --model .model/pcfg_grammar.json --min-len 8"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pcfg.add_argument("pcfg_action", choices=["train", "generate"], default="generate",
                         nargs="?", help="Action: train or generate (default: generate)")
    p_pcfg.add_argument("--wordlist", nargs="+", metavar="FILE",
                         help="Training file(s) — one password per line")
    p_pcfg.add_argument("--model", metavar="FILE", default=".model/pcfg_grammar.json",
                         help="Grammar model file (default: .model/pcfg_grammar.json)")
    p_pcfg.add_argument("--model-output", dest="model_output", metavar="FILE",
                         help="Output path for trained model")
    p_pcfg.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                         help="Max training lines (0 = unlimited)")
    p_pcfg.add_argument("--top-structures", dest="top_structures", type=int, default=0,
                         help="Limit to top N structures (0 = all)")
    p_pcfg.add_argument("--top-terminals", dest="top_terminals", type=int, default=0,
                         help="Limit terminals per class to top N (0 = all)")
    p_pcfg.add_argument("--min-len", dest="min_len", type=int, default=1,
                         help="Min password length (default: 1)")
    p_pcfg.add_argument("--max-len", dest="max_len", type=int, default=64,
                         help="Max password length (default: 64)")
    p_pcfg.add_argument("--limit", type=int, default=0,
                         help="Max candidates to generate (0 = unlimited)")
    p_pcfg.add_argument("-o", "--output", help="Output file")

    # ── markov ───────────────────────────────────────────────────────────
    p_mk = sub.add_parser(
        "markov",
        help="OMEN-style positional Markov generator — train or generate",
        description=(
            "Positional Markov chain password generator (OMEN-style).\n"
            "Learns character transition probabilities per position and\n"
            "generates candidates in ascending cost order.\n\n"
            "Examples:\n"
            "  wfh.py markov train --wordlist rockyou.txt --order 4\n"
            "  wfh.py markov generate --limit 500000\n"
            "  wfh.py markov generate --min-len 8 --max-len 12 --max-cost 30"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mk.add_argument("markov_action", choices=["train", "generate"], default="generate",
                       nargs="?", help="Action: train or generate (default: generate)")
    p_mk.add_argument("--wordlist", nargs="+", metavar="FILE",
                       help="Training file(s)")
    p_mk.add_argument("--model", metavar="FILE", default=".model/markov_model.json",
                       help="Model file (default: .model/markov_model.json)")
    p_mk.add_argument("--model-output", dest="model_output", metavar="FILE",
                       help="Output path for trained model")
    p_mk.add_argument("--order", type=int, default=3,
                       help="N-gram order (default: 3)")
    p_mk.add_argument("--smoothing", type=float, default=0.01,
                       help="Laplace smoothing alpha for unseen n-grams (default: 0.01)")
    p_mk.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max training lines (0 = unlimited)")
    p_mk.add_argument("--max-cost", dest="max_cost", type=int, default=0,
                       help="Max total cost threshold (0 = no limit)")
    p_mk.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min password length (default: 4)")
    p_mk.add_argument("--max-len", dest="max_len", type=int, default=16,
                       help="Max password length (default: 16)")
    p_mk.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_mk.add_argument("-o", "--output", help="Output file")

    # ── kwalk ────────────────────────────────────────────────────────────
    p_kw = sub.add_parser(
        "kwalk",
        help="Keyboard walk password generator (kwprocessor-style)",
        description=(
            "Generate passwords based on physical keyboard adjacency walks.\n"
            "Supports QWERTY, AZERTY, QWERTZ, Dvorak, and numpad layouts.\n\n"
            "Examples:\n"
            "  wfh.py kwalk --min-len 6 --max-len 10\n"
            "  wfh.py kwalk --layout qwerty,numpad --no-shift\n"
            "  wfh.py kwalk --max-changes 2 --start-chars qaz1\n"
            "  wfh.py kwalk --list-layouts"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_kw.add_argument("--layout", default="qwerty",
                       help="Comma-separated layout names (default: qwerty)")
    p_kw.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min walk length (default: 4)")
    p_kw.add_argument("--max-len", dest="max_len", type=int, default=10,
                       help="Max walk length (default: 10)")
    p_kw.add_argument("--max-changes", dest="max_changes", type=int, default=3,
                       help="Max direction changes per walk (default: 3)")
    p_kw.add_argument("--directions", metavar="LIST",
                       help="Comma-separated directions: N,S,E,W,NE,NW,SE,SW")
    p_kw.add_argument("--no-shift", dest="no_shift", action="store_true",
                       help="Exclude shifted layer (uppercase/symbols)")
    p_kw.add_argument("--start-chars", dest="start_chars", metavar="CHARS",
                       help="Restrict starting characters")
    p_kw.add_argument("--route", metavar="START:DIRS",
                       help="Explicit walk route, e.g. q:3467 or q,3467 (0-7 = N..NW)")
    p_kw.add_argument("--route-file", dest="route_file", metavar="FILE",
                       help="Route file: one 'start dirs' per line (kwprocessor-style)")
    p_kw.add_argument("--list-layouts", dest="list_layouts", action="store_true",
                       help="List available keyboard layouts")
    p_kw.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_kw.add_argument("-o", "--output", help="Output file")

    # ── rulegen ──────────────────────────────────────────────────────────
    p_rg = sub.add_parser(
        "rulegen",
        help="Auto-generate hashcat .rule files from password analysis",
        description=(
            "Analyze real passwords to discover transformation rules\n"
            "and generate hashcat-compatible .rule files.\n\n"
            "Examples:\n"
            "  wfh.py rulegen --wordlist leaked.txt -o rules.rule\n"
            "  wfh.py rulegen --wordlist passwords.lst --dictionary english.txt --top-rules 200\n"
            "  wfh.py rulegen --wordlist hashes.pot --max-lines 100000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rg.add_argument("--wordlist", nargs="+", metavar="FILE",
                       help="Password file(s) to analyze")
    p_rg.add_argument("--dictionary", metavar="FILE",
                       help="Optional base word dictionary for matching")
    p_rg.add_argument("--top-rules", dest="top_rules", type=int, default=100,
                       help="Number of top rules to output (default: 100)")
    p_rg.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max passwords to analyze (0 = all)")
    p_rg.add_argument("-o", "--output", help="Output file (.rule for hashcat format)")

    # ── benchmark ────────────────────────────────────────────────────────
    p_bm = sub.add_parser(
        "benchmark",
        help="Measure wordlist quality against a reference set",
        description=(
            "Benchmark a generated wordlist against a reference password set.\n"
            "Measures hit rate, coverage, efficiency, diversity, and more.\n"
            "Inspired by MAYA (IEEE S&P 2026) benchmarking framework.\n\n"
            "Examples:\n"
            "  wfh.py benchmark --wordlist generated.lst --reference rockyou.txt\n"
            "  wfh.py benchmark --wordlist out.lst --reference test_set.txt --json report.json\n"
            "  wfh.py benchmark --wordlist my_list.lst --reference leaked.txt --max-candidates 1000000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bm.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Generated wordlist to evaluate")
    p_bm.add_argument("--reference", required=True, metavar="FILE",
                       help="Reference password set (ground truth)")
    p_bm.add_argument("--max-candidates", dest="max_candidates", type=int, default=0,
                       help="Max lines to read from wordlist (0 = all)")
    p_bm.add_argument("--max-reference", dest="max_reference", type=int, default=0,
                       help="Max lines to read from reference (0 = all)")
    p_bm.add_argument("--json", dest="json_output", metavar="FILE",
                       help="Save results as JSON report")
    p_bm.add_argument("-o", "--output", help="Save text report to file")

    # anomaly-score
    p_anm = sub.add_parser(
        "anomaly-score",
        help="Rank wordlist entries by anomaly score (most unusual first)",
        description=(
            "Score each password in a wordlist using a native ensemble of\n"
            "IsolationForest-lite and HBOS-lite algorithms. No external\n"
            "ML library required. Higher score = more anomalous.\n\n"
            "Examples:\n"
            "  wfh.py anomaly-score passwords/wlist_brasil.lst --top 50\n"
            "  wfh.py anomaly-score leak.txt --top 100 -o rare.txt\n"
            "  wfh.py anomaly-score corpus.lst --max-lines 200000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_anm.add_argument("wordlist", metavar="WORDLIST", help="Input wordlist file path")
    p_anm.add_argument("--top", type=int, default=0, metavar="N",
                       help="Return only the top-N most anomalous entries (0 = all)")
    p_anm.add_argument("--max-lines", dest="max_lines", type=int, default=100_000,
                       help="Maximum lines to read from wordlist (default: 100000)")
    p_anm.add_argument("-o", "--output", metavar="FILE",
                       help="Save scored password list to file (one per line, no scores)")

    # ── prince ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser(
        "prince",
        help="PRINCE attack — chained element combination",
        description=(
            "PRINCE (PRobability INfinite Chained Elements) attack mode.\n"
            "Generates passwords by chaining elements from a wordlist.\n"
            "Discovers multi-word passwords like 'correcthorsebatterystaple'.\n\n"
            "Examples:\n"
            "  wfh.py prince --wordlist base_words.txt --min-elem 2 --max-elem 4\n"
            "  wfh.py prince --wordlist words.txt --separator '-' --case-permute\n"
            "  wfh.py prince --wordlist top1000.txt --min-len 8 --max-len 20 --limit 500000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pr.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Input wordlist (element source)")
    p_pr.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Min password length (default: 1)")
    p_pr.add_argument("--max-len", dest="max_len", type=int, default=32,
                       help="Max password length (default: 32)")
    p_pr.add_argument("--min-elem", dest="min_elem", type=int, default=1,
                       help="Min elements per chain (default: 1)")
    p_pr.add_argument("--max-elem", dest="max_elem", type=int, default=4,
                       help="Max elements per chain (default: 4)")
    p_pr.add_argument("--separator", default="",
                       help="Element separator (default: empty, use EMPTY for none)")
    p_pr.add_argument("--case-permute", dest="case_permute", action="store_true",
                       help="Generate case permutations")
    p_pr.add_argument("--wordlen-min", dest="wordlen_min", type=int, default=0,
                       help="Min element word length (0 = no filter)")
    p_pr.add_argument("--wordlen-max", dest="wordlen_max", type=int, default=0,
                       help="Max element word length (0 = no filter)")
    p_pr.add_argument("--superchop", type=int, default=0,
                       help="Truncate each element to N chars (pp64 superchop parity)")
    p_pr.add_argument("--max-words", dest="max_words", type=int, default=0,
                       help="Max words to load from file (0 = all)")
    p_pr.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_pr.add_argument("-o", "--output", help="Output file")

    # ── br-names ─────────────────────────────────────────────────────────
    p_brn = sub.add_parser(
        "br-names",
        help="Generate username list from BRWordList Brazilian name files",
        description=(
            "Loads name lists from the BRWordList submodule and produces\n"
            "a deduplicated username wordlist suitable for credential attacks.\n\n"
            "Requires: git submodule update --init submodules/Wordlists/BRWordList\n\n"
            "Examples:\n"
            "  wfh.py br-names\n"
            "  wfh.py br-names --category surnames -o surnames.lst\n"
            "  wfh.py br-names --category all --leet -o names_leet.lst\n"
            "  wfh.py br-names --brwordlist-path /opt/BRWordList"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_brn.add_argument(
        "--category", default="names",
        choices=["names", "surnames", "full_names", "initials", "rev_initials", "a-z", "all"],
        help="Name category to load (default: names)",
    )
    p_brn.add_argument(
        "--leet", action="store_true",
        help="Also generate basic leet variants",
    )
    p_brn.add_argument(
        "--brwordlist-path", dest="brwordlist_path", metavar="PATH",
        help="Explicit path to BRWordList root (auto-detected if omitted)",
    )
    p_brn.add_argument("-o", "--output", help="Output file")

    # ── iwlgen ───────────────────────────────────────────────────────────
    p_iw = sub.add_parser(
        "iwlgen",
        help="Intelligence keyword permutation wordlist generator",
        description=(
            "Generates wordlists from keyword permutations with optional\n"
            "leet substitution, abbreviation, reversal, and numeric tails.\n"
            "Native Python 3 port of intelligence-wordlist-generator.\n\n"
            "Examples:\n"
            "  wfh.py iwlgen --keywords admin,router,2024 --connectors @.\n"
            "  wfh.py iwlgen --keywords empresa,corp --leet --abbreviation\n"
            "  wfh.py iwlgen --keywords cisco,admin --num-tails 1-99 --connectors ._\n"
            "  wfh.py iwlgen --keywords guest,pass --connectors '' -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_iw.add_argument(
        "--keywords", required=True, metavar="KW1,KW2,...",
        help="Comma-separated keywords (e.g. admin,router,2024)",
    )
    p_iw.add_argument(
        "--connectors", default="", metavar="CHARS",
        help=(
            "Connector characters to join keywords, specified as a string.\n"
            "Each character becomes a separate connector (default: '._-@' empty).\n"
            "Example: --connectors '@._' uses @, ., _ and also empty string."
        ),
    )
    p_iw.add_argument(
        "--leet", action="store_true",
        help="Apply leet-speak substitutions to generated words",
    )
    p_iw.add_argument(
        "--abbreviation", action="store_true",
        help="Generate single-character abbreviation variants",
    )
    p_iw.add_argument(
        "--reverse", action="store_true",
        help="Generate element-reversal variants",
    )
    p_iw.add_argument(
        "--num-tails", dest="num_tails", metavar="SPEC",
        help="Numeric tail specs, comma-separated (e.g. '1,2,01-05,2024')",
    )
    p_iw.add_argument(
        "--min-length", dest="min_length", type=int, default=4,
        help="Minimum entry length (default: 4)",
    )
    p_iw.add_argument(
        "--max-length", dest="max_length", type=int, default=64,
        help="Maximum entry length (default: 64)",
    )
    p_iw.add_argument("-o", "--output", help="Output file")

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

    stress_n = getattr(args, "crc32_stress", 0) or 0
    if stress_n > 0:
        from wfh_modules.benchmark_suite import stress_crc32_dedup, format_crc32_stress_report
        _info(f"Running CRC32 dedup stress test ({stress_n:,} lines)...")
        result = stress_crc32_dedup(stress_n)
        print(format_crc32_stress_report(result))


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

    # ── SecLists corpus ──────────────────────────────────────────────────────────
    seclists_flag = getattr(args, "seclists", None)
    if seclists_flag:
        from wfh_modules.seclists_trainer import find_seclists_root, train_from_seclists

        hint = None if seclists_flag == "auto" else seclists_flag
        sl_root = find_seclists_root(hint)
        if sl_root:
            _info(f"SecLists root: {sl_root}")
            sl_cats = getattr(args, "seclists_categories", None)
            sl_summary = train_from_seclists(
                model, sl_root, categories=sl_cats,
            )
            pw_f = sl_summary.get("password_files", 0)
            pw_s = sl_summary.get("password_samples", 0)
            un_f = sl_summary.get("username_files", 0)
            un_s = sl_summary.get("username_samples", 0)
            fr_f = sl_summary.get("frequency_files", 0)
            fr_s = sl_summary.get("frequency_samples", 0)
            skipped = sl_summary.get("skipped", [])

            _info(f"  SecLists passwords:  {pw_f} files, {pw_s:,} samples")
            _info(f"  SecLists usernames:  {un_f} files, {un_s:,} samples")
            _info(f"  SecLists frequency:  {fr_f} files, {fr_s:,} samples")
            if skipped:
                _warn(f"  Skipped (not found): {', '.join(skipped)}")
            if pw_f + un_f + fr_f > 0:
                trained_any = True
        else:
            _warn("SecLists not found. Use --seclists PATH or place SecLists alongside WFH.")

    if not trained_any:
        _warn("No training data provided. Use --csv, --wordlist, --usernames, --auto, or --seclists.")
        return

    # ── Save model ─────────────────────────────────────────────────────────────
    out_path = getattr(args, "output", None) or str(DEFAULT_MODEL_FILE)
    saved = model.save(out_path)
    print()
    _info(f"Model saved: {saved}")
    print(model.describe())


def cmd_osint_perm(args: argparse.Namespace) -> None:
    """Generate OSINT-based password candidates from target profile."""
    from wfh_modules.osint_perm import OsintProfile, OsintPermGenerator

    profile = OsintProfile(
        first_name=getattr(args, "first_name", "") or "",
        last_name=getattr(args, "last_name", "") or "",
        nickname=getattr(args, "nick", "") or "",
        birth_date=getattr(args, "birth", "") or "",
        pet_name=getattr(args, "pet", "") or "",
        phone=getattr(args, "phone", "") or "",
        complexity=getattr(args, "complexity", 1),
        keywords=list(getattr(args, "keywords", None) or []),
    )
    gen = OsintPermGenerator()
    results = gen.generate(profile)
    output = getattr(args, "output", None)
    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(results), encoding="utf-8")
        _info(f"Saved {len(results)} candidates to: {output}")
    else:
        for r in results[:50]:
            print(r)
        if len(results) > 50:
            _info(f"... and {len(results)-50} more. Use -o FILE to save all.")
    _info(f"Generated {len(results)} OSINT-based candidates.")


def cmd_cupp(args: argparse.Namespace) -> None:
    """Generate target-specific passwords from user profile (CUPP-style)."""
    from wfh_modules.cupp_engine import CuppEngine, CuppProfile

    profile = CuppProfile(
        first_name=getattr(args, "first_name", "") or "",
        last_name=getattr(args, "last_name", "") or "",
        nickname=getattr(args, "nick", "") or "",
        birth_date=getattr(args, "birth", "") or "",
        pet_name=getattr(args, "pet", "") or "",
        company=getattr(args, "company", "") or "",
        extra_words=list(getattr(args, "words", None) or []),
    )
    engine = CuppEngine()
    results = engine.generate(profile, max_output=getattr(args, "max_output", 0))
    output = getattr(args, "output", None)
    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(results), encoding="utf-8")
        _info(f"Saved {len(results)} candidates to: {output}")
    else:
        for r in results[:50]:
            print(r)
        if len(results) > 50:
            _info(f"... and {len(results)-50} more. Use -o FILE to save all.")
    _info(f"Generated {len(results)} CUPP-style candidates.")


def cmd_pattern_rank(args: argparse.Namespace) -> None:
    """Analyze wordlist patterns: keyboard walks, Hashcat masks, PTBR months."""
    from wfh_modules.pattern_ranker import analyze_wordlist, score_keyboard_walk, build_hashcat_mask

    path = getattr(args, "wordlist", None)
    if not path:
        _warn("pattern-rank requires a wordlist path.")
        return
    layout = getattr(args, "layout", "qwerty") or "qwerty"
    max_l = getattr(args, "max_lines", 500_000)

    _info(f"Analyzing {path} (layout={layout})...")
    result = analyze_wordlist(path, max_lines=max_l, layout=layout)

    print(f"\n  Pattern Analysis: {path}")
    print(f"  Total analyzed  : {result['total_analyzed']:,}")
    print(f"  Unique masks    : {result['unique_masks']:,}")
    print(f"  Keyboard walk   : {result['keyboard_walk_pct']:.1f}% of passwords")
    print(f"  PTBR months     : {result['ptbr_month_pct']:.1f}% of passwords")
    print("\n  Top 10 Hashcat masks:")
    for mask, count, pct in result["top_masks"][:10]:
        print(f"    {mask:<30} {count:>8}  ({pct:.1f}%)")
    print()


def cmd_scrape_target(args: argparse.Namespace) -> None:
    """Crawl a target URL and extract words for wordlist generation."""
    from wfh_modules.target_spider import TargetSpider

    url = getattr(args, "url", None)
    if not url:
        _warn("scrape-target requires --url")
        return
    depth = getattr(args, "depth", 2)
    min_len = getattr(args, "min_len", 4)
    output = getattr(args, "output", None)

    spider = TargetSpider(min_len=min_len, max_pages=getattr(args, "max_pages", 20))
    _info(f"Crawling {url} (depth={depth})...")

    try:
        words = spider.crawl(url, depth=depth)
    except ImportError as exc:
        _warn(f"requests/beautifulsoup4 required: {exc}")
        return

    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(words), encoding="utf-8")
        _info(f"Saved {len(words)} words to: {output}")
    else:
        for w in words[:40]:
            print(w)
        if len(words) > 40:
            _info(f"... and {len(words)-40} more. Use -o FILE to save all.")
    _info(f"Extracted {len(words)} words from {url}")


def cmd_anomaly_score(args: argparse.Namespace) -> None:
    """Rank passwords in a wordlist by anomaly score (most unusual first).

    Uses a native ensemble of IsolationForest-lite and HBOS-lite algorithms
    reimplemented without any external ML dependency.

    Example:
        wfh anomaly-score passwords/wlist_brasil.lst --top 50
        wfh anomaly-score leak.txt --top 100 --output rare_passwords.txt
    """
    from wfh_modules.anomaly_scorer import score_wordlist

    path = getattr(args, "wordlist", None)
    if not path:
        _warn("anomaly-score requires a wordlist path as argument.")
        return

    top_n = getattr(args, "top", 0)
    max_lines = getattr(args, "max_lines", 100_000)
    output = getattr(args, "output", None)

    try:
        results = score_wordlist(path, top_n=top_n, max_lines=max_lines)
    except FileNotFoundError as exc:
        _warn(str(exc))
        return

    lines_out = [f"{score:.4f}\t{pw}" for pw, score in results]

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(pw for pw, _ in results), encoding="utf-8")
        _info(f"Saved {len(results)} entries to: {out_path}")
    else:
        print(f"{'Score':>8}  Password")
        print("-" * 40)
        for pw, score in results:
            print(f"{score:>8.4f}  {pw}")

    _info(f"Scored {len(results)} password(s). Higher score = more anomalous.")


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

    # ── Apply locale ──────────────────────────────────────────────────────────
    _raw_lang = getattr(args, "lang", None)
    if _raw_lang:
        from wfh_modules.i18n import set_session_locale as _set_locale
        _active_locale = _set_locale(_raw_lang)
        _GLOBAL_CTX["locale"] = _active_locale
    else:
        _GLOBAL_CTX.setdefault("locale", "en")

    # ── Apply global execution context ────────────────────────────────────────
    from wfh_modules.thread_pool import validate_thread_count, DEFAULT_THREADS
    from wfh_modules.compute_backend import set_backend

    raw_threads    = getattr(args, "threads", DEFAULT_THREADS) or DEFAULT_THREADS
    compute_mode   = getattr(args, "compute", "auto") or "auto"
    global_use_ml  = not getattr(args, "no_ml_global", False)
    global_limit   = getattr(args, "limit", 0) or 0
    global_timeout = getattr(args, "timeout", 0) or 0
    global_min_len = getattr(args, "global_min_len", 0) or 0
    global_max_len = getattr(args, "global_max_len", 0) or 0

    # Validate and store thread count
    threads = validate_thread_count(raw_threads, clamp=True)
    _GLOBAL_CTX["threads"]      = threads
    _GLOBAL_CTX["compute_mode"] = compute_mode
    _GLOBAL_CTX["use_ml"]       = global_use_ml
    _GLOBAL_CTX["limit"]        = global_limit
    _GLOBAL_CTX["timeout"]      = global_timeout
    _GLOBAL_CTX["start_time"]   = time.time()
    _GLOBAL_CTX["min_len"]      = global_min_len
    _GLOBAL_CTX["max_len"]      = global_max_len

    if global_min_len or global_max_len:
        parts = []
        if global_min_len:
            parts.append(f"min={global_min_len}")
        if global_max_len:
            parts.append(f"max={global_max_len}")
        _info(f"Length filter active: {', '.join(parts)} (global)")

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
        "leet":       cmd_leet,
        "leet-perm":  cmd_leet_perm,
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
        "improve":       cmd_improve,
        "maya-rank":     cmd_maya_rank,
        "default-creds": cmd_default_creds,
        "isp-keygen":    cmd_isp_keygen,
        "password-dna":  cmd_password_dna,
        "combiner":      cmd_combiner,
        "pcfg":          cmd_pcfg,
        "markov":        cmd_markov,
        "kwalk":         cmd_kwalk,
        "rulegen":       cmd_rulegen,
        "benchmark":     cmd_benchmark,
        "prince":        cmd_prince,
        "anomaly-score": cmd_anomaly_score,
        "osint-perm":    cmd_osint_perm,
        "cupp":          cmd_cupp,
        "pattern-rank":  cmd_pattern_rank,
        "scrape-target": cmd_scrape_target,
        "br-names":      cmd_br_names,
        "iwlgen":        cmd_iwlgen,
        "phrase":        cmd_phrase,
        "mutate":        cmd_mutate,
        "num2text":      cmd_num2text,
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
