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
- Adicionar/rotacionar um segredo: editar `/etc/passafacil.env` → `sudo systemctl restart passafacil-api`.
- Ver o ambiente que o processo enxerga: `sudo tr '\0' '\n' < /proc/$(systemctl show passafacil-api -p MainPID --value)/environ`.

## 4. Estado atual das features

- **Auth** (JWT), **billing** (Asaas Pix — `asaas_sandbox=true` por padrão), **conversão Google Ads server-side** (desligada por padrão), **feedback** (widget "Fale conosco"), **banco de questões / import de PDF**, **simulados**, **revisões**, **estudo do dia**, **teste grátis** (telemetria anônima, retenção 180 dias — LGPD).
- **Correção por IA das discursivas (Fase 2) — ✅ NO AR (2026-08-16).** `apps/api/app/services/grading.py`: cascata de provedores gratuitos (Groq → Gemini → OpenRouter → Cerebras) via endpoint compatível com a API OpenAI. Corrige critério a critério com **crédito parcial**; nota salva em `discursive_submissions.ai_*`. Sem chaves/falha → **degrada para a autoavaliação manual** (Fase 1). Hoje ativa com **Groq**; as outras 3 são backup opcional (basta adicionar as chaves no `/etc`).
- **Áudio-piloto:** 8 MP3 estáticos (voz ElevenLabs) em `apps/api/media/audio_pilot/`, servidos em `/api/v1/study/audio-pilot` só para o dono revisar. Menu "Áudios" segue **"em breve"**. A chave da ElevenLabs **não está guardada** — os áudios foram pré-gerados por um script descartável (perdido); a chave vive só na conta ElevenLabs do dono.

## 5. Pendências / próximos passos

- [ ] **Mesclar** o branch `feat/correcao-ia-discursivas` na `main` (quando o dono aprovar).
- [ ] (Opcional) Adicionar chaves de **Gemini / OpenRouter / Cerebras** no `/etc/passafacil.env` para dar resiliência à cascata (hoje só Groq).
- [ ] Feature de **Áudios** ainda "em breve". Se for regerar/ampliar: criar `apps/api/scripts/gerar_audios.py` **versionado**, lendo `ELEVENLABS_API_KEY` do `/etc` (nunca hardcoded).
- [ ] `asaas_sandbox` ainda `true` — trocar para produção quando for cobrar de verdade.

## 6. Convenções / lições aprendidas

- **HTTP externo:** sempre `urllib` + **`User-Agent` explícito**. ⚠️ O WAF (Cloudflare) da Groq responde **HTTP 403** ao `User-Agent` padrão do Python (`Python-urllib/x.y`). Todo cliente HTTP novo deve mandar um UA próprio (ver `services/grading.py`).
- **Testes que batem em rede:** mock esconde erros de borda (WAF, headers). Validar de verdade contra o serviço no ar antes de dar como pronto.
- **Migrações:** sem Alembic — acrescentar colunas em `main.py::_ensure_columns` (idempotente, funciona em Postgres e SQLite).
- **Git:** trabalhar em branch de feature; **só commitar/pushar quando o dono pedir**. O working tree costuma ter muita coisa não commitada — conferir escopo antes de `git add -A`.
- **Segredos:** só em `/etc/passafacil.env` + restart. Nunca commitar `.env`.

---

## 7. Diário de bordo

### 2026-08-16 — Correção por IA das discursivas no ar + doc viva
- **Fase 2 (correção por IA)** implementada e **ativada em produção** com Groq. Antes só havia autoavaliação manual (o "0 de 20" que o dono via era o placar inicial, não uma correção — origem da queixa de "nota zero").
  - Novo `apps/api/app/services/grading.py` (cascata grátis, `urllib`). Colunas `ai_*` em `DiscursiveSubmission` + micro-migração em `main.py`. Rotas `discursive` corrigem no `submit`/`demo`. Front: painel "Correção da IA" (nota + justificativa por critério + comentário), com fallback para a autoavaliação. `.env.example` documenta as chaves.
- **Bug encontrado e corrigido no ar:** a chamada à Groq dava **HTTP 403** porque faltava `User-Agent` (bloqueio de WAF). Corrigido em `grading.py`. Só foi pego testando de verdade contra a API no servidor (o teste unitário com mock não pegou).
- **Validação real:** resposta no tema recebeu **5,5/10** com notas parciais por critério (N1 2,0 · N2 1,5 · N3 2,0). Crédito parcial funcionando.
- Commit inicial em `feat/correcao-ia-discursivas` (pushed) incluiu também avanços já presentes no working tree (billing, feedback, SEO, materiais em `docs/`).
- **Criado este arquivo** (`docs/ESTADO_DO_SISTEMA.md`) como memória viva entre sessões, a pedido do dono (que apontou, com razão, o risco de perda de contexto entre sessões).
