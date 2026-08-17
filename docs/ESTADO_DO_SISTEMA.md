# Estado do Sistema & Diário de Bordo — Passa Fácil

> **📖 PARA A IA (Claude Code): leia este arquivo INTEIRO no início de cada sessão.**
> Ao terminar qualquer trabalho relevante, **atualize**:
> 1. a seção **Estado atual das features** (o que mudou de status);
> 2. a seção **Pendências** (o que virou próximo passo);
> 3. adicione uma entrada nova no topo do **Diário de bordo** (data + o que foi feito, onde, e por quê).
> Este arquivo é a **fonte da verdade** entre sessões — a memória do assistente é volátil, este arquivo não. Nunca apague histórico do diário; só acrescente.
> Datas no formato AAAA-MM-DD. Não guarde segredos aqui (chaves ficam em `/etc/passafacil.env`).

---

## 1. Visão geral / arquitetura

- **Produto:** app de estudo adaptativo para concursos (foco: TCE-SP 2026, cargo de TI).
- **Monorepo:** `apps/api` (backend) + `apps/web` (frontend).
- **Backend:** FastAPI (Python), SQLAlchemy 2.0. HTTP externo feito **só com a stdlib `urllib`** (padrão do projeto — sem `httpx`/`requests`). Sem Alembic: micro-migrações idempotentes em `apps/api/app/main.py` (`_ensure_columns`, via `ALTER TABLE ... ADD COLUMN`).
- **Frontend:** Next.js (App Router). A tela principal é praticamente toda `apps/web/app/page.tsx` (arquivo grande, com todas as "views"). Estilos em `apps/web/app/globals.css` (com modo claro/escuro via `[data-theme]`).
- **Banco:** Postgres em produção; SQLite em dev. Tabelas criadas no startup (`Base.metadata.create_all`) + seed idempotente do TCE-SP.

## 2. Onde as coisas moram (produção — passafacil.jussa.com.br)

| Item | Caminho / valor |
|---|---|
| Código | `/home/jussa/FileShare/development/passa_facil` |
| venv da API | `apps/api/.venv` |
| **Segredos / chaves** | **`/etc/passafacil.env`** (`root:jussa`, `0640`) — **NUNCA** no repo (está no `.gitignore`) |
| API | `127.0.0.1:9000` — uvicorn via systemd `passafacil-api.service` (WorkingDirectory `apps/api`, `EnvironmentFile=-/etc/passafacil.env`) |
| Web | `127.0.0.1:9001` — Next standalone via systemd `passafacil-web.service` (node do nvm) |
| Postgres | `127.0.0.1:5433` — container Docker `passafacil-postgres` |
| Proxy/SSL | Apache (`infra/apache/*.conf`) + Let's Encrypt |
| Unit files (versionados) | `infra/systemd/passafacil-{api,web}.service` |
| Doc de deploy | `docs/DEPLOY_DEBIAN.md` |

**Modelo mental do deploy:** a API e a web rodam direto da árvore de código via systemd (a API **não** usa Docker; só o Postgres usa). Então "publicar" mudança de backend = editar o código na árvore + **`sudo systemctl restart passafacil-api`**. Mudança de frontend exige rebuild do Next (`.next/standalone`) antes de reiniciar a web.

## 3. Como rodar / testar

