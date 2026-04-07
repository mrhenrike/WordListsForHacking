"""
dns_wordlist.py — Geração de wordlists para fuzzing DNS/subdomínios.

Inspirado em DNSCewl (codingo) e alterx (projectdiscovery).

Funcionalidades:
  - Permutações de palavras com separadores (. - _ e customizáveis)
  - Prefixos e sufixos comuns
  - Geração de subdomínios por template inline ou arquivo YAML
  - Combinação com listas de entrada
  - Suporte a múltiplos domínios via arquivo
  - Filtro e exclusão por regex no output

Uso:
  wfh.py dns -w palavras.lst -d empresa.com.br
  wfh.py dns -t "dev-{word}.{domain}" -w palavras.lst
  wfh.py dns --domain-list domains.txt -w palavras.lst
  wfh.py dns -d empresa.com.br --template-file patterns.yaml -w palavras.lst
  wfh.py dns -d empresa.com.br --match-regex "^api" --filter-regex "test"
  wfh.py dns -d empresa.com.br --separator "_"

Autor: André Henrique (@mrhenrike)
Versão: 1.1.0
"""
from __future__ import annotations

import logging
import re
from itertools import permutations, product
from pathlib import Path
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
    match_regex: Optional[str] = None,
    filter_regex: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Gera permutações de subdomínios combinando palavras, prefixos e sufixos.

    Args:
        words: Lista de palavras base.
        domain: Domínio alvo (ex: empresa.com.br).
        separators: Separadores a usar entre tokens (padrão: ["", "-", "."]).
        use_prefixes: Se True, inclui prefixos comuns.
        use_suffixes: Se True, inclui sufixos comuns.
        match_regex: Regex de inclusão no output (opcional).
        filter_regex: Regex de exclusão do output (opcional).

    Yields:
        FQDNs gerados (ex: api-dev.empresa.com.br).
    """
    seps = separators or DNS_SEPARATORS
    match_re = re.compile(match_regex) if match_regex else None
    filter_re = re.compile(filter_regex) if filter_regex else None
    seen: set[str] = set()

    def emit(sub: str) -> Optional[str]:
        fqdn = f"{sub}.{domain}"
        if fqdn in seen:
            return None
        seen.add(fqdn)
        if match_re and not match_re.search(fqdn):
            return None
        if filter_re and filter_re.search(fqdn):
            return None
        return fqdn

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


def load_templates_from_yaml(filepath: str) -> list[str]:
    """
    Carrega templates de subdomínios de um arquivo YAML.

    Formato esperado:
      templates:
        - "{{word}}-{{sub}}.{{domain}}"
        - "api-{{word}}.{{domain}}"
        - "dev.{{word}}.{{domain}}"

    Aceita tanto {word} quanto {{word}} como sintaxe de variável.

    Args:
        filepath: Caminho para o arquivo YAML.

    Returns:
        Lista de templates como strings.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ImportError: Se PyYAML não estiver instalado.
    """
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML é necessário para templates YAML. Instale: pip install pyyaml"
        ) from exc

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Template file não encontrado: {filepath}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    templates: list[str] = []
    if isinstance(data, dict):
        raw = data.get("templates", [])
    elif isinstance(data, list):
        raw = data
    else:
        raw = []

    for t in raw:
        if isinstance(t, str):
            # Normalizar {{word}} → {word} para usar com str.format
            normalized = t.replace("{{", "{").replace("}}", "}")
            templates.append(normalized)

    return templates


def generate_from_yaml_templates(
    templates: list[str],
    words: list[str],
    domain: str,
    match_regex: Optional[str] = None,
    filter_regex: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Gera subdomínios a partir de templates YAML com variáveis.

    Variáveis suportadas nos templates:
      {word}   → cada palavra da lista de entrada
      {domain} → domínio alvo
      {sub}    → alias para {word}

    Args:
        templates: Lista de templates (ex: ["api-{word}.{domain}"]).
        words: Lista de palavras base.
        domain: Domínio alvo.
        match_regex: Se definido, mantém apenas saídas que casem este regex.
        filter_regex: Se definido, descarta saídas que casem este regex.

    Yields:
        FQDNs gerados.
    """
    match_re = re.compile(match_regex) if match_regex else None
    filter_re = re.compile(filter_regex) if filter_regex else None
    seen: set[str] = set()

    for template in templates:
        for word in words:
            try:
                result = template.format(word=word, sub=word, domain=domain)
            except KeyError:
                result = template.replace("{word}", word).replace("{sub}", word).replace("{domain}", domain)

            if result in seen:
                continue
            seen.add(result)

            if match_re and not match_re.search(result):
                continue
            if filter_re and filter_re.search(result):
                continue

            yield result


def generate_multi_domain(
    domain_list_file: str,
    words: list[str],
    separators: Optional[list[str]] = None,
    use_prefixes: bool = True,
    use_suffixes: bool = True,
    match_regex: Optional[str] = None,
    filter_regex: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Processa múltiplos domínios de um arquivo e gera permutações para cada um.

    Args:
        domain_list_file: Arquivo com um domínio por linha.
        words: Lista de palavras base.
        separators: Separadores a usar entre tokens.
        use_prefixes: Se True, inclui prefixos comuns.
        use_suffixes: Se True, inclui sufixos comuns.
        match_regex: Regex de inclusão no output.
        filter_regex: Regex de exclusão no output.

    Yields:
        FQDNs gerados para todos os domínios.
    """
    match_re = re.compile(match_regex) if match_regex else None
    filter_re = re.compile(filter_regex) if filter_regex else None

    domains = load_words_from_file(domain_list_file)
    if not domains:
        logger.error("Nenhum domínio encontrado em: %s", domain_list_file)
        return

    for domain in domains:
        domain = domain.strip()
        if not domain or domain.startswith("#"):
            continue
        for entry in generate_subdomain_permutations(
            words, domain, separators, use_prefixes, use_suffixes
        ):
            if match_re and not match_re.search(entry):
                continue
            if filter_re and filter_re.search(entry):
                continue
            yield entry


def filter_dns_output(
    generator: Generator[str, None, None],
    match_regex: Optional[str] = None,
    filter_regex: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Aplica filtros de regex (match e exclusão) ao output de um gerador DNS.

    Args:
        generator: Gerador de FQDNs.
        match_regex: Regex de inclusão — mantém apenas linhas que casem.
        filter_regex: Regex de exclusão — descarta linhas que casem.

    Yields:
        FQDNs filtrados.
    """
    match_re = re.compile(match_regex) if match_regex else None
    filter_re = re.compile(filter_regex) if filter_regex else None

    for entry in generator:
        if match_re and not match_re.search(entry):
            continue
        if filter_re and filter_re.search(entry):
            continue
        yield entry
