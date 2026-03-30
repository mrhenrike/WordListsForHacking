# WordListsForHacking

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
crunch 8 8 0123456789 -t "%%%%%%%%" | awk '{print $0"00010001"}' > cnpj-filtered.lst
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
for ddd in 11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 \
           41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 \
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

## Verifique se Sua Senha Está Nesta Lista

Você pode verificar rapidamente se sua senha aparece em `wlist_brasil.lst` usando
ferramentas nativas do sistema — **sem precisar instalar nada**.

> ⚠️ Faça essa verificação **offline**, após baixar o arquivo localmente.
> Nunca digite sua senha real em um formulário online nem a transmita pela rede.

### Passo 1 — Baixar o arquivo

```bash
# Linux / macOS
wget https://raw.githubusercontent.com/mrhenrike/WordListsForHacking/main/wlist_brasil.lst
# ou
curl -O https://raw.githubusercontent.com/mrhenrike/WordListsForHacking/main/wlist_brasil.lst
```

```powershell
# Windows PowerShell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/mrhenrike/WordListsForHacking/main/wlist_brasil.lst" `
  -OutFile "wlist_brasil.lst"
```

### Passo 2 — Buscar sua senha

Substitua `suasenha` pela senha que deseja verificar.

```bash
# Linux / macOS — correspondência exata, diferencia maiúsculas/minúsculas
grep -Fx "suasenha" wlist_brasil.lst \
  && echo "⚠️  ENCONTRADA — MUDE SUA SENHA IMEDIATAMENTE" \
  || echo "✓  Não encontrada nesta lista"
```

```bash
# Linux / macOS — sem diferenciar maiúsculas (captura variantes leet também)
grep -Fix "suasenha" wlist_brasil.lst \
  && echo "⚠️  ENCONTRADA — MUDE SUA SENHA IMEDIATAMENTE" \
  || echo "✓  Não encontrada nesta lista"
```

```powershell
# Windows PowerShell — correspondência exata
$result = Select-String -Path "wlist_brasil.lst" -Pattern "^suasenha$" -CaseSensitive
if ($result) { Write-Host "⚠️  ENCONTRADA — MUDE SUA SENHA IMEDIATAMENTE" -ForegroundColor Red }
else          { Write-Host "✓  Não encontrada nesta lista" -ForegroundColor Green }
```

```cmd
:: Windows CMD — correspondência exata
findstr /x /c:"suasenha" wlist_brasil.lst
:: Se aparecer alguma saída: sua senha foi encontrada. Mude-a imediatamente.
```

### Passo 3 — O que fazer se sua senha for encontrada

1. **Mude imediatamente** em todos os serviços onde a utiliza
2. **Nunca reutilize senhas** — cada conta deve ter uma credencial única
3. **Use um gerenciador de senhas**: [Bitwarden](https://bitwarden.com) (gratuito/open-source),
   KeePass, 1Password ou o cofre nativo do seu sistema
4. **Gere senhas verdadeiramente aleatórias** — evite: nomes, datas, sequências de
   teclado, nomes de empresas, times de futebol, letras de músicas ou variações
   leet de palavras do dicionário
5. **Ative MFA/2FA** em todas as contas que oferecem esse recurso

> **Importante:** se sua senha for encontrada aqui, isso **não** significa que ela
> foi extraída de um vazamento, vault ou sistema PAM específico. Significa que ela
> segue um **padrão previsível** que esta wordlist foi construída para detectar —
> e que qualquer atacante motivado tentaria primeiro. Encare isso como um alerta.

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
