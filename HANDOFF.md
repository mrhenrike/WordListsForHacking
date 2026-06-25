# HANDOFF — WordListsForHacking

## [2026-06-25] — v2.7.2 aliases unificados, leet numérico, defaults de export

### Estado ao encerrar
- Wizard: um único prompt para apelidos/nicknames/partes do nome (`field.aliases`)
- Leet mode: seleção por número 1–4 ou slug (none/basic/medium/aggressive)
- Finalização: prompts indicam defaults (Enter=sim/0/lst) + resumo `output.summary`
- `setup_venv.sh`: recria venv quebrado; usa `.venv/bin/pip` (PEP 668)

---

## [2026-06-25] — v2.7.1 wizard UX e seleção de motores

### Estado ao encerrar
- `generation_engines.py`: Enter no menu de motores usa defaults (`default_on`), não NUCLEAR; bloqueio de RAM antes do pipeline
- `profiler.py` / `archive_export.py`: i18n de saída corrigido; caminho único; `-o` respeitado; default em cwd
- `wfh.py`: menu interativo — exit sem prompt de output; validação de motores antes do preview
- `i18n/prompts.py`: labels de data, multi-line hint, mensagens de motores

### Próximo passo imediato
- Wiki: nota v2.7.1 changelog (wizard/profile)

---

## [2026-06-23] — Parsers CLI, fase 4 parity, README local-only

### Estado ao encerrar
- wfh.py: parsers expostos para `osint-perm`, `cupp`, `pattern-rank`, `scrape-target` (handlers já existiam)
- wfh.py: `--leet` default None — perfil YAML `leet_mode: aggressive` não é mais sobrescrito
- kwalk_gen.py: rotas explícitas via `--route` / `--route-file` (paridade kwprocessor)
- markov_engine.py: smoothing Laplace (`--smoothing`, default 0.01)
- combiner.py: dedup case-insensitive via `casefold()`
- prince_engine.py: flags `--wordlen-min/max` e `--superchop`
- sanitizer.py: senhas iniciando com `#` (ex. `#d@ryu5@CS`) não são tratadas como comentário
- profiler.py: pets pool prioriza nomes plain + sufixos de adoção; slices triple/pair ampliados
- pipeline_engine.py: `max_len` estende para `known_targets`; feedback após export final
- i18n: chaves `engines.cewl_mut.*` e `.desc` para motores principais
- README: badge PyPI removido; instalação só clone + requirements; 43 subcomandos
- **Melissa pipeline: 3/3 known_targets (100% hit rate)**

### Próximo passo imediato
- Wiki: documentar novos subcomandos e `improve`/`maya-rank`

### Pendências conhecidas
- [ ] Stress test CRC32 dedup >100k linhas em hardware alvo (use `sysinfo --crc32-stress 150000`)

### Ambiente necessário
- Python 3.9+
- PyYAML, requirements.txt
- Perfil Melissa: `Projetos-SafeLabs/laboratory/training/iot-xpl-forge/examples/melissa-andrade-profile.yaml`

### Paths importantes
- Linux: `/home/mrhenrike/Documentos/Projetos/Projetos-SafeLabs/submodules/Uniao-Geek/WordListsForHacking/`

## [2026-06-25 13:45] — Criação de rsmangler_engine e generation_engines

### Estado ao encerrar
- Criado `wfh_modules/rsmangler_engine.py`: port Python do RSMangler v1.5, todas as 20 regras de mangling, deduplicação via CRC32 em streaming, sem dependência Ruby
- Criado `wfh_modules/generation_engines.py`: registry completo de 28 motores, presets L/M/P/NUCLEAR, funções de seleção interativa com verificação de RAM
- Ambos os módulos passaram smoke tests (sem erros de lint)

### Próximo passo imediato
- Integrar `rsmangler_engine.mangle()` no pipeline do motor ID 11 (`rsmangler`) dentro do fluxo `profile` do WFH
- Conectar `generation_engines.ask_engine_selection()` ao CLI principal

### Pendências conhecidas
- [ ] Integrar `generation_engines.py` ao comando `profile` do CLI
- [ ] Wiring do motor 11 (rsmangler) com o profiler para receber tokens extraídos
- [ ] Testar dedup CRC32 com wordlists grandes (>100 k linhas) para medir colisões
- [ ] Adicionar chaves i18n ao bundle de tradução existente (`wfh_modules/i18n/`)

### Ambiente necessário
- Python 3.10+
- `psutil` opcional (RAM check para NUCLEAR; sem ele, threshold não bloqueia)

