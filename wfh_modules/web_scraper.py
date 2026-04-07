"""
web_scraper.py — Spider web para extração de palavras (estilo CeWL + CeWLeR).

Funcionalidades:
  - Spider de URL com controle de profundidade
  - Extração de palavras únicas com filtro de comprimento
  - Extração de emails e metadados (Author, Generator)
  - Suporte a proxy HTTP/SOCKS (--proxy)
  - Suporte a cookies, User-Agent customizável e headers adicionais
  - Autenticação HTTP básica
  - Exclusão de stop-words (EN/PT-BR) via --no-stopwords ou arquivo customizado
  - Output streaming para arquivo ou stdout

Exemplos:
  wfh.py scrape https://empresa.com.br
  wfh.py scrape https://empresa.com.br -d 2 --min-word 6 --emails --meta
  wfh.py scrape https://empresa.com.br --auth usuario:senha
  wfh.py scrape https://empresa.com.br --proxy http://127.0.0.1:8080
  wfh.py scrape https://empresa.com.br --no-stopwords
  wfh.py scrape https://empresa.com.br --user-agent "Mozilla/5.0 (custom)"
  wfh.py scrape https://empresa.com.br --header "X-Api-Key: abc123"

Autor: André Henrique (@mrhenrike)
Versão: 1.1.0
"""

import logging
import re
import time
from collections import deque
from typing import Generator, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False
    logger.warning("requests e beautifulsoup4 não instalados. web_scraper desativado.")


# Padrão para extração de palavras (sem números puros)
_WORD_RE = re.compile(r"[a-zA-ZÀ-ÿ\u0100-\u024F][a-zA-ZÀ-ÿ\u0100-\u024F'-]*[a-zA-ZÀ-ÿ\u0100-\u024F]")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_META_FIELDS = ["author", "generator", "description", "keywords", "creator"]

# Stop-words padrão EN + PT-BR (fusão para uso offline, sem dependências externas)
DEFAULT_STOPWORDS: frozenset[str] = frozenset({
    # EN
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "had", "has", "his", "how", "its", "who",
    "did", "get", "may", "new", "now", "old", "see", "two", "way", "use",
    "she", "each", "from", "have", "that", "this", "they", "will", "with",
    "your", "more", "also", "into", "than", "then", "them", "some", "what",
    "when", "been", "only", "over", "such", "most", "make", "like", "time",
    "just", "very", "well", "even", "know", "said", "back", "after", "first",
    "last", "long", "place", "come", "about", "could", "would", "should",
    "there", "their", "where", "which", "while", "think", "these", "other",
    "people", "those", "being", "because", "between", "before", "through",
    # PT-BR
    "que", "não", "com", "uma", "para", "por", "como", "mas", "foi", "isso",
    "ele", "ela", "são", "nas", "nos", "seu", "sua", "esse", "essa", "isto",
    "nós", "eles", "elas", "dos", "das", "num", "uma", "uns", "umas", "mais",
    "também", "ser", "ter", "tem", "era", "foi", "ser", "está", "este",
    "esta", "isso", "aqui", "ali", "bem", "sim", "não", "já", "ainda",
    "mesmo", "muito", "pouco", "todo", "toda", "todos", "todas", "outro",
    "outra", "outros", "outras", "quando", "onde", "porque", "como", "assim",
    "então", "depois", "antes", "agora", "sempre", "nunca", "até", "sobre",
})


