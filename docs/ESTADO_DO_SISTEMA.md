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
- [x] **Full remake — Sessão B = F2 NO AR** (confiança + feedback adaptativo + microaula em camadas; backend `services/feedback.py` + `page.tsx`). Falta **autorar conteúdo** (misconceptions por alternativa + microaula estruturada `essential`/`deep`) — vem na F8/autoria; hoje degrada gracioso.
- [x] **Full remake — Sessão C = F3+F4 NO AR**: `MemoryScheduler` (estilo-FSRS próprio) + `AdaptiveLearningEngine` + `ReviewQueue`/`TransferQuestionSelector` + sessão inteligente / "Memória de hoje"; `/reviews/*` migrado para `PaidUser`.
- [x] **Full remake — Sessão D = F5 (dashboard) NO AR**: aba "Meu conhecimento" (`services/knowledge_map.py` + `GET /study/knowledge-map` + `KnowledgeView`): indicadores, mapa por disciplina/habilidade, riscos, erros conceituais recorrentes.
- [x] **Full remake — Sessão E = F6 (aulas e áudio interativo) NO AR**: `models/lessons.py` + endpoints `/study/lessons*` + `LessonsView` (modos interativo/contínuo + transcrição); aula-demo a partir dos 8 pilotos.
- [x] **Full remake — Sessão F = F7 (dissertativas) NO AR**: correção item-a-item (status/evidência) + "Nota estimada" + reescrita ativa (`ai_items`, `EssayRewrite`, `grade_criterion`, `/rewrite`).
- [ ] **Full remake — Sessão G = F8 (migração/classificação) + F9 (QA)**: classificar o acervo em skills/misconceptions (motor/fila/dashboard só ganham massa com isso) + rodar tests/lint/typecheck/build/migração.
- [ ] **Revisar os gabaritos SINALIZADOS** pela varredura (`review_status='needs_review'`; relatório `docs/acervo/observacoes/gabaritos_check.json`) — 14 até 900/1074 processadas; terminar a varredura e corrigir os confirmados.
- [ ] **Autorar conteúdo adaptativo** (skills + misconceptions + microaula em camadas) além da questão-demo — para o motor/fila/dashboard terem massa. Vem com a F8 / painel de autoria (§50).
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

### 2026-08-20 (acervo aula 10h) — decks das apresentações + Arq3 importado
- **Fonte nova:** 5 PDFs em `docs/acervo/Arq{1..5}_aula10h*` (slides da "Revisão de Véspera – Auditor de Controle Externo", Gran). Mapa: Arq1 Língua Portuguesa (Márcio Wesley, 43pg, imagem), Arq2 Noções de Informática (Fabrício Melo, 41pg, imagem, tem questões A–E no slide), **Arq3 Controle Externo (30pg, TEXTO extraível)**, Arq4 Direito Constitucional (Aragone, 25pg, imagem), Arq5 Licitações/Contratos Lei 14.133 (Guilherme Pereira, 47pg, imagem). Decks em imagem têm texto nítido → dá pra extrair por leitura visual. Dono: usar os slides como fonte; transcrição só p/ pegadinhas.
- **Arq3 IMPORTADO e PUBLICADO:** 11 questões VUNESP reais (gabaritos lidos pelos marcadores do slide). 3 arquivos em `docs/acervo/questoes/`: `arq3_controle.json` (4 → `legislacao`: Declaração de Lima/EFS, sustação de contrato art.71 CF, LC 709/93 contas irregulares, Regimento/Consulta), `arq3_auditoria.json` (6 → `cont-auditoria`: ceticismo ISSAI 100, risco inerente/controle/detecção, matriz de responsabilização, asseguração razoável/limitada), `arq3_etica_tcesp.json` (1 → `etica`: Código de Ética TCE-SP Res. 20/2024). Importador rodado (dry-run→apply): 11 novas, 32 dedup, 0 rejeitadas, 6 tópicos criados. Publicadas via `import_batch='acervo-aula10h-2026-08'`. **Total 1085/1085.** Explicações nomeiam a norma ([[citar-artigo-com-a-lei]]).
- **Arq2 IMPORTADO e PUBLICADO (needs_review):** 19 questões de Noções de Informática (`arq2_informatica.json` → `informatica`, 7 tópicos novos: Windows/arquivos, atalhos, internet/URL/e-mail, busca Google, segurança CID, IA generativa, Office 365). Decks em imagem NÃO trazem gabarito impresso (professor fala) — apuramos o gabarito (vários confirmados pelos slides de resposta: Q1/Q5/Q11) e marcamos **`needs_review`** p/ o dono confirmar 1-clique no [[editor-questoes-gerencial]]. Enunciados reescritos AUTOSSUFICIENTES (listas/tabelas embutidas no texto). Total **1104** (needs_review = 22 = 19 Arq2 + 3 gabaritos).
- **Decisão de escopo (dono):** importar TODOS os decks priorizando TI; matérias que caem em todos os cargos (Licitações, Português, Dir. Constitucional) ficam no escopo; em dúvida, grupo "Outras" ou no grupo respectivo. App já tem estrutura multi-cargo.
- **Arq4 IMPORTADO e PUBLICADO (needs_review):** 10 questões de Direito Constitucional (`arq4_constitucional.json` → `dir-constitucional`, 8 tópicos: eficácia das normas, federalismo/municípios, nacionalidade/extradição, legislativo/mandato, judiciário, direitos políticos, servidores/previdência, TC na CF). Nível Procurador/Juiz, sem gabarito impresso (slides em branco) → gabarito apurado e `needs_review`. Q8/Q9/Q10 são sobre Tribunal de Contas (art. 71/31) — bem relevantes. Total **1114** (needs_review 32).
- **PENDENTE:** extrair Arq1 (Português, 43pg), Arq5 (Licitações 14.133, 47pg); pegadinhas da transcrição; e Sessão G = F8 (classificar acervo em skills/misconceptions) + F9 (QA). Decks em imagem: apurar gabarito + `needs_review`.

