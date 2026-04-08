"""
analyzer.py — Statistical wordlist analysis (Pipal parity).

Metrics:
  - Total entries, unique, duplicates
  - Length: min, max, avg, distribution, buckets (1-6, 1-8, >8)
  - Top N most frequent entries
  - Char type distribution (15 pipal categories + char set ordering)
  - Number/special position analysis
  - Trailing digits: exactly 1/2/3 digits at end, last digit 0-9 histogram
  - Character frequency by position
  - Hashcat mask analysis (?u?l?d?s)
  - Base word extraction with frequency ranking
  - Export: JSON, CSV, Markdown

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import csv
import io
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_NUM_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[^a-zA-Z0-9]")
_LETTER_RE = re.compile(r"[a-zA-ZÀ-ÿ]")
# Regex para strip de sufixo numérico/especial ao extrair palavras-base
_TRAILING_JUNK_RE = re.compile(r"[^a-zA-ZÀ-ÿ]+$")
_LEADING_JUNK_RE = re.compile(r"^[^a-zA-ZÀ-ÿ]+")


def _classify_ordering(entry: str) -> str:
    """Classify char set ordering (pipal: stringdigit, digitstring, etc.)."""
    pattern = ""
    prev = ""
    for ch in entry:
        if ch.isalpha():
            cur = "string"
        elif ch.isdigit():
            cur = "digit"
        else:
            cur = "special"
        if cur != prev:
            pattern += cur
            prev = cur
    return pattern or "empty"


def _classify_composition(entry: str) -> str:
    """Classify into pipal's 15 char set categories."""
    has_lower = any(c.islower() for c in entry)
    has_upper = any(c.isupper() for c in entry)
    has_digit = any(c.isdigit() for c in entry)
    has_special = bool(_SPECIAL_RE.search(entry))

    if has_lower and not has_upper and not has_digit and not has_special:
        return "loweralpha"
    if has_upper and not has_lower and not has_digit and not has_special:
        return "upperalpha"
    if has_digit and not has_lower and not has_upper and not has_special:
        return "numeric"
    if has_special and not has_lower and not has_upper and not has_digit:
        return "special"
    if has_lower and has_upper and not has_digit and not has_special:
        return "mixedalpha"
    if has_lower and has_digit and not has_upper and not has_special:
        return "loweralphanum"
    if has_upper and has_digit and not has_lower and not has_special:
        return "upperalphanum"
    if has_lower and has_upper and has_digit and not has_special:
        return "mixedalphanum"
    if has_lower and has_special and not has_upper and not has_digit:
        return "loweralphaspecial"
    if has_upper and has_special and not has_lower and not has_digit:
        return "upperalphaspecial"
    if has_digit and has_special and not has_lower and not has_upper:
        return "specialnum"
    if has_lower and has_digit and has_special and not has_upper:
        return "loweralphaspecialnum"
    if has_upper and has_digit and has_special and not has_lower:
        return "upperalphaspecialnum"
    if has_lower and has_upper and has_special and not has_digit:
        return "mixedalphaspecial"
    if has_lower and has_upper and has_digit and has_special:
        return "mixedalphaspecialnum"
    return "other"


