# Spec — Servidor MCP do Passa Fácil

> Documento para construção agêntica via Claude Code.
> Objetivo duplo: (1) dar ao Passa Fácil uma interface de IA reutilizável e (2) servir de **portfólio demonstrável** de integração MCP + tool use.

---

## 1. Objetivo

Criar um **servidor MCP (Model Context Protocol)** que expõe as capacidades do Passa Fácil (banco de questões, simulados e correção discursiva com IA) como *tools*, *resources* e *prompts*. Assim, qualquer cliente MCP (Claude Desktop, Claude Code, Cursor, agentes próprios) pode operar a plataforma em linguagem natural.

Exemplos de uso que devem funcionar ao final:
- "Me traga 10 questões de Direito Administrativo da VUNESP, nível difícil."
- "Monte um simulado de 20 questões para o TCE-SP com foco em Controle Externo."
- "Corrija esta redação no padrão da banca FCC e me diga a nota."
- "Quantas questões temos por banca e por matéria?"

---

## 2. Contexto do projeto existente

- Backend: **Python + FastAPI**
- Banco: **MySQL**
- Infra: **Linux + Nginx**
- Já existe (ou está em desenvolvimento) a **correção discursiva com IA**, com abstração de provider (Anthropic/OpenAI), fila assíncrona e requisitos de LGPD (ver `spec-correcao-discursiva.md`).

---

## 3. Fase 0 — Reconhecimento (obrigatório antes de codar)

O Claude Code deve, **antes de escrever qualquer código**:

1. Mapear a estrutura do repositório (models/ORM, schemas Pydantic, services, routers, fila).
2. Identificar as tabelas e os models de: questões, bancas, matérias/assuntos, concursos, simulados e redações/correções.
3. Identificar a **camada de serviço** existente. O servidor MCP deve **reutilizar os services** e nunca duplicar regra de negócio nem escrever SQL paralelo.
4. Verificar a versão atual do SDK oficial `mcp` (PyPI) e a API do `FastMCP` incluída nele.
5. Apresentar um resumo do que encontrou e um plano de implementação, e **aguardar aprovação**.

---

## 4. Arquitetura

```
passa-facil/
├── app/                    # FastAPI existente (não alterar comportamento)
│   └── services/           # reutilizado pelo MCP
└── mcp_server/
    ├── __init__.py
    ├── server.py           # instância FastMCP + registro de tools/resources/prompts
    ├── tools/
    │   ├── questoes.py
    │   ├── simulados.py
    │   └── correcao.py
    ├── resources.py
    ├── prompts.py
    ├── config.py           # settings via env vars
    ├── auth.py             # token para transporte HTTP (fase 2)
    └── tests/
```

- **SDK:** `mcp` oficial (`from mcp.server.fastmcp import FastMCP`).
- **Processo separado** do FastAPI, importando a camada de services.
- **Transporte:**
  - Fase 1: `stdio` (uso local com Claude Desktop / Claude Code).
  - Fase 2: `streamable-http` atrás do Nginx, com autenticação por token.
- **Banco:** usuário MySQL **somente leitura** para as tools de consulta. A submissão de redação usa o service existente, que já enfileira o trabalho.

---

## 5. Tools

Todas as tools devem ter type hints, docstring clara (o modelo lê a docstring para decidir quando usar a tool), validação de entrada e limites de resultado.

| Tool | Parâmetros | Retorno | Observações |
|---|---|---|---|
| `buscar_questoes` | `banca?`, `materia?`, `assunto?`, `concurso?`, `ano?`, `dificuldade?`, `limite=10` (máx. 50) | lista de questões (id, enunciado, alternativas, banca, ano) **sem gabarito** | gabarito nunca vem junto |
| `obter_gabarito` | `questao_id` | alternativa correta + comentário | separado de propósito, para uso em modo estudo |
| `listar_filtros` | — | bancas, matérias, concursos disponíveis | ajuda o modelo a montar filtros válidos |
| `estatisticas_banco` | `agrupar_por` (`banca`, `materia`, `ano`) | contagens | consulta agregada |
| `montar_simulado` | `concurso?`, `materias[]`, `quantidade`, `distribuicao?` | id do simulado + questões | reutiliza a lógica de simulado existente, se houver |
| `submeter_redacao` | `texto`, `banca`, `tema?` | `job_id` | **assíncrono**: enfileira via service da correção discursiva |
| `consultar_correcao` | `job_id` | status (`pendente`/`processando`/`concluida`/`erro`) + nota e feedback quando concluída | polling |

---

## 6. Resources

- `passafacil://concursos` — lista de concursos com edital/status.
- `passafacil://concursos/{id}` — detalhes do concurso (matérias cobradas, banca, datas).
- `passafacil://criterios/{banca}` — critérios de correção discursiva por banca.

---

## 7. Prompts

- `plano_de_estudos(concurso, semanas_ate_prova)` — gera um plano usando `estatisticas_banco` e `listar_filtros`.
- `revisao_de_erros(materia)` — conduz uma revisão guiada com `buscar_questoes` + `obter_gabarito`.

---

## 8. Segurança e LGPD

- **Nenhum dado pessoal de aluno** é exposto pelas tools (sem nome, e-mail, CPF ou histórico individual).
- Redações submetidas via MCP são **anônimas**, com retenção conforme a política definida em `spec-correcao-discursiva.md`.
- Usuário de banco read-only e queries parametrizadas (sem SQL montado por string).
- Limite de resultados por chamada e rate limit por token na fase 2.
- Segredos só via variáveis de ambiente (`.env` fora do git).
- Logs sem conteúdo de redação.

---

## 9. Testes

- `pytest` para cada tool, com o banco de teste ou mocks dos services.
- Teste manual com o **MCP Inspector**:
  ```bash
  npx @modelcontextprotocol/inspector python -m mcp_server.server
  ```
- Teste de ponta a ponta no **Claude Desktop** (`claude_desktop_config.json`):
  ```json
  {
    "mcpServers": {
      "passa-facil": {
        "command": "python",
        "args": ["-m", "mcp_server.server"],
        "cwd": "/caminho/para/passa-facil",
        "env": { "PF_DB_URL": "mysql+...://readonly:...@localhost/passafacil" }
      }
    }
  }
  ```
- E no Claude Code:
  ```bash
  claude mcp add passa-facil -- python -m mcp_server.server
  ```

---

## 10. Entrega de portfólio

1. **README em inglês** em `mcp_server/README.md`: o que é, arquitetura (diagrama simples), lista de tools, como rodar, decisões de design (reuso de services, async, LGPD).
2. **Demo gravada** (GIF ou vídeo de 1–2 min) do Claude Desktop montando um simulado e corrigindo uma redação via MCP.
3. Repositório público **só do servidor MCP** (ou do projeto com dados sensíveis removidos), com dados de exemplo (seed) para quem clonar conseguir rodar.

---

## 11. Fases

| Fase | Escopo | Critério de aceite |
|---|---|---|
| 1 | `listar_filtros`, `buscar_questoes`, `obter_gabarito`, `estatisticas_banco` via stdio | funciona no Inspector e no Claude Desktop; testes passando |
| 2 | `montar_simulado`, `submeter_redacao`, `consultar_correcao`, resources e prompts | fluxo assíncrono de correção completo via MCP |
| 3 | transporte HTTP + token + Nginx + rate limit | acessível remotamente com autenticação |
| 4 | README em inglês, seed, demo gravada | repositório pronto para mostrar em candidatura |
