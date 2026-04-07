"""
analyzer.py — Análise estatística de wordlists (estilo Pipal).

Métricas:
  - Total de entradas, únicas, duplicatas
  - Comprimento: mínimo, máximo, médio, distribuição
  - Top N senhas mais frequentes
  - Distribuição de tipos de char (só letras, só números, misto)
  - Posição de números e especiais na senha
  - Análise de máscaras estilo Hashcat (?u?l?d?s)
  - Extração de palavras-base (sem sufixo numérico/especial)
  - Export em JSON e CSV

Uso:
  wfh.py analyze wordlist.lst
  wfh.py analyze wordlist.lst --top 20 --masks --base-words --format json

Autor: André Henrique (@mrhenrike)
Versão: 1.1.0
"""

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

    return {
        "total":          total,
        "unique":         unique,
        "duplicates":     duplicates,
        "min_length":     min_len,
        "max_length":     max_len,
        "avg_length":     round(avg_len, 2),
        "length_distribution": dict(sorted(length_dist.items())),
        "char_types": {
            "only_alpha":   only_alpha,
            "only_digits":  only_digits,
            "only_lower":   only_lower,
            "only_upper":   only_upper,
            "has_special":  has_special,
            "has_number":   has_number,
            "mixed":        mixed,
        },
        "top_passwords":  top,
        "number_positions": {
            "starts_with_number": num_start,
            "ends_with_number":   num_end,
        },
        "special_positions": {
            "starts_with_special": sp_start,
            "ends_with_special":   sp_end,
        },
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
        "number_positions": metrics["number_positions"],
        "special_positions": metrics["special_positions"],
        "length_distribution": metrics["length_distribution"],
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
    lines.append(f"# Wordlist Analysis Report")
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
        lines.append(f"## Hashcat Mask Analysis")
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