### 2026-08-20 (gerencial) — Editor de questões publicadas + revisão dos 15 gabaritos
- **Revisão dos 15 gabaritos sinalizados:** analisei uma a uma (enunciado+alternativas+explicação+lei). **Conclusão: os 15 estão corretos como cadastrados; a IA errou nas 15** (tropeçou nas pegadinhas). Nenhum `correct_option` alterado. **12 liberadas** (`review_status`→`reviewed`, gabarito mantido); **3 mantidas `needs_review`** p/ o dono conferir em fonte oficial: `647d6266` (internet "gratuita"), `8c9bd1c4` (prazo 60 dias TCE), `ed4b49cc` (HTTPS simétrica×assimétrica). Relatório `gabaritos_check.json` atualizado (campo `resolucao` por flag + `flags_pendentes`).
- **Feedback do dono → memória [[citar-artigo-com-a-lei]]:** ao citar artigo numa explicação, SEMPRE nomear a lei. Apliquei já em 8 das 15 explicações (citações soltas viraram "art. X da CF/Lei 13.303/LAI…"). Pendente: varredura da base toda.
- **Editor de questões (NOVO, proprietário) no ar:** menu admin "Editor de questões". Backend `question_bank.py`: `GET /manage/queue` (fila prioritária = needs_review, com sugestão da IA do relatório), `GET /manage/search?q=` (qualquer questão por texto), `GET /manage/{id}` (detalhe editável), `PATCH /manage/{id}` (enunciado, alternativas+gabarito com validação, explicação, `micro_lesson` pegadinha/macete, tópico, publicar/despublicar, baixar selo needs_review), `POST /manage/{id}/image` (upload multipart → `media/question_assets`, seta `image_url`; nome estável `q-<uuid>.<ext>`). Schema `ManageQuestionUpdate` (exclude_unset). Front `QuestionEditorView` (busca + fila destacada + editor reaproveitando `.draft-editor`; upload/troca/remoção de figura). **Resolve a lacuna:** antes só dava p/ editar rascunhos do PDF; agora edita as 1074 publicadas (explicação/pegadinha/figura/gabarito) por tela, sem script.
- **Validado:** e2e SQLite+TestClient (queue/search/get/patch/422/upload/baixa-selo), `tsc` limpo. **Deploy:** restart API + rebuild front. Endpoints respondem 401 sem token (protegidos).

