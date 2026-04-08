# WordListsForHacking (WFH)

<p align="center">
  <img src="https://img.shields.io/github/stars/mrhenrike/WordListsForHacking?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/mrhenrike/WordListsForHacking?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-2.1.2-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/pypi/v/wfh-wordlist?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI">
</p>

**Unified wordlist generation toolkit for pentest and red team operations.** Combines charset generation, target profiling, web scraping, OCR extraction, leet speak permutation, DNS fuzzing, phone number generation, corporate domain user enumeration, ML-based ranking, and statistical analysis — all in a single CLI tool.

This is **not** a fork of CUPP, Crunch, CeWL, or any other tool. It is an original project inspired by the best ideas in the offensive security ecosystem.

---

> **DISCLAIMER:** This tool is intended **exclusively for authorized security testing, penetration testing, and educational purposes**. Unauthorized use against systems you do not own or have explicit written permission to test is **illegal** and unethical. The author assumes no liability for misuse. Always obtain proper authorization before conducting any security assessment.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Wordlists](#wordlists)
- [wfh.py — CLI Tool](#wfhpy--cli-tool)
  - [Global Flags](#global-flags)
  - [Subcommands](#subcommands)
- [Usage Examples](#usage-examples)
  - [Charset Generation](#charset-generation)
  - [Pattern Generation](#pattern-generation)
  - [Personal Target Profiling](#personal-target-profiling)
  - [Corporate Target Profiling](#corporate-target-profiling)
  - [Corporate Domain Users](#corporate-domain-users)
  - [Phone Number Generation](#phone-number-generation)
  - [Web Scraping](#web-scraping)
  - [OCR Extraction](#ocr-extraction)
  - [File Extraction](#file-extraction)
  - [Leet Speak Variants](#leet-speak-variants)
  - [XOR Crypto](#xor-crypto)
  - [Wordlist Analysis](#wordlist-analysis)
  - [Merge Wordlists](#merge-wordlists)
  - [DNS Fuzzing](#dns-fuzzing)
  - [Healthcare / Pharmacy Patterns](#healthcare--pharmacy-patterns)
  - [Sanitize Wordlist](#sanitize-wordlist)
  - [Reverse Lines](#reverse-lines)
  - [Corporate Prefixes](#corporate-prefixes)
  - [ML Model Training](#ml-model-training)
  - [System Info](#system-info)
  - [Multi-threading](#multi-threading)
  - [CPU / GPU Compute](#cpu--gpu-compute)
  - [ML-based Ranking](#ml-based-ranking)
- [ML Model](#ml-model)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)
- [Credits & Inspiration](#credits--inspiration)
- [Brazilian Wordlist (wlist_brasil.lst)](#brazilian-wordlist-wlist_brasillst)
- [Is My Password in This List?](#is-my-password-in-this-list)

---

## Quick Start

### Option A — Install via pip (recommended)

```bash
pip install wfh-wordlist
```

With optional extras:

```bash
pip install wfh-wordlist[full]    # all optional deps (OCR, document parsing)
pip install wfh-wordlist[docs]    # PDF/XLSX/DOCX parsing only
pip install wfh-wordlist[ocr]     # OCR/image text extraction only
```

After installation, the `wfh` command is available globally:

```bash
wfh --help
wfh charset -h
```

### Option B — Clone from source

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

Or install manually:

```bash
pip install -r requirements.txt
```

### Run

```bash
wfh                        # interactive menu (if installed via pip)
python wfh.py              # interactive menu (from source)
python wfh.py --help       # full CLI help
python wfh.py charset -h   # help for a specific subcommand
```

### OS Prerequisites

| Platform | Python | Extra packages |
|----------|--------|----------------|
| **Windows 10/11** | [python.org](https://python.org) or `winget install Python.Python.3.12` | For OCR: `winget install UB-Mannheim.TesseractOCR` |
| **Ubuntu/Debian** | `sudo apt install python3 python3-pip python3-venv` | `sudo apt install libxml2-dev libxslt1-dev tesseract-ocr` |
| **Fedora/RHEL** | `sudo dnf install python3 python3-pip` | `sudo dnf install libxml2-devel libxslt-devel tesseract` |
| **Arch Linux** | `sudo pacman -S python python-pip` | `sudo pacman -S libxml2 libxslt tesseract` |
| **macOS** | `brew install python3` | `brew install tesseract` |
| **Android (Termux)** | `pkg install python` | `pkg install clang libxml2 libxslt libjpeg-turbo libpng` |
| **Alpine** | `apk add python3 py3-pip` | `apk add libxml2-dev libxslt-dev tesseract-ocr` |

> **Note:** OCR and Tesseract are only needed if you use the `ocr` subcommand. Core functionality works without them.

---

## Repository Structure

```
WordListsForHacking/
├── labs/                          # Workshop & training wordlists
│   ├── labs_passwords.lst         # Passwords for security events
│   ├── labs_users.lst             # Usernames for classes/events
│   └── labs_mikrotik_pass.lst     # MikroTik-specific passwords
├── usernames/
│   └── username_br.lst            # Brazilian + global usernames (~1.1K)
├── passwords/
│   ├── wlist_brasil.lst           # Brazilian passwords (~3.88M unique)
│   └── default-creds-combo.lst    # Default credential combos
├── data/
│   ├── behavior_patterns.json     # Behavioral patterns (religious, cultural, industry)
│   └── corp_prefix_patterns.json  # Corporate prefix patterns (MSP/MSSP/SOC/DevOps/etc)
├── wfh.py                         # Main CLI tool (v2.1.0)
├── wfh_modules/                   # Python modules (22 modules)
│   ├── analyzer.py                # Statistical wordlist analysis
│   ├── charset_gen.py             # Charset generation (crunch-style + hashcat masks)
│   ├── compute_backend.py         # CPU/GPU compute abstraction
│   ├── corp_prefixes.py           # Corporate prefix username generation
│   ├── corp_profiler.py           # Corporate target profiling
│   ├── dns_wordlist.py            # DNS/subdomain fuzzing
│   ├── domain_users.py            # Corporate domain user/password generation
│   ├── file_extractor.py          # File extraction (PDF/XLSX/DOCX)
│   ├── hw_profiler.py             # Hardware profiler (CPU/RAM/GPU)
│   ├── leet_permuter.py           # Leet speak permutations
│   ├── linkedin_search.py         # LinkedIn API integration
│   ├── merger.py                  # Wordlist merge & deduplication
│   ├── ml_patterns.py             # ML pattern learning model
│   ├── ocr_extractor.py           # OCR text extraction
│   ├── pattern_engine.py          # Template-based pattern generation
│   ├── phone_gen.py               # Phone number wordlist generation
│   ├── profiler.py                # Personal target profiling (CUPP-style)
│   ├── mangler.py                 # Hashcat-style wordlist mangling
│   ├── sanitizer.py               # Wordlist cleaning/sanitization
│   ├── thread_pool.py             # Multi-threading support
│   ├── web_scraper.py             # Web scraping (CeWL-style)
│   └── xor_crypto.py              # XOR crypto utilities
├── .model/                        # ML trained model (gitignored)
├── pyproject.toml                 # PyPI packaging config (pip install wfh-wordlist)
├── MANIFEST.in                    # sdist include rules
├── requirements.txt               # Core + optional dependencies
├── setup_venv.sh                  # Linux/macOS/Termux setup script
├── setup_venv.ps1                 # Windows PowerShell setup script
└── update_wordlists.py
```

---

## Wordlists

### Passwords

| File | Description | Entries |
|------|-------------|---------|
| `passwords/wlist_brasil.lst` | Brazilian password corpus — generated by the WFH tool using cultural word banks, behavioral patterns, leet speak permutations, keyboard walks, corporate naming conventions, and Portuguese dictionary. Company names and CNPJs are public data obtained via OSINT. Sanitized, deduplicated, min 5 chars. | ~3.88M |
| `passwords/default-creds-combo.lst` | Default credential user:password combos | — |

### Usernames

| File | Description | Entries |
|------|-------------|---------|
| `usernames/username_br.lst` | Brazilian + global username patterns | ~1.1K |

### Labs (Training & Workshops)

| File | Description |
|------|-------------|
| `labs/labs_passwords.lst` | Passwords curated for security workshops |
| `labs/labs_users.lst` | Usernames curated for training events |
| `labs/labs_mikrotik_pass.lst` | MikroTik router default/common passwords |

### Data

| File | Description |
|------|-------------|
| `data/behavior_patterns.json` | Behavioral patterns — religious, cultural, industry keywords, 14-language word banks, keyboard layouts, leet maps, charsets, phone formats, default credentials |
| `data/corp_prefix_patterns.json` | Corporate prefix patterns — MSP, MSSP, SOC, DevOps, red/blue/purple team |

---

## wfh.py — CLI Tool

`wfh.py` is a modular CLI tool with **20 subcommands** covering the entire wordlist generation lifecycle: creation, transformation, analysis, and maintenance.

### Global Flags

These flags apply to **all** subcommands:

| Flag | Description | Default |
|------|-------------|---------|
| `--threads N` | Thread count (1–300). Warnings at >50, >100, >200 | `5` |
| `--compute MODE` | Compute backend: `auto`, `cpu`, `gpu`, `cuda`, `rocm`, `mps`, `hybrid` | `auto` |
| `--no-ml` | Disable ML pattern ranking globally | off |
| `-v` / `--verbose` | Enable verbose logging | off |

### Subcommands

#### 1. `charset` — Charset Generation

Generate wordlists by character set and length range. Supports crunch-style charsets, hashcat masks (`?u?l?d?s?a`), and constrained composition.

```bash
python wfh.py charset <min_len> <max_len> [charset] [options]
```

| Flag | Description |
|------|-------------|
| `<min_len> <max_len>` | Length range |
| `[charset]` | Character set name or string (default: `lalpha`) |
| `-p, --pattern` | Crunch-style pattern (`@` = lowercase, `,` = uppercase, `%` = digit, `^` = symbol) |
| `--mask` | Hashcat mask (`?u`, `?l`, `?d`, `?s`, `?a`) |
| `--digits N` | Exact number of digits (constrained) |
| `--lower N` | Exact number of lowercase chars (constrained) |
| `--upper N` | Exact number of uppercase chars (constrained) |
| `--special N` | Exact number of special chars (constrained) |
| `--create-charset FILE` | Interactive charset config creator |
| `-o, --output FILE` | Output file |

#### 2. `pattern` — Template-based Generation

Generate wordlists from templates with variable expansion.

```bash
python wfh.py pattern -t "TEMPLATE" --vars key=value [options]
```

| Flag | Description |
|------|-------------|
| `-t, --template` | Template string with `{var}` placeholders |
| `--template-file FILE` | YAML/text template file |
| `--vars key=val` | Variable definitions (repeatable). Supports ranges (`cod=100-200`), lists, files |
| `-o, --output FILE` | Output file |

#### 3. `profile` — Personal Target Profiling

Interactive CUPP-style profiling to generate targeted wordlists based on personal information.

```bash
python wfh.py profile [options]
```

| Flag | Description |
|------|-------------|
| `--profile-file FILE` | Load profile from YAML file |
| `--name "Full Name"` | Non-interactive: target full name |
| `--nick NICK` | Non-interactive: target nickname |
| `--birth DD/MM/YYYY` | Non-interactive: birth date |
| `--leet MODE` | Leet mode: `basic`, `medium`, `aggressive` |
| `--year-start YYYY` | Start year for suffix range |
| `--year-end YYYY` | End year for suffix range |
| `--suffix-range START-END` | Numeric suffix range (e.g., `00-99`) |
| `-o, --output FILE` | Output file |

#### 4. `corp` — Corporate Target Profiling

Interactive corporate profiling — company name, domains, industry, products, locations, technologies.

```bash
python wfh.py corp [options]
```

| Flag | Description |
|------|-------------|
| `--leet MODE` | Leet mode: `basic`, `medium`, `aggressive` |
| `-o, --output FILE` | Output file |

#### 5. `corp-users` — Corporate Domain User/Password Generation

Generate usernames, passwords, and user:password combos for corporate domain targets. Supports 50+ username patterns, 118 password patterns, leet-speak variants, and ML ranking.

```bash
python wfh.py corp-users [options]
```

| Flag | Description |
|------|-------------|
| `--domain DOMAIN` | Target domain (e.g., `acme.com.br`) |
| `--company NAME` | Company name (auto-detected from domain if omitted) |
| `--file FILE` | File with employee names (one per line: `First Last`) |
| `--names "Name1,Name2"` | Comma-separated employee names |
| `--search COMPANY` | Search for employees online (Google dorks + LinkedIn) |
| `--no-api` | Disable LinkedIn API for online search |
| `--max-results N` | Max online search results (default: 50) |
| `--separators SEP` | Username separators: `.` (default), `all`, `none`, or comma-separated custom list |
| `--subdomain SUB` | Subdomains (comma-separated) |
| `--passwords` | Generate password list |
| `--combo` | Generate `user:password` combos |
| `--no-users` | Skip username generation |
| `--no-at` | Skip `user@domain` format |
| `--no-ml` | Disable ML ranking for this command |
| `--year-start YYYY` | Start year (default: 2020) |
| `--year-end YYYY` | End year (default: 2026) |
| `-o, --output FILE` | Output file |

#### 6. `phone` — Phone Number Generation

Generate phone number wordlists with support for multiple countries, formats, and phone types.

```bash
python wfh.py phone [options]
```

| Flag | Description |
|------|-------------|
| `--country NAME` | Country: `brazil`, `usa`, `uk`, etc. |
| `--ddi CODE` | Country dialing code (e.g., `55`) |
| `--ddd CODE` | Area code (e.g., `11` for São Paulo) |
| `--type TYPE` | Phone type: `mobile`, `landline`, `all` |
| `--format FMT` | Output format: `e164`, `local`, `bare` |
| `-o, --output FILE` | Output file |

#### 7. `scrape` — Web Scraping

Extract words from web pages (CeWL-style) with customizable depth, proxy, and authentication.

```bash
python wfh.py scrape <URL> [options]
```

| Flag | Description |
|------|-------------|
| `<URL>` | Target URL |
| `--depth N` | Crawl depth |
| `--min-len N` | Minimum word length |
| `--max-len N` | Maximum word length |
| `--proxy URL` | Proxy URL |
| `--auth USER:PASS` | HTTP basic auth |
| `--headers "K:V"` | Custom headers (repeatable) |
| `--stopwords FILE` | Stopwords file to exclude |
| `-o, --output FILE` | Output file |

#### 8. `ocr` — OCR Text Extraction

Extract text from images using EasyOCR.

```bash
python wfh.py ocr <image_file> [options]
```

| Flag | Description |
|------|-------------|
| `<image_file>` | Input image path |
| `--lang LANG` | OCR language (default: `en`) |
| `-o, --output FILE` | Output file |

#### 9. `extract` — File Extraction

Extract wordlists from PDF, XLSX, DOCX, and image files.

```bash
python wfh.py extract <file1> [file2 ...] [options]
```

| Flag | Description |
|------|-------------|
| `<files>` | Input files (PDF, XLSX, DOCX, images) |
| `--min-len N` | Minimum word length |
| `-o, --output FILE` | Output file |

#### 10. `leet` — Leet Speak Variants

Generate leet speak permutations of input words.

```bash
python wfh.py leet <word> [options]
```

| Flag | Description |
|------|-------------|
| `<word>` | Input word or file |
| `-m, --mode MODE` | Mode: `basic`, `medium`, `aggressive`, `custom` |
| `--map FILE` | Custom leet mapping file (JSON) |
| `-o, --output FILE` | Output file |

#### 11. `xor` — XOR Encryption/Decryption

XOR encrypt, decrypt, or brute-force hex strings.

```bash
python wfh.py xor [options]
```

| Flag | Description |
|------|-------------|
| `--encrypt TEXT` | Encrypt plaintext |
| `--decrypt HEX` | Decrypt hex string with key |
| `--brute HEX` | Brute-force XOR key (1-byte) |
| `--key KEY` | XOR key (for encrypt/decrypt) |
| `-o, --output FILE` | Output file |

#### 12. `analyze` — Wordlist Analysis

Statistical analysis of wordlists (pipal-style). Extracts length distribution, charset frequency, hashcat masks, base words, and more.

```bash
python wfh.py analyze <wordlist> [options]
```

| Flag | Description |
|------|-------------|
| `<wordlist>` | Input wordlist file |
| `--top N` | Top N results per category |
| `--export FORMAT` | Export: `json`, `csv` |
| `-o, --output FILE` | Output file (for export) |

#### 13. `merge` — Merge & Deduplicate

Merge multiple wordlists with deduplication and filters.

```bash
python wfh.py merge <file1> <file2> [file3 ...] [options]
```

| Flag | Description |
|------|-------------|
| `<files>` | Input wordlist files |
| `--min-len N` | Minimum length filter |
| `--max-len N` | Maximum length filter |
| `--sort` | Sort output |
| `-o, --output FILE` | Output file |

#### 14. `dns` — DNS/Subdomain Fuzzing

Generate DNS subdomain fuzzing wordlists (alterx-style). Supports YAML templates and multi-domain input.

```bash
python wfh.py dns [options]
```

| Flag | Description |
|------|-------------|
| `-w, --wordlist FILE` | Base wordlist |
| `-d, --domain DOMAIN` | Target domain(s) (repeatable) |
| `--template FILE` | YAML template file |
| `--depth N` | Subdomain depth |
| `-o, --output FILE` | Output file |

#### 15. `pharma` — Healthcare/Pharmacy Patterns

Generate credential patterns specific to Brazilian healthcare and retail pharmacy chains.

```bash
python wfh.py pharma [options]
```

| Flag | Description |
|------|-------------|
| `-o, --output FILE` | Output file |

#### 16. `sanitize` — Wordlist Sanitization

Clean and normalize wordlists: deduplicate, sort, filter by regex or length, remove blank lines and comments. Supports in-place editing.

```bash
python wfh.py sanitize <wordlist> [options]
```

| Flag | Description |
|------|-------------|
| `<wordlist>` | Input wordlist file |
| `--min-len N` | Minimum length |
| `--max-len N` | Maximum length |
| `--regex PATTERN` | Keep only lines matching regex |
| `--sort` | Sort output |
| `--inplace` | Edit file in-place |
| `-o, --output FILE` | Output file |

#### 17. `reverse` — Reverse Line Order

Reverse the line order of a file (equivalent to `tac`).

```bash
python wfh.py reverse <file> [options]
```

| Flag | Description |
|------|-------------|
| `<file>` | Input file |
| `-o, --output FILE` | Output file |

#### 18. `corp-prefixes` — Corporate Prefix Usernames

Generate usernames using corporate prefix patterns — MSP, MSSP, SOC, DevOps, red/blue/purple team conventions, and more.

```bash
python wfh.py corp-prefixes [options]
```

| Flag | Description |
|------|-------------|
| `--category CAT` | Filter by category (e.g., `msp`, `soc`, `devops`, `redteam`) |
| `--name "First Last"` | Employee name |
| `--domain DOMAIN` | Target domain |
| `-o, --output FILE` | Output file |

#### 19. `train` — Train ML Pattern Model

Train the ML pattern learning model from existing wordlists and CSV exports.

```bash
python wfh.py train <wordlist> [options]
```

| Flag | Description |
|------|-------------|
| `<wordlist>` | Training wordlist (or CSV export from `analyze`) |
| `--epochs N` | Training epochs |
| `-o, --output FILE` | Model output path (default: `.model/pattern_model.json`) |

#### 20. `sysinfo` — Hardware & Compute Info

Display hardware profile (CPU, RAM, GPU) and available compute backends.

```bash
python wfh.py sysinfo
```

---

## Usage Examples

### Charset Generation

Generate all 6-to-8 character combinations of `abc123`:

```bash
python wfh.py charset 6 8 abc123 -o generated/charset_out.lst
```

Using hashcat mask syntax (uppercase + 4 digits + symbol):

```bash
python wfh.py charset 6 6 --mask "?u?u?d?d?d?d?s" -o generated/mask_out.lst
```

Constrained composition — exactly 2 digits, 3 lowercase, 1 special in 6-char passwords:

```bash
python wfh.py charset 6 6 --digits 2 --lower 3 --special 1 -o generated/constrained.lst
```

### Pattern Generation

Template with variables:

```bash
python wfh.py pattern -t "ACME{cod}@rd.com.br" --vars cod=1200-1300 -o generated/pattern_out.lst
```

Company-specific pattern with year:

```bash
python wfh.py pattern -t "{empresa}{ano}!" --vars empresa=acme --vars ano=2020-2026 -o generated/corp_pattern.lst
```

### Personal Target Profiling

Interactive mode (CUPP-style wizard):

```bash
python wfh.py profile -o generated/target_profile.lst
```

Non-interactive with YAML:

```bash
python wfh.py profile --profile-file target.yaml --leet medium -o generated/profile.lst
```

Non-interactive CLI:

```bash
python wfh.py profile --name "João Silva" --nick joao --birth 15/03/1990 --leet basic -o generated/joao.lst
```

### Corporate Target Profiling

```bash
python wfh.py corp --leet basic -o generated/corp_acme.lst
```

### Corporate Domain Users

From a file of employee names:

```bash
python wfh.py corp-users --domain acme.com.br --file employees.txt --passwords --combo -o generated/acme_users.lst
```

Manual names with custom separators:

```bash
python wfh.py corp-users --domain acme.com.br --names "João Silva,Maria Santos" --separators ".,_,-" --combo -o generated/acme_combo.lst
```

Online search with LinkedIn integration:

```bash
python wfh.py corp-users --domain acme.com.br --search "ACME Corp" --max-results 100 --passwords -o generated/acme_online.lst
```

Using all separators and ML ranking:

```bash
python wfh.py corp-users --domain acme.com.br --file names.txt --separators all --combo -o generated/acme_full.lst
```

### Phone Number Generation

Brazilian mobile numbers for São Paulo (DDD 11):

```bash
python wfh.py phone --country brazil --ddd 11 --type mobile --format e164 -o generated/phones_sp.lst
```

Bare format (digits only):

```bash
python wfh.py phone --ddi 55 --ddd 21 --type all --format bare -o generated/phones_rj.lst
```

### Web Scraping

```bash
python wfh.py scrape https://acme.com.br --depth 2 --min-len 4 -o generated/scraped_acme.lst
```

With proxy and authentication:

```bash
python wfh.py scrape https://intranet.acme.com.br --proxy http://127.0.0.1:8080 --auth admin:admin --depth 3 -o generated/intranet.lst
```

### OCR Extraction

```bash
python wfh.py ocr screenshot.png --lang pt -o generated/ocr_words.lst
```

### File Extraction

```bash
python wfh.py extract report.pdf spreadsheet.xlsx document.docx --min-len 5 -o generated/extracted.lst
```

### Leet Speak Variants

Basic mode:

```bash
python wfh.py leet "password" -m basic -o generated/leet_basic.lst
```

Aggressive mode from file:

```bash
python wfh.py leet wordlist.lst -m aggressive -o generated/leet_aggressive.lst
```

### XOR Crypto

Encrypt:

```bash
python wfh.py xor --encrypt "secret" --key "mykey"
```

Brute-force single-byte XOR:

```bash
python wfh.py xor --brute 4a5b6c7d
```

### Wordlist Analysis

Full statistical analysis with JSON export:

```bash
python wfh.py analyze passwords.lst --top 20 --export json -o generated/analysis.json
```

Quick terminal analysis:

```bash
python wfh.py analyze passwords.lst --top 10
```

### Merge Wordlists

```bash
python wfh.py merge list1.lst list2.lst list3.lst --sort --min-len 6 --max-len 32 -o generated/merged.lst
```

### DNS Fuzzing

```bash
python wfh.py dns -w subdomains.lst -d acme.com.br --depth 2 -o generated/dns_fuzz.lst
```

Multi-domain with YAML template:

```bash
python wfh.py dns -w words.lst -d acme.com.br -d acme.com --template dns_template.yaml -o generated/dns_multi.lst
```

### Healthcare / Pharmacy Patterns

```bash
python wfh.py pharma -o generated/pharma_creds.lst
```

### Sanitize Wordlist

Deduplicate, sort, and filter:

```bash
python wfh.py sanitize raw_list.lst --sort --min-len 6 --max-len 64 -o generated/clean.lst
```

In-place sanitization:

```bash
python wfh.py sanitize raw_list.lst --sort --inplace
```

Filter by regex (keep only lines with at least one digit):

```bash
python wfh.py sanitize raw_list.lst --regex ".*[0-9].*" -o generated/with_digits.lst
```

### Reverse Lines

```bash
python wfh.py reverse wordlist.lst -o generated/reversed.lst
```

### Corporate Prefixes

```bash
python wfh.py corp-prefixes --name "João Silva" --domain acme.com.br --category soc -o generated/soc_users.lst
```

### ML Model Training

Train from an existing wordlist:

```bash
python wfh.py train passwords.lst --epochs 10
```

Train from an analysis CSV export:

```bash
python wfh.py train analysis_export.csv --epochs 20 -o .model/custom_model.json
```

### System Info

```bash
python wfh.py sysinfo
```

### Multi-threading

Increase thread count for large-scale generation:

```bash
python wfh.py --threads 50 charset 6 10 lalpha-numeric -o generated/large.lst
```

High thread count (with confirmation warnings):

```bash
python wfh.py --threads 200 corp-users --domain acme.com.br --file big_names.txt --combo -o generated/acme_fast.lst
```

### CPU / GPU Compute

Force CPU backend:

```bash
python wfh.py --compute cpu charset 8 8 lalpha-numeric -o generated/cpu_out.lst
```

Use CUDA GPU:

```bash
python wfh.py --compute cuda charset 8 8 lalpha-numeric -o generated/gpu_out.lst
```

Hybrid mode (CPU + GPU):

```bash
python wfh.py --compute hybrid --threads 100 charset 6 10 mixalpha-numeric -o generated/hybrid.lst
```

### ML-based Ranking

ML is enabled by default. Disable it per command:

```bash
python wfh.py corp-users --domain acme.com.br --file names.txt --no-ml -o generated/no_ml.lst
```

Disable ML globally:

```bash
python wfh.py --no-ml corp-users --domain acme.com.br --file names.txt -o generated/noml_global.lst
```

---

## ML Model

WFH includes a lightweight ML pattern model that learns password composition patterns from real-world wordlists. The model ranks generated candidates by likelihood, placing the most probable passwords first.

**How it works:**

1. **Train** the model on curated wordlists or CSV exports from `analyze`:
   ```bash
   python wfh.py train wordlist.lst --epochs 10
   ```
2. The trained model is saved to `.model/pattern_model.json` (gitignored).
3. Subcommands like `corp-users` automatically use the model for ranking when available.
4. Disable ML with `--no-ml` (per command) or the global `--no-ml` flag.

**Training data:** The model learns character n-gram distributions, positional patterns, and structural features (e.g., "word + 4 digits + symbol" patterns). It does **not** store or reproduce individual passwords from the training set.

---

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/mrhenrike/WordListsForHacking).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Disclaimer

This tool and the wordlists in this repository are provided for **authorized security testing, penetration testing, education, and research purposes only**. The author is not responsible for any misuse or damage caused by this tool. Always ensure you have explicit written authorization before testing any system. Unauthorized access to computer systems is illegal in most jurisdictions.

**Use responsibly. Hack ethically.**

---

## Credits & Inspiration

WFH was built from scratch as a unified toolkit, inspired by the following projects:

| Project | Inspiration |
|---------|-------------|
| [CUPP](https://github.com/Mebus/cupp) | Personal target profiling approach |
| [Crunch](https://github.com/jim3ma/crunch) | Charset-based wordlist generation |
| [CeWL](https://github.com/digininja/CeWL) | Web scraping for wordlist creation |
| [alterx](https://github.com/projectdiscovery/alterx) | DNS/subdomain pattern generation |
| [pipal](https://github.com/digininja/pipal) | Statistical wordlist analysis |
| [SecLists](https://github.com/danielmiessler/SecLists) | Curated security wordlists reference |
| [elpscrk](https://github.com/D4Vinci/elpscrk) | Permutation-based password generation with levels |
| [BEWGor](https://github.com/berzerk0/BEWGor) | Biographical wordlist generator with zodiac/culture |
| [intelligence-wordlist-generator](https://github.com/zfrenchee/intelligence-wordlist-generator) | OSINT keyword permutation with connectors |
| [pnwgen](https://github.com/toxydose/pnwgen) | Phone number wordlist generation |

---

## Brazilian Wordlist (wlist_brasil.lst)

The file `passwords/wlist_brasil.lst` is the largest curated Brazilian password corpus available, with **~3.88 million unique entries**, generated by the WFH tool using its pattern, profile, charset, leet speak, corporate naming, and cultural word bank modules. Company names and CNPJs included are public data obtained via OSINT.

### How It Was Built

| Source Type | Description |
|-------------|-------------|
| **Cultural Word Banks** | Portuguese dictionary words, Brazilian names, soccer clubs, religious terms, regional slang — all from `data/behavior_patterns.json` |
| **Leet Speak** | Systematic character substitutions (a→@, e→3, o→0, s→$, etc.) applied to Portuguese words |
| **Keyboard Walks** | ABNT2/QWERTY keyboard walking patterns common in Brazilian environments |
| **Corporate Patterns** | Credential patterns from Brazilian corporate environments — company names and CNPJs are public data (Receita Federal / OSINT) |
| **Pattern Generation** | Template-based patterns: `{company}{sep}{code}`, `{name}{year}`, `{word}{separator}{number}`, etc. |
| **ML-Ranked** | WFH's ML model ranks generated entries by structural pattern probability |

### What's Inside

- Portuguese dictionary words and their leet speak variants
- Common Brazilian password structures (name+date, name+number, word+separator+digits)
- Corporate credential patterns (company+store_code, company+CNPJ, platform+CNPJ)
- Cultural phrases and expressions (sports, religion, politics, slang)
- Keyboard walk sequences for ABNT2 and QWERTY layouts
- Healthcare and retail chain patterns (public company names + public CNPJ data)

### Sanitization Rules Applied

- Minimum 5 characters
- Pure numeric entries removed (except CPF/CNPJ patterns)
- Formatting separators stripped from CPF/CNPJ patterns
- Fully deduplicated
- Company names and CNPJs are publicly available data (Receita Federal, OSINT)
- All entries are reproducible via WFH's generation modules

---

## Is My Password in This List?

If you want to check whether your password appears in `wlist_brasil.lst` (or any other wordlist), you can use the following methods:

### Using grep (Linux/macOS)

```bash
grep -qxF 'YourPasswordHere' passwords/wlist_brasil.lst && echo "FOUND — change it!" || echo "Not found"
```

### Using PowerShell (Windows)

```powershell
if (Select-String -Path passwords\wlist_brasil.lst -Pattern '^YourPasswordHere$' -SimpleMatch -Quiet) { "FOUND — change it!" } else { "Not found" }
```

### Using Python

```python
import sys
password = sys.argv[1]
with open("passwords/wlist_brasil.lst", "r") as f:
    found = any(line.strip() == password for line in f)
print("FOUND — change it!" if found else "Not found")
```

### Using WFH Analyze

```bash
# Create a file with your password and analyze it
echo "YourPassword" > /tmp/check.txt
python wfh.py analyze /tmp/check.txt --format text
```

### If Your Password Was Found

If your password appears in this list, it is considered **compromised** and should be changed immediately. Here are recommended actions:

1. **Change your password immediately** on all services where you use it
2. **Enable MFA/2FA** (Multi-Factor Authentication) on all accounts — use an authenticator app (Google Authenticator, Microsoft Authenticator, Authy) instead of SMS when possible
3. **Use a password manager** (Bitwarden, 1Password, KeePass) to generate and store unique passwords for each service
4. **Never reuse passwords** across multiple services
5. **Request a password reset** on critical services (banking, email, corporate accounts)
6. **Check for breaches** at [Have I Been Pwned](https://haveibeenpwned.com/) to see if your email/accounts have been compromised
7. **Review account activity** for any unauthorized access
8. **Use passwords with at least 14 characters** combining uppercase, lowercase, digits, and special characters — or use passphrases (4+ random words)

---

<p align="center">
  Created by <a href="https://github.com/mrhenrike">André Henrique (@mrhenrike)</a> — <a href="https://github.com/Uniao-Geek">União Geek</a>
</p>

<p align="center">
  <a href="README.pt-BR.md">Leia em Português</a>
</p>
