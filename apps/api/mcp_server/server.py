"""Instância FastMCP + registro das tools. Transporte stdio (Fase 1): roda como

    python -m mcp_server.server

a partir de `apps/api` (onde `app` é importável). O transporte HTTP + token é
da Fase 3 (ver spec §4)."""

from mcp.server.fastmcp import FastMCP

from mcp_server.config import SERVER_NAME
from mcp_server.tools import questoes

mcp = FastMCP(SERVER_NAME)
questoes.register(mcp)


def main() -> None:
    mcp.run()  # transporte padrão: stdio


if __name__ == "__main__":
    main()
