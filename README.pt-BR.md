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
  <a href="https://github.com/mrhenrike/WordListsForHacking/releases"><img src="https://img.shields.io/badge/version-2.6.1-blue?style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8%2B-yellow?style=flat-square" alt="Python"></a>
  <a href="https://github.com/mrhenrike/WordListsForHacking"><img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos%20%7C%20termux-lightgrey?style=flat-square" alt="Platform"></a>
  <a href="https://pypi.org/project/wfh-wordlist/"><img src="https://img.shields.io/pypi/v/wfh-wordlist?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI"></a>
</p>

<p align="center">
  Toolkit unificado de geração de wordlists para pentest autorizado, red team e treinamentos de segurança — 36 subcomandos em uma única CLI. Geração por charset/máscara, profiling pessoal e corporativo, scraping web (JS/CSS/PDF), OCR, parsing de documentos (PDF/XLSX/DOCX), leet speak, XOR crypto, DNS fuzzing, telefones, enumeração de usuários corporativos, padrões de credenciais para redes varejistas, base de credenciais default (IoT/ICS/SCADA/PLC/HMI), keyspace WiFi ISP, análise comportamental password-DNA, combinador de keywords, word mangling, merge e sanitização, ranking ML com corpus SecLists, análise estatística, gramática probabilística PCFG, geração Markov OMEN-style, geração por keyboard walks, auto-geração de regras hashcat, ataque PRINCE combinatorial, benchmarking de qualidade de wordlists, <strong>gerador de senhas por acrosstico de frases, motor de mutação de senha existente, gerador de variações dígito-para-texto (EN/PT/BR/ES), filtros globais de comprimento e verificação de espaço em disco.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> · Português (Brasil)
</p>

---