### 2026-08-19 (correção grave) — suporte a FIGURA em questão (enunciados figurais) no ar
- **Problema (dono):** questões com desenho/figura foram importadas só como texto — a figura não era reproduzida. Questão figural sem figura é impossível de responder. **Raiz:** `Question` não tinha NENHUM campo de imagem e o front renderizava o enunciado como texto puro — a plataforma era incapaz de guardar/mostrar figura. Varredura das 1074 (4 categorias): só **1 questão figural viva no ar** — `c885eefc` (*"sequência de figuras 3x3…"* = `quest9Raciocinio.jpg`). O resto do risco era futuro (o novo acervo trará questões VUNESP com figura).
- **Correção de raiz (backend):** `Question.image_url` (nome do arquivo; NULL = questão textual) em `entities.py` + `main.py::_ensure_columns` (VARCHAR(255), idempotente, aplicado em prod). Novo `app/core/assets.py` (`QUESTION_ASSET_DIR = apps/api/media/question_assets`, `question_asset_url`, `resolve_asset` com bloqueio de path traversal + whitelist de tipo). Rota pública `GET /study/question-asset/{name}` (padrão do áudio-piloto, `FileResponse`). `image_url` incluído em TODOS os serializadores de questão: study (practice/session/memory-today/trial/trial-full/checkpoint), reviews, simulations.
- **Front:** componente `QuestionFigure` (usa `API_ORIGIN`, `max-width:100%`, nunca estoura a tela) inserido após o enunciado em prática, simulado, revisão, caderno de erros, recap do simulado e checkpoint de aula. CSS `.question-figure`. `image_url` nos tipos `Question`/`LessonCheckpointQ`.
- **Conteúdo:** `quest9Raciocinio.jpg` copiada p/ `media/question_assets/`, `c885eefc.image_url` setado em prod. **Importador** (`importar_acervo.py`): novo `copy_figure()` — quando a questão do acervo tem `"needs_figure": true`, copia `fonte_imagem` (procura em `novas/`, `docs/acervo/figuras/`, `docs/acervo/`) p/ os assets e liga em `image_url`; **rejeita** se figural mas sem a origem (não deixa entrar questão quebrada). q09 marcada `needs_figure:true` em `logica.json`.
- **Validado:** smoke SQLite (coluna criada, URL, traversal bloqueado, idempotência), `tsc` limpo, import das rotas ok. **Deploy:** restart API + rebuild front standalone. **Prova em prod:** figura serve 200 `image/jpeg` 257371 bytes pelo domínio público; traversal/inexistente = 404; campo `image_url` presente na serialização.

### 2026-08-19 (conteúdo) — varredura de gabaritos concluída + aulão pausado
- **Varredura de gabaritos por IA CONCLUÍDA:** 1074/1074 processadas, **15 questões sinalizadas** `review_status='needs_review'` (relatório `docs/acervo/observacoes/gabaritos_check.json`). Predominam legislação/controle (LRF, Lei 13.303, LAI, quarentena, TCE). **PENDENTE:** o dono revisa quais estão de fato erradas e a gente corrige os `correct_option`. São *sinais* da IA — não alterei nenhuma questão.
- **Aulão 10h (`novas/aulao_10h.txt`) — importação PAUSADA a pedido do dono** ("vou gerar um acervo melhor"). Construí o pipeline `apps/api/scripts/extrair_aulao.py` (limpa timestamps → blocos → IA extrai questões/pegadinhas/leis, resumível). Prova (5/93 blocos): **pegadinhas e leis vêm ótimas e confiáveis; as questões vêm fracas** (transcrição falada raramente lê as 5 alternativas → alternativas/gabarito incompletos). Decisão: NÃO importar questões cruas. Blocos extraídos ficam em `docs/acervo/aulao/chunks/` (untracked, exploratório). O dono começou a subir fontes melhores (PDFs em `docs/acervo/`: Competências/Organização do TCE-SP).

