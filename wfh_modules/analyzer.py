"""
analyzer.py — Análise estatística de wordlists (estilo Pipal).

Métricas:
  - Total de entradas, únicas, duplicatas
  - Comprimento: mínimo, máximo, médio, distribuição
  - Top N senhas mais frequentes
  - Distribuição de tipos de char (só letras, só números, misto)
  - Posição de números e especiais na senha
  - Charset mais comuns

Uso:
  wfh.py analyze wordlist.lst
  wfh.py analyze wordlist.lst --top 20 --out relatorio.txt

Autor: André Henrique (@mrhenrike)
Versão: 1.0.0
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_NUM_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[^a-zA-Z0-9]")
_LETTER_RE = re.compile(r"[a-zA-ZÀ-ÿ]")


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
