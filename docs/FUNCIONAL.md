# Passa Fácil — Documentação Funcional

> O que o produto faz, do ponto de vista do usuário e das regras de negócio.
> Complementa a [Arquitetura](ARQUITETURA.md) (como é construído) e a
> [Referência de API](API_REFERENCE.md) / [Swagger](api/swagger.html) (contratos).

---

## 1. Para quem é

App de **estudo adaptativo para concursos**, focado no **TCE‑SP 2026 — Auditor de
Controle Externo, Especialidade TI** (banca VUNESP, prova 11/10/2026). O aluno
estuda por questões comentadas, mede desempenho por matéria, treina os pontos
fracos, faz simulados no formato da prova e pratica a **discursiva (estudo de
caso)** com correção automática por IA.

### Perfis de usuário

| Perfil | Como se identifica | O que acessa |
|---|---|---|
| **Visitante** | sem login | site público, **teste grátis** (amostra fixa), dissertativa demo, feedback |
| **Cadastrado (free)** | login, e-mail a verificar | conta criada; conteúdo pago bloqueado até pagar |
| **Assinante (pro)** | pagou (Pix) + e-mail verificado | todo o conteúdo de estudo por 2 anos |
| **Dono/Admin** | `is_admin` | tudo + banco de questões, revisões, simulados diagnósticos, analytics |

---

## 2. Jornadas principais

### 2.1 Visitante → teste grátis
1. Chega pelo site (SEO / anúncio com `?gclid=`).
2. Faz o **teste grátis**: 8 questões fixas cobrindo 8 matérias (Gerais + TI),
   com dificuldades variadas. A ordem é embaralhada a cada acesso, mas a
   interpretação longa ("O Sobrado") nunca abre a amostra (primeira impressão).
3. Responde e vê **gabarito + explicação + micro‑aula** por questão.
4. Pode abrir a **dissertativa demo** (estudo de caso de método), escrever a
   resposta e receber o **espelho + correção da IA** — sem salvar nada (anônimo).
5. Toda a jornada emite **telemetria anônima** (funil: iniciou → respondeu → viu
   resultados → abriu a dissertativa → escreveu).

### 2.2 Visitante → cadastro → pagamento → assinante
1. **Cadastro** (`/auth/register`): nome, e-mail, senha (≥8). Cria `User` +
   `Subscription` (free) e dispara **e-mail de verificação**. O `gclid` do
   anúncio é capturado aqui.
2. **Verificação de e-mail** (link no e-mail → página de confirmação).
3. **Checkout** (`/billing/checkout`): informa CPF/CNPJ; o sistema gera uma
   **cobrança Pix** no Asaas e devolve **QR code + copia‑e‑cola**. Exige e-mail
   verificado.
4. **Pagamento** confirmado por **webhook** do Asaas ou por **confirmação
   preguiçosa** (o `/billing/status` reconsulta o Asaas). Ao confirmar:
   - plano vira **pro**, acesso por **2 anos** (730 dias);
   - marca a **conversão Google Ads** como pendente (o front dispara o `gtag`; se
     a via server-side estiver ligada e houver `gclid`, envia direto pela API e
     dispensa o front).
5. Agora com acesso pago, o aluno entra na área de estudo.

### 2.3 Assinante — estudo do dia a dia
- **Dashboard** (`/study/dashboard`): tarefas do dia, questões respondidas,
  acurácia geral, minutos estudados hoje, **cobertura** (questões distintas
  respondidas ÷ publicadas) e desempenho por matéria.
- **Praticar** (`/study/practice`): sessão contínua que **intercala matérias**
  (round‑robin). Prioriza questões **inéditas**; depois as **erradas**; por
  último as já acertadas (reforço). Não repete questão enquanto houver inédita.
  `focus=gaps` treina só lacunas (inéditas + erradas). A primeira questão nunca é
  "pesada" (texto longo).
- **Questões avulsas** (`/study/questions`): lote de questões ainda não
  respondidas no escopo escolhido.
- **Responder** (`/study/questions/{id}/answer`): registra a tentativa, devolve
  gabarito + explicação + micro‑aula; se **errar**, agenda **revisão** para hoje.