class WebScraper:
    """
    Spider de URL com extração de palavras, emails e metadados.

    Atributos:
        start_url: URL inicial de crawl.
        depth: Profundidade máxima de seguimento de links.
        min_word_len: Comprimento mínimo de palavra a extrair.
        max_word_len: Comprimento máximo de palavra a extrair.
        extract_emails: Se True, extrai emails.
        extract_meta: Se True, extrai metadados Author/Generator.
        user_agent: User-Agent HTTP.
        delay: Delay em segundos entre requisições.
        timeout: Timeout HTTP em segundos.
        auth: Tupla (usuario, senha) para HTTP Basic Auth.
        proxy: URL do proxy HTTP/SOCKS (ex: 'http://127.0.0.1:8080').
        extra_headers: Headers HTTP adicionais.
        stopwords: Set de palavras a excluir do resultado.
    """

    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        start_url: str,
        depth: int = 2,
        min_word_len: int = 6,
        max_word_len: int = 32,
        extract_emails: bool = False,
        extract_meta: bool = False,
        user_agent: Optional[str] = None,
        delay: float = 0.5,
        timeout: int = 10,
        auth: Optional[tuple[str, str]] = None,
        cookies: Optional[dict] = None,
        proxy: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
        stopwords: Optional[frozenset[str]] = None,
        with_numbers: bool = False,
        with_spaces: bool = False,
        capture_paths: bool = False,
        capture_subdomains: bool = False,
    ) -> None:
        self.start_url = start_url
        self.depth = depth
        self.min_word_len = min_word_len
        self.max_word_len = max_word_len
        self.extract_emails = extract_emails
        self.extract_meta = extract_meta
        self.delay = delay
        self.timeout = timeout
        self.stopwords: frozenset[str] = stopwords if stopwords is not None else frozenset()
        self.with_numbers = with_numbers
        self.with_spaces = with_spaces
        self.capture_paths = capture_paths
        self.capture_subdomains = capture_subdomains

        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self._parsed_start = parsed

        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent or self.DEFAULT_UA
        if extra_headers:
            self.session.headers.update(extra_headers)
        if auth:
            self.session.auth = auth
        if cookies:
            self.session.cookies.update(cookies)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _fetch(self, url: str) -> Optional[str]:
        """
        Baixa o HTML de uma URL.

        Args:
            url: URL a baixar.

        Returns:
            HTML como string ou None em caso de erro.
        """
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            # Forçar UTF-8 se charset não declarado, evitando UnicodeDecodeError
            if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1", "windows-1252"):
                resp.encoding = "utf-8"
            return resp.content.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.debug("Erro ao acessar %s: %s", url, exc)
            return None

    def _extract_words(self, html: str, url: str = "") -> set[str]:
        """
        Extrai palavras únicas de um HTML.

        Args:
            html: Conteúdo HTML.
            url: Source URL for path/subdomain extraction.

        Returns:
            Set de palavras extraídas.
        """
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        words: set[str] = set()

        for match in _WORD_RE.finditer(text):
            word = match.group()
            if self.min_word_len <= len(word) <= self.max_word_len:
                if word.lower() not in self.stopwords:
                    words.add(word)

        if self.with_numbers:
            _NUM_WORD_RE = re.compile(r"[a-zA-Z0-9À-ÿ][a-zA-Z0-9À-ÿ'-]+")
            for match in _NUM_WORD_RE.finditer(text):
                word = match.group()
                if self.min_word_len <= len(word) <= self.max_word_len:
                    if word.lower() not in self.stopwords:
                        words.add(word)

        if self.with_spaces:
            _PHRASE_RE = re.compile(r"[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s'-]{4,60}")
            for match in _PHRASE_RE.finditer(text):
                phrase = match.group().strip()
                if " " in phrase and self.min_word_len <= len(phrase) <= self.max_word_len:
                    words.add(phrase)

        if url and self.capture_paths:
            parsed = urlparse(url)
            segments = [s for s in parsed.path.split("/") if s and len(s) >= 2]
            for seg in segments:
                clean = re.sub(r"[^a-zA-Z0-9_-]", "", seg)
                if clean and len(clean) >= self.min_word_len:
                    words.add(clean)

        if url and self.capture_subdomains:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            labels = hostname.split(".")
            for label in labels[:-2]:
                if label and len(label) >= 2:
                    words.add(label)

        return words

    def _extract_emails(self, html: str) -> set[str]:
        """
        Extrai emails únicos de um HTML.

        Args:
            html: Conteúdo HTML.

        Returns:
            Set de emails encontrados.
        """
        return set(_EMAIL_RE.findall(html))

    def _extract_meta(self, html: str) -> set[str]:
        """
        Extrai valores de metadados (Author, Generator, Keywords).

        Args:
            html: Conteúdo HTML.

        Returns:
            Set de palavras extraídas de metadados.
        """
        soup = BeautifulSoup(html, "lxml")
        values: set[str] = set()
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = meta.get("content") or ""
            if name in _META_FIELDS and content:
                for match in _WORD_RE.finditer(content):
                    word = match.group()
                    if self.min_word_len <= len(word) <= self.max_word_len:
                        values.add(word)
        return values

    def _extract_links(self, html: str, current_url: str) -> list[str]:
        """
        Extrai links internos de uma página.

        Args:
            html: Conteúdo HTML.
            current_url: URL atual para resolução de URLs relativas.

        Returns:
            Lista de URLs internas únicas.
        """
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(current_url, href)
            if full.startswith(self.base_domain):
                clean = full.split("#")[0].split("?")[0]
                links.append(clean)
        return list(set(links))

    def crawl(self) -> Generator[str, None, None]:
        """
        Executa o crawl e gera palavras/emails/metadados extraídos.

        Yields:
            Strings únicas extraídas do site.
        """
        if not _DEPS_OK:
            logger.error("Instale: pip install requests beautifulsoup4 lxml")
            return

        visited: set[str] = set()
        all_words: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(self.start_url, 0)])

        while queue:
            url, current_depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            logger.info("Crawling [depth=%d]: %s", current_depth, url)
            html = self._fetch(url)
            if not html:
                continue

            words = self._extract_words(html, url=url)
            new_words = words - all_words
            all_words |= words

            for word in sorted(new_words):
                yield word

            if self.extract_emails:
                for email in self._extract_emails(html):
                    if email not in all_words:
                        all_words.add(email)
                        yield email

            if self.extract_meta:
                for meta_word in self._extract_meta(html):
                    if meta_word not in all_words:
                        all_words.add(meta_word)
                        yield meta_word

            if current_depth < self.depth:
                for link in self._extract_links(html, url):
                    if link not in visited:
                        queue.append((link, current_depth + 1))

            if self.delay > 0:
                time.sleep(self.delay)
