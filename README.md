# WordListsForHacking
Compiled list of words tested and used in everyday life, to meet the need for a list for Pentesters focused on common words from real environments in Brazil and other clients in the world.

**Portuguese (pt-BR):** [README.pt-BR.md](README.pt-BR.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
+ This list of words was created 4 years ago and is being updated whenever possible.

|Title|Description|
|----|--|
| wlist_brasil.lst | Brazilian words based on my experience (music, musicians, bands, famous people, artists, tv shows, food and churches) with 5 or more characters |
| usernames_br.lst  | Most popular usernames from Brazil |
| labs_passwords.lst  | Most common passwords that I use in my class and events |
| labs_users.lst  | Most common users that I use in my class and events |
| labs_mikrotik_pass.lst  | Most common passwords that I use in my class and events with MikrotikAPI-BF tool |

- - -
## Wordlists from SecLists
+ SecLists is the security tester's companion

**Zip**
```
wget -c https://github.com/danielmiessler/SecLists/archive/master.zip -O SecList.zip \
  && unzip SecList.zip \
  && rm -f SecList.zip
```

**Git (Small)**
```
git clone --depth 1 \
  https://github.com/danielmiessler/SecLists.git
```

**Git (Complete)**
```
git clone https://github.com/danielmiessler/SecLists.git
```

**Kali Linux** ([Tool Page](https://www.kali.org/tools/seclists/))
```
$sudo apt -y install seclists

After the installation, you can locate this wordlist in:
/usr/share/seclists
```
- - -

## Others Wordslist
**OpenOffice Dictionary (various world languages)**
```
Debian-based, Ubuntu, Kali Linux:
$ sudo apt install wbrazilian -y

For other languages choice the packet:
wgerman-medical
wesperanto
wcanadian-small
wcanadian-large
wcanadian-insane
wcanadian-huge
wcanadian
wbritish-small
wbritish-large
wbritish-insane
wbritish-huge
wamerican-small
wamerican-large
wamerican-insane
wamerican-huge
wukrainian
wswiss
wswedish
wspanish
wportuguese
wpolish
wogerman
wnorwegian
wngerman
witalian
wgalician-minimos
wfrench
wfaroese
wdutch
wdanish
wcatalan
wbulgarian
wbritish
wbrazilian
wamerican
miscfiles

After the installation, you can locate this wordlist in:
/usr/share/dict/
```

### Compiled from:
+ **Personal and hands-on experience with clients in Brazil**
+ [BRDumps/wordlists](https://github.com/BRDumps/wordlists)
+ [sysevil/Brazilian-wordlist](https://github.com/sysevil/Brazilian-wordlist)
+ [cyb3rp4c3/brazilian-wordlists](https://github.com/cyb3rp4c3/brazilian-wordlists)
+ [Mr-P4p3r/wordlist-br](https://github.com/Mr-P4p3r/wordlist-br)
+ [mmatje/br-wordlist](https://github.com/mmatje/br-wordlist)

---

## License

This project is released under the **MIT License** — see [LICENSE](LICENSE).

Previously the repository used **GNU GPLv3**; as the sole rights holder, the license was **relicensed to MIT** to simplify reuse, forks, and contributions while still requiring **preservation of copyright notices** in distributions.

---

<!-- LEGAL-NOTICE-UG-MRH -->

## Aviso legal / legal notice

- **Uso** — Listas para pesquisa, educação e testes **autorizados** (ex.: pentest com contrato). Não utilize para acesso não autorizado ou violação de lei.
- **Sem garantia** — Conteúdo **AS IS**; sem garantias de exaustividade, correção ou adequação a qualquer fim.
- **Responsabilidade** — O autor **não responde** por danos, uso indevido ou reclamações de terceiros; **uso por sua conta e risco**.
- **Atribuição** — Mantenha os avisos de copyright e referência a este repositório ao redistribuir. Contribuições via **pull request** são bem-vindas.
- **Conteúdo de terceiros** — Referências a [SecLists](https://github.com/danielmiessler/SecLists) e outras fontes mantêm as **licenças originais** desses projetos quando você copiar material deles diretamente.