- **O dono testa SEMPRE em produção, no servidor** (não usar `.env` local; não criar `apps/api/.env`).
- Aplicar mudança de backend no ar: salvar o código → `sudo systemctl restart passafacil-api` → validar `curl -s http://127.0.0.1:9000/health`.
- **Aplicar mudança de FRONTEND no ar (não esquecer — mudança em `apps/web` NÃO aparece sem rebuild!):**
  ```bash
  export PATH="/home/jussa/.nvm/versions/node/v24.1.0/bin:$PATH"
  export NEXT_PUBLIC_API_URL="https://passafacil.jussa.com.br/api/v1"  # ⚠️ OBRIGATÓRIO
  cd apps/web && ./node_modules/.bin/next build            # 1) build standalone
  rm -rf .next/standalone/.next/static && cp -r .next/static .next/standalone/.next/static  # 2) copiar assets
  sudo systemctl restart passafacil-web                     # 3) reiniciar
  ```
  ⚠️ **NUNCA rode `next build` sem exportar `NEXT_PUBLIC_API_URL`.** O Next embute o valor no bundle em tempo de build; sem ele, o front cai no default `http://localhost:9000/api/v1` e **quebra o login/todas as chamadas** no navegador do usuário.
  Conferir no ar: `curl -s http://127.0.0.1:9001/ -o /dev/null -w "%{http_code}\n"`; garantir que o bundle tem a URL de produção e **não** `localhost`: `grep -rl localhost:9000 .next/standalone/.next/static/`.
- Adicionar/rotacionar um segredo: editar `/etc/passafacil.env` → `sudo systemctl restart passafacil-api`.
- Ver o ambiente que o processo enxerga: `sudo tr '\0' '\n' < /proc/$(systemctl show passafacil-api -p MainPID --value)/environ`.

## 4. Estado atual das features

- **Auth** (JWT), **billing** (Asaas Pix — `asaas_sandbox=true` por padrão), **conversão Google Ads server-side** (desligada por padrão), **feedback** (widget "Fale conosco"), **banco de questões / import de PDF**, **simulados**, **revisões**, **estudo do dia**, **teste grátis** (telemetria anônima, retenção 180 dias — LGPD).
- **Correção por IA das discursivas (Fase 2) — ✅ NO AR (2026-08-16).** `apps/api/app/services/grading.py`: cascata de provedores gratuitos (Groq → Gemini → OpenRouter → Cerebras) via endpoint compatível com a API OpenAI. Corrige critério a critério com **crédito parcial**; nota salva em `discursive_submissions.ai_*`. Sem chaves/falha → **degrada para a autoavaliação manual** (Fase 1). Hoje ativa com **Groq (principal) + Gemini (`gemini-flash-latest`, fallback)** — cascata validada no ar (Groq 503 simulado → cai no Gemini e corrige). Cerebras e OpenRouter ficam **fora da cascata** (exigem crédito/cartão); chaves/modelos prontos para retomar depois. **A autoavaliação manual foi REMOVIDA da tela** (confundia): agora a IA marca os três botões (Não completou / Em parte / Completou) com nota realista por critério. Se a IA falhar (raro), mostra aviso "correção indisponível" — sem self-scoring.
- **Áudio-piloto:** 8 MP3 estáticos (voz ElevenLabs) em `apps/api/media/audio_pilot/`, servidos em `/api/v1/study/audio-pilot` só para o dono revisar. Menu "Áudios" segue **"em breve"**. A chave **`ELEVENLABS_API_KEY` está guardada em `/etc/passafacil.env`** (o app **não a consome** — os áudios são pré-gerados e servidos estáticos). O que **não** está versionado é o *script* de geração (foi descartável); a chave nunca se perdeu.

## 5. Pendências / próximos passos

- [x] **Full remake — F1 aplicada em produção** (2026-08-17, commit `079275e`; 8 tabelas + colunas criadas, 1074 questões preservadas). Branch `feat/full-remake-adaptativo` **não mesclada na `main` ainda**.
- [ ] **Full remake — Sessão B = F2**: confiança (chutei/dúvida/confiante), feedback adaptativo por alternativa/misconception, microaula em camadas 1/2/3 — para **pagos logados + gratuitos** (nunca owner-only, ver §2.1 do doc de arquitetura). Mexe em rotas + `page.tsx` → exige rebuild de front.
- [ ] **Mesclar** o branch `feat/correcao-ia-discursivas` na `main` (quando o dono aprovar).
- [x] **Gemini** adicionado como fallback (chave no `/etc`, modelo `gemini-flash-latest`) — cascata Groq→Gemini validada no ar.
- [ ] **Escalar a cascata quando crescer a base de assinantes:** Cerebras (chave `csk-…` já no `/etc`, modelo `gpt-oss-120b`) e/ou OpenRouter — ambos exigem crédito/cartão. Retomar é só incluir o nome no `GRADING_ORDER` + garantir crédito na conta.
- [ ] Feature de **Áudios** ainda "em breve". Se for regerar/ampliar: criar `apps/api/scripts/gerar_audios.py` **versionado**, lendo `ELEVENLABS_API_KEY` do `/etc` (nunca hardcoded).
- [x] Pagamento Asaas em **produção** (`ASAAS_SANDBOX=false` no `/etc`) — o default do código é `true`, o `/etc` sobrescreve.

