#!/usr/bin/env python3
"""
wfh.py — WordList For Hacking v1.0.0

Ferramenta unificada de geração de wordlists para pentest e red team.
Merge de funcionalidades: CUPP + Crunch + CeWL + BEWGor + alterx + pipal + ...

Modos de uso:
  python wfh.py                          # menu interativo
  python wfh.py charset 6 8 abc123       # por charset + comprimento
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile                  # profiling interativo de alvo
  python wfh.py scrape https://site.com  # scraping web
  python wfh.py ocr imagem.png           # OCR de imagem
  python wfh.py extract arq1.pdf arq2.xlsx
  python wfh.py leet palavra -m medium   # variações leet
  python wfh.py xor --brute HEXSTRING    # XOR brute-force
  python wfh.py analyze lista.lst        # análise estatística
  python wfh.py merge l1.lst l2.lst      # merge e deduplicação
  python wfh.py dns -w words.lst -d empresa.com.br
  python wfh.py pharma                   # padrões de farmácias BR
  python wfh.py charset --create-charset meu_charset.cfg

Autor: André Henrique (@mrhenrike)
Versão: 1.0.0
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Generator, Optional

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

VERSION = "1.0.0"

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
    + "  Autor: Andre Henrique (@mrhenrike)\n"
    + "  CUPP + Crunch + CeWL + alterx + pipal + ...\n"
    + f"{Style.RESET_ALL}"
)

MENU = f"""
{Fore.CYAN}=== MENU PRINCIPAL ==={Style.RESET_ALL}

  {Fore.GREEN}[1]{Style.RESET_ALL} charset    — Gerar por charset e comprimento (Crunch-style)
  {Fore.GREEN}[2]{Style.RESET_ALL} pattern    — Gerar por template/padrão com variáveis
  {Fore.GREEN}[3]{Style.RESET_ALL} profile    — Profiling interativo de alvo (CUPP-style)
  {Fore.GREEN}[4]{Style.RESET_ALL} scrape     — Scraping web (CeWL-style)
  {Fore.GREEN}[5]{Style.RESET_ALL} ocr        — Extrair texto de imagem via OCR
  {Fore.GREEN}[6]{Style.RESET_ALL} extract    — Extrair wordlist de arquivos (pdf/xlsx/docx/img)
  {Fore.GREEN}[7]{Style.RESET_ALL} leet       — Variações leet speak (basic/medium/aggressive/custom)
  {Fore.GREEN}[8]{Style.RESET_ALL} xor        — Criptografia/brute-force XOR
  {Fore.GREEN}[9]{Style.RESET_ALL} analyze    — Análise estatística de wordlist (Pipal-style)
  {Fore.GREEN}[10]{Style.RESET_ALL} merge     — Merge e deduplicação de wordlists
  {Fore.GREEN}[11]{Style.RESET_ALL} dns       — Wordlist para fuzzing DNS/subdomínios
  {Fore.GREEN}[12]{Style.RESET_ALL} pharma    — Padrões farmacêuticos e planos de saúde BR
  {Fore.GREEN}[0]{Style.RESET_ALL} Sair
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
    Escreve o output do gerador em arquivo ou stdout com progress bar.

    Args:
        generator: Gerador de strings.
        output: Caminho de arquivo ou None para stdout.
        estimate: Estimativa de itens para progress bar.
        min_len: Filtro de comprimento mínimo.
        max_len: Filtro de comprimento máximo.

    Returns:
        Total de entradas escritas.
    """
    count = 0

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        f = out_path.open("w", encoding="utf-8")
        _info(f"Gravando em: {output}")
    else:
        f = None  # type: ignore

    try:
        if _TQDM and estimate and estimate > 0:
            pbar = _tqdm(total=estimate, unit="palavras", ncols=80)
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
    Solicita confirmação do usuário antes de gerar listas muito grandes.

    Args:
        estimate: Estimativa de entradas a gerar.
        threshold: Threshold para solicitar confirmação.

    Returns:
        True se o usuário confirmar.
    """
    if estimate <= threshold:
        return True
    _warn(f"Estimativa: {estimate:,} entradas. Isso pode demorar muito.")
    try:
        resp = input("  Continuar? [s/N]: ").strip().lower()
        return resp in ("s", "sim", "y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


# ── Handlers de cada modo ────────────────────────────────────────────────────

def cmd_charset(args: argparse.Namespace) -> None:
    """Handler para modo charset."""
    from wfh_modules.charset_gen import (
        get_charset, generate_by_charset, generate_by_pattern,
        estimate_size, create_charset_wizard, PLACEHOLDER_MAP,
    )

    if args.create_charset:
        create_charset_wizard(args.create_charset)
        return

    if args.pattern:
        _info(f"Gerando por pattern: {args.pattern}")
        gen = generate_by_pattern(
            args.pattern,
            charset_file=args.charset_file,
            extra_charset=args.charset if args.charset else None,
        )
        count = _write_output(gen, args.output)
        _ok(f"Geradas: {count:,} entradas")
        return

    charset_str = get_charset(args.charset or "lalpha", args.charset_file)
    total, size = estimate_size(len(charset_str), args.min_len, args.max_len)
    _info(f"Charset: {len(charset_str)} chars | {args.min_len}..{args.max_len} | "
          f"Estimativa: {total:,} entradas ~ {size}")

    if not _confirm_large(total):
        _warn("Operação cancelada.")
        return

    gen = generate_by_charset(charset_str, args.min_len, args.max_len)
    count = _write_output(gen, args.output, estimate=total)
    _ok(f"Geradas: {count:,} entradas")


def cmd_pattern(args: argparse.Namespace) -> None:
    """Handler para modo pattern."""
    from wfh_modules.pattern_engine import (
        render_template, generate_from_template_file, expand_variable,
        generate_company_patterns,
    )

    # Parsear variáveis: --vars cod=1200-1300 empresa=Drogasil,Hapvida
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
        _err("Informe --template ou --template-file")
        return

    count = _write_output(gen, args.output)
    _ok(f"Geradas: {count:,} entradas")


def cmd_profile(args: argparse.Namespace) -> None:
    """Handler para modo profiling."""
    from wfh_modules.profiler import interactive_profile, generate_from_profile

    if hasattr(args, "name") and args.name:
        profile = {
            "name": args.name,
            "nick": getattr(args, "nick", ""),
            "birth_year": getattr(args, "birth", ""),
            "birth_day": "", "birth_month": "", "partner_name": "",
            "partner_nick": "", "partner_birth": "", "pet_name": "",
            "child_name": "", "child_birth": "", "company": "",
            "keywords": "", "special_dates": "",
        }
    else:
        profile = interactive_profile()

    leet_mode = getattr(args, "leet", "basic") or "basic"
    _info(f"Gerando wordlist por perfil [leet={leet_mode}]...")
    gen = generate_from_profile(profile, leet_mode=leet_mode)
    count = _write_output(gen, args.output)
    _ok(f"Geradas: {count:,} entradas")


def cmd_scrape(args: argparse.Namespace) -> None:
    """Handler para modo scraping web."""
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
    _ok(f"Extraídas: {count:,} palavras")


def cmd_ocr(args: argparse.Namespace) -> None:
    """Handler para modo OCR."""
    from wfh_modules.ocr_extractor import extract_from_image

    _info(f"Processando OCR: {args.image}")
    try:
        result = extract_from_image(args.image, lang=args.lang.split(","))
    except ImportError:
        _err("easyocr não instalado. Execute: pip install easyocr")
        return

    _ok(f"Extraídos: {len(result['usernames'])} users, "
        f"{len(result['passwords'])} senhas, {len(result['words'])} palavras")

    all_tokens = result["usernames"] + result["passwords"] + result["words"]

    def gen():
        yield from all_tokens

    count = _write_output(gen(), args.output)
    _ok(f"Total gravado: {count:,}")


def cmd_extract(args: argparse.Namespace) -> None:
    """Handler para modo extração de arquivos."""
    from wfh_modules.file_extractor import extract_wordlist_from_files

    _info(f"Extraindo de {len(args.files)} arquivo(s)...")
    gen = extract_wordlist_from_files(
        args.files, min_len=args.min_len, max_len=args.max_len,
    )
    count = _write_output(gen, args.output)
    _ok(f"Extraídas: {count:,} palavras")


def cmd_leet(args: argparse.Namespace) -> None:
    """Handler para modo leet."""
    from wfh_modules.leet_permuter import generate_all_variations

    _info(f"Gerando variações leet [{args.mode}] para: {args.word}")
    gen = generate_all_variations(
        args.word,
        leet_mode=args.mode,
        custom_mapping=getattr(args, "custom_map", "") or "",
        max_leet=args.max_results,
    )
    count = _write_output(gen, args.output)
    _ok(f"Geradas: {count:,} variações")


def cmd_xor(args: argparse.Namespace) -> None:
    """Handler para modo XOR."""
    from wfh_modules.xor_crypto import (
        brute_force_display, xor_encrypt_str, xor_decrypt_str,
    )

    if args.brute:
        brute_force_display(args.brute)
    elif args.encrypt and args.key:
        import binascii
        enc = xor_encrypt_str(args.encrypt, args.key)
        _ok(f"Cifrado (hex): {binascii.hexlify(enc).decode()}")
    elif args.decrypt and args.key:
        import binascii
        data = bytes.fromhex(args.decrypt)
        result = xor_decrypt_str(data, args.key)
        _ok(f"Decifrado: {result!r}")
    else:
        _err("Informe --brute, --encrypt ou --decrypt com --key")


def cmd_analyze(args: argparse.Namespace) -> None:
    """Handler para análise de wordlist."""
    from wfh_modules.analyzer import analyze_wordlist, format_report

    _info(f"Analisando: {args.wordlist}")
    try:
        metrics = analyze_wordlist(args.wordlist, top_n=args.top)
    except FileNotFoundError as e:
        _err(str(e))
        return

    report = format_report(metrics, args.wordlist)
    print(report)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        _ok(f"Relatório salvo em: {args.output}")


def cmd_merge(args: argparse.Namespace) -> None:
    """Handler para merge de wordlists."""
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
    _ok(f"Total: {count:,} entradas")


def cmd_dns(args: argparse.Namespace) -> None:
    """Handler para geração de wordlist DNS."""
    from wfh_modules.dns_wordlist import (
        generate_subdomain_permutations, generate_from_template, load_words_from_file,
    )

    words: list[str] = []
    if args.wordlist:
        words = load_words_from_file(args.wordlist)
    if args.words:
        words.extend(args.words)

    if not words:
        _err("Informe palavras com --wordlist ou --words")
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
    _ok(f"Gerados: {count:,} subdomínios")


def cmd_pharma(args: argparse.Namespace) -> None:
    """Handler para padrões farmacêuticos BR."""
    from wfh_modules.pattern_engine import (
        generate_pharma_patterns, generate_company_patterns,
    )

    store_codes_arg = getattr(args, "codes", None)
    if store_codes_arg:
        store_codes = [c.strip() for c in store_codes_arg.split(",")]
    else:
        # Usa faixa OCR + vizinhos por padrão
        store_codes = [str(c) for c in range(1200, 1215)]

    _info(f"Gerando padrões farmacêuticos BR [{len(store_codes)} códigos de loja]...")
    gen = generate_pharma_patterns(store_codes=store_codes)
    count = _write_output(gen, args.output)
    _ok(f"Geradas: {count:,} entradas")


# ── Menu interativo ───────────────────────────────────────────────────────────

def interactive_menu() -> None:
    """Exibe e processa o menu interativo principal."""
    print(MENU)
    choice = input(f"{Fore.CYAN}Escolha uma opção: {Style.RESET_ALL}").strip()

    output = input("  Arquivo de saída (Enter para stdout): ").strip() or None

    ns = argparse.Namespace(output=output)

    if choice == "1":
        ns.charset = input("  Charset (nome built-in ou chars): ").strip() or "lalpha"
        ns.min_len = int(input("  Comprimento mínimo: ").strip() or "6")
        ns.max_len = int(input("  Comprimento máximo: ").strip() or "8")
        ns.charset_file = None
        ns.pattern = None
        ns.create_charset = None
        cmd_charset(ns)

    elif choice == "2":
        ns.template = input("  Template (ex: DS{cod}@rd.com.br): ").strip()
        ns.template_file = None
        ns.vars = []
        while True:
            v = input("  Variável (formato nome=valor, Enter para encerrar): ").strip()
            if not v:
                break
            ns.vars.append(v)
        cmd_pattern(ns)

    elif choice == "3":
        ns.name = None
        ns.leet = input("  Modo leet (basic/medium/aggressive/none): ").strip() or "basic"
        cmd_profile(ns)

    elif choice == "4":
        ns.url = input("  URL a crawlear: ").strip()
        ns.depth = int(input("  Profundidade (padrão 2): ").strip() or "2")
        ns.min_word = int(input("  Comprimento mínimo de palavra (6): ").strip() or "6")
        ns.max_word = int(input("  Comprimento máximo (32): ").strip() or "32")
        ns.emails = input("  Extrair emails? [s/N]: ").strip().lower() in ("s", "y")
        ns.meta = input("  Extrair metadados? [s/N]: ").strip().lower() in ("s", "y")
        ns.auth = None
        ns.delay = 0.5
        cmd_scrape(ns)

    elif choice == "5":
        ns.image = input("  Caminho da imagem: ").strip()
        ns.lang = input("  Idiomas OCR (padrão: pt,en): ").strip() or "pt,en"
        cmd_ocr(ns)

    elif choice == "6":
        files_raw = input("  Arquivos (separados por espaço): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Comprimento mínimo (4): ").strip() or "4")
        ns.max_len = int(input("  Comprimento máximo (64): ").strip() or "64")
        cmd_extract(ns)

    elif choice == "7":
        ns.word = input("  Palavra base: ").strip()
        ns.mode = input("  Modo (basic/medium/aggressive/custom): ").strip() or "basic"
        ns.custom_map = ""
        if ns.mode == "custom":
            ns.custom_map = input("  Mapeamento (ex: a=@,4;t=7;s=$): ").strip()
        ns.max_results = int(input("  Máx resultados (10000): ").strip() or "10000")
        cmd_leet(ns)

    elif choice == "8":
        sub = input("  [1] Brute-force  [2] Encriptar  [3] Decriptar: ").strip()
        ns.brute = None
        ns.encrypt = None
        ns.decrypt = None
        ns.key = None
        if sub == "1":
            ns.brute = input("  Hex string: ").strip()
        elif sub == "2":
            ns.encrypt = input("  Texto a cifrar: ").strip()
            ns.key = input("  Chave: ").strip()
        elif sub == "3":
            ns.decrypt = input("  Hex cifrado: ").strip()
            ns.key = input("  Chave: ").strip()
        cmd_xor(ns)

    elif choice == "9":
        ns.wordlist = input("  Wordlist a analisar: ").strip()
        ns.top = int(input("  Top N (20): ").strip() or "20")
        cmd_analyze(ns)

    elif choice == "10":
        files_raw = input("  Arquivos a fundir (espaço): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Comprimento mínimo (6): ").strip() or "6")
        ns.max_len = int(input("  Comprimento máximo (128): ").strip() or "128")
        ns.no_numeric = input("  Remover puramente numéricos? [s/N]: ").strip().lower() in ("s", "y")
        ns.filter = None
        ns.no_dedupe = False
        ns.sort = input("  Ordenar (alpha/length/random/Enter para skip): ").strip() or None
        cmd_merge(ns)

    elif choice == "11":
        ns.domain = input("  Domínio alvo: ").strip()
        ns.wordlist = input("  Arquivo de palavras (ou Enter): ").strip() or None
        ns.words = []
        ns.template = None
        ns.no_prefixes = False
        ns.no_suffixes = False
        cmd_dns(ns)

    elif choice == "12":
        ns.codes = input("  Códigos de loja (ex: 1200-1300 ou 1200,1201, ou Enter para padrão): ").strip() or None
        cmd_pharma(ns)

    elif choice == "0":
        _info("Encerrando wfh.py.")
        sys.exit(0)

    else:
        _warn("Opção inválida.")