- **Escopo:** o aluno escolhe **especialidade** (ex.: TI traz as comuns + as de
  TI) e/ou **matérias específicas**. `/study/subjects` lista as matérias com
  contagem de questões.

### 2.4 Simulado (formato da prova)
- `/study/test` monta um simulado **sem gabarito na ida**. Sem matérias
  escolhidas, respeita a **proporção da prova: 75% Específicas (TI) + 25% Gerais**
  (edital: 60 + 20 = 80), escalada para o tamanho pedido. Faz **rodízio**:
  prioriza inéditas e recicla vistas quando o estoque acaba.
- `mode=fixed` devolve **sempre o mesmo conjunto** (para medir evolução no mesmo
  teste); `mode=random` sorteia.
- `/study/test/submit` corrige tudo de uma vez: registra tentativas, agenda
  revisão para os erros e devolve **resultado por questão + resumo por matéria**.

### 2.5 Resultados e lacunas
- `/study/results`: desempenho por matéria (acurácia, cobertura), os **5 maiores
  gaps** (pior aproveitamento com ≥3 tentativas ou menor cobertura) e uma
  **recomendação**: `focus_gaps` (ainda há o que cobrir) ou `repeat_all` (já viu
  tudo). Comparação com outros usuários fica reservada para quando houver base.

### 2.6 Discursiva / estudo de caso (com correção por IA)
1. Aluno lista casos (`/discursive/cases`) e abre um (só o enunciado, **sem o
   espelho**).
2. Escreve a resposta e envia (`/discursive/cases/{id}/submit`).
3. No envio, a **IA corrige** critério a critério (crédito parcial, notas
   decimais) e o sistema revela o **espelho + micro‑aula**. A correção mostra,
   por critério, a nota atribuída e a justificativa, mais um comentário geral e a
   nota total. **A IA marca os três botões** (Não completou / Em parte /
   Completou) em modo leitura — a antiga autoavaliação manual foi removida.
4. Se a IA estiver indisponível (raro), aparece um aviso "correção indisponível"
   — sem autonota.
5. **Histórico** (`/discursive/me/history`): notas por caso ao longo do tempo.

> **Como a IA corrige:** compara a resposta com o *espelho* e a *grade de
> critérios*, dá crédito parcial, ignora erros de forma (avalia conteúdo),
> reconhece paráfrases. Usa uma **cascata de provedores gratuitos** (Groq →
> Gemini). Só aceita a correção se **todos** os critérios foram pontuados; caso
> contrário, tenta o próximo provedor. Ver [Arquitetura §2.5](ARQUITETURA.md).

### 2.7 Suporte — "Fale conosco"
- Widget público (`/feedback`): categorias ajuda / reclamação / sugestão / elogio
  / outro. Grava no banco e **avisa o suporte por e-mail** (best‑effort). Funciona
  logado ou não; se logado, guarda quem enviou.

---

## 3. Regras de negócio (resumo)

| Tema | Regra |
|---|---|
| **Acesso pago** | Pagamento único → plano `pro`, **730 dias** de acesso. `has_access` = plano ∈ {plus,pro} + status ativo/trial + dentro do prazo. Admin sempre tem acesso. |
| **Verificação de e-mail** | Obrigatória para pagar e para conteúdo pago (admin dispensado). |
| **Confirmação de pagamento** | Webhook do Asaas **ou** confirmação preguiçosa via `/billing/status`; ambos reconsultam o Asaas antes de liberar. Idempotente. |
| **Conversão Google Ads** | Marcada na liberação. Via server‑side (se ligada + `gclid`) ou `gtag` no front; deduplicada pelo `transaction_id`. |
| **Rodízio de questões** | Inéditas antes de repetir; erradas antes das já acertadas. |
| **Proporção do simulado** | 75% TI / 25% Gerais quando não há matérias escolhidas. |
| **Revisão espaçada** | Errou → revisão hoje (intervalo 1 dia). Acertou na revisão → 1→7→21→45 dias. Errou na revisão → volta a 1. |
| **Correção por IA** | Crédito parcial; só vale se cobrir todos os critérios; cada nota clampada ao teto; falha → degrada sem quebrar. |
| **Teste grátis** | Conjunto **fixo** de 8 questões; correção pública só para elas; não registra tentativa. |
| **Telemetria do teste** | Anônima (`anon_id` do navegador), só tipos conhecidos, textos truncados, retenção 180 dias (LGPD). |

