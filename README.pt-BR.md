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
  <a href="https://github.com/mrhenrike/WordListsForHacking/releases"><img src="https://img.shields.io/badge/version-2.2.0-blue?style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8%2B-yellow?style=flat-square" alt="Python"></a>
  <a href="https://github.com/mrhenrike/WordListsForHacking"><img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos%20%7C%20termux-lightgrey?style=flat-square" alt="Platform"></a>
  <a href="https://pypi.org/project/wfh-wordlist/"><img src="https://img.shields.io/pypi/v/wfh-wordlist?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI"></a>
</p>

<p align="center">
  Toolkit unificado de geração de wordlists para pentest autorizado, red team e treinamentos de segurança. Inclui scraping web com extração JS/CSS/PDF, base de credenciais default (IoT/routers/impressoras/ICS), gerador de keyspace ISP e treino ML com corpus SecLists.
</p>

<p align="center">
  <a href="README.md">English</a> · Português (Brasil)
</p>

---

> **Autor:** André Henrique ([@mrhenrike](https://github.com/mrhenrike))
> **Versão:** 2.2.0 · **Licença:** MIT · **Python:** 3.8+

> **Documentação completa:** [Wiki](https://github.com/mrhenrike/WordListsForHacking/wiki)

---

## Aviso Legal

**Este repositório destina-se exclusivamente a testes de segurança autorizados, exercícios de red team, treinamentos de SOC e workshops acadêmicos.** Utilize apenas em ambientes com autorização explícita e por escrito. O autor não se responsabiliza por uso indevido.

---

## Quick Start

### Instalar via pip (recomendado)

```bash
pip install wfh-wordlist            # core
pip install wfh-wordlist[full]      # todos os extras (OCR, parsing de documentos)
```

### Ou clonar do repositório

```bash
git clone https://github.com/mrhenrike/WordListsForHacking.git
cd WordListsForHacking

# Linux / macOS / Termux
chmod +x setup_venv.sh && ./setup_venv.sh && source .venv/bin/activate

# Windows PowerShell
.\setup_venv.ps1; .\.venv\Scripts\Activate.ps1
```

### Executar

```bash
wfh                        # menu interativo (pip install)
python wfh.py              # menu interativo (do código-fonte)
python wfh.py --help       # ajuda completa da CLI
```

> **Pré-requisitos por SO (OCR):** veja a [página de Instalação na Wiki](https://github.com/mrhenrike/WordListsForHacking/wiki/Installation).

---

## Subcomandos

| # | Comando | Descrição |
|---|---------|-----------|
| 1 | `charset` | Geração por charset/máscara (estilo crunch + hashcat) |
| 2 | `pattern` | Geração por template com variáveis |
| 3 | `profile` | Profiling pessoal (estilo CUPP) |
| 4 | `corp` | Profiling corporativo |
| 5 | `corp-users` | Geração de users/senhas corporativos (50+ padrões) |
| 6 | `phone` | Wordlists de telefone (BR, US, UK) |
| 7 | `scrape` | Web scraping (estilo CeWL/CeWLeR) com extração JS/CSS/PDF |
| 8 | `ocr` | Extração OCR de imagens |
| 9 | `extract` | Extração de PDF/XLSX/DOCX |
| 10 | `leet` | Permutações leet speak |
| 11 | `xor` | XOR encrypt/decrypt/brute-force |
| 12 | `analyze` | Análise estatística (estilo pipal) |
| 13 | `merge` | Merge e deduplicação |
| 14 | `dns` | DNS/subdomain fuzzing (estilo alterx) |
| 15 | `pharma` | Padrões de credenciais saúde/farmácia |
| 16 | `sanitize` | Limpeza e normalização |
| 17 | `reverse` | Inversão de linhas |
| 18 | `corp-prefixes` | Prefixos corporativos (MSP/SOC/DevOps) |
| 19 | `train` | Treinar modelo ML (local + corpus SecLists) |
| 20 | `sysinfo` | Info de hardware e compute |
| 21 | `mangle` | Regras de word mangling |
| 22 | `default-creds` | Consulta base de credenciais default (IoT/routers/impressoras/ICS) |
| 23 | `isp-keygen` | Gerador de keyspace WiFi padrão de ISPs |

> **Sintaxe detalhada e exemplos de cada subcomando:** [Wiki — Subcomandos](https://github.com/mrhenrike/WordListsForHacking/wiki)

### Flags Globais

```bash
python wfh.py --threads 20 --compute cuda --no-ml <subcomando>
```

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--threads N` | `5` | Threads de trabalho (1–300) |
| `--compute MODE` | `auto` | `auto` / `cpu` / `gpu` / `cuda` / `rocm` / `mps` / `hybrid` |
| `--no-ml` | off | Desabilitar ranking ML |
| `-v` | off | Logging detalhado |

---

## Exemplos Mais Comuns

### Pentest corporativo — gerar users + senhas

```bash
python wfh.py corp-users --domain acme.com.br --file funcionarios.txt --passwords --combo -o acme_combo.lst
```

### Profiling de alvo pessoal

```bash
python wfh.py profile --name "João Silva" --nick joao --birth 15/03/1990 --leet aggressive -o alvo.lst
```

### Charset com máscara hashcat

```bash
python wfh.py charset 8 8 --mask "?u?l?l?l?d?d?d?s" -o senhas.lst
```

### Geração por template

```bash
python wfh.py pattern -t "{empresa}{ano}!" --vars empresa=acme,globex ano=2020-2026 -o patterns.lst
```

### Fuzzing de subdomínios DNS

```bash
python wfh.py dns -d acme.com.br --words dev staging api admin portal -o subdomains.lst
```

### Analisar uma wordlist existente

```bash
python wfh.py analyze senhas.lst --top 30 --masks --format json -o analise.json
```

### Consultar credenciais default

```bash
python wfh.py default-creds --list-vendors
python wfh.py default-creds --vendor mikrotik --format combo -o mikrotik_creds.lst
python wfh.py default-creds --protocol snmp --format user -o snmp_users.lst
```

### Geração de keyspace WiFi ISP

```bash
python wfh.py isp-keygen --list
python wfh.py isp-keygen --isp xfinity_comcast --estimate
python wfh.py isp-keygen --isp xfinity_comcast --limit 100000 -o xfinity.lst
```

### Web scraping com JS/CSS/PDF

```bash
python wfh.py scrape https://alvo.com --include-js --include-css --include-pdf --lowercase -o palavras.lst
python wfh.py scrape https://alvo.com --emails --output-emails emails.txt --output-urls urls.txt
python wfh.py scrape https://alvo.com --subdomain-strategy children --stream -o stream.lst
```

### Merge e sanitização

```bash
python wfh.py merge lista1.lst lista2.lst --min-len 6 --sort -o merged.lst
python wfh.py sanitize merged.lst --inplace
```

> **Mais exemplos e cenários completos:** [Wiki — Quick Start](https://github.com/mrhenrike/WordListsForHacking/wiki/Quick-Start)

---

## Wordlists

| Arquivo | Descrição | Entradas |
|---------|-----------|----------|
| `passwords/wlist_brasil.lst` | Corpus brasileiro de senhas — bancos culturais, padrões corporativos, leet speak, keyboard walks. Nomes de empresas e CNPJs são dados públicos (OSINT). | ~3.88M |
| `passwords/default-creds-combo.lst` | Credenciais-padrão user:password (routers, impressoras, ICS/SCADA) | ~3K |
| `data/default_credentials.json` | Base estruturada de credenciais default (1.329 entradas, 88 vendors, 14 protocolos) | — |
| `fuzzing/discovery_br.lst` | Paths de descoberta web e API fuzzing brasileiros | ~900 |
| `usernames/username_br.lst` | Usernames brasileiros e globais | ~1.6K |
| `labs/*.lst` | Wordlists para workshops e treinamentos | — |

> **Detalhes:** [Wiki — Wordlist Brasileira](https://github.com/mrhenrike/WordListsForHacking/wiki/Brazilian-Wordlist)

---

## Minha Senha Está Nesta Lista?

```bash
# Linux/macOS
grep -qxF 'SuaSenha' passwords/wlist_brasil.lst && echo "ENCONTRADA!" || echo "Não encontrada"

# Windows PowerShell
Select-String -Path passwords\wlist_brasil.lst -Pattern '^SuaSenha$' -SimpleMatch -Quiet
```

Se encontrada: **troque imediatamente**, habilite MFA/2FA, use um gerenciador de senhas e nunca reutilize senhas.

> **Guia completo:** [Wiki — Password Check](https://github.com/mrhenrike/WordListsForHacking/wiki/Password-Check)

---

## Modelo ML

O WFH inclui um modelo ML leve que ranqueia candidatos gerados por probabilidade de padrão estrutural. Treine com dados locais ou com o corpus SecLists:

```bash
python wfh.py train --auto                    # apenas wordlists locais
python wfh.py train --seclists                # corpus SecLists (auto-discover)
python wfh.py train --auto --seclists         # combinado (recomendado)
python wfh.py train --seclists /path/to/SecLists --seclists-categories password frequency
```

O modelo armazena **apenas padrões estruturais** — sem PII, senhas ou nomes de empresa.

> **Detalhes:** [Wiki — ML Model](https://github.com/mrhenrike/WordListsForHacking/wiki/ML-Model)

---

## Disclaimer Ético

Se uma senha pertencente a você ou sua organização aparece nesta wordlist, isso significa que ela corresponde a regras determinísticas da metodologia — e não que foi extraída de qualquer sistema ou banco de dados. Qualquer atacante habilidoso poderia construir as mesmas entradas aplicando os mesmos algoritmos publicamente documentados.

**Nunca use padrões desta lista como credenciais reais. Use um gerenciador de senhas.**

---

## Créditos e Inspiração

| Projeto | Inspiração |
|---------|------------|
| [CUPP](https://github.com/Mebus/cupp) | Profiling pessoal |
| [Crunch](https://github.com/jim3ma/crunch) | Geração por charset |
| [CeWL](https://github.com/digininja/CeWL) | Web scraping |
| [CeWLeR](https://github.com/roys/cewler) | Web scraping moderno em Python (JS/CSS/PDF) |
| [routersploit](https://github.com/threat9/routersploit) | Credenciais default IoT/routers |
| [alterx](https://github.com/projectdiscovery/alterx) | DNS/subdomain fuzzing |
| [pipal](https://github.com/digininja/pipal) | Análise estatística |
| [SecLists](https://github.com/danielmiessler/SecLists) | Listas curadas |
| [elpscrk](https://github.com/D4Vinci/elpscrk) | Geração por permutação |
| [BEWGor](https://github.com/berzerk0/BEWGor) | Gerador biográfico |
| [pnwgen](https://github.com/toxydose/pnwgen) | Geração de telefones |

---

## Contributing

Contribuições são bem-vindas. Veja o [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[MIT License](LICENSE) — Copyright (c) 2026 André Henrique ([@mrhenrike](https://github.com/mrhenrike))

---

<p align="center">
  <strong>Autor:</strong> André Henrique (<a href="https://github.com/mrhenrike">@mrhenrike</a>) | <a href="https://github.com/Uniao-Geek">União Geek</a>
</p>

<p align="center">
  <a href="README.md">English version</a> · <a href="https://github.com/mrhenrike/WordListsForHacking/wiki">Documentação Completa (Wiki)</a>
</p>