# ── Parser de argumentos ─────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="wfh.py",
        description="WordList For Hacking — Geração profissional de wordlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemplos:
  python wfh.py charset 6 8 abc123
  python wfh.py charset 8 8 --pattern "Pass@@@%%%" 
  python wfh.py charset 6 8 -f charsets.cfg mixalpha-numeric
  python wfh.py charset --create-charset meus_charsets.cfg
  python wfh.py pattern -t "DS{cod}@rd.com.br" --vars cod=1200-1300
  python wfh.py profile
  python wfh.py scrape https://site.com.br -d 2 --emails
  python wfh.py ocr imagem.png -o wordlist.txt
  python wfh.py extract relatorio.pdf planilha.xlsx -o extraido.txt
  python wfh.py leet admin -m aggressive
  python wfh.py leet senha -m custom --custom-map "a=@,4;s=$;e=3"
  python wfh.py xor --brute 1a2b3c4d
  python wfh.py analyze wlist_brasil.lst --top 30
  python wfh.py merge l1.lst l2.lst --no-numeric --sort alpha -o merged.lst
  python wfh.py dns -w palavras.lst -d empresa.com.br
  python wfh.py pharma --codes 1200-1250 -o pharma_senhas.lst
""",
    )
    parser.add_argument("--version", action="version", version=f"wfh.py {VERSION}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")

    sub = parser.add_subparsers(dest="command", help="Modo de operação")

    # ── charset ───────────────────────────────────────────────────────────
    p_cs = sub.add_parser("charset", help="Gerar por charset e comprimento")
    p_cs.add_argument("min_len", nargs="?", type=int, default=6, help="Comprimento mínimo")
    p_cs.add_argument("max_len", nargs="?", type=int, default=8, help="Comprimento máximo")
    p_cs.add_argument("charset", nargs="?", default="lalpha",
                       help="Charset: nome built-in ou string de chars diretos")
    p_cs.add_argument("-f", "--charset-file", dest="charset_file", help="Arquivo .cfg de charsets")
    p_cs.add_argument("-p", "--pattern", help="Pattern com placeholders (@,%,^,,)")
    p_cs.add_argument("--create-charset", dest="create_charset", metavar="FILE",
                       help="Wizard para criar arquivo de charset")
    p_cs.add_argument("-o", "--output", help="Arquivo de saída")

    # ── pattern ───────────────────────────────────────────────────────────
    p_pt = sub.add_parser("pattern", help="Gerar por template com variáveis")
    p_pt.add_argument("-t", "--template", help="Template (ex: DS{cod}@rd.com.br)")
    p_pt.add_argument("-f", "--template-file", dest="template_file", help="Arquivo de templates")
    p_pt.add_argument("--vars", nargs="+", metavar="KEY=VALUE",
                       help="Variáveis (ex: cod=1200-1300 empresa=Drogasil,Hapvida)")
    p_pt.add_argument("-o", "--output", help="Arquivo de saída")

    # ── profile ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser("profile", help="Profiling interativo de alvo")
    p_pr.add_argument("--name", help="Nome do alvo")
    p_pr.add_argument("--nick", help="Apelido")
    p_pr.add_argument("--birth", help="Ano de nascimento")
    p_pr.add_argument("--leet", default="basic",
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Modo leet speak")
    p_pr.add_argument("-o", "--output", help="Arquivo de saída")

    # ── scrape ────────────────────────────────────────────────────────────
    p_sc = sub.add_parser("scrape", help="Scraping web (CeWL-style)")
    p_sc.add_argument("url", help="URL alvo")
    p_sc.add_argument("-d", "--depth", type=int, default=2, help="Profundidade de crawl")
    p_sc.add_argument("--min-word", type=int, default=6, dest="min_word")
    p_sc.add_argument("--max-word", type=int, default=32, dest="max_word")
    p_sc.add_argument("--emails", action="store_true", help="Extrair emails")
    p_sc.add_argument("--meta", action="store_true", help="Extrair metadados")
    p_sc.add_argument("--auth", help="HTTP Basic Auth (usuario:senha)")
    p_sc.add_argument("--delay", type=float, default=0.5)
    p_sc.add_argument("-o", "--output", help="Arquivo de saída")

    # ── ocr ───────────────────────────────────────────────────────────────
    p_oc = sub.add_parser("ocr", help="Extrair texto de imagem via OCR")
    p_oc.add_argument("image", help="Caminho da imagem")
    p_oc.add_argument("--lang", default="pt,en", help="Idiomas OCR (padrão: pt,en)")
    p_oc.add_argument("-o", "--output", help="Arquivo de saída")

    # ── extract ───────────────────────────────────────────────────────────
    p_ex = sub.add_parser("extract", help="Extrair wordlist de arquivos")
    p_ex.add_argument("files", nargs="+", help="Arquivos de entrada (máximo 50)")
    p_ex.add_argument("--min-len", type=int, default=4, dest="min_len")
    p_ex.add_argument("--max-len", type=int, default=64, dest="max_len")
    p_ex.add_argument("-o", "--output", help="Arquivo de saída")

    # ── leet ─────────────────────────────────────────────────────────────
    p_lt = sub.add_parser("leet", help="Variações leet speak")
    p_lt.add_argument("word", help="Palavra base")
    p_lt.add_argument("-m", "--mode", default="basic",
                       choices=["basic", "medium", "aggressive", "custom"],
                       help="Modo de substituição leet")
    p_lt.add_argument("--custom-map", dest="custom_map", default="",
                       help="Mapeamento custom (ex: a=@,4;t=7;s=$;l=1,|)")
    p_lt.add_argument("--max-results", type=int, default=10000, dest="max_results")
    p_lt.add_argument("-o", "--output", help="Arquivo de saída")

    # ── xor ───────────────────────────────────────────────────────────────
    p_xr = sub.add_parser("xor", help="Criptografia/brute-force XOR")
    xr_group = p_xr.add_mutually_exclusive_group(required=True)
    xr_group.add_argument("--brute", metavar="HEX", help="Brute-force de chave 1 byte")
    xr_group.add_argument("--encrypt", metavar="TEXT", help="Cifrar texto")
    xr_group.add_argument("--decrypt", metavar="HEX", help="Decifrar hex")
    p_xr.add_argument("--key", help="Chave para encrypt/decrypt")
    p_xr.add_argument("-o", "--output", help="Arquivo de saída")

    # ── analyze ───────────────────────────────────────────────────────────
    p_an = sub.add_parser("analyze", help="Análise estatística (Pipal-style)")
    p_an.add_argument("wordlist", help="Wordlist a analisar")
    p_an.add_argument("--top", type=int, default=20, help="Top N mais frequentes")
    p_an.add_argument("-o", "--output", help="Salvar relatório em arquivo")

    # ── merge ─────────────────────────────────────────────────────────────
    p_mg = sub.add_parser("merge", help="Merge e deduplicação de wordlists")
    p_mg.add_argument("files", nargs="+", help="Wordlists de entrada")
    p_mg.add_argument("--min-len", type=int, default=6, dest="min_len")
    p_mg.add_argument("--max-len", type=int, default=128, dest="max_len")
    p_mg.add_argument("--no-numeric", action="store_true", dest="no_numeric",
                       help="Remover entradas puramente numéricas")
    p_mg.add_argument("--filter", help="Filtro regex (apenas matches passam)")
    p_mg.add_argument("--no-dedupe", action="store_true", dest="no_dedupe")
    p_mg.add_argument("--sort", choices=["alpha", "length", "random"])
    p_mg.add_argument("-o", "--output", help="Arquivo de saída")

    # ── dns ───────────────────────────────────────────────────────────────
    p_dn = sub.add_parser("dns", help="Wordlist para fuzzing DNS/subdomínios")
    p_dn.add_argument("-d", "--domain", required=True, help="Domínio alvo")
    p_dn.add_argument("-w", "--wordlist", help="Arquivo de palavras")
    p_dn.add_argument("--words", nargs="+", help="Palavras diretas")
    p_dn.add_argument("-t", "--template", help="Template (ex: dev-{word}.{domain})")
    p_dn.add_argument("--no-prefixes", action="store_true", dest="no_prefixes")
    p_dn.add_argument("--no-suffixes", action="store_true", dest="no_suffixes")
    p_dn.add_argument("-o", "--output", help="Arquivo de saída")

    # ── pharma ────────────────────────────────────────────────────────────
    p_ph = sub.add_parser("pharma", help="Padrões farmacêuticos e planos de saúde BR")
    p_ph.add_argument("--codes", help="Códigos de loja (ex: 1200-1300 ou 1200,1201)")
    p_ph.add_argument("-o", "--output", help="Arquivo de saída")

    return parser


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    """Ponto de entrada principal do wfh.py."""
    print(BANNER)

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose if hasattr(args, "verbose") else False:
        logging.getLogger().setLevel(logging.DEBUG)

    # Sem subcomando -> menu interativo
    if not args.command:
        try:
            while True:
                interactive_menu()
                print()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            _info("Encerrando.")
        return

    # Dispatch para handler do subcomando
    handlers = {
        "charset": cmd_charset,
        "pattern": cmd_pattern,
        "profile": cmd_profile,
        "scrape":  cmd_scrape,
        "ocr":     cmd_ocr,
        "extract": cmd_extract,
        "leet":    cmd_leet,
        "xor":     cmd_xor,
        "analyze": cmd_analyze,
        "merge":   cmd_merge,
        "dns":     cmd_dns,
        "pharma":  cmd_pharma,
    }

    handler = handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\n")
            _warn("Interrompido pelo usuário.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