### 2026-08-19 (full-remake · Sessão F, F7) — dissertativas: item-a-item + reescrita ativa
- **Fase 7 (dissertativas)** completa e no ar — evolução do MVP (não reescreveu). Correção **item-a-item** com **status Atendido/Parcial/Ausente + evidência (trecho do candidato)**, rótulo **"Nota estimada"** e **reescrita ativa**.
- **Backend:**
  - `models/entities.py`: `DiscursiveSubmission.ai_items` (JSON: {codigo: {nota,status,evidencia,justificativa}}) + nova tabela **`EssayRewrite`** (reescrita de um critério + recorreção). Migração `ai_items` no `_ensure_columns`; `essay_rewrites` via create_all.
  - `services/grading.py`: `GradingResult.items` + prompt pede **status/evidência** por critério (deriva status da nota se faltar); nova `grade_criterion(case, criterion, texto)` recorrige UM critério (para a reescrita). Compat mantida (ai_scores/ai_total/ai_feedback).
  - `routes/discursive.py`: correção expõe `items` + `nota_estimada=True` (spec §28); `submit` persiste `ai_items`; **`POST /discursive/submissions/{id}/rewrite`** (recorrige o critério, grava `EssayRewrite`, devolve antes/depois §30); `get_submission` traz `rewrites`.
  - Testado em produção (`/discursive/demo/submit`): retorna `items` com status/evidência + `nota_estimada`.
- **Frontend (`page.tsx` + `globals.css`):** `DiscCorrecaoPanel` evoluído — ✅/🟡/❌ por critério + **evidência "No seu texto: …"** + "Nota estimada". No fluxo pago, botão **"Reescrever este ponto"** nos itens não atendidos → editor → **recorreção com antes→depois**. Demo (anônimo) mostra item-a-item, sem reescrita (não persiste).
- **Progresso: A✓ B✓ C✓ D✓ E✓ F✓ de 7 blocos. Falta só a Sessão G = F8 (migração/classificação do acervo em skills) + F9 (QA).**

### 2026-08-19 (correções + QA de conteúdo) — formatação, setas no celular, ordem, varredura de gabaritos
- **Bugs reportados pelo dono (testes) corrigidos e no ar:**
  - **Micro-aulas "mal formatadas":** a explicação tem estrutura em parágrafos (`Gabarito:`/`MICRO-AULA`/`⚠️ PEGADINHA` separados por `\n\n`), mas `.teach`/`.explanation` não preservavam quebras → viravam um blocão. Adicionado `white-space: pre-line`. (O banco NÃO tem markdown cru.)
  - **Setas estourando no celular:** `.question-top` sem `flex-wrap`. Na media `max-width:620px`: `flex-wrap`, título ocupa 100%, `.question-nav` alinhado à direita e `.question-count` menor.
- **Ordem das questões (decisão do dono):** `study.practice` agora é **aleatória e NÃO repete a mesma questão** enquanto houver inéditas (reforça o ASSUNTO com questões diferentes). Só quando TUDO foi visto o reforço repete questões (erradas → já acertadas). Antes concatenava as já-acertadas ao lote, gerando a repetição que ele notou.
- **QA de gabaritos por IA (varredura que SINALIZA):** `app/services/answer_check.py::verify_answer` (reaproveita a cascata de `grading.py`) + `scripts/verificar_gabaritos.py` (resumível; relatório em `docs/acervo/observacoes/gabaritos_check.json`). Para cada questão a IA diz a alternativa correta; onde discorda com confiança alta/media, marca `review_status='needs_review'` — **não altera** enunciado/alternativas/`correct_option` (correção é humana, §10/§52). **Estruturalmente o banco está íntegro** (0 questões com resposta fora da faixa/sem alternativa/sem explicação); o problema é gabarito semântico em parte das extraídas de imagem. Varredura rodando em lotes.
  - ⚠️ **Achado colateral:** o **Groq está retornando HTTP 404** (modelo/endpoint desatualizado); a cascata cai no **Gemini**. Afeta também a correção das discursivas (hoje via Gemini como fallback silencioso) — conferir `settings.groq_model`/`groq_base_url`.