def analyze_wordlist(
    filepath: str,
    top_n: int = 20,
) -> dict:
    """
    Analisa uma wordlist e retorna métricas estatísticas.

    Args:
        filepath: Caminho da wordlist.
        top_n: Número de entradas mais frequentes a listar.

    Returns:
        Dict com métricas: total, unique, duplicates, length_distribution,
        char_types, top_passwords, number_positions, special_positions.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist não encontrada: {filepath}")

    entries: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = line.rstrip("\n\r")
            if entry:
                entries.append(entry)

    total = len(entries)
    counter = Counter(entries)
    unique = len(counter)
    duplicates = total - unique

    # Distribuição de comprimentos
    lengths = [len(e) for e in entries]
    length_dist: Counter = Counter(lengths)
    min_len = min(lengths) if lengths else 0
    max_len = max(lengths) if lengths else 0
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    # Tipos de char
    only_alpha = sum(1 for e in entries if e.isalpha())
    only_digits = sum(1 for e in entries if e.isdigit())
    only_lower = sum(1 for e in entries if e.islower())
    only_upper = sum(1 for e in entries if e.isupper())
    has_special = sum(1 for e in entries if _SPECIAL_RE.search(e))
    has_number = sum(1 for e in entries if _NUM_RE.search(e))
    mixed = sum(1 for e in entries if _LETTER_RE.search(e) and _NUM_RE.search(e))

    # Top N
    top = counter.most_common(top_n)

    # Posição de números
    num_start = sum(1 for e in entries if e and _NUM_RE.match(e[0]))
    num_end = sum(1 for e in entries if e and _NUM_RE.match(e[-1]))

    # Posição de especiais
    sp_start = sum(1 for e in entries if e and _SPECIAL_RE.match(e[0]))
    sp_end = sum(1 for e in entries if e and _SPECIAL_RE.match(e[-1]))

    # ── Pipal-style enhancements ─────────────────────────────────────────────

    # Length buckets (pipal parity)
    len_1_6 = sum(1 for l in lengths if 1 <= l <= 6)
    len_1_8 = sum(1 for l in lengths if 1 <= l <= 8)
    len_gt8 = sum(1 for l in lengths if l > 8)

    # Last digit histogram (pipal parity)
    last_digit_hist: Counter = Counter()
    trailing_1 = 0
    trailing_2 = 0
    trailing_3 = 0
    for e in entries:
        if e and e[-1].isdigit():
            last_digit_hist[e[-1]] += 1
            trailing_1 += 1
            if len(e) >= 2 and e[-2].isdigit():
                trailing_2 += 1
                if len(e) >= 3 and e[-3].isdigit():
                    trailing_3 += 1

    # Char set ordering (pipal parity: stringdigit, digitstring, etc.)
    ordering: Counter = Counter()
    for e in entries:
        ordering[_classify_ordering(e)] += 1

    # Char set composition (15 pipal categories)
    composition: Counter = Counter()
    for e in entries:
        composition[_classify_composition(e)] += 1

    # First-upper-last-digit / first-upper-last-special (pipal parity)
    first_upper_last_digit = sum(
        1 for e in entries if len(e) >= 2 and e[0].isupper() and e[-1].isdigit()
    )
    first_upper_last_special = sum(
        1 for e in entries
        if len(e) >= 2 and e[0].isupper() and not e[-1].isalnum()
    )

    return {
        "total":          total,
        "unique":         unique,
        "duplicates":     duplicates,
        "min_length":     min_len,
        "max_length":     max_len,
        "avg_length":     round(avg_len, 2),
        "length_distribution": dict(sorted(length_dist.items())),
        "length_buckets": {
            "1_to_6":  len_1_6,
            "1_to_8":  len_1_8,
            "over_8":  len_gt8,
        },
        "char_types": {
            "only_alpha":   only_alpha,
            "only_digits":  only_digits,
            "only_lower":   only_lower,
            "only_upper":   only_upper,
            "has_special":  has_special,
            "has_number":   has_number,
            "mixed":        mixed,
        },
        "char_composition": dict(composition.most_common()),
        "char_ordering": dict(ordering.most_common()),
        "top_passwords":  top,
        "number_positions": {
            "starts_with_number": num_start,
            "ends_with_number":   num_end,
        },
        "special_positions": {
            "starts_with_special": sp_start,
            "ends_with_special":   sp_end,
        },
        "trailing_digits": {
            "exactly_1_digit": trailing_1,
            "exactly_2_digits": trailing_2,
            "exactly_3_digits": trailing_3,
        },
        "last_digit_histogram": dict(sorted(last_digit_hist.items())),
        "first_upper_last_digit": first_upper_last_digit,
        "first_upper_last_special": first_upper_last_special,
    }


def format_report(metrics: dict, filepath: str) -> str:
    """
    Formata métricas de análise em relatório texto.

    Args:
        metrics: Dict retornado por analyze_wordlist().
        filepath: Caminho da wordlist analisada.

    Returns:
        String formatada do relatório.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"Análise de Wordlist: {filepath}")
    lines.append("=" * 60)
    lines.append(f"Total de entradas:  {metrics['total']:,}")
    lines.append(f"Entradas únicas:    {metrics['unique']:,}")
    lines.append(f"Duplicatas:         {metrics['duplicates']:,}")
    lines.append(f"Comprimento: min={metrics['min_length']}  max={metrics['max_length']}  "
                 f"média={metrics['avg_length']}")
    lines.append("")
    lines.append("--- Tipos de Caractere ---")
    ct = metrics["char_types"]
    lines.append(f"  Só letras:          {ct['only_alpha']:,}")
    lines.append(f"  Só dígitos:         {ct['only_digits']:,}")
    lines.append(f"  Só minúsculas:      {ct['only_lower']:,}")
    lines.append(f"  Só maiúsculas:      {ct['only_upper']:,}")
    lines.append(f"  Tem especial:       {ct['has_special']:,}")
    lines.append(f"  Tem número:         {ct['has_number']:,}")
    lines.append(f"  Misto letra+num:    {ct['mixed']:,}")
    lines.append("")
    lines.append("--- Posição de Números ---")
    np_ = metrics["number_positions"]
    lines.append(f"  Começa com número:  {np_['starts_with_number']:,}")
    lines.append(f"  Termina com número: {np_['ends_with_number']:,}")
    lines.append("")
    lines.append("--- Posição de Especiais ---")
    sp = metrics["special_positions"]
    lines.append(f"  Começa com especial:  {sp['starts_with_special']:,}")
    lines.append(f"  Termina com especial: {sp['ends_with_special']:,}")
    lines.append("")
    lines.append(f"--- Top {len(metrics['top_passwords'])} Entradas Mais Frequentes ---")
    for i, (entry, count) in enumerate(metrics["top_passwords"], 1):
        lines.append(f"  {i:3d}. {entry!r} ({count}x)")
    lines.append("")
    lines.append("--- Distribuição por Comprimento ---")
    for length, count in sorted(metrics["length_distribution"].items()):
        pct = count / metrics["total"] * 100 if metrics["total"] else 0
        bar = "█" * int(pct / 2)
        lines.append(f"  Len {length:3d}: {count:8,}  ({pct:5.1f}%) {bar}")
    lines.append("=" * 60)

    return "\n".join(lines)