## 6. Convenções / lições aprendidas

- **HTTP externo:** sempre `urllib` + **`User-Agent` explícito**. ⚠️ O WAF (Cloudflare) da Groq responde **HTTP 403** ao `User-Agent` padrão do Python (`Python-urllib/x.y`). Todo cliente HTTP novo deve mandar um UA próprio (ver `services/grading.py`).
- **Testes que batem em rede:** mock esconde erros de borda (WAF, headers). Validar de verdade contra o serviço no ar antes de dar como pronto.
- **Migrações:** sem Alembic — acrescentar colunas em `main.py::_ensure_columns` (idempotente, funciona em Postgres e SQLite).
- **Git:** trabalhar em branch de feature; **só commitar/pushar quando o dono pedir**. O working tree costuma ter muita coisa não commitada — conferir escopo antes de `git add -A`.
- **Segredos:** só em `/etc/passafacil.env` + restart. Nunca commitar `.env`.

---

## 7. Diário de bordo

### 2026-08-17 (full-remake · Sessão A) — F0 auditoria + F1 modelo de dados
- Início do **"full remake"** (plataforma adaptativa; spec em `full_remake/full-remake.txt`, 10 fases). Trabalho por **blocos de sessão** para economizar créditos — esta é a **Sessão A = F0 + F1**. **Branch dedicada `feat/full-remake-adaptativo`**, **commit `079275e`** (ainda não mesclado/pushado).
- **F0 (auditoria):** criado **`docs/adaptive-learning-architecture.md`** — estado atual, incompatibilidades com a spec (I1–I14), estratégia de migration e o modelo de dados da F1. Leitura obrigatória para as próximas fases.
- **F1 (modelo de dados + migrations), aditivo e seguro:**
  - **8 tabelas novas** em **`apps/api/app/models/adaptive.py`**: `skills`, `skill_relations`, `question_skills`, `misconceptions`, `option_misconceptions`, `user_skill_states`, `learning_events`, `question_families` (criadas por `create_all`). Registradas em `models/__init__.py`.
  - **Colunas novas** (ao lado das originais, todas nullable/com default): em `questions` (`primary_skill_id`, `question_family_id`, `difficulty`, `question_type`, `review_status`, `content_version`, `ai_generated`, `reviewed_at/by`, **`original_explanation`**, **`original_micro_lesson`**) e em `attempts` (`confidence`, `hints_used`, `session_id`, `skill_id`, `is_transfer`). Adicionadas ao ORM (`entities.py`) **e** ao `main.py::_ensure_columns` (padrão do projeto — mesma dupla de `gclid`/`ai_*`).
  - **DDL do `_ensure_columns` agora é dialect-aware** (UUID → `UUID` no Postgres / `CHAR(32)` no SQLite; timestamp tz correto) para casar com o tipo que o ORM gera em bases novas.
  - **Enums das entidades novas como `String` + constantes** (não Enum nativo do Postgres): sem Alembic, `ALTER TYPE ADD VALUE` seria doloroso e esses vocabulários vão evoluir. Rationale no doc §3.