### 2026-08-18 (full-remake · Sessão E, F6) — aulas e áudio interativo no ar
- **Fase 6 (aulas/áudio interativo)** completa e no ar. O menu **"Áudios (em breve)" virou "Aulas em áudio"** — a feature saiu do "em breve".
- **Backend — `app/models/lessons.py` (4 tabelas novas via create_all):** `Lesson`, `LessonSection` (unidade semântica com texto/transcrição + `audio_url`, §20/§22), `RetrievalCheckpoint` (checkpoint que reaproveita uma `Question`, §21) e `LessonSkill` (aula↔habilidade, §23). Endpoints em `study.py`: `GET /study/lessons` (lista), `GET /study/lessons/{slug}` (seções + checkpoint sem gabarito), `POST /study/lessons/checkpoint/{question_id}/answer` (feedback adaptativo + evento `AUDIO_CHECKPOINT_ANSWERED` §34 + atualiza `UserSkillState`; **não cria Attempt** — checkpoint é apoio, não conta no placar).
- **Aula-demo** (`scripts/seed_demo_lesson.py`, idempotente): "Revisão em áudio — Conhecimentos Gerais + TI", **8 seções** a partir dos 8 MP3-piloto (`media/audio_pilot/`), cada trecho com áudio + transcrição (o enunciado) + checkpoint = a questão do trial correspondente. Semeada em produção.
- **Frontend (`page.tsx` + `globals.css`) — `LessonsView`:** lista de aulas → player com **dois modos** (spec §21): **"🧠 Aula interativa"** (ouve o trecho → checkpoint → responde → feedback via `QuestionTeach` → próximo) e **"▶ Ouvir continuamente"** (todos os trechos com player + transcrição colapsável). Áudio servido pelo endpoint público `/study/audio-pilot/*`. Tema claro/escuro. (Removida a tag morta "EM BREVE" da nav.)
- **Validado:** tabelas criadas (SQLite + prod), seed 8/8 seções com áudio+checkpoint, endpoints 401 sem token (vivos), áudio público 200, `tsc` limpo, front build sem `localhost`, web 200. Sem regressão.
- **Progresso: A✓ B✓ C✓ D✓ E✓ de 7 blocos. Próximo: Sessão F = F7 (dissertativas — evolui o MVP: OfficialRubric/RubricItem, correção semântica, "Nota estimada", reescrita ativa).**

### 2026-08-17 (conteúdo) — TODAS as questões publicadas (sem etapa de validação)
- A pedido do dono: **todas as questões publicadas, sem exceção**. `UPDATE questions SET is_published=true` em produção → **1074/1074 publicadas** (antes 1026; +48, das quais 29 nem apareciam por não serem owner_only). Os 3 estudos de caso já estavam publicados. Sem restart (a API lê `is_published` ao vivo). Preferência permanente registrada na memória — **publicar logo após qualquer import novo** (o `importar_acervo.py` ainda importa como `owner_only`/não publicado).

### 2026-08-17 (full-remake · Sessão D, F5) — dashboard "Meu conhecimento" no ar
- **Fase 5 (dashboard adaptativo)** completa e no ar (backend + frontend). Nova aba **"Meu conhecimento"** com mapa de habilidades, riscos e erros conceituais — consome `UserSkillState` + `LearningEvent`.
- **Backend — `app/services/knowledge_map.py` + `GET /study/knowledge-map` (PaidUser):** `build_knowledge_map` (lógica fora da rota, §57) devolve **indicadores** (domínio/retenção estimados, dominadas, frágeis, transferências, erros confiantes, tempo médio §42), **mapa por disciplina→habilidade** com estado visual (Dominado/Consolidando/Frágil/Precisa estudar/Ainda não avaliado §18), **riscos** ("o que está me fazendo perder pontos" §19: ordena por (1-domínio)+frágil+erros confiantes+baixa retenção, top 5, com "errou X de Y") e **erros conceituais recorrentes** (§42: conta misconceptions nas respostas erradas via `LearningEvent`→`OptionMisconception`). Estimativas rotuladas como tais (§18 — sem precisão científica falsa).
- **Frontend (`page.tsx` + `globals.css`):** nav **"Meu conhecimento"** → `KnowledgeView` (auto-busca): grade de indicadores, card de **riscos** com botão **"Corrigir agora"** (→ sessão inteligente), **mapa por disciplina** com barras de domínio + chips de estado coloridos por bucket, e **erros conceituais recorrentes**. **Estado vazio encorajador** quando o aluno ainda não tem habilidades vistas (caso do dono hoje). Tema claro/escuro.
- **Validado:** `build_knowledge_map` e2e (SQLite: 3 habilidades em estados diferentes → indicadores/mapa/riscos ordenados/misconceptions contados; vazio gracioso) + read-only prod (dono: 0 habilidades → mapa vazio); `tsc` limpo; endpoint 401 sem token; front build sem `localhost`, web 200. Sem regressão.
- **Deploy + push:** API restart + front rebuild; branch `feat/full-remake-adaptativo` pushada. **Progresso: A✓ B✓ C✓ D✓ de 7 blocos. Próximo: Sessão E = F6 (aulas e áudio interativo com checkpoints).**

