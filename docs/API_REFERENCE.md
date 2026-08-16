# Passa Fácil — Referência de API

> Catálogo legível dos endpoints. O contrato **canônico e sempre atual** é o
> OpenAPI gerado pela própria API:
>
> - **Swagger UI ao vivo:** a API FastAPI expõe `/docs` (Swagger) e `/redoc`.
> - **Spec versionado neste repo:** [`api/openapi.json`](api/openapi.json)
>   (60 rotas) + visualizador offline [`api/swagger.html`](api/swagger.html).
>
> Regenerar o spec após mudar rotas:
> ```bash
> cd apps/api && .venv/bin/python -c "import json;from app.main import app;\
> json.dump(app.openapi(), open('../../docs/api/openapi.json','w'), ensure_ascii=False, indent=2)"
> ```

## Convenções

- **Base:** `/api/v1` (exceto `GET /health`, na raiz).
- **Auth:** `Authorization: Bearer <jwt>`. Colunas de acesso:
  🟢 público · 🔑 logado (`CurrentUser`) · 💳 pago (`PaidUser`) · 🛠️ admin (`AdminUser`).
- **Erros comuns:** `401` sem/invalid token · `402` sem assinatura · `403`
  e-mail não verificado ou não‑admin · `404` recurso · `409` conflito ·
  `422` validação.
- Respostas sob `/api/v1` vêm com `Cache-Control: no-store`.

---

