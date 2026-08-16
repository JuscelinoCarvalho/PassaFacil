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
