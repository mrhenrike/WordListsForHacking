"""
profiler.py — Geração de wordlist por profiling interativo de alvo.

Combina o questionário do CUPP com a abrangência do BEWGor e elpscrk.
Gera senhas ranqueadas por probabilidade com base em dados pessoais:
  - Nome, apelido, data de nascimento, parceiro, pet, filhos
  - Empresa, keywords, datas especiais

Exemplo de uso:
  wfh.py profile                          # modo interativo
  wfh.py profile --name "João" --nick "jo" --birth 1990

Autor: André Henrique (@mrhenrike)
Versão: 1.0.0
"""

import logging
from itertools import permutations
from typing import Generator, Optional

from .leet_permuter import generate_all_variations
from .pattern_engine import DEFAULT_ANOS, strip_accents

logger = logging.getLogger(__name__)

# ── Sufixos mais comuns em senhas com palavras pessoais ─────────────────────
COMMON_SUFFIXES = [
    "", "1", "12", "123", "1234", "12345",
    "!", "!!", "@", "@1", "#", "#1",
    "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
    "01", "010", "007", "69", "99", "100",
]

# ── Prefixos comuns ──────────────────────────────────────────────────────────
COMMON_PREFIXES = ["", "1", "the", "my", "mr", "dr", "admin"]

# ── Separadores comuns entre tokens ─────────────────────────────────────────
TOKEN_SEPARATORS = ["", ".", "-", "_", "@", "#", "!"]


def _variations(word: str, leet: bool = True) -> list[str]:
    """
    Gera variações básicas de uma palavra: case + leet basic.

    Args:
        word: Palavra base.
        leet: Se True, inclui variações leet basic.

    Returns:
        Lista de variações únicas.
    """
    if not word:
        return []
    clean = strip_accents(word.strip())
    base = [clean, clean.lower(), clean.upper(), clean.title()]
    if leet:
        leet_variants = list(generate_all_variations(clean, leet_mode="basic", max_leet=50))
        base.extend(leet_variants)
    return list(dict.fromkeys(base))


def _combine_tokens(
    tokens: list[str],
    separators: Optional[list[str]] = None,
    min_len: int = 6,
    max_len: int = 32,
) -> Generator[str, None, None]:
    """
    Combina tokens com separadores e filtra por comprimento.

    Args:
        tokens: Lista de strings a combinar.
        separators: Separadores a usar.
        min_len: Comprimento mínimo.
        max_len: Comprimento máximo.

    Yields:
        Combinações únicas de tokens com separadores.
    """
    seps = separators or TOKEN_SEPARATORS
    seen: set[str] = set()

    # Par de tokens
    for i in range(len(tokens)):
        for j in range(len(tokens)):
            if i == j:
                continue
            for sep in seps:
                result = f"{tokens[i]}{sep}{tokens[j]}"
                if result not in seen and min_len <= len(result) <= max_len:
                    seen.add(result)
                    yield result

    # Token único + sufixo
    for tok in tokens:
        for suf in COMMON_SUFFIXES:
            result = f"{tok}{suf}"
            if result not in seen and min_len <= len(result) <= max_len:
                seen.add(result)
                yield result

    # Prefixo + token
    for pref in COMMON_PREFIXES:
        for tok in tokens:
            result = f"{pref}{tok}"
            if result not in seen and min_len <= len(result) <= max_len:
                seen.add(result)
                yield result


def interactive_profile() -> dict:
    """
    Conduz questionário interativo para coletar dados do alvo.

    Retorna dict com os dados coletados, prontos para gerar wordlist.

    Returns:
        Dict com campos: name, nick, birth_year, birth_day, birth_month,
        partner_name, partner_nick, partner_birth, pet_name, child_name,
        child_birth, company, keywords, special_dates.
    """
    print("\n=== wfh.py — Profiling de Alvo (modo CUPP) ===\n")
    print("Pressione Enter para pular um campo.\n")

    def ask(prompt: str) -> str:
        return input(f"  {prompt}: ").strip()

    profile = {
        "name":           ask("Nome do alvo"),
        "nick":           ask("Apelido"),
        "birth_year":     ask("Ano de nascimento (YYYY)"),
        "birth_day":      ask("Dia de nascimento (DD)"),
        "birth_month":    ask("Mês de nascimento (MM)"),
        "partner_name":   ask("Nome do parceiro(a)"),
        "partner_nick":   ask("Apelido do parceiro(a)"),
        "partner_birth":  ask("Ano de nascimento do parceiro(a)"),
        "pet_name":       ask("Nome do pet"),
        "child_name":     ask("Nome do filho(a)"),
        "child_birth":    ask("Ano de nascimento do filho(a)"),
        "company":        ask("Empresa onde trabalha"),
        "keywords":       ask("Palavras-chave (separadas por vírgula)"),
        "special_dates":  ask("Datas especiais sem separadores (ex: 1506 para 15/06)"),
    }

    return profile


def generate_from_profile(
    profile: dict,
    leet_mode: str = "basic",
    min_len: int = 6,
    max_len: int = 32,
) -> Generator[str, None, None]:
    """
    Gera wordlist a partir de dados de perfil coletados.

    Args:
        profile: Dict retornado por interactive_profile().
        leet_mode: Modo leet para variações ('basic', 'medium', etc.).
        min_len: Comprimento mínimo das senhas geradas.
        max_len: Comprimento máximo das senhas geradas.

    Yields:
        Strings de senhas geradas.
    """
    seen: set[str] = set()

    def emit(s: str) -> bool:
        if s and s not in seen and min_len <= len(s) <= max_len:
            seen.add(s)
            return True
        return False

    # Coletar todos os tokens base
    raw_tokens: list[str] = []

    for field in [
        "name", "nick", "partner_name", "partner_nick",
        "pet_name", "child_name", "company",
    ]:
        value = profile.get(field, "")
        if value:
            raw_tokens.extend(_variations(value, leet=(leet_mode != "none")))

    # Keywords
    kws = profile.get("keywords", "")
    if kws:
        for kw in kws.split(","):
            raw_tokens.extend(_variations(kw.strip()))

    # Datas
    dates: list[str] = []
    for field in ["birth_year", "birth_day", "birth_month", "partner_birth", "child_birth"]:
        v = profile.get(field, "")
        if v:
            dates.append(v)

    special = profile.get("special_dates", "")
    if special:
        dates.append(special)

    # Combinações de tokens
    for combo in _combine_tokens(raw_tokens, min_len=min_len, max_len=max_len):
        if emit(combo):
            yield combo

    # Token + data
    for tok in raw_tokens[:20]:  # limitar para não explodir
        for date in dates:
            for sep in TOKEN_SEPARATORS:
                for r in [f"{tok}{sep}{date}", f"{date}{sep}{tok}"]:
                    if emit(r):
                        yield r

    # Leet sobre tokens
    if leet_mode != "none" and leet_mode != "basic":
        for tok in raw_tokens[:10]:
            for leet in generate_all_variations(tok, leet_mode=leet_mode, max_leet=100):
                for suf in COMMON_SUFFIXES[:8]:
                    r = f"{leet}{suf}"
                    if emit(r):
                        yield r