### 2026-08-17 (full-remake · melhoria F2) — quadro "por que as demais estão erradas"
- A pedido do dono, o feedback ganhou um **quadro resumido** logo depois de "Por que a correta está certa": **"Por que as demais estão erradas"**, listando **uma alternativa incorreta por linha** com um rótulo curto do erro. Compacto (não quebra a tela do celular/PC).
- **Backend (`services/feedback.py`):** `build_answer_feedback` agora devolve `wrong_options` = lista `{index, letter, reason}` das alternativas incorretas **exceto a correta e a que o aluno marcou** (essa já vai no `why_wrong`). `reason` = **nome do misconception** (rótulo curto/impessoal) ou, na falta, a explicação da alternativa. Só aparece o que estiver autorado (degrada gracioso). Query única (dict por índice) — sem N+1.
- **Frontend (`page.tsx` + `globals.css`):** no `QuestionTeach`, após o bloco "sua resposta", um `.wrong-list` (lista `letra — motivo`, borda fina entre linhas, tema claro/escuro). Verificado na questão-demo: escolhendo D (correta) lista A/B/E; escolhendo B lista A/E (B vai em "sua resposta", C sem misconception fica de fora).
- Deployado (API restart + front rebuild) e **branch pushada** p/ `origin/feat/full-remake-adaptativo` (ainda não mesclada na `main`).

### 2026-08-17 (full-remake · Sessão C, F3+F4 completas) — ReviewQueue + sessão inteligente no ar
- Fechada a **Sessão C**: ReviewQueue/TransferSelector, migração das revisões e a **sessão inteligente / "Memória de hoje"** (F4). Backend + frontend no ar.
- **C4 — `app/services/review_queue.py`:** `ReviewQueue.build()` monta a fila priorizando (spec §14) vencido/em risco → frágil → erro conceitual de alta confiança → consolidação → relevância no edital → retrievabilidade baixa, e **completa com conteúdo novo** (nunca vem vazia). `TransferQuestionSelector` (spec §9) escolhe uma questão **diferente da mesma habilidade** (prefere nunca respondida) para testar transferência. `due_skill_count()` alimenta a "Memória de hoje". Scheduler/fila tornados **robustos a datetime naive** (SQLite) via `_as_utc` (Postgres já é tz-aware).
- **C4 — migração de acesso:** rotas **`/reviews/*` deixaram de ser owner-only** (`get_admin_user`+`get_owner_user`) e agora são **`PaidUser` por-usuário** (§2.1 do doc de arquitetura). A revisão também passa pelo motor adaptativo (evento `REVIEW_COMPLETED`, §34) — recuperação após intervalo atualiza memória/domínio. Usuário gratuito continua no test-drive (revisão exige conta).
- **C5 (F4):** endpoints **`GET /study/memory-today`** (nº de habilidades a recuperar + minutos) e **`GET /study/session`** (fila adaptativa: revisão + frágeis + transferência + novo, com `reason`/`skill` por item). Front (`page.tsx`): card **"Sessão inteligente / 🧠 Memória de hoje"** na home + botão **"Começar sessão"/"Fortalecer memória"** que carrega `/study/session` no fluxo de questões (modo aprendizagem). `loadDashboard` também busca a memória de hoje. CSS `.smart-session-card` (tema claro/escuro).
- **Validado:** scheduler + engine + reviewqueue e2e (SQLite, determinístico); `build()` conferido **read-only contra o prod** (dono: 0 revisões vencidas → 6 itens novos, fallback gracioso OK); `tsc` limpo; endpoints 401 sem token (vivos); front build sem `localhost`, web 200. Sem regressão.
- **Efeito prático:** ao responder a questão-demo (única com skill hoje), o `UserSkillState` evolui e, quando vencer, aparece em "Memória de hoje"/sessão inteligente. O resto do acervo ganha skill na **F8**. **Próximo: Sessão D = F5 (dashboard: mapa de conhecimento, riscos, erros conceituais, evolução).**