- **Validação real (SQLite scratch):** cenário *base nova* (create_all cria as 8 tabelas + colunas) e cenário *upgrade de banco existente* (colunas entram numa tabela antiga **sem perder a linha existente**, defaults aplicados); `_ensure_columns` **idempotente** (roda 2× sem erro). Import da app OK. Testes: as 4 falhas de `test_auth.py` são **pré-existentes/ambientais** (owner 401 sem OWNER; `reportlab` ausente) — confirmado por baseline com meu código em stash; **sem regressão**.
- **F1 NÃO altera comportamento** de nenhuma rota/UI. **APLICADA EM PRODUÇÃO** (2026-08-17, `restart passafacil-api`): health 200; confirmado no Postgres — 8 tabelas novas criadas, colunas novas em `questions`/`attempts` (`primary_skill_id` como `UUID` nativo), e **1074 questões preservadas** (zero perda). Sem rebuild de front (nada mudou em `apps/web`).
- **Próxima sessão (B):** F2 — confiança (chutei/dúvida/confiante), feedback adaptativo por alternativa/misconception e microaula em camadas 1/2/3.

### 2026-08-17 (acervo) — ingestão das 64 imagens de `novas/` (pipeline resumível)
- Criado o **acervo** em `docs/acervo/` a partir das 64 imagens JPG de estudo (Gran Concursos, Maratona TCE-SP 2026 — Conhecimentos Gerais: Português, RLM, Ética/OCDE, Legislação; + estudos de caso). Pipeline **anti-quebra-de-sessão**: cada imagem lida vira JSON em disco + checkpoint em `ingest/_manifest.json` (retomável). Ver `docs/acervo/README.md`.
- **Resultado (64/64 processadas):** 62 concluídas, 1 duplicata descartada (`quest2bRaciocinio`), 1 bloqueada (`qUEST1b` — faltam alternativas D/E). Entregas:
  - **19 questões objetivas** com micro-aula + pegadinha (`questoes/{logica,portugues,etica,legislacao}.json`), prontas para import, dedup por content_hash — **validadas** (hashes únicos, sem erros).
  - **Acervo de leis** (`leis/*.json` + `.md`): 18 dispositivos (CF/88 70-75, LC 709/93, Regimento, Lei 10.261/68, Instruções 1/2024, LRF) com macro-resumo + pegadinhas + "para discursiva" — base do futuro módulo "decorar leis".
  - **OCDE** (`etica/integridade-ocde.*`): 4 pilares + 10 princípios com correspondência na Lei 14.133/2021. + Código de Ética SP (Decreto 69.328/2025).
  - **3 estudos de caso** (`estudos_caso/casos.json`) modelados como `DiscursiveCase` (enunciado + espelho + micro-aula + grade — **rascunho a revisar**).
  - **Observações** (`observacoes/padroes.md`): ranking de probabilidade por norma, checklist "7 pontos", regra-mestra VUNESP (troca prazo/quórum/competência/órgão). Pendências em `observacoes/insumos_faltantes.md`.
- **Como aplicar no banco:** `apps/api/scripts/importar_acervo.py` (versionado, idempotente, dedup). `--dry-run` para simular. Questões entram **owner_only / não publicadas** (revisão do dono antes de publicar). **AINDA NÃO EXECUTADO** — aguarda o dono revisar os artefatos.
- Nenhuma alteração em produção nesta fase (só arquivos no repo).

### 2026-08-17 (deploy) — acervo aplicado no banco + front reconstruído
- **Import aplicado em produção:** `importar_acervo.py` gravou **32 questões** (0 duplicatas, 12 tópicos novos). 13 de Noções de Informática entraram **publicadas** (authorial); as 19 do acervo de imagens entraram **owner_only** (revisão). Matéria `etica` criada no banco (o seed de produção era o antigo, com Ética junto de Legislação).
- **Front reconstruído e no ar** com a navegação do simulado (Anterior/Próxima + retomada estável). Bundle com a URL de produção (sem localhost); web 200.
- **Questão do mnemônico MANÉ** (para conferência do dono): ID `2e058342-377e-4988-a640-5116f239a1a7` (Raciocínio Lógico → Estruturas lógicas; negação de condicional "trabalhadora e honesta"). A `rlm-q05` (jovens/sociedade) também traz o MANÉ.

