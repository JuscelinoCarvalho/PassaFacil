# Passa Fácil

Plataforma SaaS de preparação adaptativa para concursos. O MVP começa pelo
TCE-SP 2026, mas o modelo é multiusuário e multiconcurso.

## O que já existe

- dashboard responsivo com progresso, plano do dia e pontos de atenção;
- API FastAPI documentada em `/docs`;
- autenticação JWT (cadastro, login e perfil);
- modelos de usuários, assinaturas, concursos, disciplinas, tópicos, questões
  e tentativas;
- PostgreSQL no Docker Compose;
- dados iniciais do TCE-SP 2026;
- testes básicos de saúde, cadastro e autenticação.

## Execução local no Windows

O Docker é opcional e serve apenas para levantar o ambiente local completo sem
instalar PostgreSQL, Python e Node.js separadamente.

1. Copie `.env.example` para `.env`.
2. Execute:

   ```bash
   docker compose up --build
   ```

3. Acesse:

   - aplicação: http://localhost:9001
   - documentação da API: http://localhost:9000/docs

O banco é criado automaticamente e a API inclui o concurso TCE-SP 2026 na
primeira inicialização.

## Execução para desenvolvimento

Frontend:

```bash
cd apps/web
npm install
npm run dev -- --port 9001
```

Backend:

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 9000
```

Testes:

```bash
cd apps/api
pytest
```

## Produção no Debian 13

O ambiente de produção não depende de Docker. A arquitetura prevista usa:

- Apache com HTTPS e proxy reverso;
- frontend Next.js executado pelo `systemd`;
- API FastAPI executada pelo `systemd`;
- PostgreSQL instalado diretamente no Debian.

O procedimento completo e os modelos de configuração estão em
[`docs/DEPLOY_DEBIAN.md`](docs/DEPLOY_DEBIAN.md).

## Estrutura

```text
apps/web       Next.js, TypeScript e Tailwind
apps/api       FastAPI, SQLAlchemy e autenticação JWT
docs           produto, arquitetura e roadmap
infra          Docker local e configuração nativa para Debian/Apache
```

Consulte [MASTER_PLAN.md](docs/MASTER_PLAN.md) para escopo e prioridades.
