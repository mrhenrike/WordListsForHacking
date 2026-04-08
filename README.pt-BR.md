<p align="center">
  <pre align="center">
 __          _______ _    _
 \ \        / /  ____| |  | |
  \ \  /\  / /| |__  | |__| |
   \ \/  \/ / |  __| |  __  |
    \  /\  /  | |    | |  | |
     \/  \/   |_|    |_|  |_|
  </pre>
</p>

<h1 align="center">WordListsForHacking</h1>

<p align="center">
  <a href="https://github.com/mrhenrike/WordListsForHacking/releases"><img src="https://img.shields.io/badge/version-2.1.2-blue?style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8%2B-yellow?style=flat-square" alt="Python"></a>
  <a href="https://github.com/mrhenrike/WordListsForHacking"><img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos%20%7C%20termux-lightgrey?style=flat-square" alt="Platform"></a>
  <a href="https://pypi.org/project/wfh-wordlist/"><img src="https://img.shields.io/pypi/v/wfh-wordlist?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI"></a>
</p>

<p align="center">
  Wordlists curadas e ferramenta unificada de geração para pentest autorizado, red team e treinamentos de segurança.
</p>

<p align="center">
  <a href="README.md">English</a> · Português (Brasil)
</p>

---

> **Autor:** André Henrique ([@mrhenrike](https://github.com/mrhenrike))  
> **Versão:** 2.1.2 · **Licença:** MIT · **Python:** 3.8+

---

## Aviso Legal

**Este repositório destina-se exclusivamente a testes de segurança autorizados, exercícios de red team, treinamentos de SOC e workshops acadêmicos.**

- Utilize apenas em ambientes onde você possua **autorização explícita e por escrito**
- Nunca utilize para acesso não autorizado a qualquer sistema
- O autor não se responsabiliza por uso indevido
- Mantenha a atribuição ao redistribuir

---

## Sumário

- [Quick Start](#quick-start)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Wordlists](#wordlists)
- [wfh.py — Ferramenta de Geração](#wfhpy--ferramenta-de-geração)
  - [Flags Globais](#flags-globais)
  - [Subcomandos](#subcomandos)
    - [charset](#1-charset)
    - [pattern](#2-pattern)
    - [profile](#3-profile)
    - [corp](#4-corp)
    - [corp-users](#5-corp-users)
    - [phone](#6-phone)
    - [scrape](#7-scrape)
    - [ocr](#8-ocr)
    - [extract](#9-extract)
    - [leet](#10-leet)
    - [xor](#11-xor)
    - [analyze](#12-analyze)
    - [merge](#13-merge)
    - [dns](#14-dns)
    - [pharma](#15-pharma)
    - [sanitize](#16-sanitize)
    - [reverse](#17-reverse)
    - [corp-prefixes](#18-corp-prefixes)
    - [train](#19-train)
    - [sysinfo](#20-sysinfo)
- [Exemplos de Uso](#exemplos-de-uso)
- [Modelo ML](#modelo-ml)
- [Contributing](#contributing)
- [Licença](#licença)
- [Disclaimer Ético](#disclaimer-ético)
- [Créditos e Referências](#créditos-e-referências)
- [Wordlist Brasileira (wlist_brasil.lst)](#wordlist-brasileira-wlist_brasillst)
- [Minha Senha Está Nesta Lista?](#minha-senha-está-nesta-lista)

---

## Quick Start

### Opção A — Instalar via pip (recomendado)

```bash
pip install wfh-wordlist
```

Com extras opcionais:

```bash
pip install wfh-wordlist[full]    # todas as dependências opcionais (OCR, parsing de documentos)
pip install wfh-wordlist[docs]    # apenas parsing de PDF/XLSX/DOCX
pip install wfh-wordlist[ocr]     # apenas extração OCR de imagens
```

Após instalação, o comando `wfh` fica disponível globalmente:

```bash
wfh --help
wfh charset -h
```

### Opção B — Clonar do repositório

```bash
git clone https://github.com/mrhenrike/WordListsForHacking.git
cd WordListsForHacking
```

**Linux / macOS / Termux (Android):**

```bash
chmod +x setup_venv.sh
./setup_venv.sh
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.\setup_venv.ps1
.\.venv\Scripts\Activate.ps1
```

Ou instale manualmente:

```bash
pip install -r requirements.txt
```

### Executar

```bash
wfh                        # menu interativo (instalado via pip)
python wfh.py              # menu interativo (do código-fonte)
python wfh.py --help       # ajuda completa da CLI
python wfh.py charset -h   # ajuda de um subcomando específico
```

### Pré-requisitos por Sistema Operacional

| Plataforma | Python | Pacotes adicionais |
|------------|--------|--------------------|
| **Windows 10/11** | [python.org](https://python.org) ou `winget install Python.Python.3.12` | Para OCR: `winget install UB-Mannheim.TesseractOCR` |
| **Ubuntu/Debian** | `sudo apt install python3 python3-pip python3-venv` | `sudo apt install libxml2-dev libxslt1-dev tesseract-ocr` |
| **Fedora/RHEL** | `sudo dnf install python3 python3-pip` | `sudo dnf install libxml2-devel libxslt-devel tesseract` |
| **Arch Linux** | `sudo pacman -S python python-pip` | `sudo pacman -S libxml2 libxslt tesseract` |
| **macOS** | `brew install python3` | `brew install tesseract` |
| **Android (Termux)** | `pkg install python` | `pkg install clang libxml2 libxslt libjpeg-turbo libpng` |
| **Alpine** | `apk add python3 py3-pip` | `apk add libxml2-dev libxslt-dev tesseract-ocr` |

> **Nota:** OCR e Tesseract são necessários apenas se você usar o subcomando `ocr`. A funcionalidade principal funciona sem eles.

---

## Estrutura do Repositório

```
WordListsForHacking/
├── labs/                        # Wordlists para workshops e aulas (curadoria manual)
│   ├── labs_passwords.lst       # Senhas usadas em eventos do Prof. André
│   ├── labs_users.lst           # Usernames usados em aulas e eventos
│   └── labs_mikrotik_pass.lst   # Senhas MikroTik para demonstrações
│
├── usernames/                   # Listas de usernames consolidadas
│   └── username_br.lst          # Usernames brasileiros e globais (~1.1K entradas)
│
├── passwords/                   # Listas de senhas consolidadas + geradas
│   ├── wlist_brasil.lst         # Senhas brasileiras (~3.88M entradas únicas)
│   └── default-creds-combo.lst  # Credenciais-padrão user:password (~2.4K)
│
├── generated/                   # Saída do wfh.py (gitignored)
│
├── wfh.py                       # CLI unificada de geração (v2.1.0)
├── wfh_modules/                 # Módulos do wfh.py (22 módulos)
│   ├── analyzer.py              # Análise estatística (estilo pipal)
│   ├── charset_gen.py           # Geração por charset, máscara e composição
│   ├── compute_backend.py       # Backend de computação (CPU/GPU)
│   ├── corp_prefixes.py         # Prefixos corporativos
│   ├── corp_profiler.py         # Profiling corporativo
│   ├── dns_wordlist.py          # DNS/subdomain fuzzing
│   ├── domain_users.py          # Geração de users/senhas corporativos
│   ├── file_extractor.py        # Extração de PDF/XLSX/DOCX
│   ├── hw_profiler.py           # Detecção de hardware
│   ├── leet_permuter.py         # Variações leet speak
│   ├── linkedin_search.py       # Busca online de funcionários
│   ├── mangler.py               # Mangling estilo hashcat/John
│   ├── merger.py                # Merge e deduplicação
│   ├── ml_patterns.py           # Modelo ML de padrões
│   ├── ocr_extractor.py         # Extração OCR
│   ├── pattern_engine.py        # Templates com variáveis
│   ├── phone_gen.py             # Geração de wordlists de telefone
│   ├── profiler.py              # Profiling pessoal (estilo CUPP)
│   ├── sanitizer.py             # Limpeza e normalização
│   ├── thread_pool.py           # Pool de threads paralelo
│   ├── web_scraper.py           # Web scraping (estilo CeWL)
│   └── xor_crypto.py            # XOR criptografia/brute-force
│
├── data/                        # Dados estáticos para geração
│   ├── corp_prefix_patterns.json   # Padrões de prefixos corporativos (intl)
│   └── behavior_patterns.json      # Padrões comportamentais (intl)
│
├── .model/                      # Modelo ML treinado (gitignored)
│   └── pattern_model.json       # Pesos estatísticos (sem PII)
│
├── pyproject.toml               # Config de empacotamento PyPI
├── MANIFEST.in                  # Regras de inclusão para sdist
├── requirements.txt             # Dependências core + opcionais
├── setup_venv.sh                # Setup automatizado (Linux/macOS/Termux)
├── setup_venv.ps1               # Setup automatizado (Windows)
├── update_wordlists.py          # Script de consolidação de wordlists
├── CONTRIBUTING.md              # Guia de contribuição
├── CODE_OF_CONDUCT.md           # Código de conduta
└── LICENSE                      # Licença MIT
```

---

## Wordlists

### `labs/` — Workshop e Treinamento

| Arquivo | Tipo | Entradas | Finalidade |
|---------|------|----------|------------|
| `labs_passwords.lst` | Senhas | ~116 | Senhas usadas em aulas e eventos de segurança |
| `labs_users.lst` | Usernames | ~10 | Usernames usados em aulas e eventos |
| `labs_mikrotik_pass.lst` | Senhas | ~38 | Senhas MikroTik para demonstrações de ferramentas |

> **Nota:** Listas de lab são mantidas manualmente pelo instrutor. Não altere via scripts.

### `usernames/` — Usernames Consolidados

| Arquivo | Tipo | Entradas | Finalidade |
|---------|------|----------|------------|
| `username_br.lst` | Usernames | ~1.168 | Usernames brasileiros e globais: padrões corporativos, contas-padrão, padrões MSP/MSSP |

### `passwords/` — Senhas Consolidadas

| Arquivo | Tipo | Entradas | Finalidade |
|---------|------|----------|------------|
| `wlist_brasil.lst` | Senhas | ~3.88M | Corpus de senhas brasileiras gerado pela ferramenta WFH usando bancos de palavras culturais, padrões corporativos, permutações leet speak, keyboard walks e dicionário português. Nomes de empresas e CNPJs são dados públicos obtidos via OSINT. Sanitizado, deduplicado, min 5 chars. |
| `default-creds-combo.lst` | `user:password` | ~2.440 | Credenciais-padrão para 200+ fabricantes de dispositivos/software |

### `generated/` — Saída do wfh.py

Listas geradas pelo **wfh.py** são salvas aqui por padrão. Esta pasta é gitignored — adicione listas específicas ao controle de versão apenas quando curadas e validadas.

---

## wfh.py — Ferramenta de Geração

**wfh.py** é uma CLI unificada que combina as capacidades de CUPP, Crunch, CeWL, alterx e pipal em uma única ferramenta, com 20 subcomandos, threading paralelo, suporte a GPU e ranking por modelo ML.

### Modos de Execução

```bash
# Menu interativo (sem argumentos)
python wfh.py

# Subcomando direto
python wfh.py <subcomando> [opções]
```

### Flags Globais

Estas flags são aplicadas **antes** do subcomando e afetam todos os modos:

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--threads N` / `-T N` | `5` | Threads de trabalho para geração paralela (1–300) |
| `--compute MODE` | `auto` | Backend de computação: `auto` \| `cpu` \| `gpu` \| `cuda` \| `rocm` \| `mps` \| `hybrid` |
| `--no-ml` | desativado | Desabilita ranking ML globalmente; todos os módulos usam modo baseado em regras |
| `-v` / `--verbose` | desativado | Modo verbose com logs detalhados |

**Exemplos de uso com flags globais:**

```bash
# 20 threads + GPU CUDA
python wfh.py --threads 20 --compute cuda corp-users --domain acme.com.br --file nomes.txt

# Sem ML, modo CPU forçado
python wfh.py --no-ml --compute cpu corp-users --domain acme.com.br --names "João Silva"

# Verbose para debug
python wfh.py -v analyze wordlist.lst --masks
```

> **Nota sobre threads:** valores acima de 50 geram aviso, acima de 100 geram alerta, acima de 200 geram alerta crítico. O valor recomendado é calculado automaticamente com base no hardware.

---

### Subcomandos

#### 1. charset

Geração por charset e comprimento (estilo Crunch), máscaras hashcat (`?u?l?d?s`), composição restrita.

```bash
# Charset padrão (letras minúsculas, 6-8 caracteres)
python wfh.py charset 6 8

# Charset customizado
python wfh.py charset 6 8 abc123

# Charset com arquivo .cfg
python wfh.py charset 6 8 -f charsets.cfg mixalpha-numeric

# Padrão estilo Crunch (@ = minúscula, , = maiúscula, % = dígito, ^ = especial)
python wfh.py charset 8 8 --pattern "Pass@@@%%%"

# Máscara hashcat (?u=upper ?l=lower ?d=digit ?s=special ?a=all)
python wfh.py charset 8 8 --mask "?u?l?l?l?d?d?s"

# Máscara com charset customizado para ?1
python wfh.py charset 8 8 --mask "?u?l?l?1?d?d" --custom-charset1 "aeiou"

# Composição restrita (exatamente N de cada tipo)
python wfh.py charset 8 8 --digits 2 --lower 4 --upper 1 --special 1

# Assistente para criar arquivo de charset
python wfh.py charset --create-charset meu_charset.cfg

# Saída para arquivo
python wfh.py charset 6 8 abc123 -o generated/charset.lst
```

---

#### 2. pattern

Geração por template com variáveis substituíveis.

```bash
# Template com variável de range numérico
python wfh.py pattern -t "DS{cod}@acme.com.br" --vars cod=1200-1300

# Template com variável de lista
python wfh.py pattern -t "{empresa}@{ano}" --vars empresa=acme,apex ano=2024-2026

# Template a partir de arquivo
python wfh.py pattern -f templates.txt --vars cod=100-200

# Saída para arquivo
python wfh.py pattern -t "user{n}@acme.com.br" --vars n=001-999 -o generated/patterns.lst
```

---

#### 3. profile

Profiling pessoal interativo (estilo CUPP) — coleta informações sobre o alvo e gera wordlist personalizada.

```bash
# Modo interativo (wizard completo)
python wfh.py profile

# Modo CLI direto
python wfh.py profile --name "João Silva" --nick "joao" --birth 15/03/1990

# Carregar perfil de arquivo YAML
python wfh.py profile --profile-file alvo.yaml -o generated/profile.lst

# Controlar range de anos e sufixos numéricos
python wfh.py profile --name "João Silva" --year-start 2000 --year-end 2026 --suffix-range 00-99

# Modo leet speak
python wfh.py profile --name "João Silva" --leet aggressive -o generated/profile.lst
```

**Modos leet disponíveis:** `basic`, `medium`, `aggressive`, `none`

---

#### 4. corp

Profiling corporativo interativo — coleta informações sobre a empresa-alvo e gera wordlist.

```bash
# Modo interativo (wizard completo)
python wfh.py corp

# Com modo leet
python wfh.py corp --leet medium -o generated/corp.lst
```

---

#### 5. corp-users

Geração de usernames e senhas corporativos com 50+ padrões de username, 118 padrões de senha, variações leet-speak e ranking ML.

```bash
# Modo interativo (wizard)
python wfh.py corp-users

# Nomes a partir de arquivo (TXT/CSV/XLSX/PDF/DOCX)
python wfh.py corp-users --domain acme.com.br --file funcionarios.txt -o generated/users.lst

# Busca online (Google dorks + LinkedIn API opcional)
python wfh.py corp-users --domain acme.com.br --search "ACME Corp" -o generated/users.lst

# Nomes inline
python wfh.py corp-users --domain acme.com.br --names "João Silva,Maria Santos" -o generated/users.lst

# Gerar senhas também
python wfh.py corp-users --domain acme.com.br --file nomes.txt --passwords -o generated/combo.lst

# Gerar combo user:password
python wfh.py corp-users --domain acme.com.br --names "João Silva" --combo -o generated/combo.lst

# Separadores customizados (padrão: ".")
python wfh.py corp-users --domain acme.com.br --names "João Silva" --separators "_"
python wfh.py corp-users --domain acme.com.br --names "João Silva" --separators all
python wfh.py corp-users --domain acme.com.br --names "João Silva" --separators ".,_,none"

# Padrões de admin para subdomínios
python wfh.py corp-users --domain acme.com.br --subdomain portal,webmail -o generated/admins.lst

# Sem @domain nos usernames
python wfh.py corp-users --domain acme.com.br --names "João Silva" --no-at

# Range de anos para senhas
python wfh.py corp-users --domain acme.com.br --file nomes.txt --year-start 2020 --year-end 2026

# Desabilitar ML para este comando
python wfh.py corp-users --domain acme.com.br --file nomes.txt --no-ml
```

**Padrões de username gerados:**
`firstname.lastname`, `f.lastname`, `flastname`, `lastname.firstname`, `firstname`, `lastname`, `firstnamel`, `initials`, entre 15+ variações adicionais.

---

#### 6. phone

Geração de wordlist de números de telefone (Brasil, EUA, UK) com DDI/DDD, mobile/fixo, formatos E.164/local/bare.

```bash
# Modo interativo
python wfh.py phone

# Brasil — celulares de São Paulo
python wfh.py phone --country brazil --state SP --type mobile -o generated/phones_sp.lst

# EUA — Nova York, todos os formatos
python wfh.py phone --country usa --state NY --formats e164,local -o generated/phones_ny.lst

# DDI/DDD manual com padrão customizado
python wfh.py phone --ddi 55 --ddd 11 --pattern "9XXXX-XXXX" -o generated/custom.lst

# UK — fixos
python wfh.py phone --country uk --type landline -o generated/phones_uk.lst
```

**Países suportados:** Brasil (55), EUA (1), UK (44)  
**Formatos de saída:** `e164` (+5511999999999), `local` (11999999999), `bare` (999999999)

---

#### 7. scrape

Web scraping de wordlists (estilo CeWL) com suporte a proxy, autenticação, headers customizados e stop-words.

```bash
# Scraping básico
python wfh.py scrape https://acme.com.br -o generated/scrape.lst

# Com profundidade e extração de emails
python wfh.py scrape https://acme.com.br -d 3 --emails -o generated/scrape.lst

# Com filtro de stop-words
python wfh.py scrape https://acme.com.br --no-stopwords -o generated/scrape.lst

# Com proxy
python wfh.py scrape https://acme.com.br --proxy http://127.0.0.1:8080

# Com autenticação HTTP Basic
python wfh.py scrape https://acme.com.br --auth usuario:senha

# User-Agent e headers customizados
python wfh.py scrape https://acme.com.br --user-agent "Mozilla/5.0" --header "X-Token: abc123"

# Stop-words customizadas
python wfh.py scrape https://acme.com.br --stopwords-file meus_stopwords.txt

# Controlar tamanho das palavras extraídas
python wfh.py scrape https://acme.com.br --min-word 4 --max-word 20

# Delay entre requisições
python wfh.py scrape https://acme.com.br --delay 1.0

# Extrair metadados (Author, Generator)
python wfh.py scrape https://acme.com.br --meta
```

---

#### 8. ocr

Extração de texto de imagens via OCR (EasyOCR). Identifica usernames, senhas e palavras-chave.

```bash
# OCR básico (português + inglês)
python wfh.py ocr screenshot.png -o generated/ocr.lst

# OCR com idiomas específicos
python wfh.py ocr documento.jpg --lang pt,en,es -o generated/ocr.lst
```

---

#### 9. extract

Extração de wordlist a partir de arquivos PDF, XLSX, DOCX e imagens.

```bash
# Extrair de múltiplos arquivos
python wfh.py extract relatorio.pdf planilha.xlsx -o generated/extracted.lst

# Com filtro de comprimento
python wfh.py extract documento.docx --min-len 6 --max-len 32 -o generated/extracted.lst
```

**Formatos suportados:** PDF, XLSX, DOCX, RTF, imagens (via OCR)

---

#### 10. leet

Variações leet speak com 4 modos de intensidade e mapeamento customizado.

```bash
# Modo básico
python wfh.py leet admin -m basic -o generated/leet.lst

# Modo agressivo (mais variações)
python wfh.py leet password -m aggressive -o generated/leet.lst

# Mapeamento customizado
python wfh.py leet password -m custom --custom-map "a=@,4;s=$;e=3;l=1,|"

# Limitar número de resultados
python wfh.py leet admin -m aggressive --max-results 5000 -o generated/leet.lst
```

**Modos:** `basic`, `medium`, `aggressive`, `custom`

---

#### 11. xor

Criptografia XOR e brute-force de chave single-byte.

```bash
# Brute-force de chave (testa 256 chaves)
python wfh.py xor --brute 1a2b3c4d

# Criptografar texto
python wfh.py xor --encrypt "texto secreto" --key "chave"

# Descriptografar hex
python wfh.py xor --decrypt 1a2b3c --key "chave"
```

---

#### 12. analyze

Análise estatística de wordlists (estilo pipal) com máscaras hashcat e extração de base-words.

```bash
# Análise básica (top 20)
python wfh.py analyze wordlist.lst

# Top 50 com máscaras hashcat
python wfh.py analyze wordlist.lst --top 50 --masks

# Exportar relatório em JSON
python wfh.py analyze wordlist.lst --masks --format json -o stats.json

# Exportar em CSV
python wfh.py analyze wordlist.lst --format csv -o stats.csv

# Extrair base-words (strip de dígitos/especiais do final)
python wfh.py analyze wordlist.lst --base-words --base-output bases.lst
```

**Métricas incluídas:**
- Distribuição de comprimento
- Frequência de caracteres
- Top N senhas mais comuns
- Análise de complexidade
- Máscaras hashcat (`?u?l?d?s`) e suas frequências
- Extração de base-words

---

#### 13. merge

Merge e deduplicação de múltiplas wordlists.

```bash
# Merge simples
python wfh.py merge lista1.lst lista2.lst -o generated/merged.lst

# Merge com filtros
python wfh.py merge lista1.lst lista2.lst --min-len 8 --max-len 32 -o generated/merged.lst

# Remover entradas puramente numéricas
python wfh.py merge lista1.lst lista2.lst --no-numeric -o generated/merged.lst

# Filtro regex (apenas entradas que contêm letras)
python wfh.py merge lista1.lst lista2.lst --filter "^[a-zA-Z]" -o generated/merged.lst

# Ordenar resultado
python wfh.py merge lista1.lst lista2.lst --sort alpha -o generated/merged.lst

# Sem deduplicação
python wfh.py merge lista1.lst lista2.lst --no-dedupe -o generated/merged.lst
```

**Modos de ordenação:** `alpha`, `length`, `random`

---

#### 14. dns

DNS/subdomain fuzzing (estilo alterx) com permutações, templates YAML e multi-domínio.

```bash
# Permutações de subdomínio
python wfh.py dns -w words.lst -d acme.com.br -o generated/subdomains.lst

# Palavras inline
python wfh.py dns -d acme.com.br --words dev staging api admin

# Template inline
python wfh.py dns -d acme.com.br -t "dev-{word}.{domain}" -w words.lst

# Templates a partir de arquivo YAML
python wfh.py dns -d acme.com.br --template-file patterns.yaml -w words.lst

# Multi-domínio (arquivo com um domínio por linha)
python wfh.py dns --domain-list dominios.txt -w words.lst -o generated/subdomains.lst

# Separador customizado
python wfh.py dns -d acme.com.br -w words.lst --separator "_"

# Filtros regex
python wfh.py dns -d acme.com.br -w words.lst --match-regex "^api" --filter-regex "test"

# Somente prefixos ou sufixos
python wfh.py dns -d acme.com.br -w words.lst --no-suffixes
```

---

#### 15. pharma

Padrões de credenciais de redes de varejo/saúde brasileiras (farmácias, planos de saúde, operadoras).

```bash
# Padrão (códigos de loja 1200-1214)
python wfh.py pharma -o generated/pharma.lst

# Range de códigos customizado
python wfh.py pharma --codes 1200-1300 -o generated/pharma.lst

# Códigos específicos
python wfh.py pharma --codes 1200,1201,1250 -o generated/pharma.lst
```

---

#### 16. sanitize

Limpeza e normalização de wordlists existentes.

```bash
# Sanitização básica (remove duplicatas, linhas em branco, comentários)
python wfh.py sanitize wordlist.lst -o generated/clean.lst

# In-place (sobrescreve o arquivo original)
python wfh.py sanitize wordlist.lst --inplace

# Com filtro de comprimento
python wfh.py sanitize wordlist.lst --min-len 8 --max-len 32 -o generated/clean.lst

# Ordenar resultado
python wfh.py sanitize wordlist.lst --sort alpha -o generated/clean.lst

# Regex: incluir apenas linhas que começam com letras
python wfh.py sanitize wordlist.lst --filter "^[a-zA-Z]" -o generated/clean.lst

# Regex: excluir linhas que terminam com 3+ dígitos
python wfh.py sanitize wordlist.lst --exclude "\d{3,}$" -o generated/clean.lst

# Manter linhas em branco e comentários
python wfh.py sanitize wordlist.lst --keep-blank --keep-comments -o generated/clean.lst
```

**Pipeline de sanitização (ordem):** comentários → brancos → comprimento → regex → deduplicação → ordenação

**Modos de ordenação:** `alpha`, `alpha-rev`, `length`, `length-rev`, `random`

---

#### 17. reverse

Inverter ordem de linhas (equivalente ao `tac`).

```bash
# Saída para arquivo
python wfh.py reverse wordlist.lst -o generated/reversed.lst

# In-place
python wfh.py reverse wordlist.lst --inplace
```

---

#### 18. corp-prefixes

Geração de usernames com prefixos corporativos (MSP/MSSP/SOC/DevOps/Red-Blue-Purple team). Padrões carregados de `data/corp_prefix_patterns.json`.

```bash
# Gerar com prefixos para um nome
python wfh.py corp-prefixes --names "João Silva" --domain acme.com.br -o generated/prefixed.lst

# Prefixos específicos
python wfh.py corp-prefixes --names "João Silva" --prefixes svc,adm,ti --separators "."

# Por categorias
python wfh.py corp-prefixes --names "João Silva" --categories department,role

# Por setor
python wfh.py corp-prefixes --names "João Silva" --sector judicial

# Nomes a partir de arquivo
python wfh.py corp-prefixes --file funcionarios.txt --domain acme.com.br -o generated/prefixed.lst

# Listar todos os prefixos disponíveis
python wfh.py corp-prefixes --list-prefixes

# Sem sufixo @domain
python wfh.py corp-prefixes --names "João Silva" --domain acme.com.br --no-at

# Sem variantes numéricas
python wfh.py corp-prefixes --names "João Silva" --no-numeric

# Arquivo de configuração customizado
python wfh.py corp-prefixes --names "João Silva" --config meus_prefixos.json
```

**Categorias de prefixos:**

| Categoria | Exemplos |
|-----------|----------|
| `department` | ti, helpdesk, adm, rh, fin, seg, dev, redes, ... |
| `role` | svc, admin, ger, dir, analista, trainee, ... |
| `contractor` | ext, externo, terceiro, vendor, pj, ... |
| `temp` | temp, tmp, provisorio, ... |
| `generic` | user, usr, account, login, ... |

**Setores suportados:** `energia_utilities`, `judicial`, `financas`, `saude`, `governo`, `generic`, entre outros.

---

#### 19. train

Treinar modelo ML de padrões a partir de exports AD, wordlists e listas de usernames.

```bash
# Auto-discovery (treina a partir de wordlists locais conhecidas)
python wfh.py train --auto

# A partir de CSV de export AD
python wfh.py train --csv export.csv --auto -o .model/pattern_model.json

# Múltiplas fontes
python wfh.py train --csv users.csv --wordlist wlist_brasil.lst --usernames username_br.lst

# Colunas customizadas do CSV
python wfh.py train --csv export.csv --uid-col samaccountname --mail-col mail

# Limitar linhas processadas
python wfh.py train --wordlist grande.lst --max-lines 100000
```

> **Privacidade:** apenas padrões estruturais são extraídos — nenhum username, senha, nome de empresa ou dado pessoal é armazenado no modelo.

---

#### 20. sysinfo

Mostrar perfil de hardware e backend de computação.

```bash
# Informações do sistema
python wfh.py sysinfo

# Com backend específico
python wfh.py --compute gpu sysinfo

# Com threads customizadas
python wfh.py --threads 20 sysinfo
```

**Informações exibidas:**
- CPU (modelo, cores físicos/lógicos)
- RAM (total/disponível)
- GPU(s) detectadas
- Backend de computação ativo
- Status do ML
- Threads ativas e recomendadas

---

## Exemplos de Uso

### Cenário 1 — Pentest corporativo

```bash
# 1. Coletar nomes de funcionários de arquivo
python wfh.py corp-users \
  --domain acme.com.br \
  --file funcionarios.txt \
  --passwords \
  --combo \
  -o generated/acme_combo.lst

# 2. Adicionar prefixos corporativos
python wfh.py corp-prefixes \
  --file funcionarios.txt \
  --domain acme.com.br \
  -o generated/acme_prefixed.lst

# 3. Merge dos resultados
python wfh.py merge \
  generated/acme_combo.lst \
  generated/acme_prefixed.lst \
  --sort alpha \
  -o generated/acme_final.lst
```

### Cenário 2 — Wordlist personalizada para alvo

```bash
# 1. Profiling do alvo
python wfh.py profile \
  --name "João Silva" \
  --nick "joaos" \
  --birth 15/03/1990 \
  --leet aggressive \
  -o generated/joao_profile.lst

# 2. Scraping do site do alvo
python wfh.py scrape https://acme.com.br \
  -d 2 \
  --emails \
  --no-stopwords \
  -o generated/acme_scrape.lst

# 3. Merge + sanitização
python wfh.py merge \
  generated/joao_profile.lst \
  generated/acme_scrape.lst \
  --min-len 6 \
  -o generated/joao_final.lst
```

### Cenário 3 — Fuzzing de subdomínios

```bash
# Gerar permutações DNS
python wfh.py dns \
  -d acme.com.br \
  --words dev staging api admin portal vpn mail \
  -o generated/acme_subdomains.lst

# Usar com ferramentas externas
cat generated/acme_subdomains.lst | httpx -silent
cat generated/acme_subdomains.lst | dnsx -silent
```

### Cenário 4 — Análise de wordlist existente

```bash
# Análise completa com máscaras e base-words
python wfh.py analyze passwords/wlist_brasil.lst \
  --top 30 \
  --masks \
  --base-words \
  --base-output generated/bases.lst \
  --format json \
  -o generated/analysis.json
```

### Cenário 5 — Geração de telefones para spray

```bash
# Celulares de São Paulo
python wfh.py phone \
  --country brazil \
  --state SP \
  --type mobile \
  --formats e164,local \
  -o generated/phones_sp.lst
```

---

## Modelo ML

O arquivo `.model/pattern_model.json` contém pesos estatísticos extraídos de:

- **~183K amostras de username** — padrões estruturais gerados pelo WFH (corp-users, corp-prefixes)
- **~502K amostras de senha** — padrões gerados pelo WFH (profile, pattern, charset, leet)
- **Fontes:** Padrões comportamentais gerados pelo WFH, bancos de palavras culturais, convenções corporativas genéricas, análise de ferramentas open-source

**Privacidade:** o modelo armazena apenas **padrões estruturais** (e.g., `fi_ln_num`, `fn_sep_ln`) e seus pesos. Nenhum dado pessoal, username, senha ou nome de empresa é armazenado.

**Padrões de username rastreados:**

| Padrão | Exemplo | Descrição |
|--------|---------|-----------|
| `fi_ln_num` | `jsilva01` | Inicial + sobrenome + número |
| `fn_sep_ln` | `joao.silva` | Nome + separador + sobrenome |
| `numeric` | `12345` | Apenas numérico |
| `fn_only` | `joao` | Apenas primeiro nome |
| `fn_sep_ln_num` | `joao.silva01` | Nome + sep + sobrenome + número |
| `fn_sep_mn_sep_ln` | `joao.carlos.silva` | Nome + meio + sobrenome |

**Setores suportados no modelo:** `generic`, `ong_institucional`, `ad_local`, `portal_cloud`, `outsourcing_msp`

### Treinar o modelo

```bash
# Auto-discovery de fontes locais
python wfh.py train --auto

# Com dados de AD export
python wfh.py train --csv ad_export.csv --auto
```

---

## Contributing

Contribuições são bem-vindas. Consulte o [CONTRIBUTING.md](CONTRIBUTING.md) para as regras completas.

**Resumo:**

1. Abra uma issue primeiro para mudanças substanciais
2. Fork o repositório e crie um branch de feature
3. Mantenha commits focados
4. Teste localmente antes de abrir PR
5. Nunca inclua segredos, chaves de API ou dados reais de clientes

---

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).

```
MIT License

Copyright (c) 2026 André Henrique (https://github.com/mrhenrike)
```

---

## Disclaimer Ético

**Se uma senha pertencente a você ou sua organização aparece nesta wordlist, isso significa que ela corresponde a uma ou mais regras determinísticas descritas na metodologia — e não que foi extraída de qualquer sistema, banco de dados, cofre, PAM ou credential store.**

Qualquer atacante ou programador razoavelmente habilidoso poderia construir as mesmas entradas de forma independente aplicando os mesmos algoritmos publicamente documentados.

Esta wordlist é uma **ferramenta de conscientização de segurança**. Ela demonstra que:

- Padrões baseados em nomes de empresas, anos e keyboard walks são trivialmente adivinháveis
- Leet-speak **NÃO** torna uma senha forte se a palavra-base está em um dicionário
- Referências culturais brasileiras estão entre os primeiros candidatos em ataques direcionados

**Nunca use padrões desta lista como credenciais reais. Use um gerenciador de senhas e gere credenciais verdadeiramente aleatórias.**

---

## Créditos e Referências

Este projeto foi inspirado e referencia as seguintes ferramentas e projetos:

| Projeto | Descrição | Link |
|---------|-----------|------|
| **CUPP** | Common User Passwords Profiler | [github.com/Mebus/cupp](https://github.com/Mebus/cupp) |
| **Crunch** | Gerador de wordlists por charset/pattern | [github.com/jim3ma/crunch](https://github.com/jim3ma/crunch) |
| **CeWL** | Custom Word List generator (web scraping) | [github.com/digininja/CeWL](https://github.com/digininja/CeWL) |
| **alterx** | Gerador de subdomínios por permutação | [github.com/projectdiscovery/alterx](https://github.com/projectdiscovery/alterx) |
| **pipal** | Analisador estatístico de senhas | [github.com/digininja/pipal](https://github.com/digininja/pipal) |
| **SecLists** | Coleção de listas para testes de segurança | [github.com/danielmiessler/SecLists](https://github.com/danielmiessler/SecLists) |
| **elpscrk** | Geração de senhas por permutação com níveis | [github.com/D4Vinci/elpscrk](https://github.com/D4Vinci/elpscrk) |
| **BEWGor** | Gerador de wordlists biográfico com zodíaco/cultura | [github.com/berzerk0/BEWGor](https://github.com/berzerk0/BEWGor) |
| **intelligence-wordlist-generator** | Permutação de keywords OSINT com conectores | [github.com/zfrenchee/intelligence-wordlist-generator](https://github.com/zfrenchee/intelligence-wordlist-generator) |
| **pnwgen** | Geração de wordlists de números de telefone | [github.com/toxydose/pnwgen](https://github.com/toxydose/pnwgen) |

---

## Wordlist Brasileira (wlist_brasil.lst)

O arquivo `passwords/wlist_brasil.lst` é o maior corpus curado de senhas brasileiras disponível, com **~3.88 milhões de entradas únicas**, gerado pela ferramenta WFH usando seus módulos de padrão, perfil, charset, leet speak, padrões corporativos e bancos de palavras culturais. Nomes de empresas e CNPJs incluídos são dados públicos obtidos via OSINT (Receita Federal, bases públicas).

### Como Foi Construída

| Tipo de Fonte | Descrição |
|---------------|-----------|
| **Bancos de Palavras** | Dicionário português, nomes brasileiros, clubes de futebol, termos religiosos, gírias regionais — todos de `data/behavior_patterns.json` |
| **Leet Speak** | Substituições sistemáticas (a→@, e→3, o→0, s→$, etc.) aplicadas a palavras em português |
| **Keyboard Walks** | Padrões de caminhada de teclado ABNT2/QWERTY comuns no Brasil |
| **Padrões Corporativos** | Padrões de credenciais corporativas brasileiras — nomes de empresas e CNPJs são dados públicos (Receita Federal / OSINT) |
| **Geração por Padrão** | Templates como `{empresa}{sep}{código}`, `{nome}{ano}`, `{palavra}{separador}{número}`, etc. |
| **ML-Ranked** | Modelo ML do WFH ranqueia entradas por probabilidade de padrão estrutural |

### Regras de Sanitização Aplicadas

- Mínimo 5 caracteres
- Entradas puramente numéricas removidas (exceto padrões CPF/CNPJ)
- Separadores de formatação removidos de padrões CPF/CNPJ
- Totalmente deduplicado
- Nomes de empresas e CNPJs são dados públicos (Receita Federal, OSINT público)
- Todas as entradas são reproduzíveis pelos módulos de geração do WFH

---

## Minha Senha Está Nesta Lista?

Se você quer verificar se sua senha aparece na `wlist_brasil.lst` (ou qualquer outra wordlist):

### Usando grep (Linux/macOS)

```bash
grep -qxF 'SuaSenhaAqui' passwords/wlist_brasil.lst && echo "ENCONTRADA — troque!" || echo "Não encontrada"
```

### Usando PowerShell (Windows)

```powershell
if (Select-String -Path passwords\wlist_brasil.lst -Pattern '^SuaSenhaAqui$' -SimpleMatch -Quiet) { "ENCONTRADA — troque!" } else { "Não encontrada" }
```

### Usando Python

```python
import sys
senha = sys.argv[1]
with open("passwords/wlist_brasil.lst", "r") as f:
    encontrada = any(line.strip() == senha for line in f)
print("ENCONTRADA — troque!" if encontrada else "Não encontrada")
```

### Se Sua Senha Foi Encontrada

Se sua senha aparece nesta lista, ela é considerada **comprometida** e deve ser trocada imediatamente:

1. **Troque sua senha imediatamente** em todos os serviços onde a utiliza
2. **Habilite MFA/2FA** (Autenticação Multifator) em todas as contas — use um app autenticador (Google Authenticator, Microsoft Authenticator, Authy) em vez de SMS quando possível
3. **Use um gerenciador de senhas** (Bitwarden, 1Password, KeePass) para gerar e armazenar senhas únicas para cada serviço
4. **Nunca reutilize senhas** entre diferentes serviços
5. **Solicite reset de senha** em serviços críticos (banco, e-mail, contas corporativas)
6. **Verifique vazamentos** em [Have I Been Pwned](https://haveibeenpwned.com/) para ver se seu e-mail/contas foram comprometidos
7. **Revise a atividade da conta** para qualquer acesso não autorizado
8. **Use senhas com pelo menos 14 caracteres** combinando maiúsculas, minúsculas, dígitos e caracteres especiais — ou use passphrases (4+ palavras aleatórias)

---

<p align="center">
  <strong>Autor:</strong> André Henrique (<a href="https://github.com/mrhenrike">@mrhenrike</a>) | União Geek — <a href="https://github.com/Uniao-Geek">github.com/Uniao-Geek</a>
</p>

<p align="center">
  <a href="README.md">English version (README.md)</a>
</p>