## Auth — `/auth`
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/auth/register` | 🟢 | Cria usuário + assinatura free; envia verificação; captura `gclid`. Retorna token. |
| POST | `/auth/login` | 🟢 | Autentica; retorna JWT + usuário. |
| GET | `/auth/me` | 🔑 | Perfil, `has_access`, plano, conversão pendente. |
| GET | `/auth/verify?token=` | 🟢 | Confirma e-mail (página HTML). |
| POST | `/auth/resend-verification` | 🟢 | Reenvia link de ativação (resposta genérica). |
| POST | `/auth/forgot-password` | 🟢 | Envia link de reset (resposta genérica). |
| GET | `/auth/reset?token=` | 🟢 | Formulário HTML de nova senha. |
| POST | `/auth/reset-password` | 🟢 | Redefine a senha a partir do token. |

## Billing — `/billing`
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/billing/checkout` | 🔑 | Gera cobrança **Pix** (Asaas); retorna QR + copia‑e‑cola. Exige e-mail verificado. |
| GET | `/billing/status` | 🔑 | Acesso/plano; **confirmação preguiçosa** do pagamento. |
| POST | `/billing/conversion/reported` | 🔑 | Front avisa que disparou o `gtag` (evita reenvio). |
| POST | `/billing/webhook/asaas` | 🟢* | Webhook do Asaas (*valida `asaas-access-token*). Libera acesso no pagamento. |

## Study — `/study`
### Conteúdo pago
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/study/subjects` | 🔑 | Matérias com especialidade e contagem de questões. |
| GET | `/study/dashboard` | 🔑 | Tarefas do dia, stats, cobertura, desempenho por matéria. |
| PATCH | `/study/tasks/{task_id}/toggle` | 🔑 | Marca/desmarca tarefa do dia. |
| GET | `/study/questions` | 💳 | Lote de questões inéditas no escopo (`limit`, `subjects`, `specialty`). |
| GET | `/study/practice` | 💳 | Sessão intercalada; inéditas→erradas→acertadas; `focus=gaps`. |
| GET | `/study/results` | 🔑 | Desempenho, gaps e recomendação no escopo. |
| GET | `/study/test` | 💳 | Monta simulado (proporção 75/25; `mode`, `size`, escopo). |
| POST | `/study/test/submit` | 💳 | Corrige o simulado; registra tentativas; resumo por matéria. |
| POST | `/study/questions/{question_id}/answer` | 💳 | Responde questão avulsa; agenda revisão se errar. |
### Teste grátis (público)
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/study/trial` | 🟢 | Amostra fixa (8 questões, sem gabarito). |
| GET | `/study/trial/full` | 🟢 | Amostra completa (com gabarito/explicação) — SEO. |
| POST | `/study/trial/{question_id}/answer` | 🟢 | Corrige só as questões da amostra (não registra). |
| POST | `/study/trial/event` | 🟢 | Telemetria anônima (tipos conhecidos). |
| GET | `/study/trial/audios` | 🟢 | Lista as 8 aulas em áudio do teste. |
| GET | `/study/trial/analytics` | 🛠️ | Funil + questões + textos da dissertativa demo. |
### Piloto de áudio (revisão do dono)
| GET | `/study/audio-pilot` | 🟢 | Página HTML com os MP3 do piloto. |
| GET | `/study/audio-pilot/{name}` | 🟢 | Serve um MP3 do piloto. |

## Discursivas — `/discursive`
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/discursive/demo` | 🟢 | Enunciado do caso demo (sem espelho). |
| POST | `/discursive/demo/submit` | 🟢 | Revela espelho + **correção da IA** (não persiste). |
| GET | `/discursive/cases` | 💳 | Lista de estudos de caso publicados. |
| GET | `/discursive/cases/{case_id}` | 💳 | Enunciado (sem espelho). |
| POST | `/discursive/cases/{case_id}/submit` | 💳 | Envia resposta; persiste; **corrige por IA**; revela espelho. |
| GET | `/discursive/submissions/{submission_id}` | 💳 | Envio + correção + espelho. |
| PATCH | `/discursive/submissions/{submission_id}` | 💳 | Autoavaliação (legado/fallback). |
| GET | `/discursive/me/history` | 💳 | Histórico de notas por caso. |

## Reviews — `/reviews` (🛠️ admin / dono)
| GET | `/reviews/due` | 🛠️ | Revisões devidas do dono. |
| POST | `/reviews/{review_id}/answer` | 🛠️ | Responde revisão; reagenda (1→7→21→45). |
| GET | `/reviews/errors` | 🛠️ | Caderno de erros. |

## Simulations — `/simulations` (🛠️ admin / dono)
| POST | `/simulations` | 🛠️ | Cria simulado diagnóstico. |
| GET | `/simulations/latest` | 🛠️ | Último simulado. |
| GET | `/simulations/{id}` | 🛠️ | Simulado por id. |
| POST | `/simulations/{id}/questions/{qid}` | 🛠️ | Salva resposta. |
| POST | `/simulations/{id}/finish` | 🛠️ | Finaliza e apura. |

## Question Bank — `/question-bank` (🛠️ admin / dono)
| GET | `/question-bank/stats` | 🛠️ | Totais e fontes. |
| GET | `/question-bank/topics` | 🛠️ | Tópicos para associação. |
| POST | `/question-bank/import` | 🛠️ | Importa questões via JSON em lote (dedup por hash/key). |
| POST | `/question-bank/pdf/inspect` | 🛠️ | Envia PDF (prova/gabarito) e extrai candidatos. |
| GET | `/question-bank/pdf/jobs` | 🛠️ | Lista importações. |
| GET | `/question-bank/pdf/jobs/{job_id}` | 🛠️ | Prévia de uma importação. |
| POST | `/question-bank/pdf/jobs/{job_id}/reprocess` | 🛠️ | Reprocessa o PDF. |
| GET | `/question-bank/pdf/jobs/{job_id}/images/{filename}` | 🛠️ | Imagem PNG de questão. |
| POST | `/question-bank/pdf/associate` | 🛠️ | Casa prova + gabarito → rascunhos. |
| GET | `/question-bank/drafts` | 🛠️ | Lista rascunhos (`status`, `exam_job_id`). |
| PATCH | `/question-bank/drafts/{draft_id}` | 🛠️ | Edita rascunho. |
| POST | `/question-bank/drafts/bulk` | 🛠️ | Ação em lote (review/reject). |
| POST | `/question-bank/drafts/{draft_id}/publish` | 🛠️ | Publica rascunho revisado como questão. |

## Feedback / Health
| POST | `/feedback` | 🟢 | Mensagem "Fale conosco"; grava + avisa suporte. |
| GET | `/health` | 🟢 | Liveness (`{"status":"ok"}`). |
