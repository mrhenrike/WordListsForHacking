# WordListsForHacking (WFH)

<p align="center">
  <img src="https://img.shields.io/github/stars/mrhenrike/WordListsForHacking?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/mrhenrike/WordListsForHacking?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-2.3.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/pypi/v/wfh-wordlist?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI">
</p>

**Unified wordlist generation toolkit for pentest and red team operations.** Combines charset generation, target profiling, web scraping (with JS/CSS/PDF extraction), OCR extraction, leet speak, DNS fuzzing, phone number generation, corporate user enumeration, default credential databases, ISP keyspace generation, ML-based ranking with SecLists corpus training, and statistical analysis — all in a single CLI tool.

> **Full documentation:** [Wiki](https://github.com/mrhenrike/WordListsForHacking/wiki)

---

> **DISCLAIMER:** This tool is intended **exclusively for authorized security testing, penetration testing, and educational purposes**. Unauthorized use against systems you do not own or have explicit written permission to test is **illegal** and unethical. The author assumes no liability for misuse.

---

## Quick Start

### Install via pip (recommended)

```bash
pip install wfh-wordlist            # core
pip install wfh-wordlist[full]      # all extras (OCR, document parsing)
```

### Or clone from source

```bash
git clone https://github.com/mrhenrike/WordListsForHacking.git
cd WordListsForHacking

# Linux / macOS / Termux
chmod +x setup_venv.sh && ./setup_venv.sh && source .venv/bin/activate

# Windows PowerShell
.\setup_venv.ps1; .\.venv\Scripts\Activate.ps1
```

### Run

```bash
wfh                        # interactive menu (pip install)
python wfh.py              # interactive menu (from source)
python wfh.py --help       # full CLI help
```

> **OS prerequisites (OCR only):** see the [Installation wiki page](https://github.com/mrhenrike/WordListsForHacking/wiki/Installation).

---

## Subcommands

| # | Command | Description |
|---|---------|-------------|
| 1 | `charset` | Charset/mask generation (crunch-style + hashcat masks) |
| 2 | `pattern` | Template-based generation with variables |
| 3 | `profile` | Personal target profiling (CUPP-style) |
| 4 | `corp` | Corporate target profiling |
| 5 | `corp-users` | Corporate domain user/password generation (50+ patterns) |
| 6 | `phone` | Phone number wordlists (BR, US, UK) |
| 7 | `scrape` | Web scraping (CeWL/CeWLeR-style) with JS/CSS/PDF extraction |
| 8 | `ocr` | OCR text extraction from images |
| 9 | `extract` | Extract words from PDF/XLSX/DOCX |
| 10 | `leet` | Leet speak permutations |
| 11 | `xor` | XOR encrypt/decrypt/brute-force |
| 12 | `analyze` | Statistical analysis (pipal-style) |
| 13 | `merge` | Merge & deduplicate wordlists |
| 14 | `dns` | DNS/subdomain fuzzing (alterx-style) |
| 15 | `pharma` | Healthcare/pharmacy credential patterns |
| 16 | `sanitize` | Clean & normalize wordlists |
| 17 | `reverse` | Reverse line order |
| 18 | `corp-prefixes` | Corporate prefix usernames (MSP/SOC/DevOps) |
| 19 | `train` | Train ML pattern model (local + SecLists corpus) |
| 20 | `sysinfo` | Hardware & compute info |
| 21 | `mangle` | Word mangling rules |
| 22 | `default-creds` | Query default credentials database (IoT/routers/printers/ICS) |
| 23 | `isp-keygen` | ISP default WiFi password keyspace generator |
| 24 | `combiner` | Keyword combiner (intelligence-wordlist-generator style) |

> **Detailed syntax and examples for each subcommand:** [Wiki — Subcommands](https://github.com/mrhenrike/WordListsForHacking/wiki)

### Global Flags

```bash
python wfh.py --threads 20 --compute cuda --no-ml <subcommand>
```

| Flag | Default | Description |
|------|---------|-------------|
| `--threads N` | `5` | Thread count (1–300) |
| `--compute MODE` | `auto` | `auto` / `cpu` / `gpu` / `cuda` / `rocm` / `mps` / `hybrid` |
| `--no-ml` | off | Disable ML ranking |
| `-v` | off | Verbose logging |

---

## Common Usage Examples

### Corporate pentest — generate users + passwords

```bash
python wfh.py corp-users --domain acme.com.br --file employees.txt --passwords --combo -o acme_combo.lst
```

### Personal target profiling

```bash
python wfh.py profile --name "João Silva" --nick joao --birth 15/03/1990 --leet aggressive -o target.lst
```

### Charset with hashcat mask

```bash
python wfh.py charset 8 8 --mask "?u?l?l?l?d?d?d?s" -o passwords.lst
```

### Template-based patterns

```bash
python wfh.py pattern -t "{company}{year}!" --vars company=acme,globex year=2020-2026 -o patterns.lst
```

### DNS subdomain fuzzing

```bash
python wfh.py dns -d acme.com.br --words dev staging api admin portal -o subdomains.lst
```

### Analyze an existing wordlist

```bash
python wfh.py analyze passwords.lst --top 30 --masks --format json -o analysis.json
```

### Default credentials lookup

```bash
python wfh.py default-creds --list-vendors
python wfh.py default-creds --vendor mikrotik --format combo -o mikrotik_creds.lst
python wfh.py default-creds --protocol snmp --format user -o snmp_users.lst
```

### ISP WiFi keyspace generation

```bash
python wfh.py isp-keygen --list
python wfh.py isp-keygen --isp xfinity_comcast --estimate
python wfh.py isp-keygen --isp xfinity_comcast --limit 100000 -o xfinity.lst
```

### Web scraping with JS/CSS/PDF

```bash
python wfh.py scrape https://target.com --include-js --include-css --include-pdf --lowercase -o words.lst
python wfh.py scrape https://target.com --emails --output-emails emails.txt --output-urls urls.txt
python wfh.py scrape https://target.com --subdomain-strategy children --stream -o stream.lst
```

### Merge & sanitize

```bash
python wfh.py merge list1.lst list2.lst --min-len 6 --sort -o merged.lst
python wfh.py sanitize merged.lst --inplace
```

> **More examples and scenarios:** [Wiki — Quick Start](https://github.com/mrhenrike/WordListsForHacking/wiki/Quick-Start)

---

## Wordlists

| File | Description | Entries |
|------|-------------|---------|
| `passwords/wlist_brasil.lst` | Brazilian password corpus — cultural word banks, corporate patterns, leet speak, keyboard walks. Company names and CNPJs are public OSINT data. | ~3.88M |
| `passwords/default-creds-combo.lst` | Default credential user:password combos (routers, printers, ICS/SCADA) | ~3K |
| `data/default_credentials.json` | Structured default credentials database (1,329 entries, 88 vendors, 14 protocols) | — |
| `fuzzing/discovery_br.lst` | Brazilian web discovery & API fuzzing paths | ~900 |
| `usernames/username_br.lst` | Brazilian + global username patterns | ~1.6K |
| `labs/*.lst` | Workshop & training wordlists | — |

> **Details:** [Wiki — Brazilian Wordlist](https://github.com/mrhenrike/WordListsForHacking/wiki/Brazilian-Wordlist)

---

## Is My Password in This List?

```bash
# Linux/macOS
grep -qxF 'YourPassword' passwords/wlist_brasil.lst && echo "FOUND!" || echo "Not found"

# Windows PowerShell
Select-String -Path passwords\wlist_brasil.lst -Pattern '^YourPassword$' -SimpleMatch -Quiet
```

If found: **change it immediately**, enable MFA/2FA, use a password manager, and never reuse passwords.

> **Full guide:** [Wiki — Password Check](https://github.com/mrhenrike/WordListsForHacking/wiki/Password-Check)

---

## ML Model

WFH includes a lightweight ML model that ranks generated candidates by structural pattern probability. Train it with local data or the SecLists corpus:

```bash
python wfh.py train --auto                    # local wordlists only
python wfh.py train --seclists                # SecLists corpus (auto-discover)
python wfh.py train --auto --seclists         # combined (recommended)
python wfh.py train --seclists /path/to/SecLists --seclists-categories password frequency
```

The model stores **only structural patterns** — no PII, passwords, or company names.

> **Details:** [Wiki — ML Model](https://github.com/mrhenrike/WordListsForHacking/wiki/ML-Model)

---

## Credits & Inspiration

| Project | Inspiration |
|---------|-------------|
| [CUPP](https://github.com/Mebus/cupp) | Personal target profiling |
| [Crunch](https://github.com/jim3ma/crunch) | Charset-based generation |
| [CeWL](https://github.com/digininja/CeWL) | Web scraping for wordlists |
| [CeWLeR](https://github.com/roys/cewler) | Modern Python web scraping (JS/CSS/PDF) |
| [routersploit](https://github.com/threat9/routersploit) | Default credentials for IoT/routers |
| [alterx](https://github.com/projectdiscovery/alterx) | DNS/subdomain fuzzing |
| [pipal](https://github.com/digininja/pipal) | Statistical analysis |
| [SecLists](https://github.com/danielmiessler/SecLists) | Curated security lists |
| [elpscrk](https://github.com/D4Vinci/elpscrk) | Permutation-based generation |
| [BEWGor](https://github.com/berzerk0/BEWGor) | Biographical wordlist generator |
| [pnwgen](https://github.com/toxydose/pnwgen) | Phone number generation |

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT License](LICENSE) — Copyright (c) 2026 André Henrique ([@mrhenrike](https://github.com/mrhenrike))

---

<p align="center">
  Created by <a href="https://github.com/mrhenrike">André Henrique (@mrhenrike)</a> — <a href="https://github.com/Uniao-Geek">União Geek</a>
</p>

<p align="center">
  <a href="README.pt-BR.md">Leia em Português</a> · <a href="https://github.com/mrhenrike/WordListsForHacking/wiki">Full Documentation (Wiki)</a>
</p>
