# WordListsForHacking

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
crunch 8 8 0123456789 -t "%%%%%%%%" | awk '{print $0"00010001"}' > cnpj-filtered.lst
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
for ddd in 11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 \
           41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 \
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