### 2026-08-17 (full-remake · Sessão C, F3 core) — MemoryScheduler + AdaptiveLearningEngine no ar
- Início da **Fase 3 (motor adaptativo)**. Entregue o núcleo: **scheduler de memória** + **motor** que atualiza o estado do conhecimento a cada resposta. Backend puro, no ar (só `restart passafacil-api` — sem colunas novas; as tabelas `user_skill_states`/`learning_events` já vieram na F1).
- **`app/services/scheduler.py` — `MemoryScheduler`** (interface) + **`SimpleFsrsScheduler`** (implementação própria **estilo-FSRS em Python puro**, SEM dependência nova — decisão do doc de arquitetura §5; *seam* para plugar `py-fsrs` via adapter depois). Curva de esquecimento `R(t)=(1+19/81·t/S)^-0,5`; estabilidade/dificuldade; `next_review` no ponto em que R cai ao alvo (0,9 → intervalo≈S). `Rating` AGAIN/HARD/GOOD/EASY + `map_response_to_rating` (spec §13: erro→AGAIN; dica/chute/baixa confiança→HARD; normal→GOOD; confiante s/ dica→EASY; tempo ajuda mas não decide). **Pesos todos em `SchedulerConfig`** (spec §13, "não espalhados pelo código").
- **`app/services/adaptive_engine.py` — `AdaptiveLearningEngine.evaluate_attempt`**: a cada resposta atualiza o `UserSkillState` — **domínio** (`mastery_score` = média móvel da *qualidade* da tentativa, NÃO acerto bruto; erro confiante = pior sinal §44; acerto com dica/chute vale menos; questão mais difícil vale mais) separado da **memória** (delega ao scheduler: `memory_stability`, `retrievability`, `next_review_at`), contadores, `high_confidence_errors`/`low_confidence_corrects`/`transfer_successes`, e a **máquina de estados** UNSEEN→EXPOSED→LEARNING→CONSOLIDATING→MASTERED com FRAGILE/LAPSED (§11). Desacoplado da UI (§57).
- **Wiring:** `study.answer` chama o motor e grava os snapshots do scheduler + `review_interval` no `LearningEvent` (§35). **No-op gracioso** para questões sem `primary_skill` (só a questão demo tem, por ora — F8 classificará o acervo). Nenhuma mudança de UI nesta fatia.
- **Validado** (SQLite, determinístico): scheduler (mapeamento, curva, efeito de espaçamento, lapso, EASY>GOOD>HARD) e motor e2e (EXPOSED→MASTERED após revisões em dia → LAPSED no erro confiante; no-op sem skill; 1 estado por user+skill). Sem regressão (feedback F2 + pytest smoke OK).
- **Pendente na Sessão C:** **C4** — `ReviewQueue` (§14) + `TransferQuestionSelector` (§9) + **migrar `/reviews/*` de owner-only → `PaidUser`+gratuito**; **C5 (F4)** — "Estudar agora"/"Memória de hoje"/fila adaptativa (endpoints + home).

