# Passa Fácil — Documentação de Arquitetura

> Documento de arquitetura técnica. Para o dia a dia entre sessões, a fonte da
> verdade operacional é [`ESTADO_DO_SISTEMA.md`](ESTADO_DO_SISTEMA.md). Este
> arquivo descreve *como o sistema é construído*; o funcional está em
> [`FUNCIONAL.md`](FUNCIONAL.md); a referência de endpoints em
> [`API_REFERENCE.md`](API_REFERENCE.md) e no [Swagger](api/swagger.html).

---

## 1. Visão geral

Passa Fácil é um app de **estudo adaptativo para concursos** (foco atual:
TCE‑SP 2026, cargo de Auditor de Controle Externo — TI). O produto combina banco
de questões objetivas comentadas, simulados no formato da prova, revisão
espaçada, estudo de caso discursivo com **correção por IA**, teste grátis público
e cobrança via Pix.

É um **monorepo** com dois aplicativos independentes:

| App | Stack | Papel |
|---|---|---|
| `apps/api` | FastAPI + SQLAlchemy 2.0 (Python) | Fonte da verdade. Regras de negócio, persistência, integrações. |
| `apps/web` | Next.js 16 (App Router) + React 19 | Interface pública (SEO/teste grátis) e área autenticada. |

```text
                 HTTPS (Let's Encrypt)
Navegador ─────────────► Apache (proxy/SSL)
                          │
              /api/*      │      resto
              ▼           │        ▼
      FastAPI (127.0.0.1:9000)   Next.js standalone (127.0.0.1:9001)
              │
              ├─► PostgreSQL (127.0.0.1:5433, container Docker)
              ├─► Asaas (Pix)            — urllib
              ├─► Provedores de IA       — urllib (Groq → Gemini → …)
              └─► Google Ads API         — urllib (conversão server-side, opcional)
```

**Princípio de ouro do projeto:** todo HTTP externo usa **apenas a stdlib
`urllib`** — sem `httpx`/`requests`. Cada cliente novo manda um `User-Agent`
explícito (o WAF Cloudflare da Groq devolve HTTP 403 ao UA padrão do Python).

---

## 2. Backend (`apps/api`)

### 2.1 Camadas

```
app/
├── main.py            # cria o FastAPI, CORS, lifespan (create_all + migração + seed), inclui routers
├── core/
│   ├── config.py      # Settings (pydantic-settings), lê env / .env
│   └── security.py    # Argon2 (pwdlib), JWT (PyJWT): access, verificação de e-mail, reset de senha
├── db/
│   ├── base.py        # Base declarativa + mixins (UUIDMixin, TimestampMixin)
│   ├── session.py     # engine, SessionLocal, get_db()
│   └── seed.py        # seed idempotente do concurso TCE‑SP + usuário dono
├── models/
│   └── entities.py    # todas as tabelas (ORM)
├── schemas/           # Pydantic (contratos de entrada/saída por domínio)
├── services/          # integrações externas e lógica pesada (urllib)
│   ├── asaas.py       # cobrança Pix
│   ├── google_ads.py  # upload de conversão server-side
│   ├── grading.py     # correção por IA (cascata de provedores)
│   ├── pdf_questions.py # extração de questões de PDF (pypdf/pdfplumber/Pillow)
│   └── email.py       # SMTP (verificação, reset, feedback)
└── api/
    ├── deps.py        # dependências: DbSession, CurrentUser, AdminUser, PaidUser, get_owner_user
    └── routes/        # um módulo por domínio (routers), todos sob /api/v1
```

### 2.2 Ciclo de vida (startup — `main.py::lifespan`)

Sem Alembic. A cada boot, em ordem:

1. `Base.metadata.create_all()` — cria tabelas novas.
2. `_ensure_columns()` — **micro‑migração idempotente**: adiciona colunas que
   `create_all` não adiciona a tabelas já existentes, via `ALTER TABLE ... ADD
   COLUMN` (funciona em Postgres e SQLite). Cobre as colunas de conversão do
   Google Ads em `subscriptions` e as colunas `ai_*` da correção por IA em
   `discursive_submissions`.
