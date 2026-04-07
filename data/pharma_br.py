"""
Dados de farmácias e planos de saúde brasileiros para geração de padrões.

Fonte: Dados públicos CNPJ (Receita Federal) + pesquisa pública de mercado.
Autor: André Henrique (@mrhenrike)
Versão: 1.0.0
"""

# ── Padrões identificados via OCR (imagem Drogasil W1) ────────────────────────
#
#   DS{codigo_loja}@rd.com.br      -> login corporativo RD Saúde
#   memed{cnpj}                    -> portal memed + CNPJ completo (14 dígitos)
#   Drogasil#{codigo_loja}         -> senha padrão por empresa + separador
#   DROGA{codigo_loja}             -> abreviação + código (login = senha)
#   drogasil{codigo_loja}          -> empresa minúscula + código
#   IJ{numero_sequencial}          -> terminal TC (sequencial 6 dígitos)
#   mng{n}                         -> usuário genérico de portal (1, 2, ...)
#   61585865200916 (CNPJ)          -> CNPJ como login E como parte de senha
#
# Código de loja Drogasil/RD Saúde observado: DS1206 (4 dígitos)
# CNPJ observado: 61585865200916

# ── Faixas de códigos de loja RD Saúde (estimativa pública) ─────────────────
# RD Saúde opera >3.200 lojas; códigos DS observados iniciando em ~DS1000
DS_CODE_RANGE = range(1000, 9999)

# ── Prefixos de domínio corporativo ─────────────────────────────────────────
RD_DOMAIN = "rd.com.br"

# ── Redes farmacêuticas brasileiras com patterns conhecidos ─────────────────
PHARMA_CHAINS = {
    "drogasil": {
        "nomes": ["Drogasil", "DROGASIL", "drogasil"],
        "abrev": "DROGA",
        "dominio": "rd.com.br",
        "portais": ["memed", "iclinix", "servicenow"],
        "prefixo_ds": "DS",
        "prefixo_terminal": "IJ",
    },
    "droga_raia": {
        "nomes": ["DrogaRaia", "DROGA RAIA", "drogaraia"],
        "abrev": "RAIA",
        "dominio": "rd.com.br",
        "portais": ["memed", "servicenow"],
        "prefixo_ds": "DS",
    },
    "pague_menos": {
        "nomes": ["PagueMenos", "Pague Menos", "PAGUE MENOS", "paguemenos"],
        "abrev": "PM",
        "dominio": "paguemenos.com.br",
        "portais": [],
    },
    "extrafarma": {
        "nomes": ["Extrafarma", "EXTRAFARMA", "extrafarma"],
        "abrev": "EF",
        "dominio": "extrafarma.com.br",
        "portais": [],
    },
    "pacheco": {
        "nomes": ["Pacheco", "PACHECO", "DrogariaPacheco"],
        "abrev": "PAC",
        "dominio": "drogariapacheco.com.br",
        "portais": [],
    },
    "sao_paulo": {
        "nomes": ["DrogariaSaoPaulo", "Drogaria São Paulo"],
        "abrev": "DSP",
        "dominio": "dsp.com.br",
        "portais": [],
    },
    "panvel": {
        "nomes": ["Panvel", "PANVEL"],
        "abrev": "PNV",
        "dominio": "panvel.com.br",
        "portais": [],
    },
    "nissei": {
        "nomes": ["Nissei", "NISSEI", "Preço Popular"],
        "abrev": "NSS",
        "dominio": "nissei.com.br",
        "portais": [],
    },
    "araujo": {
        "nomes": ["Araujo", "ARAUJO", "DrogariaAraujo"],
        "abrev": "ARJ",
        "dominio": "araujo.com.br",
        "portais": [],
    },
    "sao_joao": {
        "nomes": ["SaoJoao", "São João", "FarmaciaSaoJoao"],
        "abrev": "SJF",
        "dominio": "farmaciassaojoao.com.br",
        "portais": [],
    },
}

