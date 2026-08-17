# Arquitetura de Aprendizagem Adaptativa — Passa Fácil

> **Documento da Fase 0 (Auditoria) do "full remake".** Spec-fonte: `full_remake/full-remake.txt` (61 seções).
> Registra o **estado atual** do sistema, as **incompatibilidades** com a especificação adaptativa, a **estratégia de migration** escolhida e o **modelo de dados da Fase 1**.
> Complementa (não substitui) `docs/ESTADO_DO_SISTEMA.md` (diário de bordo) e `docs/ARQUITETURA.md` (arquitetura geral).
>
> **Regras duras do remake (§OBJETIVO da spec):** não reescrever do zero; não destruir questões/explicações/microaulas/áudios/simulados/dissertativas; migrations compatíveis; preservar campos originais ao lado dos novos; branch git dedicada (`feat/full-remake-adaptativo`).

Última atualização: **2026-08-17** (Sessão A — F0 + F1).

---

## 1. Estado atual do sistema (auditoria)

### 1.1 Stack
- **Backend:** FastAPI 0.116 + SQLAlchemy 2.0 (ORM tipado, `Mapped[...]`). Pydantic v2 / pydantic-settings. Auth JWT (PyJWT + argon2 via pwdlib).
- **HTTP externo:** **somente `urllib` da stdlib** com `User-Agent` explícito (padrão do projeto; sem `httpx`/`requests`). Ver `services/grading.py`, `services/asaas.py`.
- **Frontend:** Next.js (App Router). A UI é quase toda `apps/web/app/page.tsx` (arquivo grande com todas as "views"); estilos em `app/globals.css` com tema claro/escuro via `[data-theme]`.
- **Banco:** Postgres em produção (`127.0.0.1:5433`, container Docker); SQLite em dev. Tabelas criadas no startup por `Base.metadata.create_all`.
- **Deploy:** systemd sem Docker para a app (API `:9000`, web `:9001`); Apache faz proxy/SSL. Detalhes e armadilhas em `docs/ESTADO_DO_SISTEMA.md` §2/§3.

### 1.2 Ciclo de vida do schema (⚠️ **não há Alembic**)
No `lifespan` de `app/main.py`, em ordem:
1. `Base.metadata.create_all(bind=engine)` — cria **tabelas novas** (mas **não** altera tabelas existentes).
2. `_ensure_columns()` — **micro-migração idempotente**: `ALTER TABLE ... ADD COLUMN` para colunas novas em tabelas já existentes. Funciona em Postgres e SQLite. Hoje cobre `subscriptions` (gclid etc.) e `discursive_submissions` (campos `ai_*`).
3. `_purge_old_trial_events()` — expurgo LGPD (telemetria anônima > 180 dias).
4. `seed_tce_sp(db)` — seed idempotente, **guardado por `if not exam`** (não altera produção; só popula bases novas).

> **Consequência para o remake:** tabelas novas "aparecem sozinhas" via `create_all`; **colunas novas em tabelas existentes** (ex.: `questions`, `attempts`) exigem entrada no `_ensure_columns`. É esse o mecanismo de migration — mantido.

### 1.3 Modelo de dados atual (`app/models/entities.py`)
| Tabela | Papel | Campos-chave relevantes ao remake |
|---|---|---|
| `users` | Conta/login | is_admin, email_verified |
| `subscriptions` | Plano/pagamento | plan (free/plus/pro), status, gclid, conversão Ads |
| `exams` | Concurso | slug, exam_date, is_published |
| `subjects` | Disciplina | slug, category (general/specific), **weight** (peso editorial), specialty (ti/…), display_order |
| `topics` | Tópico | slug, difficulty (1–5, metadado) |
| `questions` | Questão objetiva | statement, **options (JSON em Text)**, **correct_option (int index)**, explanation, source, is_published |
| `question_provenance` | Proveniência/direitos | content_hash (dedup), rights_status, import_batch |
| `question_import_jobs` / `question_drafts` | Pipeline de import de PDF | status, confidence |
| `attempts` | Tentativa numa questão | selected_option, is_correct, response_time_seconds, answered_at |
| `study_tasks` | Tarefa do "estudo do dia" | activity_type, scheduled_date, is_completed |
| `review_items` | Revisão espaçada (SM-2 cru) | due_date, interval_days, repetitions, last_result |
| `simulations` / `simulation_answers` | Simulado | status, display_order, is_correct |
| `discursive_cases` / `discursive_criteria` / `discursive_submissions` | Dissertativa/estudo de caso + correção por IA | model_answer (espelho), criteria (grade N1/N2…), ai_scores/ai_total/ai_feedback |
| `feedback_messages` | Widget "Fale conosco" | — |
| `trial_events` | Telemetria anônima do teste grátis | anon_id, event_type, payload |

