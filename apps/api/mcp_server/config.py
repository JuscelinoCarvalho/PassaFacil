"""Configuração do servidor MCP. O banco vem das MESMAS settings da API
(`app.core.config.settings.database_url` → `DATABASE_URL` no ambiente), então o
MCP sempre lê o mesmo banco que a plataforma, sem configuração paralela."""

import os

# Nome anunciado ao cliente MCP (aparece no Claude Desktop / Inspector).
SERVER_NAME = os.getenv("PF_MCP_SERVER_NAME", "passa-facil")
