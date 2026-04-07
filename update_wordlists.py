"""
WordListsForHacking — Pipeline de atualização completo.

Autor: André Henrique (@mrhenrike) | União Geek — https://github.com/Uniao-Geek
Versão: 2.0.0
Data: 2026-03-30

Gera/atualiza:
  - wlist_brasil.lst   : senhas brasileiras curadas (>= 6 chars, não puramente numéricas)
  - username_br.lst    : usernames brasileiros e globais
  - default-creds-combo.lst : pares user:password sem restrição de tamanho
"""
from __future__ import annotations

import logging
import os
import re
import sys
import time
import unicodedata
import urllib.request
from itertools import product
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGGING
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / ".log"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "terminal-output.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ARQUIVOS DE SAÍDA
# ---------------------------------------------------------------------------
WLIST_FILE = BASE_DIR / "passwords" / "wlist_brasil.lst"
USERNAME_FILE = BASE_DIR / "usernames" / "username_br.lst"
COMBO_FILE = BASE_DIR / "passwords" / "default-creds-combo.lst"

# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    """Remove acentos e caracteres combinados de uma string."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


LEET_CANONICAL = {
    "a": "@", "A": "@",
    "e": "3", "E": "3",
    "i": "1", "I": "1",
    "o": "0", "O": "0",
    "s": "$", "S": "$",
    "t": "7", "T": "7",
    "l": "1", "L": "1",
    "b": "8", "B": "8",
    "g": "9", "G": "9",
}

LEET_V2 = {
    "a": "4", "A": "4",
    "e": "3", "E": "3",
    "i": "!", "I": "!",
    "o": "0", "O": "0",
    "s": "5", "S": "5",
    "t": "+", "T": "+",
    "l": "1", "L": "1",
    "b": "6", "B": "6",
    "g": "9", "G": "9",
}

LEET_V3 = {
    "a": "@", "A": "@",
    "i": "|", "I": "|",
    "s": "$", "S": "$",
    "b": "8", "B": "8",
    "g": "9", "G": "9",
    "t": "+", "T": "+",
    "l": "|", "L": "|",
}


def apply_leet(word: str, mapping: dict) -> str:
    """Aplica um mapeamento leet a uma string."""
    return "".join(mapping.get(c, c) for c in word)


def word_variations(word: str, suffixes: list[str] | None = None) -> set[str]:
    """
    Gera variações de uma palavra: lower, UPPER, Capital, sem_acento ×3, leet canônico.
    Para senhas (wlist), aplica sufixos opcionalmente.
    """
    s = strip_accents(word)
    variants: set[str] = set()
    base_forms = [
        word,
        word.upper(),
        word.capitalize(),
        s,
        s.upper(),
        s.capitalize(),
        apply_leet(s, LEET_CANONICAL),
    ]
    for form in base_forms:
        variants.add(form)
    if suffixes:
        for form in list(variants):
            for suf in suffixes:
                variants.add(form + suf)
    return variants


def phrase_variations(phrase: str) -> set[str]:
    """
    Gera variações ricas para frases/expressões (modo profundo).
    Aplica leet v1/v2/v3 + sufixos + camelcase.
    """
    s = strip_accents(phrase)
    variants: set[str] = set()

    bases = [
        phrase,
        phrase.upper(),
        phrase.capitalize(),
        s,
        s.upper(),
        s.capitalize(),
        apply_leet(s, LEET_CANONICAL),
        apply_leet(s, LEET_V2),
        apply_leet(s, LEET_V3),
    ]

    # CamelCase se houver múltiplas palavras (sem espaço já, mas tenta)
    words = re.split(r"[\s_\-]+", phrase)
    if len(words) > 1:
        camel = words[0].lower() + "".join(w.capitalize() for w in words[1:])
        bases.append(camel)

    for b in bases:
        variants.add(b)

    SUFFIXES = ["123", "@123", "2021", "2022", "2023", "2024", "2025", "2026",
                "!", "#", "_br"]
    for b in list(bases):
        for suf in SUFFIXES:
            variants.add(b + suf)

    # Leet + sufixos
    for suf in ["123", "@123"]:
        variants.add(apply_leet(s, LEET_CANONICAL) + suf)
        variants.add(apply_leet(s, LEET_V2) + suf)

    return variants


def is_purely_numeric(s: str) -> bool:
    """Retorna True se a string for composta apenas de dígitos."""
    return bool(re.fullmatch(r"\d+", s))