def _char_to_mask_token(ch: str) -> str:
    """Converte um caractere para o token de máscara Hashcat correspondente."""
    if ch.isupper():
        return "?u"
    if ch.islower():
        return "?l"
    if ch.isdigit():
        return "?d"
    return "?s"


def analyze_masks(
    filepath: str,
    top_n: int = 20,
) -> dict:
    """
    Analisa máscaras de senha estilo Hashcat a partir de uma wordlist.

    Converte cada entrada para uma máscara (ex: 'Admin@123' → '?u?l?l?l?l?s?d?d?d')
    e conta as máscaras mais frequentes. Útil para criar regras de ataque direcionadas.

    Args:
        filepath: Caminho da wordlist.
        top_n: Número de máscaras mais frequentes a listar.

    Returns:
        Dict com 'mask_frequency' (Counter), 'top_masks' e 'unique_masks'.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist não encontrada: {filepath}")

    mask_counter: Counter = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = line.rstrip("\n\r")
            if not entry:
                continue
            mask = "".join(_char_to_mask_token(c) for c in entry)
            mask_counter[mask] += 1

    return {
        "unique_masks": len(mask_counter),
        "top_masks": mask_counter.most_common(top_n),
        "mask_frequency": dict(mask_counter),
    }


def extract_base_words(
    filepath: str,
    min_len: int = 4,
) -> list[str]:
    """
    Extrai palavras-base removendo sufixos/prefixos numéricos e especiais.

    Por exemplo, 'password123!' → 'password', 'Admin@2024' → 'Admin'.
    Útil para identificar o vocabulário raiz de uma wordlist comprometida.

    Args:
        filepath: Caminho da wordlist.
        min_len: Comprimento mínimo da palavra-base extraída.

    Returns:
        Lista de palavras-base únicas ordenadas.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist não encontrada: {filepath}")

    seen: set[str] = set()
    bases: list[str] = []

    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = line.rstrip("\n\r")
            if not entry:
                continue
            base = _TRAILING_JUNK_RE.sub("", entry)
            base = _LEADING_JUNK_RE.sub("", base)
            if len(base) >= min_len and base not in seen:
                seen.add(base)
                bases.append(base)

    return sorted(bases)