---

## 4. Catálogo do concurso (seed TCE‑SP 2026 — TI)

Semeado em `apps/api/app/db/seed.py`. Concurso **Auditor de Controle Externo —
TI** (TCE‑SP, VUNESP). Matérias:

**Conhecimentos Gerais** (comuns): Língua Portuguesa · Raciocínio Lógico ·
Ética Pública e Integridade · Legislação.

**Específicas (TI):** Segurança da Informação · Governança e Auditoria de TI ·
Redes e Infraestrutura · Banco de Dados · Engenharia de Software ·
Desenvolvimento de Sistemas · LGPD.

Cada matéria tem tópicos e um peso; as questões pertencem a tópicos.

### 4.1. Estrutura oficial da prova — Especialidade **Tecnologia da Informação (TI)**

Divisão de matérias e quantidade de questões, conforme o edital (usar como
referência para pesos, cobertura e montagem de simulados):

**Prova Objetiva — 80 questões**

- **Conhecimentos Gerais — 20 questões**
  - Língua Portuguesa — **12**
  - Raciocínio Lógico — **4**
  - Ética Pública e Integridade — **2**
  - Legislação — **2**
- **Conhecimentos Específicos (TI) — 60 questões**

**Prova Escrita**

- **Estudo de Caso — 2 questões** (discursivas; correção por IA — ver seção de
  discursivas)

> ✅ O seed (`apps/api/app/db/seed.py`) reflete essa divisão: as matérias de
> Conhecimentos Gerais têm `weight` **12/4/2/2** (Língua Portuguesa · Raciocínio
> Lógico · Ética Pública e Integridade · Legislação), com Ética e Legislação
> como matérias **separadas**. `weight` é metadado de priorização (não é
> consumido por lógica de seleção ainda); usar como referência para simulados.

---

## 5. Funcionalidades administrativas (dono)

- **Banco de questões** (`/question-bank/*`): estatísticas por fonte; importação
  de questões via **JSON em lote** e via **PDF** (inspeciona prova e gabarito,
  associa os dois, gera rascunhos, revisa, publica). Controle de **direitos**
  (research_only/owner_only/licensed/public_domain/authorial): só licenciadas/
  domínio público/autorais são publicadas; as `owner_only` ficam visíveis apenas
  para o dono.
- **Revisões** (`/reviews/*`): revisões devidas do dono, caderno de erros.
- **Simulados diagnósticos** (`/simulations/*`): geração/andamento/finalização
  (single‑tenant, dono).
- **Analytics do teste grátis** (`/study/trial/analytics`): funil de conversão,
  questões acessadas com acerto, e os textos escritos na dissertativa demo.
- **Piloto de áudio** (`/study/audio-pilot`): página para o dono ouvir/aprovar as
  8 aulas em áudio (voz TTS). O menu "Áudios" do app segue **"em breve"** — o
  piloto não liga a feature.

---

## 6. Estados e status (referência rápida)

- **SubscriptionPlan:** `free` · `plus` · `pro`
- **SubscriptionStatus:** `trialing` · `active` · `past_due` · `canceled`
- **QuestionImportJob.status:** `uploaded` → `processing` → `review` →
  `associated` → (`failed`)
- **QuestionDraft.status:** `pending` → `reviewed` → `published` (ou `rejected`)
- **rights_status:** `research_only` · `owner_only` · `licensed` ·
  `public_domain` · `authorial`
- **TrialEvent.event_type:** `trial_start` · `question_answered` ·
  `results_viewed` · `discursive_opened` · `discursive_submitted` · `audio_opened`

---

## 7. Estado das features

Situação atualizada mantida em [`ESTADO_DO_SISTEMA.md`](ESTADO_DO_SISTEMA.md) §4.
Em resumo, **no ar**: auth (JWT), billing (Asaas Pix, produção real), banco de
questões / import de PDF, simulados, revisões, estudo do dia, teste grátis com
telemetria, feedback, e **correção por IA das discursivas** (Groq → Gemini).
**Em breve:** menu de Áudios. **Desligado por padrão:** conversão Google Ads
server‑side.