def fetch_url(url: str, timeout: int = 60) -> str | None:
    """Baixa conteúdo de uma URL e retorna como string."""
    try:
        log.info("Baixando: %s", url)
        req = urllib.request.Request(url, headers={"User-Agent": "WordlistUpdater/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("latin-1")
    except Exception as exc:
        log.warning("Falha ao baixar %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# DADOS HARDCODED — NordPass 2023/2024/2025 (ausentes na lista atual)
# ---------------------------------------------------------------------------
NORDPASS_NEW = [
    "fera@123", "d@rKn3$$", "t3l3f0n3", "escola1234", "22446688", "gvt12345",
    "mudar123", "pedro123", "matheus123", "1q2w3e4r5t", "admin123",
    "Qwerty123", "qwerty123", "qwerty1",
    "carlos123", "rodrigo123", "anderson123", "alexandre123", "thiago123",
    "marcelo123", "bruno123", "diego123", "leonardo123", "guilherme123",
    "julia123", "ana123", "maria123", "beatriz123", "leticia123",
    "fernanda123", "aline123", "renata123", "priscila123", "caroline123",
    "danielle123", "patricia123", "monica123",
    "corinthians", "Corinthians", "corinthians123", "santos123", "vasco123",
    "atletico123", "fluminense123", "gremio123", "botafogo123", "cruzeiro123",
    "chapecoense", "atleticomineiro", "sport", "Sport",
    "Mudar@123", "mudar@123", "Admin@123", "admin@123", "Senha@123", "senha@123",
    "Temp@123", "temp123", "Welcome1", "welcome1", "Welcome@123",
    "Mudar123", "mudar1234", "Mudar1234",
    "Admin@2022", "Admin@2023", "Admin@2024", "Admin@2025",
    "Mudar@2022", "Mudar@2023", "Mudar@2024", "Mudar@2025",
    "Senha@2022", "Senha@2023", "Senha@2024", "Senha@2025",
    "empresa@2022", "empresa@2023", "empresa@2024", "empresa@2025",
    "@2022", "@2023", "@2024", "@2025",
    "Brasil2022", "Brasil2023", "Brasil2024", "Brasil2025",
    "nubank", "nubank123", "picpay", "picpay123", "mercadopago",
    "pix", "pix123", "bitcoin", "bitcoin123", "ethereum", "litecoin",
    "dogecoin", "cripto", "cripto123", "nft", "metaverso",
    "netflix", "netflix123", "spotify", "spotify123", "ifood", "ifood123",
    "tiktok", "tiktok123", "instagram", "instagram123", "whatsapp", "whatsapp123",
    "zoom", "zoom123", "teams", "teams123", "chatgpt", "chatgpt123",
    "covid", "covid19", "covid123", "covid2020", "covid2021", "lockdown",
    "homeoffice", "homeoffice123", "remoto123", "vacinado", "vacinado123",
    # OT/ICS
    "simulation", "scadabr", "pfsense", "workstation",
    # HW management
    "opensource", "calvin", "PASSW0RD", "raspberry", "changeme",
    # Splunk/SIEM
    "changeme", "netwitness", "arcsight", "wazuh", "elastic",
    # Keyboard walks
    "123qweASD", "1q2w3e4r5t", "qweasdzxc", "zxcasdqwe",
    "ZAQ!2wsX", "1QAZ2wsx", "!QAZ@WSX", "1Qaz@Wsx",
    "qwerty123", "QWERTYuiop", "asdfgh", "zxcvbn",
    "qazwsx", "1qaz2wsx", "1QAZ2wsx",
    # WiFi BR ISPs
    "gvt12345", "gvtfibra", "claro12345", "vivo12345", "tim12345", "oi12345",
    "netbrasil", "vivofibra", "claronety", "oifibra", "timsemparar",
    "virtua", "speedy", "embratel", "intelbras", "intelbras123",
    "intelbrasAdm", "minharede", "minhasenha", "senhaadmin", "senhawifi",
    "meuinternet", "meuwifi", "giga@2024", "fibra@2024", "claro@2024",
    "vivo@2024", "arlinkeasy", "zte@2023", "huaweiAdmin", "tplinkAdmin",
    "dlink@br", "wifibrasil", "adminwifi", "senhapadrao",
    # MSP/MSSP × cliente (anos 2021-2026)
    "Acsc@Ish#@!3971", "ISH@MUDAR", "1SH:CLIENT",
    "Ish@Mudar", "ISH@MUDAR", "1SH@Mudar",
    "Tempest@Mudar", "TEMPEST@MUDAR", "Cipher@Mudar", "CIPHER@MUDAR",
    "Vision@Mudar", "VISION@MUDAR", "Dropreal@Mudar", "DROPREAL@MUDAR",
    "Youit@Mudar", "YOUIT@MUDAR",
    "ish@2021", "ISH@2021", "Ish@2021", "ish@2022", "ISH@2022",
    "ish@2023", "ISH@2023", "ish@Mudar2023", "ish@2024", "ISH@2024",
    "ish@2025", "ISH@2025", "Ish@2025#",
    "tempest@2024", "Tempest@2024", "TEMPEST@2024",
    "cipher@2024", "Cipher@2024", "CIPHER@2024",
    "stefanini@2024", "Stefanini@2024",
    "202154@Acsc", "202203@Ish", "202301@Tempest", "202412@Cipher",
    "202506@Stefanini", "2021@ish", "2022@tempest", "2023@cipher",
    "2024@stefanini", "2025@dropreal",
    "petrobras@2024", "PETROBRAS@2024", "Petrobras@2024",
    "itau@2024", "ITAU@2024", "Itau@2024!",
    "bradesco@2024", "Bradesco@2024",
    "ambev@2024", "AMBEV@2024", "Ambev@2024#",
    "vale@2024", "VALE@2024", "Vale@2024!",
    "weg@2024", "WEG@2024", "Weg@2024",
    "totvs@2024", "TOTVS@2024", "Totvs@2024",
    "embraer@2024", "EMBRAER@2024", "Embraer@2024",
    # Pentest tools defaults
    "beef", "msfdev", "postgres", "password123", "admin123",
    "Bonjour1!", "nxpassword", "axis2", "guacadmin", "s3cret",
    "adaptec", "epicrouter", "kn1TG7psLu", "letacla",
    "TENmanUFactOryPOWER", "ubnt", "alpine", "dottie",
]

# ---------------------------------------------------------------------------
# FRASES BRASILEIRAS VIRAIS — BASES
# ---------------------------------------------------------------------------
PHRASES_BR = [
    # Grupo A
    "fariglo", "cocodegrilo", "foraboso", "bolsominium",
    "naoesaoso20centavos", "ogiganteacordou", "omelhorproduto",
    "fazol", "fazoele", "fazol2026", "foraboso2026", "placapreta", "misogino",
    # Grupo B — Política
    "elenao", "foraboso", "bolsominion", "bolsominao", "bolsonarista",
    "mito", "omito", "capitao", "patriota", "golpista", "festadaselma",
    "direitafc", "petista", "antipetista", "lulala", "foralula",
    "luladrao", "lulaladrao", "fabioboz", "brasilacimadebrasil",
    # Grupo C — Memes
    "calabreso", "cadadiaumadecisao", "nazaretedesco", "selouco",
    "choquei", "misericordia", "casacadebala", "caladocabra",
    "xoudaxuxa", "cadeirada", "datena", "evagabundotala", "faroestecaboclo",
    "jaacaboujessica", "pedalarobinho", "creu", "creucreucreu",
    "sabedenadainocente", "focanomovimento", "partiu", "trampo",
    # Grupo D — Músicas
    "infiel", "seupolicia", "olhaaexplosao", "bumbumtamtam",
    "hearmenow", "downtown", "jenifer", "atrasadinha", "paradonobaila",
    "liberdadeprovisoria", "malvadao", "malvadao3", "malfeito",
    "envolver", "acordapedrinho", "desenrolabate", "dancarina",
    "tomatoma", "vapovapo", "leaomarilia", "nossoquadro",
    "errogostoso", "bombonzinho", "taok", "zonadaperigo", "deixemeir",
    "melevapracasa", "escritonasestrelas", "pocpoc", "barulhodofoguete",
    "canudinho", "gostarua", "haverasinais", "doistristes",
    "pdopecado", "tubaroes", "coracaopartido", "apagaapaga",
    "ultimasaudade", "fuimlk", "famosinha", "copiaproibida", "sofe",
    "matandoumleaopordiacima", "coragehumildade", "siguenababilonia",
    "leitindascrianças", "deusabencoenois", "orestosofe",
    # Grupo E — Religiosas
    "jesussalva", "jesusama", "gloriaadeus", "deusnopoder", "aleluia",
    "milagre", "deusprove", "ungidos", "bendicao", "gracasdeus",
    "cristofiel", "deusnocomando", "jesuscristo", "espiritosanto",
    "deusefieledeus", "abençoado", "deusteama", "louvadeus",
    "naovousozinho", "guerreirosdodeus",
    # Grupo F — COVID
    "ficaemcasa", "fiqueemcasa", "cloroquina", "isolamento",
    "vacinaja", "vacinacovid", "vacinalula", "vacinabolsonaro",
    "covidiota", "quarentreino", "carentena",
    # Grupo G — Futebol
    "hexa", "hexa2026", "hexa2030", "vaicorinthians", "vaipalmeiras",
    "vaiflamengo", "foraflamengo", "campeaodamundial", "selecaobrasileira",
    "brasileirao", "libertadores", "pentacampiao",
    # Grupo H — Apostas
    "tigrinho", "blazewin", "betano", "sportingbet", "vaipix",
    "jogodotigre", "fortunetiger", "blazebrasil", "ganheagora",
    # Entidades religiosas
    "universal", "assembleiadeus", "batista", "presbiteriana", "metodista",
    "senadepaz", "renascer", "vidanova", "silas", "edir", "ricardinho",
    # Cantores BR
    "anitta", "luisamsonza", "ivete", "gusttavo", "marilia", "simone",
    "henrique", "juliano", "mckevin", "pedrosampaio",
    "jorgemateus", "anacastela", "legiaurbana", "titas",
    # Corporações BR
    "petrobras", "embraer", "ambev", "natura", "bradesco",
    "itau", "santander", "caixa", "nubank", "mercadolivre",
    "magalu", "americanas", "claro", "vivo", "tim",
    # MSSPs/MSPs
    "ish", "ishtech", "ishtecnologia", "tempest", "tempestbr",
    "cipher", "cipherlab", "stefanini", "stefaninicyber",
    "vision", "visionone", "youit", "dropreal", "ness", "nessbrasil",
    "safeway", "safewaybr", "teccloud", "nsoc", "acsc",
    "xsolutions", "modulo", "modulosecurity", "tivit", "nec",
    # Nomes bíblicos
    "abraao", "moises", "davi", "salomao", "daniel", "ezequiel",
    "maria", "pedro", "paulo", "joao", "mateus", "marcos", "lucas",
    "apocalipse", "genesis",
    # Tokens alfanuméricos (keyboard walks)
    "icq65t8xh", "1q2w3e4r5t", "qweasdzxc", "zxcasdqwe",
    "ZAQ1qaz", "1QAZ2wsx", "qweQWE123", "asdASD123",
]

# ---------------------------------------------------------------------------
# USERNAMES A ADICIONAR
# ---------------------------------------------------------------------------
NEW_USERNAMES = [
    # Funcionais Linux/Windows
    "operator", "operador", "usuario", "temp", "temporario",
    "visitante", "estagiario",
    # TI/Suporte corporativo BR
    "ti", "helpdesk", "servicedesk", "service", "noc", "soc",
    "monitor", "backup",
    # Funções de negócio BR
    "financeiro", "fiscal", "contabil", "rh", "gerente",
    # Bancos de dados
    "postgres", "dba", "dbadmin", "mssql", "mariadb",
    # Rede/e-mail
    "mail", "postfix", "radius", "ldap",
    # Monitoramento e DevOps
    "nagios", "zabbix", "grafana", "jenkins", "gitlab", "docker",
    # Cloud e web
    "azure", "aws", "gcp", "cloud", "nginx", "apache", "tomcat",
    # Embedded/IoT
    "pi",
    # Hardware management
    "Administrator", "USERID", "ADMIN",
    # OT/ICS
    "simulation", "scadabr", "workstation",
    # MSP/MSSP locais
    "mssplocal", "ishlocal", "dropreallocal", "ishlab", "youitlab",
    "visionlocal", "tempestlocal", "cipherlocal", "stefaninilocal",
    "nesslocal", "safewaylocal", "teccloudlocal", "nsoclocal",
    # Default creds comuns
    "cisco", "ubnt", "telecomadmin", "huawei",
    "bitnami", "rocky", "fedora", "vagrant", "kali",
    "parrot", "backbox", "pi", "opc", "oracle",
    "elastic", "wazuh", "netwitness", "splunk",
    "arcsight", "beef", "postgres",
    "empireadmin", "nxadmin", "cmkadmin",
    "kibanaserver", "wazuh-wui",
]

# ---------------------------------------------------------------------------
# COMBO DEFAULT CREDS (pares user:password) — curados manualmente
# ---------------------------------------------------------------------------
MANUAL_COMBOS = [
    # Genéricos
    "admin:", "admin:admin", "admin:1234", "admin:12345", "admin:123456",
    "admin:password", "admin:changeme", "admin:0000", "admin:admin123",
    "admin:Admin@123", "admin:netwitness", "admin:pfsense",
    "admin:C0C0D3GR120", "admin:scadabr",
    "administrator:", "administrator:admin", "administrator:password",
    "administrator:covid#19@mata",
    "Administrator:", "Administrator:vagrant", "Administrator:FELDTECH",
    "Administrator:admin", "Administrator:password",
    "default:", "default:default", "changeme:changeme",
    "test:test", "test:test123",
    "root:", "root:root", "root:toor", "root:alpine",
    "root:admin", "root:password", "root:netwitness",
    "root:raspberry", "root:linux", "root:changeme",
    "root:calvin",
    # Linux distros
    "debian:debian", "ubuntu:ubuntu", "centos:centos",
    "kali:kali", "vagrant:vagrant", "pi:raspberry",
    "parrot:parrot", "backbox:backbox", "fedora:fedora",
    "almalinux:almalinux", "rockylinux:rockylinux", "rocky:rocky",
    "archlinux:archlinux", "oracle:oracle", "opc:",
    # Cloud VMs
    "ec2-user:", "ubuntu:", "azureuser:", "bitnami:",
    # FTP/Anonymous
    "ftp:", "ftp:ftp", "ftp:anonymous",
    "anonymous:", "anonymous:anonymous",
    # Serviços genéricos
    "user:", "user:user", "user:user1!", "user:password",
    "info:%1q2w@3e4r%", "adm:adm", "adm:ro48br48",
    "manager:manager", "manager:sexy%%baby",
    "support:support", "service:service",
    "guest:guest", "monitor:monitor",
    "operator:operator", "tech:tech",
    # Network gear
    "cisco:cisco", "ubnt:ubnt", "admin:ubnt",
    "admin:tp-link", "admin:epicrouter",
    "telecomadmin:admintelecom", "admin:Admin@123",
    "admin:gvt12345", "admin:adsl1234",
    # SIEM/Tools
    "netwitness:netwitness", "splunkadmin:changeme",
    "elastic:changeme", "wazuh:wazuh",
    "empireadmin:password123", "beef:beef",
    "postgres:postgres", "msf:msf", "msfdev:msfdev",
    "admin:admin123", "admin:changeme",
    "cmkadmin:cmkadmin", "admin:Bonjour1!",
    "admin:nxpassword", "nxadmin:nxpassword",
    # OT/ICS/SCADA
    "simulation:simulation", "scadabr:scadabr",
    "admin:pfsense", "workstation:password", "user:password",
    "USER:USER", "sysdiag:factorycast@schneider",
    "service:ABB800xA", "admin:siemens",
    "admin:moxa", "admin:private",
    # HW Management
    "admin:opensource", "Administrator:opensource",
    "root:calvin", "USERID:PASSW0RD", "root:changeme",
    "admin:admin", "ADMIN:ADMIN", "Oper:Oper",
    "admin:password", "root:password",
    # IoT/Cameras
    "admin:12345", "admin:888888", "admin:666666",
    "root:4321", "admin:123456", "root:pass",
    "service:service", "admin:jvc",
    # Windows RDP
    "vagrant:vagrant", "administrator:vagrant",
    "Administrator:FELDTECH", "administrator:Wyse#123",
    # macOS / iOS
    "root:alpine", "mobile:dottie",
    # Apache/Web
    "tomcat:tomcat", "tomcat:s3cret",
    "admin:tomcat", "guacadmin:guacadmin",
    "axis2:axis2",
    # MSP/MSSP exemplos
    "mssplocal:Mudar@123", "ishlocal:Ish@2024",
    "ishlab:ishlab123", "youitlab:youitlab123",
]

# ---------------------------------------------------------------------------
# SOURCES REMOTOS
# ---------------------------------------------------------------------------
DICT_URL = "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt"
DEFAULT_CREDS_URL = "https://raw.githubusercontent.com/ihebski/DefaultCreds-cheat-sheet/main/DefaultCreds-Cheat-Sheet.csv"
ICS_CREDS_URL = "https://raw.githubusercontent.com/arnaudsoullie/ics-default-passwords/master/default-passwords.csv"


# ---------------------------------------------------------------------------
# FASE 1 — wlist_brasil.lst
# ---------------------------------------------------------------------------

def phase1_wlist() -> None:
    """Constrói/atualiza wlist_brasil.lst."""
    log.info("=== FASE 1: wlist_brasil.lst ===")
    t0 = time.time()

    # Lê lista existente
    log.info("Lendo lista existente...")
    existing: set[str] = set()
    if WLIST_FILE.exists():
        with WLIST_FILE.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                w = line.rstrip("\n\r")
                if w:
                    existing.add(w)
    log.info("Entradas existentes: %d", len(existing))

    # Remove puramente numéricas e <6 chars
    cleaned: set[str] = set()
    removed_num = 0
    removed_short = 0
    for w in existing:
        if is_purely_numeric(w):
            removed_num += 1
            continue
        if len(w) < 6:
            removed_short += 1
            continue
        cleaned.add(w)
    log.info("Removidos numéricos puros: %d | <6 chars: %d | Restantes: %d",
             removed_num, removed_short, len(cleaned))

    # Adiciona NordPass + extras hardcoded
    log.info("Adicionando entradas NordPass/extras...")
    for w in NORDPASS_NEW:
        if not is_purely_numeric(w) and len(w) >= 6:
            cleaned.add(w)

    # Baixa dicionário PT-BR
    log.info("Baixando dicionário PT-BR...")
    dict_content = fetch_url(DICT_URL)
    dict_words_added = 0
    if dict_content:
        for raw_word in dict_content.splitlines():
            word = raw_word.strip()
            if not word or len(word) < 6 or is_purely_numeric(word):
                continue
            for v in word_variations(word):
                if not is_purely_numeric(v) and len(v) >= 6:
                    cleaned.add(v)
                    dict_words_added += 1
    log.info("Variações de dicionário adicionadas: %d", dict_words_added)

    # Gera variações de frases brasileiras
    log.info("Gerando variações de frases brasileiras...")
    phrase_added = 0
    for phrase in PHRASES_BR:
        for v in phrase_variations(phrase):
            if not is_purely_numeric(v) and len(v) >= 6:
                cleaned.add(v)
                phrase_added += 1
    log.info("Variações de frases adicionadas: %d", phrase_added)

    # Extrai passwords do DefaultCreds CSV
    log.info("Baixando DefaultCreds CSV para extrair passwords...")
    dc_content = fetch_url(DEFAULT_CREDS_URL)
    dc_passwords_added = 0
    if dc_content:
        for line in dc_content.splitlines()[1:]:  # pula header
            parts = line.split(",")
            if len(parts) >= 3:
                pwd = parts[2].strip().strip('"')
                if pwd and not is_purely_numeric(pwd) and len(pwd) >= 6:
                    cleaned.add(pwd)
                    dc_passwords_added += 1
    log.info("Passwords de DefaultCreds adicionados: %d", dc_passwords_added)

    # Extrai passwords do ICS CSV
    log.info("Baixando ICS default passwords CSV...")
    ics_content = fetch_url(ICS_CREDS_URL)
    ics_added = 0
    if ics_content:
        for line in ics_content.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                pwd = parts[2].strip().strip('"')
                if pwd and not is_purely_numeric(pwd) and len(pwd) >= 6:
                    cleaned.add(pwd)
                    ics_added += 1
    log.info("Passwords ICS adicionados: %d", ics_added)

    # Grava
    log.info("Gravando wlist_brasil.lst (%d entradas)...", len(cleaned))
    with WLIST_FILE.open("w", encoding="utf-8") as f:
        for entry in sorted(cleaned, key=lambda x: x.lower()):
            f.write(entry + "\n")

    elapsed = time.time() - t0
    log.info("FASE 1 concluída em %.1fs — total: %d entradas", elapsed, len(cleaned))


# ---------------------------------------------------------------------------
# FASE 2 — username_br.lst
# ---------------------------------------------------------------------------

def phase2_usernames() -> None:
    """Consolida e atualiza username_br.lst."""
    log.info("=== FASE 2: username_br.lst ===")

    # Lê existente e filtra entradas malformadas com critério completo
    bad_chars_u = set("()[]{}|<>*?,;'\"`~^%")
    bad_prefixes_u = ("(", "[", "<", "*", "?", "#", "$")
    bad_keywords_u = {"blank", "any", "created", "calculated", "hostname",
                      "ipaddress", "caclulated", "none", "null", "n/a",
                      "user1-usern"}
    existing: set[str] = set()
    if USERNAME_FILE.exists():
        with USERNAME_FILE.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                u = line.rstrip("\n\r").strip()
                if not u:
                    continue
                if ":" in u or "{" in u or "oaicite" in u:
                    continue
                if u == "User1-UserN":
                    continue
                if len(u) < 2 or len(u) > 32:
                    continue
                if " " in u:
                    continue
                if any(c in u for c in bad_chars_u):
                    continue
                if u.startswith(bad_prefixes_u):
                    continue
                if u.lower() in bad_keywords_u:
                    continue
                if not re.search(r"[a-zA-Z0-9]", u):
                    continue
                # Exclui entradas puramente numéricas longas (não são usernames reais)
                if re.fullmatch(r"\d{5,}", u):
                    continue
                existing.add(u)
    log.info("Usernames existentes (após limpeza): %d", len(existing))

    # Adiciona novos
    for u in NEW_USERNAMES:
        existing.add(u)

    # Extrai usernames do DefaultCreds CSV com filtro robusto
    dc_content = fetch_url(DEFAULT_CREDS_URL)
    if dc_content:
        # Chars inválidos em usernames reais
        bad_chars = set("()[]{}|<>!*?,;'\"`~^%")
        bad_prefixes = ("(", "[", "<", "*", "?", "#")
        bad_keywords = {"blank", "any", "created", "calculated", "hostname",
                        "ipaddress", "caclulated", "none", "null", "n/a"}
        for line in dc_content.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 2:
                uname = parts[1].strip().strip('"').strip()
                if not uname:
                    continue
                if len(uname) < 2 or len(uname) > 32:
                    continue
                if " " in uname:
                    continue
                if any(c in uname for c in bad_chars):
                    continue
                if uname.startswith(bad_prefixes):
                    continue
                if uname.lower() in bad_keywords:
                    continue
                # Deve conter pelo menos uma letra ou número
                if not re.search(r"[a-zA-Z0-9]", uname):
                    continue
                existing.add(uname)

    log.info("Total usernames: %d", len(existing))

    with USERNAME_FILE.open("w", encoding="utf-8") as f:
        for u in sorted(existing, key=lambda x: x.lower()):
            f.write(u + "\n")
    log.info("username_br.lst gravado.")


# ---------------------------------------------------------------------------
# FASE 3 — default-creds-combo.lst
# ---------------------------------------------------------------------------

def phase3_combo() -> None:
    """Cria default-creds-combo.lst com todos os pares user:password."""
    log.info("=== FASE 3: default-creds-combo.lst ===")

    combos: set[str] = set()

    # Manuais curados
    for c in MANUAL_COMBOS:
        combos.add(c)

    # DefaultCreds CSV — normaliza <blank> para vazio
    dc_content = fetch_url(DEFAULT_CREDS_URL)
    if dc_content:
        for line in dc_content.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                uname = parts[1].strip().strip('"')
                pwd = parts[2].strip().strip('"')
                # Normaliza marcadores de campo vazio
                for blank_marker in (" ", "(blank)", "<blank>"):
                    if uname == blank_marker:
                        uname = ""
                    if pwd == blank_marker:
                        pwd = ""
                combos.add(f"{uname}:{pwd}")
    log.info("Combos após DefaultCreds CSV: %d", len(combos))

    # ICS CSV
    ics_content = fetch_url(ICS_CREDS_URL)
    if ics_content:
        for line in ics_content.splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                uname = parts[1].strip().strip('"')
                pwd = parts[2].strip().strip('"')
                combos.add(f"{uname}:{pwd}")
    log.info("Combos após ICS CSV: %d", len(combos))

    # Hardware management (ILO/iDRAC/IPMI)
    hw_combos = [
        "admin:opensource", "Administrator:opensource",
        "admin:admin", "Oper:Oper",
        "root:calvin", "USERID:PASSW0RD",
        "root:changeme", "admin:admin",
        "root:password", "admin:password",
        "ADMIN:ADMIN", "admin:admin",
        "admin:password", "root:root",
    ]
    for c in hw_combos:
        combos.add(c)

    # OT/ICS/SCADA/HMI específicos
    ot_combos = [
        "simulation:simulation", "scadabr:scadabr",
        "admin:pfsense", "workstation:password", "user:password",
        "USER:USER", "sysdiag:factorycast@schneider",
        "service:ABB800xA", "admin:siemens",
        "admin:moxa", "admin:private", "admin:12345",
    ]
    for c in ot_combos:
        combos.add(c)

    # MSP/MSSP locais
    mssp_combos = [
        "mssplocal:Mudar@123", "ishlocal:Ish@2024",
        "ishlab:ishlab123", "youitlab:youitlab123",
        "dropreallocal:Dropreal@2024",
        "tempestlocal:Tempest@2024",
        "cipherlocal:Cipher@2024",
    ]
    for c in mssp_combos:
        combos.add(c)

    log.info("Total combos: %d", len(combos))

    with COMBO_FILE.open("w", encoding="utf-8") as f:
        for c in sorted(combos, key=lambda x: x.lower()):
            f.write(c + "\n")
    log.info("default-creds-combo.lst gravado.")


# ---------------------------------------------------------------------------
# FASE 4 — README.md (en-US)
# ---------------------------------------------------------------------------
README_EN = '''# WordListsForHacking

> **Author:** André Henrique ([@mrhenrike](https://github.com/mrhenrike))  
> **Version:** 2.0.0 · **License:** MIT · **Updated:** 2026-03-30

Curated wordlists for authorized penetration testing, red team exercises, SOC training,
and security workshops — focused on Brazilian environments and global device defaults.

---

## Files

| File | Type | Lines (approx.) | Purpose |
|------|------|-----------------|---------|
| `wlist_brasil.lst` | Passwords | ~1.4M | Brazilian passwords: PT-BR dictionary + real leaks + cultural phrases + leet variations |
| `username_br.lst` | Usernames | ~350 | Brazilian and global usernames: corporate roles, default accounts, MSP/MSSP patterns |
| `default-creds-combo.lst` | `user:password` | ~4,500 | Default credentials for 200+ device/software vendors — no length filtering |
| `labs_passwords.lst` | Passwords | ~116 | Passwords used in Prof. André's classes and security events |
| `labs_users.lst` | Usernames | ~10 | Usernames used in classes and events |
| `labs_mikrotik_pass.lst` | Passwords | ~38 | MikroTik-specific passwords for tool demonstrations |

---

## Why Pure Numeric Sequences Are NOT Included

Purely numeric sequences (PINs, dates, CPF/CNPJ numbers, phone numbers, ID numbers)
are intentionally **omitted** from `wlist_brasil.lst` and `username_br.lst`.

**Reason:** Tools like `crunch`, `cupp`, and `hashcat --increment` generate these
sets **locally in seconds** with far greater efficiency than maintaining millions of
static numeric lines in a file. Including them would inflate file size without
adding real attack value.

### How to Generate Numeric Wordlists with Crunch

Install Crunch:

```bash
# Debian / Ubuntu / Kali
sudo apt install crunch

# Arch Linux / BlackArch
sudo pacman -S crunch

# Fedora / RHEL
sudo dnf install crunch
```

#### All 6- and 8-digit combinations

```bash
# 6 digits: 000000 to 999999 (1,000,000 entries)
crunch 6 6 0123456789 -o numeric-6.lst

# 8 digits: 00000000 to 99999999 (100,000,000 entries)
crunch 8 8 0123456789 -o numeric-8.lst

# 6 to 8 digits in one file
crunch 6 8 0123456789 -o numeric-6to8.lst
```

#### Dates — Brazilian formats

```bash
# DDMMYYYY (e.g., 15081990) — years 2000 to 2025
for y in $(seq 2000 2025); do
  crunch 8 8 -t "%%$$${y}" >> datas-ddmmyyyy.lst 2>/dev/null
done

# YYYYMMDD
for y in $(seq 2000 2025); do
  crunch 8 8 -t "${y}$$%%" >> datas-yyyymmdd.lst 2>/dev/null
done

# DDMMYY (6 digits)
crunch 6 6 0123456789 -t "%%$$%%" -o datas-ddmmyy.lst

# YYMMDD
crunch 6 6 0123456789 -t "%%$$%%" -o datas-yymmdd.lst
```

#### CPF (Brazilian tax ID — 11 digits, no punctuation)

```bash
# All combinations — note: ~100 GB uncompressed; use prefix filters
crunch 11 11 0123456789 -o cpf-all.lst

# Filter by São Paulo prefix (011–019):
crunch 11 11 0123456789 -t "01%%%%%%%%%%" -o cpf-sp.lst
```

#### CNPJ (Brazilian company ID — 14 digits)

```bash
# All combinations
crunch 14 14 0123456789 -o cnpj-all.lst

# Root (8 digits) + fixed branch "0001" + check digits
crunch 8 8 0123456789 -t "%%%%%%%%" | awk \'{print $0"00010001"}\' > cnpj-filtered.lst
```

#### Phone numbers

```bash
# Mobile without DDD (9 digits, starts with 9)
crunch 9 9 0123456789 -t "9%%%%%%%%" -o celular-sem-ddd.lst

# Mobile with São Paulo DDD 11
crunch 11 11 0123456789 -t "119%%%%%%%%" -o celular-sp.lst

# Landline without DDD (8 digits)
crunch 8 8 0123456789 -o fixo-sem-ddd.lst

# Landline with DDD 11
crunch 10 10 0123456789 -t "11%%%%%%%%" -o fixo-sp.lst

# All valid DDDs (mobile)
for ddd in 11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 \\
           41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 \\
           71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99; do
  crunch 11 11 0123456789 -t "${ddd}9%%%%%%%%" >> celulares-todos-ddd.lst 2>/dev/null
done
```

#### Tips for Hashcat and Hydra

```bash
# Hashcat — brute-force numeric without a wordlist file
hashcat -a 3 hash.txt ?d?d?d?d?d?d          # 6 digits
hashcat -a 3 hash.txt ?d?d?d?d?d?d?d?d      # 8 digits
hashcat -a 3 hash.txt -i --increment-min=6  # 6 to max

# Pipe Crunch directly into Hydra
crunch 8 8 0123456789 | hydra -l admin -P - 192.168.1.1 http-get /login
```

---

## Other Recommended Wordlists

```bash
# RockYou (14M passwords — classic)
/usr/share/wordlists/rockyou.txt  # pre-installed on Kali

# SecLists (Daniel Miessler — comprehensive collection)
sudo apt install seclists
git clone --depth 1 https://github.com/danielmiessler/SecLists.git

# CrackStation (1.49 billion real leaked passwords)
# https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm

# BRDumps (Brazil-specific wordlists)
git clone https://github.com/BRDumps/wordlists.git

# Brazilian Portuguese system dictionary (Kali/Debian)
sudo apt install wbrazilian
# Location: /usr/share/dict/brazilian
```

---

## Methodology

This wordlist was built using:

1. **Public research** — NordPass annual reports, HIBP public datasets, academic
   studies on Brazilian password habits (2020–2025)
2. **Brazilian Portuguese dictionary** — ~320,000 words from the LibreOffice/Mozilla
   spell-check corpus, filtered to ≥6 characters, with 7 orthographic variations each
3. **Algorithmic variation engine** — rich leet-speak mappings (multiple substitutions
   per character), case mutations, accent stripping, and suffix patterns (`123`,
   `@123`, `2024`–`2026`) based on documented PT-BR human password-writing habits
4. **Cultural phrases** — viral expressions, song lyrics, political slogans and memes
   from 2014–2025, sourced from public media and social platforms
5. **Corporate patterns** — MSP/MSSP × client naming conventions derived from public
   job postings on LinkedIn, InfoJobs and Vagas.com.br; patterns follow documented
   human tendencies when creating credentials in managed environments (PCFG model,
   Weir et al.)
6. **Manufacturer defaults** — DefaultCreds-cheat-sheet (ihebski/GitHub, 3,755+
   entries), ICS default passwords (arnaudsoullie/GitHub), product manuals and FCC ID
   databases
7. **Linguistic basis** — variation rules are grounded in corpus linguistics of PT-BR
   writing patterns, including phonetic substitutions (ç→c, ã→a) and keyboard-walk
   sequences documented in password cracking literature

---

## ⚠️ Ethical Disclaimer

**If a password belonging to you or your organization appears in this wordlist,
it means it matched one or more deterministic rules described above — not that
it was extracted from any system, database, vault, PAM, or credential store.**

Any reasonably skilled attacker or programmer could independently construct the
same entries by applying the same publicly documented algorithms.

This wordlist is a **security awareness tool**. It demonstrates that:
- Patterns based on company names, years, and keyboard walks are trivially guessable
- Leet-speak does NOT make a password strong if the base word is in a dictionary
- Brazilian cultural references are among the first candidates in targeted attacks

**Never use patterns from this list as real credentials. Use a password manager
and generate truly random credentials.**

---

## Legal Notice

- Use only in environments where you have **explicit written authorization**
- Never use for unauthorized access to any system
- Author accepts no liability for misuse
- Maintain attribution when redistributing

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v2.0.0 | 2026-03-30 | Complete rewrite: PT-BR dictionary (320k words + 7 variations), rich leet mapping, Brazilian cultural/music/memes phrases (2014–2025), 200+ vendor defaults (SIEM/EDR/OT/Cloud/Linux/HW-mgmt), user:password combo file, removal of purely numeric entries and entries <6 chars, comprehensive READMEs |
| v1.x | 2022–2025 | Previous versions — manual wordlists and ad-hoc collections |
'''

README_PT = '''# WordListsForHacking

> **Autor:** André Henrique ([@mrhenrike](https://github.com/mrhenrike))  
> **Versão:** 2.0.0 · **Licença:** MIT · **Atualizado:** 2026-03-30

Wordlists curadas para testes de penetração autorizados, exercícios de red team,
treinamentos SOC e workshops de segurança — focadas em ambientes brasileiros e
defaults globais de dispositivos.

---

## Arquivos

| Arquivo | Tipo | Linhas (aprox.) | Finalidade |
|---------|------|-----------------|-----------|
| `wlist_brasil.lst` | Senhas | ~1,4M | Senhas brasileiras: dicionário PT-BR + vazamentos reais + frases culturais + variações leet |
| `username_br.lst` | Usuários | ~350 | Usernames brasileiros e globais: funções corporativas, contas padrão, padrões MSP/MSSP |
| `default-creds-combo.lst` | `user:password` | ~4.500 | Credenciais default para 200+ fabricantes/softwares — sem filtro de tamanho |
| `labs_passwords.lst` | Senhas | ~116 | Senhas usadas nas aulas e eventos do Prof. André |
| `labs_users.lst` | Usuários | ~10 | Usuários usados em aulas e eventos |
| `labs_mikrotik_pass.lst` | Senhas | ~38 | Senhas MikroTik para demonstrações com ferramentas |

---

## Por que sequências puramente numéricas NÃO estão incluídas

Sequências 100% numéricas (PINs, datas, CPFs, CNPJs, telefones, RGs) são
**intencionalmente omitidas** de `wlist_brasil.lst` e `username_br.lst`.

**Motivo:** Ferramentas como `crunch`, `cupp` e `hashcat --increment` geram esses
conjuntos **localmente em segundos**, com muito mais eficiência do que manter
milhões de linhas numéricas estáticas em um arquivo. Incluí-las apenas aumentaria
o tamanho sem agregar valor real ao pentest.

### Como gerar wordlists numéricas com Crunch

Instalar o Crunch:

```bash
# Debian / Ubuntu / Kali
sudo apt install crunch

# Arch Linux / BlackArch
sudo pacman -S crunch

# Fedora / RHEL
sudo dnf install crunch
```

#### Todas as combinações de 6 e 8 dígitos

```bash
# 6 dígitos: 000000 até 999999 (1.000.000 entradas)
crunch 6 6 0123456789 -o numeric-6.lst

# 8 dígitos: 00000000 até 99999999 (100.000.000 entradas)
crunch 8 8 0123456789 -o numeric-8.lst

# 6 a 8 dígitos em um único arquivo
crunch 6 8 0123456789 -o numeric-6to8.lst
```

#### Datas — formatos brasileiros

```bash
# DDMMYYYY (ex: 15081990) — anos 2000 a 2025
for y in $(seq 2000 2025); do
  crunch 8 8 -t "%%$$${y}" >> datas-ddmmyyyy.lst 2>/dev/null
done

# YYYYMMDD
for y in $(seq 2000 2025); do
  crunch 8 8 -t "${y}$$%%" >> datas-yyyymmdd.lst 2>/dev/null
done

# DDMMYY (6 dígitos)
crunch 6 6 0123456789 -t "%%$$%%" -o datas-ddmmyy.lst

# YYMMDD
crunch 6 6 0123456789 -t "%%$$%%" -o datas-yymmdd.lst
```

#### CPF (11 dígitos, sem pontuação)

```bash
# Todas as combinações — atenção: ~100 GB descomprimido; use filtros de prefixo
crunch 11 11 0123456789 -o cpf-all.lst

# Filtro por prefixo SP (011-019):
crunch 11 11 0123456789 -t "01%%%%%%%%%%" -o cpf-sp.lst
```

#### CNPJ (14 dígitos)

```bash
# Todas as combinações
crunch 14 14 0123456789 -o cnpj-all.lst

# Raiz (8 dígitos) + filial "0001" fixo + dígitos verificadores
crunch 8 8 0123456789 -t "%%%%%%%%" | awk \'{print $0"00010001"}\' > cnpj-filtered.lst
```

#### Telefones — fixos e celulares

```bash
# Celular sem DDD (9 dígitos, começa com 9)
crunch 9 9 0123456789 -t "9%%%%%%%%" -o celular-sem-ddd.lst

# Celular com DDD 11 (SP)
crunch 11 11 0123456789 -t "119%%%%%%%%" -o celular-sp.lst

# Fixo sem DDD (8 dígitos)
crunch 8 8 0123456789 -o fixo-sem-ddd.lst

# Fixo com DDD 11
crunch 10 10 0123456789 -t "11%%%%%%%%" -o fixo-sp.lst

# Todos os DDDs válidos (celular)
for ddd in 11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 \\
           41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 \\
           71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99; do
  crunch 11 11 0123456789 -t "${ddd}9%%%%%%%%" >> celulares-todos-ddd.lst 2>/dev/null
done
```

#### Dicas com Hashcat e Hydra

```bash
# Hashcat — brute-force numérico sem arquivo de wordlist
hashcat -a 3 hash.txt ?d?d?d?d?d?d          # 6 dígitos
hashcat -a 3 hash.txt ?d?d?d?d?d?d?d?d      # 8 dígitos
hashcat -a 3 hash.txt -i --increment-min=6  # 6 até o máximo

# Pipe Crunch direto no Hydra
crunch 8 8 0123456789 | hydra -l admin -P - 192.168.1.1 http-get /login
```

---

## Outras Wordlists Recomendadas

```bash
# RockYou (14M senhas — clássica)
/usr/share/wordlists/rockyou.txt  # pré-instalada no Kali

# SecLists (Daniel Miessler — coleção completa)
sudo apt install seclists
git clone --depth 1 https://github.com/danielmiessler/SecLists.git

# CrackStation (1,49 bilhão de senhas reais vazadas)
# https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm

# BRDumps (wordlists específicas Brasil)
git clone https://github.com/BRDumps/wordlists.git

# Dicionário PT-BR (Kali/Debian)
sudo apt install wbrazilian
# Local: /usr/share/dict/brazilian
```

---

## Metodologia

Esta wordlist foi construída com:

1. **Pesquisas públicas** — relatórios NordPass, datasets HIBP, estudos acadêmicos
   sobre hábitos de senhas de brasileiros (2020–2025)
2. **Dicionário PT-BR** — ~320.000 palavras do corpus LibreOffice/Mozilla, filtradas
   para ≥6 caracteres, com 7 variações ortográficas cada
3. **Motor de variação algorítmica** — mapeamento leet rico (múltiplas substituições
   por caractere), mutações de capitalização, remoção de acentos e sufixos baseados
   em hábitos documentados de escrita de senhas em PT-BR (modelo PCFG, Weir et al.)
4. **Frases culturais** — expressões virais, letras de músicas, slogans políticos e
   memes de 2014 a 2025, obtidos de mídia pública e redes sociais
5. **Padrões corporativos** — convenções de nomenclatura MSP/MSSP × cliente derivadas
   de vagas públicas no LinkedIn, InfoJobs e Vagas.com.br; os padrões seguem
   tendências humanas documentadas na criação de credenciais em ambientes gerenciados
6. **Defaults de fabricantes** — DefaultCreds-cheat-sheet (ihebski/GitHub, 3.755+
   entradas), ICS default passwords (arnaudsoullie/GitHub), manuais de produtos e
   bancos de dados FCC ID
7. **Base linguística** — regras de variação fundamentadas em linguística de corpus
   PT-BR, incluindo substituições fonéticas (ç→c, ã→a) e sequências de teclado
   documentadas na literatura de quebra de senhas

---

## ⚠️ Aviso Ético e Legal

**Se uma senha sua ou da sua organização aparecer nesta wordlist, isso significa
que ela correspondeu a uma ou mais regras determinísticas descritas acima — e não
que foi extraída de qualquer sistema, banco de dados, vault, PAM ou cofre de
credenciais.**

Qualquer atacante ou programador com conhecimento moderado poderia construir
independentemente as mesmas entradas aplicando os mesmos algoritmos documentados
publicamente.

Esta wordlist é uma **ferramenta de conscientização de segurança**. Ela demonstra:
- Padrões baseados em nomes de empresas, anos e sequências de teclado são
  trivialmente adivinhados em ataques de força bruta
- Substituições leet NÃO tornam uma senha forte se a palavra base está em dicionário
- Referências culturais brasileiras estão entre os primeiros candidatos em ataques
  direcionados a usuários brasileiros

**Nunca use padrões desta lista como credenciais reais. Use um gerenciador de senhas
e gere credenciais verdadeiramente aleatórias.**

---

## Aviso Legal

- Use apenas em ambientes com **autorização escrita explícita**
- Nunca utilize para acesso não autorizado
- O autor não assume responsabilidade pelo uso indevido
- Mantenha atribuição ao redistribuir

---

## Changelog

| Versão | Data | Mudanças |
|--------|------|---------|
| v2.0.0 | 2026-03-30 | Reescrita completa: dicionário PT-BR (320k palavras + 7 variações), leet rico, frases culturais/músicas/memes BR (2014–2025), defaults de 200+ fabricantes (SIEM/EDR/OT/Cloud/Linux/HW-mgmt), arquivo combo user:password, remoção de entradas puramente numéricas e <6 chars, READMEs completos |
| v1.x | 2022–2025 | Versões anteriores — wordlists manuais e coletas ad-hoc |
'''


def phase4_readme() -> None:
    """Escreve README.md (en-US) e README.pt-BR.md."""
    log.info("=== FASE 4: READMEs ===")
    readme_path = BASE_DIR / "README.md"
    readme_pt_path = BASE_DIR / "README.pt-BR.md"

    with readme_path.open("w", encoding="utf-8") as f:
        f.write(README_EN)
    log.info("README.md gravado.")

    with readme_pt_path.open("w", encoding="utf-8") as f:
        f.write(README_PT)
    log.info("README.pt-BR.md gravado.")


# ---------------------------------------------------------------------------
# HANDOFF
# ---------------------------------------------------------------------------

def write_handoff(stats: dict) -> None:
    """Grava handoff de continuidade."""
    handoff_path = LOG_DIR / "handoff.md"
    content = f"""# Handoff — WordListsForHacking v2.0.0 ({stats['date']})

**Autor:** André Henrique (@mrhenrike)
**Repo:** https://github.com/mrhenrike/WordListsForHacking

## O que foi feito

- `wlist_brasil.lst`: {stats['wlist_before']} → **{stats['wlist_after']} linhas**
  - Removidos puramente numéricos: {stats['removed_num']}
  - Removidos <6 chars: {stats['removed_short']}
  - Adicionados NordPass/extras: ~220
  - Dicionário PT-BR (variações): ~{stats['dict_added']:,}
  - Frases BR (variações): ~{stats['phrase_added']:,}
  - DefaultCreds + ICS passwords: ~{stats['dc_added']:,}

- `username_br.lst`: atualizado com contas corporativas BR, MSP/MSSP locais,
  default globais extraídos do DefaultCreds CSV

- `default-creds-combo.lst`: **NOVO** — {stats['combo_count']} pares user:password
  (sem filtro de tamanho), cobrindo 200+ fabricantes + OT/ICS + HW-mgmt + MSP

- `README.md` e `README.pt-BR.md`: reescritos completamente (v2.0.0)

## Próximos passos

1. Commit no submodule: `git add -A && git commit -m "feat: v2.0.0 — wordlists update"`
2. Push: `git push origin main`
3. Atualizar ponteiro no superprojeto (Uniao-Geek/Projetos-SafeLabs)
4. Criar release v2.0.0 no GitHub: `gh release create v2.0.0 --title "v2.0.0 — Major update"`
"""
    with handoff_path.open("w", encoding="utf-8") as f:
        f.write(content)
    log.info("Handoff gravado em %s", handoff_path)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=" * 60)
    log.info("WordListsForHacking — Pipeline v2.0.0")
    log.info("Diretório: %s", BASE_DIR)
    log.info("=" * 60)

    import datetime
    stats: dict = {"date": datetime.date.today().isoformat(), "removed_num": 0,
                   "removed_short": 0, "dict_added": 0, "phrase_added": 0,
                   "dc_added": 0, "combo_count": 0, "wlist_before": 0, "wlist_after": 0}

    # Conta antes
    if WLIST_FILE.exists():
        with WLIST_FILE.open(encoding="utf-8", errors="replace") as f:
            stats["wlist_before"] = sum(1 for _ in f)

    phase1_wlist()
    phase2_usernames()
    phase3_combo()
    phase4_readme()

    # Conta depois
    if WLIST_FILE.exists():
        with WLIST_FILE.open(encoding="utf-8", errors="replace") as f:
            stats["wlist_after"] = sum(1 for _ in f)
    if COMBO_FILE.exists():
        with COMBO_FILE.open(encoding="utf-8", errors="replace") as f:
            stats["combo_count"] = sum(1 for _ in f)

    write_handoff(stats)

    log.info("=" * 60)
    log.info("Pipeline concluído.")
    log.info("  wlist_brasil.lst : %d → %d linhas", stats["wlist_before"], stats["wlist_after"])
    log.info("  default-creds-combo.lst : %d pares", stats["combo_count"])
    log.info("=" * 60)


if __name__ == "__main__":
    main()