def extract_base_words_ranked(
    filepath: str,
    min_len: int = 4,
    top_n: int = 50,
) -> list[tuple[str, int]]:
    """Extract base words with frequency ranking (pipal parity).

    Returns list of (base_word, count) tuples sorted by frequency.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist not found: {filepath}")

    counter: Counter = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = line.rstrip("\n\r")
            if not entry:
                continue
            base = _TRAILING_JUNK_RE.sub("", entry)
            base = _LEADING_JUNK_RE.sub("", base).lower()
            if len(base) >= min_len:
                counter[base] += 1

    return counter.most_common(top_n)


def analyze_char_position_frequency(
    filepath: str,
    max_positions: int = 16,
) -> dict[int, dict[str, int]]:
    """Analyze character frequency by position (pipal Frequency_Checker parity).

    Returns dict mapping position → {char: count}.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist not found: {filepath}")

    pos_freq: dict[int, Counter] = {i: Counter() for i in range(max_positions)}

    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = line.rstrip("\n\r")
            for i, ch in enumerate(entry[:max_positions]):
                pos_freq[i][ch] += 1

    return {pos: dict(cnt.most_common(20)) for pos, cnt in pos_freq.items() if cnt}


def export_stats_json(metrics: dict, filepath: str, mask_data: Optional[dict] = None) -> str:
    """
    Exporta métricas de análise em formato JSON.

    Args:
        metrics: Dict retornado por analyze_wordlist().
        filepath: Caminho da wordlist analisada (para metadados).
        mask_data: Dict retornado por analyze_masks() (opcional).

    Returns:
        String JSON formatada.
    """
    export: dict = {
        "source": filepath,
        "summary": {
            "total": metrics["total"],
            "unique": metrics["unique"],
            "duplicates": metrics["duplicates"],
            "min_length": metrics["min_length"],
            "max_length": metrics["max_length"],
            "avg_length": metrics["avg_length"],
        },
        "char_types": metrics["char_types"],
        "char_composition": metrics.get("char_composition", {}),
        "char_ordering": metrics.get("char_ordering", {}),
        "number_positions": metrics["number_positions"],
        "special_positions": metrics["special_positions"],
        "trailing_digits": metrics.get("trailing_digits", {}),
        "last_digit_histogram": metrics.get("last_digit_histogram", {}),
        "first_upper_last_digit": metrics.get("first_upper_last_digit", 0),
        "first_upper_last_special": metrics.get("first_upper_last_special", 0),
        "length_distribution": metrics["length_distribution"],
        "length_buckets": metrics.get("length_buckets", {}),
        "top_passwords": [
            {"entry": e, "count": c} for e, c in metrics["top_passwords"]
        ],
    }
    if mask_data:
        export["mask_analysis"] = {
            "unique_masks": mask_data["unique_masks"],
            "top_masks": [
                {"mask": m, "count": c} for m, c in mask_data["top_masks"]
            ],
        }
    return json.dumps(export, ensure_ascii=False, indent=2)