### 2026-08-17 (simulado) — navegação anterior/próxima + retomada estável
- **Simulado (`apps/web/app/page.tsx`, componente `QuestionsView`):** cada questão numerada (N/total) com botões **Anterior/Próxima** (setas) para revisitar qualquer questão do lote; o estado (seleção/resultado) é preservado por questão via `answersMap` ao navegar.
- **Retomada:** ao sair e voltar, o simulado abre na **última questão aberta e não respondida** (localStorage `RESUME_KEY`, por ID), agora **sem reordenar** o lote (numeração estável — antes a questão de retomada era movida para a posição 1). Front sem mudança de backend.
- **Deploy:** exige rebuild do front (`next build` COM `NEXT_PUBLIC_API_URL` + copiar `.next/static` + restart `passafacil-web`) — ver seção 3.
- **Questões de Noções de Informática** (`docs/acervo/questoes/informatica.json`) marcadas `rights_status=authorial` → serão **publicadas** no import (dono aprovou). `.gitignore` passou a ignorar `novas/`. Seed inalterada.

### 2026-08-17 (acervo-txt) — transcrições de TI e das aulas processadas
- **`novas/aula_ti.txt`** (Noções de Informática básica) → **13 questões** novas em `docs/acervo/questoes/informatica.json` (IA, redes, software, Word), matéria nova `informatica`. Escopo básico — abaixo do TI-auditor; dono decide se publica.
- **`novas/transcricao_aulas.txt`** (transcrição das 64 aulas já importadas) → passo de **refino**: cruzei com o acervo e enriqueci micro-aulas/pegadinhas (particípio rejeita pronome átono; mnemônico MANÉ; título executivo extrajudicial; notórios conhecimentos = basta um; denúncia não anônima; jurisdição imprópria; sanção do Código = só censura ética + 4 processos autônomos; OCDE soft law). Registro do garimpo em `docs/acervo/observacoes/pegadinhas_transcricao.md`. **Validação:** as respostas das questões do acervo batem com o gabarito dos professores.
- `importar_acervo.py` agora cria matéria nova se o payload trouxer `subject_name`. Total no acervo: **32 questões** prontas para import (owner_only, não publicadas).
- **PENDENTE (outra sessão):** ler `novas/aulao_10h.txt` (~664 KB, aula de 10h) para extrair mais questões/pegadinhas.

### 2026-08-17 (edital) — estrutura oficial da prova de TI documentada
- O dono passou a **divisão de matérias × quantidade de questões** da especialidade **Tecnologia da Informação (TI)**. Registrado em `docs/FUNCIONAL.md` §4.1 (catálogo do concurso) para não se perder:
  - **Prova Objetiva = 80 questões**: Conhecimentos Gerais **20** (Língua Portuguesa 12 · Raciocínio Lógico 4 · Ética Pública e Integridade 2 · Legislação 2) + Conhecimentos Específicos de TI **60**.
  - **Prova Escrita = Estudo de Caso, 2 questões** (discursivas — batem com a correção por IA já no ar).
- **Discrepância anotada:** o `seed.py` hoje agrupa "Legislação e Ética" como uma matéria só; a estrutura oficial **separa** Ética Pública e Integridade (2) de Legislação (2). Ao mexer em pesos/matérias, seguir 12/4/2/2. Nenhuma mudança de código nesta entrada — só documentação.

### 2026-08-17 (seed) — Conhecimentos Gerais com pesos 12/4/2/2 + Ética separada
- Ajustado `apps/api/app/db/seed.py` para a divisão oficial: Língua Portuguesa `weight=12`, Raciocínio Lógico `4`, **nova matéria** Ética Pública e Integridade `2` (slug `etica`) e Legislação `2` (slug `legislacao`, antes "Legislação e Ética"). Docs `FUNCIONAL.md` §4/§4.1 atualizados (discrepância resolvida).
- **`weight` e `Topic.difficulty` não são consumidos por nenhuma lógica** (só metadados) — mudança é segura. O seed é **guardado por `if not exam`**: em produção o exame `tce-sp-2026-ti` já existe, então **isto NÃO altera o banco de produção** (só bases novas/reseed). Sem restart necessário para efeito; syntax check OK.

