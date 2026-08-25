#!/usr/bin/env bash
# Rotina de enriquecimento das explicações (ver scripts/enriquecer_explicacoes.py).
# Roda em lotes pequenos, respeitando o orçamento diário de tokens do Groq (TPD
# 200k/dia, compartilhado com a correção de discursivas ao vivo). É resumível: o
# relatório guarda os ids já feitos. O disjuntor (--give-up-after) faz a rodada
# parar sozinha quando a cota do dia acaba, sem starvar o serviço.
#
# Instalado no cron do usuário jussa (ver crontab -l). O jussa lê /etc/passafacil.env
# direto (grupo), então NÃO precisa de sudo.
set -eo pipefail

APP_DIR="/home/jussa/FileShare/development/passa_facil/apps/api"
LOG="$APP_DIR/../../docs/acervo/observacoes/enriquecer_cron.log"

cd "$APP_DIR"
# Carrega o env LITERALMENTE (sem expandir '$' nos valores — a chave Asaas tem '$',
# que sob 'source' viraria variável e quebraria/corromperia). Pula comentários/vazias.
while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    export "$line"
done < /etc/passafacil.env

echo "===== $(date -Is) — início =====" >>"$LOG"
# Lote pequeno: ~40 tentativas, ritmo sob o TPM, para sozinho quando a cota diária acaba.
.venv/bin/python -m scripts.enriquecer_explicacoes \
    --limit 40 --delay 15 --backoff 15 --retries 3 --give-up-after 15 \
    2>>"$LOG" | grep -vE "429|falhou" >>"$LOG" || true
echo "===== $(date -Is) — fim =====" >>"$LOG"
