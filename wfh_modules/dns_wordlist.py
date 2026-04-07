"""
dns_wordlist.py — Geração de wordlists para fuzzing DNS/subdomínios.

Inspirado em DNSCewl (codingo) e alterx (projectdiscovery).

Funcionalidades:
  - Permutações de palavras com separadores (. - _)
  - Prefixos e sufixos comuns
  - Geração de subdomínios por template
  - Combinação com listas de entrada

Uso:
  wfh.py dns -w palavras.lst -d empresa.com.br
  wfh.py dns -t "dev-{word}.{domain}" -w palavras.lst
  wfh.py dns --permute word1 word2 word3

Autor: André Henrique (@mrhenrike)
Versão: 1.0.0
"""

import logging
from itertools import permutations, product
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# Prefixos comuns de subdomínios
COMMON_PREFIXES = [
    "www", "mail", "smtp", "pop", "ftp", "api", "app", "dev",
    "staging", "test", "prod", "admin", "portal", "vpn", "remote",
    "citrix", "intranet", "internal", "cdn", "static", "media",
    "dashboard", "monitor", "ops", "git", "gitlab", "jenkins",
    "jira", "confluence", "wiki", "docs", "support", "crm", "erp",
    "sap", "oracle", "db", "sql", "mysql", "redis", "elastic",
    "kibana", "grafana", "prometheus", "k8s", "kube",
    # BR-specific
    "rede", "sistema", "servico", "sistema", "gestao", "ti",
    "suporte", "helpdesk", "financeiro", "rh", "fiscal",
]

# Sufixos/números comuns
COMMON_SUFFIXES = [
    "1", "2", "3", "01", "02", "03",
    "-old", "-new", "-bak", "-backup", "-temp",
    "-dev", "-test", "-prod", "-stg",
]

# Separadores de subdomínios
DNS_SEPARATORS = ["", "-", "."]


def generate_subdomain_permutations(
    words: list[str],
    domain: str,
    separators: Optional[list[str]] = None,
    use_prefixes: bool = True,
    use_suffixes: bool = True,
) -> Generator[str, None, None]:
    """
    Gera permutações de subdomínios combinando palavras, prefixos e sufixos.

    Args:
        words: Lista de palavras base.
        domain: Domínio alvo (ex: empresa.com.br).
        separators: Separadores a usar entre tokens.
        use_prefixes: Se True, inclui prefixos comuns.
        use_suffixes: Se True, inclui sufixos comuns.

    Yields:
        FQDNs gerados (ex: api-dev.empresa.com.br).
    """
    seps = separators or DNS_SEPARATORS
    seen: set[str] = set()

    def emit(sub: str) -> Optional[str]:
        fqdn = f"{sub}.{domain}"
        if fqdn not in seen:
            seen.add(fqdn)
            return fqdn
        return None

    # Palavras individuais
    for word in words:
        r = emit(word)
        if r:
            yield r

    # Prefixos + palavra
    if use_prefixes:
        for prefix in COMMON_PREFIXES:
            for word in words:
                for sep in seps:
                    r = emit(f"{prefix}{sep}{word}")
                    if r:
                        yield r

    # Palavra + sufixo
    if use_suffixes:
        for word in words:
            for suf in COMMON_SUFFIXES:
                r = emit(f"{word}{suf}")
                if r:
                    yield r

    # Combinações pares de palavras
    for w1, w2 in permutations(words[:20], 2):  # limitar a 20 para evitar explosão
        for sep in seps:
            r = emit(f"{w1}{sep}{w2}")
            if r:
                yield r


def generate_from_template(
    template: str,
    words: list[str],
    domain: str,
) -> Generator[str, None, None]:
    """
    Gera subdomínios a partir de um template com variáveis.

    Variáveis:
      {word}   -> cada palavra da lista
      {domain} -> domínio fornecido

    Args:
        template: Template (ex: "dev-{word}.{domain}").
        words: Lista de palavras.
        domain: Domínio alvo.

    Yields:
        FQDNs gerados pelo template.
    """
    seen: set[str] = set()
    for word in words:
        result = template.replace("{word}", word).replace("{domain}", domain)
        if result not in seen:
            seen.add(result)
            yield result


def load_words_from_file(filepath: str) -> list[str]:
    """
    Carrega palavras de um arquivo, uma por linha.

    Args:
        filepath: Caminho do arquivo.

    Returns:
        Lista de palavras não vazias.
    """
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("Arquivo não encontrado: %s", filepath)
        return []