### 1.4 Fluxos-chave hoje
- **Responder questão** (`study.answer`): grava um `Attempt` (só selected_option/is_correct/tempo). **Sem confiança, sem hints, sem session_id, sem habilidade.**
- **Revisão espaçada** (`reviews.py`): `ReviewItem` com escada fixa `interval_days ∈ [1,7,21,45]` por `repetitions`; erro zera. **Rotas `/reviews/*` hoje gated a admin/owner** (`Depends(get_admin_user)` + `get_owner_user`) — não é fluxo de aluno ainda.
- **Simulado** (`simulations.py`): monta lote, navega Anterior/Próxima, retoma por ID, corrige só no fim.
- **Dissertativa** (`discursive.py`): submit → correção por IA critério-a-critério (cascata Groq→Gemini), com espelho como referência. **Já é, conceitualmente, um MVP da Fase 7.**

---

## 2. Incompatibilidades com a especificação adaptativa

| # | Requisito da spec | Situação atual | Fase que resolve |
|---|---|---|---|
| I1 | Mapa de conhecimento (Concurso→Disciplina→Tópico→**Habilidade→Sub-habilidade**) | Só vai até **Tópico**. Não existe `Skill`. | **F1** |
| I2 | Relações entre habilidades (prerequisite_of/related_to/…) | Inexistente | **F1** |
| I3 | Questão → primary/secondary skills, difficulty, question_family, review_status | Questão só tem `topic_id`, `is_published`, `source` | **F1** (colunas + join) |
| I4 | Misconceptions + vínculo alternativa→misconception | Inexistente | **F1** |
| I5 | Confiança (chutei/dúvida/confiante), hints, session_id no evento | `Attempt` não guarda | **F1** (colunas) / **F2** (UX) |
| I6 | `UserSkillState` (mastery, memória, retrievability, estados) | Inexistente; só `review_items` cru por questão | **F1** |
| I7 | `LearningEvent` bruto (não só agregado) | Só `attempts` agregado | **F1** |
| I8 | Domínio ≠ Memória; scheduler moderno (FSRS) desacoplado | Escada fixa SM-2 acoplada à rota | **F3** |
| I9 | Feedback adaptativo + microaula em camadas 1/2/3 | Explicação monolítica | **F2** |
| I10 | Sessão inteligente / "Memória de hoje" / fila adaptativa | Inexistente | **F3/F4** |
| I11 | Dashboard mapa de conhecimento / riscos / erros conceituais | Inexistente | **F5** |
| I12 | Aulas/áudio interativo com checkpoints | Áudio-piloto estático "em breve" | **F6** |
| I13 | Dissertativa: rubric estruturada, reescrita ativa, nota estimada | MVP existe (cases/criteria/AI) — falta reescrita/rubric semântica | **F7** (evolui o que existe) |
| I14 | Blueprint do edital (pesos/quantidades) | `subject.weight` existe (peso editorial); sem entidade blueprint | **F1 (parcial)** / futuro |

> **Preservação (regra dura):** nada acima **substitui** conteúdo. Campos novos entram **ao lado** dos originais; F8 fará a reclassificação sem apagar (`original_explanation`, `original_micro_lesson`, `NEEDS_REVIEW`).

### 2.1 Modelo de acesso (regra dura — decisão do dono, 2026-08-17)

**Não pode existir feature "owner-only".** As funcionalidades adaptativas são para **usuários pagos logados** e **usuários gratuitos** — cada estado do aluno é sempre por **usuário real** (`user.id`), nunca atribuído ao dono.