### Paths importantes
- Windows: `C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking\wfh_modules\`
- Linux: `/mnt/predator/Projetos-SafeLabs/submodules/Uniao-Geek/WordListsForHacking/wfh_modules/`

## [2026-06-25 14:25] -- Extensao dos modulos leet_permuter e osint_perm

### Estado ao encerrar
- Adicionado `leet_perm_wordlist()` em `leet_permuter.py`: produto cartesiano elpscrk-style sobre wordlist completa com deduplicacao CRC32 e limite max_per_word
- Adicionada constante `ELPSCRK_LEVELS` em `leet_permuter.py`
- Expandido `OsintProfile` com campos: `level`, `years`, `nums_range`, `special_chars`, `apply_post_leet`; `complexity` mantido como alias via `__post_init__`
- Adicionada `_recipes()` em `osint_perm.py`: suffixes por nivel 0-5
- Adicionada `post_leet_perm()` em `osint_perm.py`: passe global leet via leet_perm_wordlist
- `OsintPermGenerator.generate()` atualizado para usar `profile.level` + `_recipes()` + `post_leet_perm` opcional
- Todos os testes de verificacao passaram: 16 variantes leet, 702 candidatos nivel 2, compat reversa OK

### Arquivos modificados
- `wfh_modules/leet_permuter.py`
- `wfh_modules/osint_perm.py`

### Proximo passo imediato
- Commitar as mudancas se aprovado

### Pendencias conhecidas
- [ ] Opcional: expor leet_perm_wordlist via CLI
- [ ] Testar apply_post_leet=True com perfis grandes para medir impacto de memoria

### Ambiente necessario
- Python 3.9+ (usa from __future__ import annotations)
- Sem dependencias externas alem de stdlib

### Paths importantes
- Windows: `C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking\wfh_modules\`
- Linux: `/mnt/predator/Projetos-SafeLabs/submodules/Uniao-Geek/WordListsForHacking/wfh_modules/`

## [2026-06-25 14:20] — pcfg_engine detection rules + profiler CUPP extensions

### Estado ao encerrar
- Adicionadas 7 funcs de deteccao leves (pcfg_cracker parity) em pcfg_engine.py antes da classe PCFGGrammar: detect_keyboard_walk, detect_leet, detect_year, detect_email, detect_website, detect_phone, tag_segments
- Adicionados _KB_ROWS, _KB_ADJACENT, _LEET_DETECT_MAP, _YEAR_RE, _EMAIL_RE, _WEBSITE_RE, _PHONE_RE como constantes de modulo
- profiler.py: adicionado _BIRTHSTONES dict (12 meses), get_birthstone_tokens(month)
- profiler.py: adicionado _date_fragment_combos(date_tokens) - CUPP bdss/kbdss parity, max 200 combos, import de product adicionado
- profiler.py: adicionado improve_wordlist() publico - CUPP -w parity (leet, years, specials)
- generate_from_profile: integrado birthstones (se birth_month), maiden_name, e _date_fragment_combos yield

### Arquivos modificados
- wfh_modules/pcfg_engine.py (secao detection rules adicionada, ~130 linhas novas antes da classe)
- wfh_modules/profiler.py (import product, _BIRTHSTONES, get_birthstone_tokens, _date_fragment_combos, improve_wordlist, integracao em generate_from_profile)

### Proximo passo imediato
- Opcional: integrar tag_segments no _decompose() quando use_detection=True for necessario (nao pedido na sessao)

### Pendencias conhecidas
- [ ] tag_segments integration em PCFGGrammar._decompose() com use_detection=True (arquitetura definida, nao implementada)
- [ ] improve_wordlist nao exposta no CLI ainda

### Paths importantes
- Windows: C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking\wfh_modules\
- Linux: /mnt/predator/Projetos-SafeLabs/submodules/Uniao-Geek/WordListsForHacking/wfh_modules/

## [2026-06-25 18:10] — Wiring pipeline motores 13-19-26, post-rank 15/16, profiler gating

### Estado ao encerrar
- pipeline_engine.py: estagios markov (19), osint_scrape (13), scrape_merge (26); post-rank em run_to_file para motores 15 (pattern_rank) e 16 (maya_rank)
- target_spider.py: funcao spider_words() (corrigia import quebrado no cewl_mut)
- pcfg_engine.py: _decompose(use_detection=True) via tag_segments; train() aceita use_detection
- profiler.py: honra _active_engines nos yields (motores 2-9, 24-25); motor 6 phrase_full via _emit_phrase_full_combos
- wfh.py: correcao path default do cmd improve
- Smoke: pymangler, pipeline limitado, perfil Melissa (500 linhas) com post_rank motor 15 OK

### Arquivos modificados
- wfh_modules/pipeline_engine.py
- wfh_modules/target_spider.py
- wfh_modules/pcfg_engine.py
- wfh_modules/profiler.py
- wfh.py

### Proximo passo imediato
- Rodar pipeline completo Melissa sem max_candidates para validar known_targets (motores 17,21,22,28)
- Fase 4: kwalk_gen routes, web_scraper middlewares avancados

### Pendencias conhecidas
- [ ] Motor 19 markov requer corpus (old_passwords/markov_corpus) no perfil
- [ ] Motores 13/26 requerem target_url ou scrape_merge files
- [ ] Teste CRC32 dedup >100k linhas
- [ ] Commit no submodule quando usuario pedir

### Ambiente necessario
- Python 3.9+
- PyYAML para perfis .yaml
- requests+bs4 opcional (scrape motores 13/29)

### Paths importantes
- Windows: `C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking\`
- Linux: `/mnt/predator/Projetos-SafeLabs/submodules/Uniao-Geek/WordListsForHacking/`

## [2026-06-25 19:30] — Publicado no GitHub (continuar noutro PC)

### Estado ao encerrar
- Commit `7eae4a7` pushed para `origin/main` (mrhenrike/WordListsForHacking)
- Ver superprojeto `HANDOFF.md` entrada `[2026-06-25 19:30]` para bootstrap completo no outro PC

### Proximo passo imediato
- Pipeline Melissa full + validar 3 known_targets
- Fase 4: kwalk_gen, web_scraper cewler parity