# ── 50 maiores planos de saúde — Valor 1000 / 2023 ──────────────────────────
HEALTH_PLANS = [
    "BradescoSaude",
    "Hapvida",
    "SulAmericaSaude",
    "Amil",
    "UnimedNacional",
    "PreventSenior",
    "UnimedBeloHorizonte",
    "UnimedSaude",
    "PortoSeguroSaude",
    "UnimedPortoAlegre",
    "AthenaSaude",
    "UnimedCuritiba",
    "UnimedCampinas",
    "UnimedFortaleza",
    "Omint",
    "OdontoPrev",
    "UnimedGoiania",
    "CarePlus",
    "UnimedVitoria",
    "AssimSaude",
    "VisionMed",
    "UnimedBelem",
    "UnimedFESP",
    "UnimedCuiaba",
    "UnimedGrandeFlorianopolis",
    "UnimedRecife",
    "MedSenior",
    "UnimedNatal",
    "UnimedNordesteRS",
    "UnimedSaoJoseRioPreto",
    "UnimedSorocaba",
    "UnimedJoaoPessoa",
    "UnimedLondrina",
    "UnimedLesteFluminense",
    "UnimedMaceio",
    "UnimedSantos",
    "UnimedCampoGrande",
    "UnimedMaringa",
    "UnimedRibeiraoPreto",
    "SaoCristovao",
    "Trasmontano",
    "UnimedUberlandia",
    "FSFX",
    "UnimedBlumenau",
    "UnimedSantaCatarina",
    "UnimedTeresina",
    "UnimedSaoJoseCampos",
    "UnimedPiracicaba",
    "UnimedParana",
    "UnimedSergipe",
]

# Variações simples de nome dos planos (para geração de senhas)
HEALTH_PLANS_SIMPLE = [
    "bradesco", "hapvida", "sulamerica", "amil", "unimed",
    "preventsenior", "portoseguro", "omint", "odontoprev",
    "careplus", "assim", "visionmed", "medsenior",
    "saocristovao", "trasmontano", "fsfx",
]

# ── CNPJs reais coletados do XLSX (amostra: grandes redes) ───────────────────
# Extraídos de 877420839-Co-pia-de-Farmacias-BR.xlsx — dados públicos CNPJ/RF
RD_SAUDE_CNPJS_SAMPLE = [
    "61585865200916",   # Drogasil W1 (OCR) — CNPJ usado como login e senha
    "29445575000108",
    "67458034000103",
    "79014791000169",
    "23427347000110",
    "04781096000123",
    "77233609000135",
]

# ── Portais e sistemas internos identificados (OCR + pesquisa pública) ───────
PORTAIS = ["memed", "iclinix", "servicenow", "tc", "portal drogaria", "box delivery"]

# ── Padrões de senha detectados (para pattern_engine) ────────────────────────
PATTERNS = [
    # DS{codigo}@rd.com.br  ->  DS1206@rd.com.br
    "DS{cod}@rd.com.br",
    # memed{cnpj}           ->  memed61585865200916
    "memed{cnpj}",
    # Drogasil#{cod}        ->  Drogasil#1206
    "{empresa}#{cod}",
    # DROGA{cod}            ->  DROGA1206
    "DROGA{cod}",
    # drogasil{cod}         ->  drogasil1206
    "{empresa_lower}{cod}",
    # IJ{seq6}              ->  IJ275601
    "IJ{seq6}",
    # {portal}{cnpj}        ->  memed61585865200916
    "{portal}{cnpj}",
    # {empresa}@{ano}       ->  Drogasil@2024
    "{empresa}@{ano}",
    # {empresa}#{ano}       ->  Drogasil#2024
    "{empresa}#{ano}",
    # {empresa}{cod}@{dominio}  ->  DS1206@rd.com.br
    "DS{cod}@{dominio}",
]

# ── Anos relevantes para geração de senhas ───────────────────────────────────
ANOS = list(range(2016, 2027))

# ── Top 50 cidades brasileiras para padrões cidade@ano ──────────────────────
CIDADES_BR = [
    "SaoPaulo", "RioDeJaneiro", "Brasilia", "Salvador", "Fortaleza",
    "BeloHorizonte", "Manaus", "Curitiba", "Recife", "Goiania",
    "Belem", "PortoAlegre", "Guarulhos", "Campinas", "SaoLuis",
    "SaoGoncalo", "Maceio", "Duque", "Natal", "Teresina",
    "Campo Grande", "NovaDelponte", "SaoJoao", "JoaoPessoa", "Osasco",
    "SantoCristo", "PorToVelho", "Cuiaba", "Macapa", "Joinville",
    "Londrina", "SaoJoseDosCampos", "Ananindeua", "Niteroi", "Aparecida",
    "PortoBelgo", "Uberlandia", "Contagem", "Sorocaba", "Aracaju",
    "Feira", "Ribeirão Preto", "Juiz", "Florianopolis", "PiraPora",
    "Montes", "Macaé", "Caruaru", "Olinda", "Mogi",
]

# ── Variações simples de cidades para geração ───────────────────────────────
CIDADES_SIMPLES = [
    "belem", "manaus", "natal", "recife", "fortaleza", "salvador",
    "saopaulo", "riodejaneiro", "curitiba", "goiania", "brasilia",
    "campinas", "londrina", "sorocaba", "maceio", "teresina",
    "cuiaba", "joinville", "florianopolis", "uberlandia",
]