> **Autor:** André Henrique ([@mrhenrike](https://github.com/mrhenrike))
> **Versão:** 2.4.0 · **Licença:** MIT · **Python:** 3.8+

> **Documentação completa:** [Wiki](https://github.com/mrhenrike/WordListsForHacking/wiki)

---

## Aviso Legal

**Este repositório destina-se exclusivamente a testes de segurança autorizados, exercícios de red team, treinamentos de SOC e workshops acadêmicos.** Utilize apenas em ambientes com autorização explícita e por escrito. O autor não se responsabiliza por uso indevido.

---

## Quick Start

### Instalar via pip (recomendado)

```bash
pip install wfh-wordlist                # core (charset, profile, dns, scrape, analyze, ...)
pip install wfh-wordlist[docs]         # + extração PDF/XLSX/DOCX
pip install wfh-wordlist[scrape]       # + crawl de PDFs durante web scraping
pip install wfh-wordlist[ocr]          # + OCR (requer PyTorch)
pip install wfh-wordlist[full]         # todos os extras
```

Verificar instalação:

```bash
wfh --help                              # deve mostrar 31 subcomandos
pip show wfh-wordlist                   # verificar versão
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
| 24 | `combiner` | Combinador de keywords (estilo intelligence-wordlist-generator) |
| 25 | `password-dna` | Análise de padrões de senha e geração de variantes comportamentais |
| 26 | `pcfg` | Gramática probabilística PCFG — treino e geração (Weir et al.) |
| 27 | `markov` | Gerador Markov posicional estilo OMEN |
| 28 | `kwalk` | Gerador de senhas por keyboard walk (estilo kwprocessor) |
| 29 | `rulegen` | Auto-geração de arquivos .rule hashcat a partir de análise |
| 30 | `benchmark` | Benchmarking de qualidade de wordlists (métricas MAYA) |
| 31 | `prince` | Ataque PRINCE — combinação encadeada de elementos |
| 32 | `phrase` | Gerador de senha por acróstico de frase (estilo `@0x90` / hacker-suffix) |
| 33 | `mutate` | Motor de mutação de senha existente (case / leet / prefixo / sufixo) |
| 34 | `pharma` | Padrões de credenciais para redes varejistas (marca+id, sistema+CNPJ, usernames) |
| 35 | `br-names` | Gerador de usernames a partir de nomes brasileiros |
| 36 | `num2text` | Gerador dígito-para-texto com variações de case/leet/separador (EN/PT/BR/ES) |

> **Sintaxe detalhada e exemplos de cada subcomando:** [Wiki — Subcomandos](https://github.com/mrhenrike/WordListsForHacking/wiki)

### Flags Globais

```bash
python wfh.py --threads 20 --compute cuda --no-ml --min-len 8 --max-len 20 <subcomando>
```

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--threads N` | `5` | Threads de trabalho (1–300) |
| `--compute MODE` | `auto` | `auto` / `cpu` / `gpu` / `cuda` / `rocm` / `mps` / `hybrid` |
| `--no-ml` | off | Desabilitar ranking ML |
| `--min-len N` | `0` | Filtro global de comprimento mínimo (aplicado a todos os comandos) |
| `--max-len N` | `0` | Filtro global de comprimento máximo (aplicado a todos os comandos) |
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

## Password DNA

Analise padrões de senhas e gere variantes comportamentais. O subcomando `password-dna` extrai o "DNA" estrutural de senhas conhecidas (posições de maiúsculas, minúsculas, dígitos e símbolos) e produz novos candidatos que seguem os mesmos padrões comportamentais.

```bash
# Analisar uma lista de senhas conhecidas e gerar variantes
python wfh.py password-dna --input senhas_conhecidas.lst --depth 2 -o dna_variantes.lst

# Gerar variantes a partir de uma seed com expansão agressiva
python wfh.py password-dna --seed "Empresa2024!" --depth 3 --leet -o seed_variantes.lst

# Apenas relatório de análise DNA (sem geração)
python wfh.py password-dna --input senhas_conhecidas.lst --analyze-only --format json -o dna_relatorio.json
```

---

## Motor PCFG (Gramática Probabilística)

Treina uma gramática probabilística a partir de corpus de senhas e gera candidatos em **ordem de probabilidade** (mais provável primeiro). Baseado em Weir et al. (IEEE S&P 2009).

```bash
# Treinar gramática a partir de corpus
python wfh.py pcfg train --wordlist rockyou.txt

# Gerar candidatos (ordenados por probabilidade)
python wfh.py pcfg generate -o candidatos.lst --limit 1000000

# Ajuste fino com limites de estrutura/terminais
python wfh.py pcfg generate --top-structures 50 --top-terminals 100 --min-len 8
```

## Gerador Markov (OMEN-style)

Gerador de cadeia de Markov posicional estilo OMEN. Aprende transições de caracteres por posição e gera em ordem crescente de custo.

```bash
# Treinar modelo Markov (ordem 3)
python wfh.py markov train --wordlist leaked.txt --order 3

# Gerar com threshold de custo
python wfh.py markov generate --min-len 6 --max-len 12 --max-cost 30 --limit 500000
```

## Gerador de Keyboard Walk

Gera senhas baseadas em caminhadas de adjacência no teclado físico. Suporta layouts QWERTY, AZERTY, QWERTZ, Dvorak e numpad.

```bash
# Gerar walks QWERTY (comprimento 4-10)
python wfh.py kwalk --min-len 4 --max-len 10 -o walks.lst

# Múltiplos layouts, sem shift
python wfh.py kwalk --layout qwerty,numpad --no-shift --max-changes 2

# Listar layouts disponíveis
python wfh.py kwalk --list-layouts
```

## Auto-Geração de Regras Hashcat

Analisa senhas reais e gera automaticamente arquivos `.rule` compatíveis com hashcat extraindo padrões de transformação.

```bash
# Gerar arquivo .rule a partir de análise
python wfh.py rulegen --wordlist leaked.txt -o rules.rule --top-rules 200

# Com dicionário para melhor matching de base words
python wfh.py rulegen --wordlist passwords.lst --dictionary english.txt -o optimized.rule
```

## Ataque PRINCE

PRINCE (PRobability INfinite Chained Elements) gera senhas combinando múltiplas palavras de uma wordlist. Descobre senhas multi-word como `correcthorsebatterystaple`.

```bash
# Encadear 2-4 elementos de uma wordlist base
python wfh.py prince --wordlist top1000.txt --min-elem 2 --max-elem 4 -o prince.lst

# Com separador e permutações de case
python wfh.py prince --wordlist words.txt --separator "-" --case-permute --min-len 8
```

## Benchmark de Qualidade de Wordlists

Mede a eficácia de uma wordlist gerada contra um conjunto de referência. Reporta hit rate, eficiência, diversidade, cobertura por comprimento/charset e tempos estimados de crack.

```bash
# Benchmark contra um conjunto de senhas conhecido
python wfh.py benchmark --wordlist gerada.lst --reference rockyou_sample.txt

# Salvar relatório JSON
python wfh.py benchmark --wordlist output.lst --reference test_set.txt --json relatorio.json
```

---

## Base de Credenciais Default

Consulte a base integrada com 1.329+ credenciais de fábrica cobrindo 88 vendors e 14 protocolos — routers, switches, impressoras, câmeras IP, ICS/SCADA (PLCs, HMIs, RTUs), gateways IoT e mais.

```bash
# Listar todos os vendors suportados
python wfh.py default-creds --list-vendors

# Exportar credenciais de um vendor específico
python wfh.py default-creds --vendor siemens --format combo -o siemens_creds.lst

# Filtrar por protocolo (telnet, ssh, http, snmp, modbus, s7comm, etc.)
python wfh.py default-creds --protocol modbus --format user -o modbus_users.lst

# Buscar por categoria de dispositivo
python wfh.py default-creds --category ics --format combo -o ics_defaults.lst

# Exportar base completa como JSON
python wfh.py default-creds --export-all --format json -o all_defaults.json
```

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

## Novidades v2.6 — Geradores Adicionais

### Gerador de Senha por Acróstico de Frase

Gera senhas a partir da primeira letra de cada palavra de uma frase, com mutações de case, leet e sufixos estilo hacker.

```bash
# Frase → acróstico + variações
python wfh.py phrase "minha frase secreta corporativa" -o frase.lst

# Com prefixos e sufixos personalizados
python wfh.py phrase "é mais fácil pedir do que tentar quebrar" \
    --prefixes _,__ --suffixes @0x90,#0x90 -o frase.lst
```

### Motor de Mutação de Senha Existente

Gera variações exaustivas de uma senha base já conhecida.

```bash
# Mutar uma senha conhecida
python wfh.py mutate "Verao2024" -o mutacoes.lst

# Controlar profundidade leet e faixa de tamanho
python wfh.py mutate "admin123" --leet-mode aggressive --min-len 10 --max-len 25 -o mutacoes.lst
```

### Gerador de Credenciais para Redes Varejistas

Gera senhas e usernames seguindo padrões comuns em ambientes de varejo: marca + id-loja, sistema + CNPJ, prefixos de login internos.

```bash
# Senhas e usernames para uma marca
python wfh.py pharma --brand AcmePharma --ids 1200-1210 -o pharma.lst

# Só senhas, com CNPJ
python wfh.py pharma --brand RetailCo --abbrevs RC,RET --cnpj 01234567890123 --mode passwords

# Só usernames, domínio personalizado
python wfh.py pharma --brand BrandX --ids 1000-2000 --domains corp.com.br --mode usernames
```

### Gerador Dígito-para-Texto

Converte números (até 12 dígitos) para suas representações textuais com geração completa de variantes. Suporta EN, PT, BR (com formas femininas) e ES.

```bash
# Número único em inglês (padrão)
python wfh.py num2text --number 123
# → onetwothree, ONETWOTHREE, OneTwoThree, one-two-three, ...

# Português brasileiro (inclui variantes femininas: uma, duas)
python wfh.py num2text --number 12 --lang br
# → umdois, umaduas, Um-Duas, um_duas, ...

# Espanhol
python wfh.py num2text --number 123 --lang es
# → unodostres, UNODOSTRES, uno-dos-tres, una-dos-tres, ...

# Range em lote, salvo em arquivo
python wfh.py num2text --range 0-9999 --lang pt -o numeros_pt.lst
python wfh.py num2text --range 2000-2030 --lang br -o anos_br.lst
```

Aliases aceitos para `--lang`:

| Código | Aceita também | Idioma |
|--------|--------------|--------|
| `en` | `en-us`, `en-gb` | Inglês (padrão) |
| `pt` | `pt-pt` | Português europeu |
| `br` | `pt-br` | Português brasileiro |
| `es` | `es-es`, `es-mx`, `es-la` | Espanhol |

### Filtros Globais de Comprimento

Aplica filtro de comprimento mínimo/máximo na saída de **qualquer** subcomando.

```bash
python wfh.py --min-len 8 --max-len 20 charset 8 12 -o filtrado.lst
python wfh.py --min-len 10 mutate "admin" -o variantes_longas.lst
```

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
| [intelligence-wordlist-generator](https://github.com/MichaelDim02/intelligence-wordlist-generator) | Combinador de keywords |
| [SCaDAPass](https://github.com/scadastrangelove/SCaDAPass) | Credenciais default ICS/SCADA |
| [pcfg_cracker](https://github.com/lakiw/pcfg_cracker) | Gramática probabilística PCFG (Weir et al.) |
| [OMEN](https://github.com/RUB-SysSec/OMEN) | Ordered Markov ENumerator |
| [kwprocessor](https://github.com/hashcat/kwprocessor) | Geração de keyboard walks |
| [PACK](https://github.com/iphelix/pack) | Password Analysis and Cracking Kit (rulegen) |
| [princeprocessor](https://github.com/hashcat/princeprocessor) | Modo de ataque PRINCE |
| [MAYA](https://github.com/williamcorrias/MAYA-Password-Benchmarking) | Framework de benchmarking de wordlists |

---

## Contato

- **Suporte / dúvidas gerais:** [suporte@uniaogeek.com.br](mailto:suporte@uniaogeek.com.br)
- **Segurança:** [SECURITY.md](SECURITY.md)
- **Organização:** [União Geek](https://github.com/Uniao-Geek)

## Contributing

Contribuições são bem-vindas. Veja o [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[MIT License](LICENSE) — Copyright (c) 2026 André Henrique ([@mrhenrike](https://github.com/mrhenrike))

---

<p align="center">
  <strong>Autor:</strong> André Henrique (<a href="https://github.com/mrhenrike">@mrhenrike</a>) | <a href="https://github.com/Uniao-Geek">União Geek</a><br>
  <a href="mailto:suporte@uniaogeek.com.br">suporte@uniaogeek.com.br</a>
</p>

<p align="center">
  <a href="README.md">English version</a> · <a href="https://github.com/mrhenrike/WordListsForHacking/wiki">Documentação Completa (Wiki)</a>
</p>