### 2026-08-17 (full-remake · Sessão B, demo) — exemplo adaptativo autorado numa questão real
- Para o dono **ver a F2 completa funcionando**, autorei o conteúdo adaptativo na questão da **negação da condicional** ("trabalhadora e honesta", mnemônico MANÉ; ID `2e058342-377e-4988-a640-5116f239a1a7`, Raciocínio Lógico). Script **versionado e idempotente**: `apps/api/scripts/seed_demo_adaptive.py` (referência de como a autoria da §50 mapeia no modelo).
- **Gravado em produção:** 1 `Skill` (`LOG-PROP-NEG-COND`) + `QuestionSkill` primary + `questions.primary_skill_id`; 3 `Misconception` ligados às alternativas erradas — **B** inversa (`MIS-LOG-001` ¬P→¬Q), **E** recíproca (`MIS-LOG-002` Q→P), **A** "negar tudo" (`MIS-LOG-003`); **C fica sem** misconception de propósito (mostra que cobertura parcial é OK); `questions.micro_lesson` com camadas **essential** + **deep** (camada 3 cai no `topic.description`). Verificado end-to-end contra o banco de prod.
- **Como o dono testa (logado):** Simulado → escopo **Raciocínio Lógico** → achar a questão "trabalhadora e honesta". Escolher uma alternativa **errada (B/E/A)** revela "Por que sua resposta pode estar errada" + o nome do erro conceitual; escolher **D (correta)** mostra a microaula em camadas ("Entender melhor" / "Dominar este assunto"). As **pills de confiança** aparecem ao selecionar uma alternativa.

### 2026-08-17 (full-remake · Sessão B) — F2 questões: confiança + feedback adaptativo + microaula em camadas
- **Fase 2 implementada e NO AR** (branch `feat/full-remake-adaptativo`, backend + frontend). Modo aprendizagem (o `QuestionsView` rotulado "SIMULADO", que dá feedback imediato) e o **teste grátis** ganharam a experiência adaptativa; o **Modo teste** (prova real, sem gabarito na ida) segue sem feedback, conforme spec §16.
- **Backend:**
  - Coluna JSON **`questions.micro_lesson`** (camadas `essential`/`deep`/`mastery`) — ORM + `_ensure_columns`. Aplicada no Postgres.
  - Novo **`app/services/feedback.py::build_answer_feedback`** (desacoplado da UI): monta `is_correct`, `explanation` (por que a correta está certa), **`why_wrong`** (diagnóstico da alternativa marcada via `option_misconceptions`/`misconceptions`, linguagem não acusatória "Seu raciocínio pode ter seguido…"), `misconception {code,name}` e **microaula em camadas** com **fallback gracioso** (camada 1 = `explanation`; camada 3 `mastery` cai para `topic.description` — o que hoje é a "micro-aula"). Nada autorado ainda ⇒ `why_wrong`/`essential` nulos, nada quebra.
  - `AnswerRequest` estendido (`confidence`/`hints_used`/`session_id`, opcionais/retrocompatíveis). Endpoints `answer` (pago) e `trial_answer` (gratuito) usam o serviço; `answer` **persiste a confiança no `Attempt`** e grava um **`LearningEvent` (QUESTION_ANSWERED)** bruto (spec §34/§35). `test/submit` anexa `why_wrong`/`misconception` ao diagnóstico pós-simulado (§17).
- **Frontend (`apps/web/app/page.tsx` + `globals.css`):**
  - **Pills de confiança** (Chutei / Em dúvida / Confiante) — 1 clique, opcional, só no modo aprendizagem e no trial; enviadas no corpo. `session_id` gerado por visita (agrupa os eventos).
  - Componente **`QuestionTeach`**: "Por que a correta está certa" → "Por que sua resposta pode estar errada" (+ nome do misconception) → **microaula camada 1** (estruturada, quando autorada) → **camada 2 "Entender melhor"** e **camada 3 "Dominar este assunto"** (colapsáveis; a 3 revela o conteúdo amplo do tópico, que antes ficava inline). Reusado no fluxo pago e no trial. Tema claro/escuro coberto.
- **Validação:** serviço testado em SQLite nos 3 cenários (acerto, erro com misconception, fallback) + persistência de `Attempt`/`LearningEvent`; `tsc --noEmit` limpo; endpoint testado em produção (resposta com camadas/`micro_aula`); build do front sem `localhost:9000`; web 200, API health 200. Sem regressão (falhas de `test_auth` seguem pré-existentes: owner 401 / reportlab).
- **Deploy:** API reiniciada (migração `micro_lesson`) + front reconstruído/copiado/reiniciado. **Próximo: Sessão C = F3 (motor adaptativo + MemoryScheduler + ReviewQueue) + F4 (sessão inteligente)** — e aí as rotas `/reviews/*` migram de owner-only para `PaidUser`+gratuito (ver §2.1 do doc de arquitetura).

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