def export_stats_csv(metrics: dict, mask_data: Optional[dict] = None) -> str:
    """
    Exporta distribuição de comprimento e top senhas em formato CSV.

    Args:
        metrics: Dict retornado por analyze_wordlist().
        mask_data: Dict retornado por analyze_masks() (opcional).

    Returns:
        String CSV completa.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["## SUMMARY"])
    writer.writerow(["metric", "value"])
    writer.writerow(["total", metrics["total"]])
    writer.writerow(["unique", metrics["unique"]])
    writer.writerow(["duplicates", metrics["duplicates"]])
    writer.writerow(["min_length", metrics["min_length"]])
    writer.writerow(["max_length", metrics["max_length"]])
    writer.writerow(["avg_length", metrics["avg_length"]])
    writer.writerow([])

    writer.writerow(["## LENGTH DISTRIBUTION"])
    writer.writerow(["length", "count", "percent"])
    total = metrics["total"] or 1
    for length, count in sorted(metrics["length_distribution"].items()):
        writer.writerow([length, count, f"{count/total*100:.2f}%"])
    writer.writerow([])

    writer.writerow(["## TOP PASSWORDS"])
    writer.writerow(["rank", "entry", "count"])
    for i, (entry, count) in enumerate(metrics["top_passwords"], 1):
        writer.writerow([i, entry, count])

    if mask_data:
        writer.writerow([])
        writer.writerow(["## TOP MASKS"])
        writer.writerow(["rank", "mask", "count"])
        for i, (mask, count) in enumerate(mask_data["top_masks"], 1):
            writer.writerow([i, mask, count])

    return buf.getvalue()


def export_stats_markdown(
    metrics: dict,
    filepath: str,
    mask_data: Optional[dict] = None,
) -> str:
    """
    Export analysis metrics as Markdown tables.

    Args:
        metrics: Dict returned by analyze_wordlist().
        filepath: Path of the analyzed wordlist.
        mask_data: Dict returned by analyze_masks() (optional).

    Returns:
        Markdown-formatted report string.
    """
    lines: list[str] = []
    lines.append("# Wordlist Analysis Report")
    lines.append(f"**Source:** `{filepath}`\n")

    lines.append("## Summary")
    lines.append("| Metric | Value |")
    lines.append("|--------|------:|")
    lines.append(f"| Total entries | {metrics['total']:,} |")
    lines.append(f"| Unique entries | {metrics['unique']:,} |")
    lines.append(f"| Duplicates | {metrics['duplicates']:,} |")
    lines.append(f"| Min length | {metrics['min_length']} |")
    lines.append(f"| Max length | {metrics['max_length']} |")
    lines.append(f"| Avg length | {metrics['avg_length']:.1f} |")
    lines.append("")

    lines.append("## Character Type Distribution")
    lines.append("| Type | Count | % |")
    lines.append("|------|------:|--:|")
    total = metrics["total"] or 1
    for ctype, count in sorted(metrics["char_types"].items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        lines.append(f"| {ctype} | {count:,} | {pct:.1f}% |")
    lines.append("")

    lines.append("## Length Distribution (Top 20)")
    lines.append("| Length | Count | % |")
    lines.append("|-------:|------:|--:|")
    for length, count in sorted(metrics["length_distribution"].items())[:20]:
        pct = count / total * 100
        lines.append(f"| {length} | {count:,} | {pct:.1f}% |")
    lines.append("")

    lines.append(f"## Top {len(metrics['top_passwords'])} Most Common")
    lines.append("| # | Entry | Count |")
    lines.append("|--:|-------|------:|")
    for i, (entry, count) in enumerate(metrics["top_passwords"], 1):
        safe_entry = entry.replace("|", "\\|")
        lines.append(f"| {i} | `{safe_entry}` | {count:,} |")
    lines.append("")

    if mask_data:
        lines.append("## Hashcat Mask Analysis")
        lines.append(f"**Unique masks:** {mask_data['unique_masks']:,}\n")
        lines.append(f"### Top {len(mask_data['top_masks'])} Masks")
        lines.append("| # | Mask | Count |")
        lines.append("|--:|------|------:|")
        for i, (mask, count) in enumerate(mask_data["top_masks"], 1):
            lines.append(f"| {i} | `{mask}` | {count:,} |")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by wfh.py — WordList For Hacking*")
    return "\n".join(lines)


def format_mask_report(mask_data: dict) -> str:
    """
    Formata relatório de análise de máscaras Hashcat.

    Args:
        mask_data: Dict retornado por analyze_masks().

    Returns:
        String formatada do relatório de máscaras.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("Hashcat Mask Analysis")
    lines.append("=" * 60)
    lines.append(f"Unique masks found: {mask_data['unique_masks']:,}")
    lines.append("")
    lines.append(f"--- Top {len(mask_data['top_masks'])} Masks ---")
    for i, (mask, count) in enumerate(mask_data["top_masks"], 1):
        lines.append(f"  {i:3d}. {mask}  ({count:,}x)")
    lines.append("=" * 60)
    return "\n".join(lines)