### 2026-08-16 (preço) — valor do acesso baixado de R$100 → R$25
- A pedido do dono, o preço do acesso caiu de **R$100 para R$25**. Alterados os 5 pontos que citam o número:
  - **Fonte da verdade (cobrança real + valor da conversão Google Ads):** `apps/api/app/core/config.py` → `price_reais: float = 25.0`. O backend usa `settings.price_reais` no checkout Asaas, no `billing/status` e na conversão — então cobra R$25 e reporta conversão de valor 25. (`PRICE_REAIS` **não** está no `/etc`, então o default do código vale.)
  - **Front:** `apps/web/app/page.tsx` — texto do gate (`R$ 25`), botão (`Gerar Pix de R$ 25`), e o valor-fallback de `trackPurchaseConversion` (`value = 25.0`). `apps/web/app/layout.tsx` — `price: "25.00"` no schema JSON-LD (SEO).
- **Publicado e validado no ar:** API reiniciada (`price_reais = 25.0`, health ok); front reconstruído com `NEXT_PUBLIC_API_URL` + cópia do `.next/static` + restart. HTML servido tem `"price":"25.00"`, bundle tem "R$ 25" e **sem** `localhost:9000`.
- Textos que não citam número ("pagamento único", "acesso por 2 anos/vitalício") ficaram inalterados.

### 2026-08-16 (google-ads) — diagnóstico da recomendação "finalize o acompanhamento de conversões"
- O Google Ads recomendou "finalizar o acompanhamento de conversões" ("uma ação de conversão foi criada, mas a tag ainda não foi verificada para: Compra"). **Investigado: a configuração já está completa e no ar** — nenhum código faltando.
  - Tag base (gtag.js `AW-975500543`) servida no HTML público (`apps/web/app/layout.tsx`) — confirmado no ar.
  - Snippet de evento de conversão da **Compra** (`gtag('event','conversion', send_to:'AW-975500543/YEiMCLvJ5t4cEP_pk9ED')`) implementado em `apps/web/app/page.tsx` (`trackPurchaseConversion`/`reportConversion`), disparo **one-shot por transaction_id**, com **fallback durável** via backend (`me.conversion` → dispara mesmo se a aba fechou no Pix → `POST /billing/conversion/reported`). Rótulo presente no bundle de produção (build 10:57 de 16/08).
- **Por que o Google diz "não verificada":** a conversão "Compra" só dispara num **pagamento Pix real concluído**; o robô de verificação do Google não consegue comprar (login + pagamento), e provavelmente ninguém comprou desde o deploy → zero hits recebidos. **Estado normal/esperado**; a recomendação some sozinha na 1ª venda real.
- **Único ponto a validar (fora do meu alcance — precisa do painel):** que o rótulo `YEiMCLvJ5t4cEP_pk9ED` bate com o event snippet da ação "Compra" no Google Ads. Teste sem pagar de verdade: Google Tag Assistant + disparo manual no console (`gtag('event','conversion',{send_to:'AW-975500543/YEiMCLvJ5t4cEP_pk9ED',value:100,currency:'BRL',transaction_id:'teste-manual'})`).
- **Server-side (`google_ads.py`, `GOOGLE_ADS_ENABLED=false`) continua desligado** — exige developer token aprovado + gclid; não é o que a recomendação pede. Sem mudança de código nesta sessão (só esta entrada de diário).

### 2026-08-16 (docs) — documentação completa do sistema (arquitetura, funcional, swagger)
- Criada a documentação técnica de todo o sistema, a pedido do dono:
  - `docs/ARQUITETURA.md` — stack, camadas do backend, ciclo de vida (create_all +
    micro‑migração + seed), autenticação/níveis de acesso, serviços externos
    (`urllib`), modelo de dados completo, infra/deploy e convenções.
  - `docs/FUNCIONAL.md` — perfis, jornadas (teste grátis, cadastro→pagamento,
    estudo, simulado, discursiva com IA, suporte), regras de negócio, catálogo do
    concurso e features administrativas.
  - `docs/API_REFERENCE.md` — catálogo legível dos 60 endpoints por domínio + níveis
    de acesso.
  - `docs/api/openapi.json` — **spec OpenAPI gerado da própria API** (`app.openapi()`,
    60 rotas) + `docs/api/swagger.html` (Swagger UI offline, spec embutido).
  - `docs/README.md` — índice da documentação.