Níveis de acesso do projeto (`app/api/deps.py`):
- **`PaidUser`** (`get_paid_user`): logado + e-mail verificado + acesso pago (plano ativo/trialing) ou admin → **superfície completa** das features adaptativas (sessão inteligente, mapa de conhecimento, revisão espaçada, dissertativas com IA).
- **Usuário gratuito** (rotas públicas `/study/trial*`): recebe uma **versão limitada** (test-drive) — mesma lógica adaptativa, porém com amostra reduzida de questões/conteúdo e telemetria anônima (`trial_events`, `learning_events.user_id` nullable). Cada nova feature deve oferecer uma porta de entrada gratuita bounded, no mesmo espírito do trial atual.
- **`get_admin_user`/`get_owner_user`**: **apenas** para painéis de autoria/curadoria de conteúdo (§50 da spec) e operação — **nunca** para o fluxo de estudo do aluno.

> **⚠️ GAP legado a corrigir:** as rotas `/reviews/*` hoje usam `Depends(get_admin_user)` + `get_owner_user` (piloto só do dono). Devem ser **migradas para `PaidUser` por-usuário + variante gratuita** quando a revisão virar fluxo de aluno — trabalho da **F3/F4** (ReviewQueue / sessão inteligente), não da F1. As tabelas da F1 (`user_skill_states`, `learning_events`) já nascem por-usuário, então nenhuma mudança de dados é necessária.

---

## 3. Estratégia de migration (decisão)

**Princípio:** manter o mecanismo atual (sem Alembic), pois é o que roda em produção e é idempotente/cross-dialect.

1. **Tabelas novas** (Skill, SkillRelation, QuestionSkill, Misconception, OptionMisconception, UserSkillState, LearningEvent, QuestionFamily) → declaradas em `app/models/adaptive.py`; **criadas automaticamente** por `create_all` no próximo startup. Zero DDL manual.
2. **Colunas novas em tabelas existentes** (`questions`, `attempts`) → adicionadas em `_ensure_columns` via `ALTER TABLE ADD COLUMN`, todas **nullable ou com default** para não quebrar linhas existentes nem inserts atuais.
3. **Sem FK inline no DDL de ALTER** (padrão já usado no projeto, ex.: `gclid`): em produção as colunas entram "cruas"; a FK é declarada no **modelo ORM** (vale para bases novas via `create_all` e para joins/relationships do ORM). Consistente com o estilo existente; evita divergência Postgres×SQLite no `ADD COLUMN ... REFERENCES`.
4. **Enums das novas entidades como `String` + constantes de módulo** (não `Enum` nativo do Postgres). Motivo: estados adaptativos (`UserSkillState.state`, `SkillRelation.relation_type`, papéis, `event_type`) **vão evoluir**, e sem Alembic um `ALTER TYPE ... ADD VALUE` seria doloroso. String + validação na camada de serviço dá flexibilidade sem migration de tipo. (As enums legadas de `Subscription` permanecem como estão.)
5. **Preservação:** as colunas `original_explanation` / `original_micro_lesson` são criadas já na F1, mas **só serão populadas na F8** (migração de conteúdo). A F1 não sobrescreve nada.
6. **Reversibilidade:** como tudo é aditivo (tabelas + colunas nullable), um rollback é "não usar as novas estruturas"; nenhum dado antigo é tocado.

---

## 4. Modelo de dados da Fase 1 (implementado)

Arquivo: **`app/models/adaptive.py`** (registrado em `app/models/__init__.py`). Constantes de vocabulário controlado no topo do arquivo.

### 4.1 Novas tabelas
- **`skills`** — habilidade avaliável. `code` (único), name, description, `subject_id?`, `topic_id?`, `parent_skill_id?` (auto-relação hierárquica), `difficulty_base` (float), `importance` (int 1–5), `exam_relevance` (int 1–5), `status` (active/draft/deprecated). Pré-requisitos via `skill_relations`.
- **`skill_relations`** — grafo de habilidades. `from_skill_id`, `to_skill_id`, `relation_type` ∈ {prerequisite_of, related_to, depends_on, commonly_confused_with}. Único por (from, to, type).
- **`question_skills`** — N:N questão↔habilidade. `role` ∈ {primary, secondary}, `weight`. Único por (question, skill). Fonte de verdade do mapeamento; `questions.primary_skill_id` é espelho de conveniência para consulta rápida do motor.
- **`misconceptions`** — erro conceitual recorrente. `code` (único), name, description, `wrong_pattern`, `correction`, `skill_id?`.
- **`option_misconceptions`** — vincula **alternativa errada** (por índice) a um misconception. `question_id`, `option_index` (int, casa com `questions.options`/`correct_option`), `misconception_id`, `explanation?`. Único por (question, option_index). Não precisa existir para todas as alternativas.
- **`user_skill_states`** — estado do conhecimento do aluno por habilidade (§11 da spec, todos os campos): mastery_score, memory_stability, difficulty_estimate, retrievability, timestamps (first/last/last_success/next_review), contadores (attempts/correct/wrong/consecutivos), sinais pedagógicos (high_confidence_errors, low_confidence_corrects, transfer_successes, last_response_time) e `state` ∈ {UNSEEN, EXPOSED, LEARNING, CONSOLIDATING, MASTERED, FRAGILE, LAPSED}. Único por (user, skill).
- **`learning_events`** — log bruto append-only (§34/§35). user/question/skill (todos nullable p/ robustez), event_type, selected_option, correct, confidence, response_time, hints, session_id, review_interval, `scheduler_state_before`/`scheduler_state_after` (JSON), `payload` (JSON). Nunca agregado; base para recalibração futura.
- **`question_families`** — agrupa questões do mesmo princípio para transferência (§5). `code` (único), name, description. `questions.question_family_id` aponta para cá.