3. `_purge_old_trial_events()` — expurga telemetria anônima do teste grátis mais
   velha que **180 dias** (LGPD: minimização + retenção limitada).
4. `seed_tce_sp()` — semeia o concurso, matérias, tópicos e o usuário dono
   (idempotente).

> **Regra de migração:** para adicionar coluna a tabela existente, acrescente-a
> ao dicionário apropriado em `main.py::_ensure_columns`. Nunca dependa só de
> `create_all` para alterar tabela existente.

### 2.3 Middleware

- **CORS** (`CORSMiddleware`) — origens de `settings.cors_origins`.
- **`disable_api_cache`** — injeta `Cache-Control: no-store` em toda resposta sob
  `/api/v1` (evita que proxies/navegador sirvam dados de estudo desatualizados).

### 2.4 Autenticação e autorização

- **Senhas:** Argon2 (`pwdlib`).
- **Token:** JWT HS256, curta duração (`access_token_expire_minutes`, padrão 60),
  enviado como `Authorization: Bearer <token>`. Não há refresh token ainda.
- **Tokens especiais** (também JWT, com `type`): verificação de e-mail e reset de
  senha, com expiração própria.
- **Níveis de acesso** (dependências FastAPI em `api/deps.py`):

  | Dependência | Exige | Uso típico |
  |---|---|---|
  | `DbSession` | — | sessão de banco |
  | `CurrentUser` | JWT válido | usuário logado |
  | `PaidUser` | logado + e-mail verificado + assinatura ativa | conteúdo pago (questões, simulados, discursivas) |
  | `AdminUser` | logado + `is_admin` | banco de questões, analytics, revisões |
  | `get_owner_user` | resolve o usuário **dono** por e-mail | features single-tenant (revisões, simulados diagnósticos) |

  `PaidUser` retorna **402** (sem acesso) ou **403** (e-mail não verificado);
  `AdminUser` retorna **403**. Admin sempre tem acesso pago.

- **Modelo de acesso:** pagamento único libera plano `pro` por **730 dias**
  (2 anos) — `user_has_access()` valida plano ∈ {plus, pro}, status ∈ {active,
  trialing} e `current_period_end` (None = sem prazo, para concessões antigas).

### 2.5 Serviços externos (`services/`)

Todos com `urllib` + `User-Agent` próprio. Falha nunca deve derrubar o fluxo do
usuário (padrão *best-effort* com fallback).

- **`asaas.py`** — cria cliente, gera cobrança **Pix**, busca QR code e status.
  Alterna base/chave entre sandbox e produção conforme `asaas_sandbox`.
- **`grading.py`** — **correção por IA das discursivas**. Cascata de provedores
  gratuitos compatíveis com a API OpenAI (`/chat/completions`): tenta cada um na
  ordem de `grading_order` (padrão `groq,gemini`) e cai para o próximo em falha
  de rede, limite ou resposta inválida. Valida o JSON contra a grade real,
  **clampa cada nota ao teto** do critério e só aceita a correção se **todos** os
  critérios foram pontuados; senão, tenta o próximo. Retorna `None` se tudo
  falhar → o app degrada para autoavaliação/aviso, sem quebrar. Dá **crédito
  parcial** (notas decimais).
- **`google_ads.py`** — conversão "Compra" server‑side (`uploadClickConversions`).
  Desligada por padrão; exige OAuth completo. Fallback é o `gtag` no navegador.
- **`pdf_questions.py`** — extrai questões candidatas de PDFs de prova/gabarito
  (pipeline de importação do banco de questões).
- **`email.py`** — envio SMTP de verificação, reset de senha e feedback.

### 2.6 Persistência

- **Postgres** em produção (`127.0.0.1:5433`, container Docker); **SQLite** em
  dev. O ORM abstrai o dialeto; colunas `JSON` funcionam nos dois.
- IDs **UUID** (não sequenciais). Mixins padronizam `id`, `created_at`,
  `updated_at`.