- **Como regenerar o swagger ao mudar rotas:** `cd apps/api && .venv/bin/python -c
  "import json;from app.main import app;json.dump(app.openapi(),
  open('../../docs/api/openapi.json','w'),ensure_ascii=False,indent=2)"` e reembutir
  no `swagger.html` (procedimento no cabeçalho de `API_REFERENCE.md`).
- Nenhuma mudança de código/produção — só documentação (não exige restart/rebuild).

### 2026-08-16 (hotfix) — login quebrado: rebuild sem NEXT_PUBLIC_API_URL
- O rebuild do front (item abaixo) foi feito **sem exportar `NEXT_PUBLIC_API_URL`**, então o bundle embutiu o default `http://localhost:9000/api/v1` → o navegador do usuário tentava falar com o próprio localhost → **falha de conexão no login e em tudo**.
- **Corrigido:** rebuild com `NEXT_PUBLIC_API_URL=https://passafacil.jussa.com.br/api/v1` + restart. Bundle agora tem só a URL de produção (login responde 401 p/ credenciais falsas = vivo). Passo marcado como OBRIGATÓRIO na seção 3.

### 2026-08-16 (UI) — autoavaliação removida; IA marca os botões + REBUILD do front
- **Causa de o dono ainda ver a autoavaliação:** o frontend nunca tinha sido reconstruído — o build em produção era de 14/ago, anterior às mudanças. **Lição:** mudança em `apps/web` só aparece após `next build` + copiar `.next/static` + `restart passafacil-web` (ver seção 3). Documentado para não repetir.
- **Nova tela de correção:** removida a autoavaliação manual (`selfScores`, `saveSelf`, botão "Salvar minha nota", endpoint PATCH deixou de ser usado pelo front). A IA agora **marca os três botões** (Não completou / Em parte / Completou) em modo read-only, com nota realista por critério (`fmtNota`, vírgula decimal) e total apurado. Componentes: `DiscCorrecaoPanel` (reescrito) e `DiscCorrecaoIndisponivel` (fallback quando a IA falha). Vale para a área logada e o teste grátis.
- Front reconstruído e no ar (bundle confirmado: tem "CORREÇÃO DA IA"/"Não completou"; sem "Salvar minha nota").

### 2026-08-16 (cerebras) — validado mas parado (exige pagamento)
- Chave Cerebras (`csk-…`) adicionada e **validada** (autentica). Modelos da conta: `gpt-oss-120b`, `zai-glm-4.7`, `gemma-4-31b` (sem Llama — corrigido o default `llama-3.3-70b` → `gpt-oss-120b`).
- Porém inferência retorna **`payment_required`** ("Visit your billing tab") no tier grátis — igual à OpenRouter. Por decisão do dono, **deixado fora da cascata** por ora (retomar quando crescer a base de assinantes).
- `GRADING_ORDER` padrão passa a ser **`groq,gemini`**. Restart aplicado para produção refletir. Cascata ativa = Groq → Gemini.

### 2026-08-16 (fallback) — Gemini ativo como 2º provedor
- Adicionada `GEMINI_API_KEY` no `/etc`. **Cascata Groq→Gemini validada no ar** (simulei Groq 503 → correção seguiu pelo Gemini).
- **Modelo do Gemini trocado para `gemini-flash-latest`** (em `config.py` e `.env.example`): contas novas recebem 404 "no longer available to new users" em versões antigas pinadas (`gemini-2.0-flash`, `gemini-2.5-flash`). O alias `-latest` evita isso. Exigiu restart da API (o `/etc` não define `GEMINI_MODEL`, então valia o default do código).
- **Nota sobre chaves Gemini:** a chave desta conta começa com `AQ.…` (formato novo), não com `AIza…` — normal, autenticou certo.