### 4.2 Colunas novas em tabelas existentes (via `_ensure_columns`)
**`questions`:** `primary_skill_id?` (espelho), `question_family_id?`, `difficulty?` (int 1–5), `question_type` (default `multiple_choice`), `review_status` (default `legacy`), `content_version` (default 1), `ai_generated` (default false), `reviewed_at?`, `reviewed_by?`, `original_explanation?`, `original_micro_lesson?`.

**`attempts`:** `confidence?` (chutei/duvida/confiante), `hints_used` (default 0), `session_id?`, `skill_id?` (habilidade primária avaliada, denormalizada), `is_transfer` (default false).

> Todas nullable ou com default ⇒ inserts atuais de `Attempt`/`Question` continuam funcionando sem alteração de código nesta fase. Nenhuma rota muda de comportamento na F1.

---

## 5. O que a Fase 1 **não** faz (escopo/limites deliberados)

- **Não** implementa o `MemoryScheduler`/`AdaptiveLearningEngine`/`ReviewQueue` (Fase 3) — só cria os **campos** que eles vão usar. Decisão FSRS (adotar `py-fsrs` via adapter vs. camada abstrata própria) fica registrada para a F3: **preferência por camada abstrata `MemoryScheduler` com implementação própria simples primeiro**, deixando *seam* para um adapter FSRS depois — coerente com a política do projeto de minimizar dependências (hoje até HTTP é só `urllib`).
- **Não** muda a UI nem as rotas (confiança/feedback/microaula em camadas são Fase 2).
- **Não** popula habilidades/misconceptions nem reclassifica questões existentes (Fase 8). A F1 entrega o **esqueleto de dados vazio**, seguro para produção.
- **Não** cria `ExamBlueprint` como entidade nova (o `subject.weight` já cobre peso editorial por ora; reavaliar em fase futura — I14).

---

## 6. Mapa de serviços-alvo (referência para próximas fases, §57)

`QuestionService · ContentService · KnowledgeGraphService · UserSkillService · AdaptiveLearningEngine · MemoryScheduler · MisconceptionService · SimulationService · EssayEvaluationService · LessonService · AnalyticsService`.

Regra de ouro: **UI desacoplada dos algoritmos de aprendizagem**. Nenhuma lógica de scheduler/motor dentro de componentes de tela nem dentro das rotas — em `app/services/`.

---

## 7. Ordem de execução por sessões (economia de créditos)

| Sessão | Fases | Status |
|---|---|---|
| **A** | **F0 auditoria + F1 modelo de dados/migrations** | **concluída + aplicada em prod** |
| **B** | **F2 questões (confiança, feedback adaptativo, microaula em camadas)** | **concluída + no ar** (`services/feedback.py`, `micro_lesson`, pills de confiança, `QuestionTeach`; conteúdo a autorar depois) |
| C | F3 motor + scheduler + fila / F4 sessão inteligente | pendente |
| D | F5 dashboard | pendente |
| E | F6 aulas/áudio interativo | pendente |
| F | F7 dissertativas (evolui o MVP atual) | pendente |
| G | F8 migração de conteúdo + F9 QA | pendente |

*Aplicação em produção:* como a F1 é puramente aditiva, "publicar" = `sudo systemctl restart passafacil-api` (roda `create_all` + `_ensure_columns`). Sem rebuild de frontend (nada mudou em `apps/web`).