Ver o modelo de dados completo em [§4](#4-modelo-de-dados).

---

## 3. Frontend (`apps/web`)

- **Next.js 16 (App Router)**, saída **`standalone`** (`next.config.ts`),
  React 19, Tailwind CSS 3, ícones `lucide-react`.
- **Área do app:** praticamente tudo em `app/page.tsx` (~2.9k linhas) — todas as
  "views" (login, dashboard, questões, simulado, resultados, discursivas,
  checkout) em um único componente cliente que troca de tela por estado.
- **Componentes de apoio:** `app/_components/HelpWidget.tsx` (widget "Fale
  conosco") e `OfflineBanner.tsx`.
- **Páginas públicas de SEO** (rotas próprias, indexáveis): `como-passar-tce-sp`,
  `cronograma-estudos-tce-sp`, `edital-tce-sp-2026`, `questoes-comentadas`, mais
  `robots.ts` e `sitemap.ts`. Chrome comum em `app/_seo/chrome.tsx`.
- **Contrato com a API:** a URL base é embutida em **build time** via
  `NEXT_PUBLIC_API_URL`. ⚠️ Buildar sem essa variável faz o bundle cair no
  default `http://localhost:9000/api/v1` e **quebra o login** no navegador do
  usuário (ver [`ESTADO_DO_SISTEMA.md`](ESTADO_DO_SISTEMA.md) §3).

> Consequência operacional: **mudança em `apps/web` só aparece após rebuild**
> (`next build` com a env + copiar `.next/static` + restart do serviço web).

---

## 4. Modelo de dados

Entidades em `apps/api/app/models/entities.py`. Todas herdam `UUIDMixin`
(+`TimestampMixin` na maioria).

### 4.1 Identidade e comercial
- **User** — `email` (único), `full_name`, `password_hash`, `is_active`,
  `is_admin`, `email_verified`.
- **Subscription** (1:1 com User) — `plan` (free/plus/pro), `status`
  (trialing/active/past_due/canceled), IDs do provedor, `current_period_end`, e
  campos de conversão Google Ads (`gclid`, `conversion_pending/reported/uploaded`,
  `conversion_upload_error`).

### 4.2 Catálogo de conteúdo
- **Exam** → **Subject** → **Topic** → **Question** (hierarquia).
  - `Subject.specialty` (ti / null=comum), `category` (general/specific), `weight`.
  - `Question` guarda `options` como JSON em texto, `correct_option`, `explanation`,
    `is_published`.
- **QuestionProvenance** (1:1 com Question) — origem, `content_hash` (dedup),
  `rights_status` (research_only/owner_only/licensed/public_domain/authorial),
  `external_key`, lote de importação.

### 4.3 Pipeline de importação (admin)
- **QuestionImportJob** — PDF enviado (prova ou gabarito), status do processamento.
- **QuestionDraft** — questão candidata extraída, em revisão até virar `Question`.

### 4.4 Aprendizagem
- **Attempt** — cada resposta do usuário a uma questão (acerto, tempo).
- **ReviewItem** — revisão espaçada por questão (`due_date`, `interval_days`,
  `repetitions`); intervalos 1 → 7 → 21 → 45 dias.
- **Simulation** / **SimulationAnswer** — simulado diagnóstico (single-tenant, dono).

### 4.5 Discursivas (estudo de caso)
- **DiscursiveCase** — enunciado, texto de apoio, `model_answer` (espelho),
  `micro_aula`, `pontuacao_maxima`, `is_demo`, `is_published`.
- **DiscursiveCriterion** — item da grade (N1, N2…) com `conteudo_esperado` e teto.
- **DiscursiveSubmission** — resposta do aluno + correção. Campos `self_*`
  (autoavaliação, legado/fallback) e `ai_*` (`ai_scores`, `ai_total`,
  `ai_feedback`, `ai_comentario`, `ai_provider`) preenchidos pela IA.

### 4.6 Suporte e telemetria
- **Feedback** — mensagens do widget "Fale conosco" (público; grava usuário se logado).
- **TrialEvent** — telemetria **anônima** do teste grátis (`anon_id` do
  localStorage, `event_type`, `payload` JSON). Append‑only, separada dos dados de
  usuário, retenção 180 dias.

```text
User 1─1 Subscription
User 1─* Attempt *─1 Question *─1 Topic *─1 Subject *─1 Exam
User 1─* ReviewItem   ─1 Question
User 1─* StudyTask
User 1─* Simulation 1─* SimulationAnswer ─1 Question
User 1─* DiscursiveSubmission *─1 DiscursiveCase 1─* DiscursiveCriterion
Question 1─1 QuestionProvenance
QuestionImportJob 1─* QuestionDraft
```

---

## 5. Infraestrutura e implantação (produção)

`passafacil.jussa.com.br` — Debian, sem orquestrador. Detalhes em
[`DEPLOY_DEBIAN.md`](DEPLOY_DEBIAN.md) e [`ESTADO_DO_SISTEMA.md`](ESTADO_DO_SISTEMA.md).

| Componente | Como roda |
|---|---|
| API | `uvicorn` via **systemd** `passafacil-api.service` (porta 9000). **Sem Docker.** |
| Web | Next standalone via **systemd** `passafacil-web.service` (porta 9001). |
| Postgres | Container Docker `passafacil-postgres` (porta 5433). |
| Proxy/SSL | Apache (`infra/apache/*.conf`) + Let's Encrypt. |
| Segredos | **`/etc/passafacil.env`** (`0640`), lido pelo systemd. Nunca no repo. |

**Modelo mental do deploy:** API e Web rodam direto da árvore de código.
- Backend: editar código → `sudo systemctl restart passafacil-api`.
- Frontend: `next build` **com `NEXT_PUBLIC_API_URL`** → copiar `.next/static`
  para o standalone → `sudo systemctl restart passafacil-web`.
- Segredos: editar `/etc/passafacil.env` → restart da API.

Compose (`compose.yaml`) existe apenas para **desenvolvimento local no Windows**.

---

## 6. Configuração (`core/config.py`)

Tudo via `Settings` (pydantic-settings), lido de variáveis de ambiente. Grupos:

- **App/DB/JWT:** `database_url`, `jwt_secret`, `access_token_expire_minutes`,
  `cors_origins`, `owner_email`.
- **Pagamento (Asaas):** `asaas_sandbox` (default `true`; produção usa `false` no
  `/etc`), chaves sandbox/prod, `asaas_webhook_token`, `price_reais` (100).
- **Correção por IA:** `grading_enabled`, `grading_order` (`groq,gemini`),
  `grading_timeout_seconds`, e por provedor (`*_api_key`, `*_model`, `*_base_url`)
  para Groq, Gemini, OpenRouter (fora da cascata: exige cartão) e Cerebras (idem).
- **Google Ads:** `google_ads_enabled` (default off) + credenciais OAuth.
- **E-mail/SMTP e suporte:** destinatários do feedback, remetente, host/porta.

Segredos reais vivem só em `/etc/passafacil.env`. O repo tem `.env.example` como
referência (sem valores).

---

## 7. Decisões e convenções

- **FastAPI + SQLAlchemy:** API tipada, domínio independente do dialeto de banco.
- **HTTP externo só com `urllib` + UA explícito.** Mock esconde erros de borda
  (WAF/headers) — validar contra o serviço real antes de dar como pronto.
- **Sem Alembic:** micro‑migrações idempotentes em `main.py::_ensure_columns`.
- **Best-effort em integrações:** correção por IA, e-mail, conversão e telemetria
  nunca derrubam a resposta ao usuário.
- **Git:** trabalhar em branch de feature; commitar/pushar só quando o dono pedir.
- **LGPD:** telemetria do teste grátis é anônima, minimizada e expurgada por idade.

---

## 8. Roadmap de robustez (pré-escala)

Itens conhecidos ainda não implementados (ver também `ESTADO_DO_SISTEMA.md` §5):
refresh token rotativo em cookie `httpOnly`, rate limiting, logs de auditoria,
CSP, backup testado, gestão externa de segredos, e ampliação da cascata de IA
(Cerebras/OpenRouter) quando a base de assinantes crescer.