### 2026-08-16 (cascata) — OpenRouter fora do padrão (fricção de pagamento)
- O dono apontou que a **OpenRouter "é paga"**: os modelos `:free` custam US$0, mas a plataforma exige crédito/cartão para limites úteis. Removida da cascata padrão.
- `GRADING_ORDER` padrão agora é **`groq,gemini,cerebras`** (só provedores grátis sem cartão) em `config.py` e no `.env.example`. Suporte à OpenRouter continua no código — basta re-incluí-la no `GRADING_ORDER` e pôr a chave. Backups grátis recomendados: **Gemini** (aistudio.google.com/apikey) e **Cerebras** (cloud.cerebras.ai).

### 2026-08-16 (limpeza) — organização do repositório
- Mesclado `feat/correcao-ia-discursivas` na `main` e o branch **apagado** (local + remoto).
- **Assets soltos da raiz reorganizados** (não referenciados por código — só um comentário citava "config_ads3"):
  - screenshots do app → `docs/screenshots/app/`
  - screenshots do Google Ads → `docs/screenshots/google-ads/`
  - `aprovada.png` → `docs/screenshots/`
  - `Anexo_PassaFacil_Case.pdf`, `edital_tenologia.txt`, CSV de keywords → `docs/anexos/`
- **Removidos do versionamento** (eram lixo commitado por engano no `git add -A`): um `.claude/settings.local.json.tmp.*` (temporário do harness) e `apps/web/tsconfig.tsbuildinfo` (artefato de build). `.gitignore` atualizado para não voltarem (`*.tsbuildinfo`, `.claude/settings.local.json*`).

### 2026-08-16 (correção) — ELEVENLABS_API_KEY existe no /etc
- Correção de um erro meu registrado neste doc: a `ELEVENLABS_API_KEY` **está** em `/etc/passafacil.env` (`sk_…`) — não se perdeu. Só o script de geração dos áudios é que não foi versionado. Segredos hoje no `/etc`: JWT, DATABASE_URL, CORS, OWNER, ASAAS_* (sandbox=false), GOOGLE_ADS_*, SUPPORT_*, **ELEVENLABS_API_KEY**, **GROQ_API_KEY**.
- **Nota:** `ASAAS_SANDBOX=false` no `/etc` (produção real de pagamento já ligada — o default do código é `true`, mas o `/etc` sobrescreve).

### 2026-08-16 — Correção por IA das discursivas no ar + doc viva
- **Fase 2 (correção por IA)** implementada e **ativada em produção** com Groq. Antes só havia autoavaliação manual (o "0 de 20" que o dono via era o placar inicial, não uma correção — origem da queixa de "nota zero").
  - Novo `apps/api/app/services/grading.py` (cascata grátis, `urllib`). Colunas `ai_*` em `DiscursiveSubmission` + micro-migração em `main.py`. Rotas `discursive` corrigem no `submit`/`demo`. Front: painel "Correção da IA" (nota + justificativa por critério + comentário), com fallback para a autoavaliação. `.env.example` documenta as chaves.
- **Bug encontrado e corrigido no ar:** a chamada à Groq dava **HTTP 403** porque faltava `User-Agent` (bloqueio de WAF). Corrigido em `grading.py`. Só foi pego testando de verdade contra a API no servidor (o teste unitário com mock não pegou).
- **Validação real:** resposta no tema recebeu **5,5/10** com notas parciais por critério (N1 2,0 · N2 1,5 · N3 2,0). Crédito parcial funcionando.
- Commit inicial em `feat/correcao-ia-discursivas` (pushed) incluiu também avanços já presentes no working tree (billing, feedback, SEO, materiais em `docs/`).
- **Criado este arquivo** (`docs/ESTADO_DO_SISTEMA.md`) como memória viva entre sessões, a pedido do dono (que apontou, com razão, o risco de perda de contexto entre sessões).
