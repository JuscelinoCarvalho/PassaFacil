# Publicação nativa — Debian 13 e Apache

Documento de produção do Passa Fácil, **atualizado para refletir o deploy real**
em `passafacil.jussa.com.br` (2026-08-06). Docker Compose continua disponível
apenas para desenvolvimento local no Windows.

## Arquitetura real

```text
Internet (Cloudflare, DNS-only -> 201.6.108.36)
   |
Apache :443  (passafacil.jussa.com.br)
   |-- /api/ /health /docs /openapi.json -> FastAPI  127.0.0.1:9000  (systemd)
   `-- /*                                -> Next.js  127.0.0.1:9001  (systemd)
                                                |
FastAPI ----------------------------------------+-> PostgreSQL 127.0.0.1:5433
                                                     (container Docker dedicado)
```

Apenas 80/443 são públicas. App, API e banco escutam em `127.0.0.1`.

Diferente da proposta original (`/srv/passafacil`, usuário `passafacil`,
Postgres nativo), o deploy seguiu a **convenção dos demais projetos do
servidor**: o código roda como o usuário `jussa`, direto de
`/home/jussa/FileShare/development/passa_facil`, com o `.venv` dentro do
projeto e serviços `systemd`. O Postgres roda em um container Docker dedicado
(o servidor já usa Docker para o Postgres do ML Pulse; um container separado
mantém os dados do Passa Fácil isolados).

## Caminhos e portas

```text
Código:      /home/jussa/FileShare/development/passa_facil
venv API:    apps/api/.venv
Segredos:    /etc/passafacil.env            (root:jussa 0640)
API:         127.0.0.1:9000  (uvicorn via systemd)
Web:         127.0.0.1:9001  (Next.js standalone via systemd, node do nvm)
Postgres:    127.0.0.1:5433  (container Docker passafacil-postgres)
ACME webroot:/var/www/html/passafacil-acme
Landing:     /var/www/html/jussa/index.html
```

## 1. Pacotes / módulos do Apache

```bash
sudo a2enmod proxy proxy_http headers rewrite ssl
```

Node.js é o do `nvm` do usuário `jussa` (hoje `v24.1.0`). Se o Node for
atualizado no nvm, ajuste o caminho absoluto no `passafacil-web.service`.

## 2. Segredos — /etc/passafacil.env

```dotenv
JWT_SECRET=<segredo aleatorio longo>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=postgresql+psycopg://passafacil_app:<SENHA>@127.0.0.1:5433/passafacil
CORS_ORIGINS=https://passafacil.jussa.com.br
OWNER_MODE=true
OWNER_EMAIL=juscelino.carvalho@gmail.com
```

```bash
sudo chown root:jussa /etc/passafacil.env && sudo chmod 640 /etc/passafacil.env
```

## 3. Banco de dados (Postgres em Docker)

Container dedicado, com volume nomeado e reinício automático:

```bash
docker volume create passafacil_pgdata
docker run -d --name passafacil-postgres --restart unless-stopped \
  -e POSTGRES_USER=passafacil_app \
  -e POSTGRES_PASSWORD='<SENHA>' \
  -e POSTGRES_DB=passafacil \
  -p 127.0.0.1:5433:5432 \
  -v passafacil_pgdata:/var/lib/postgresql/data \
  postgres:16-alpine
```

A API cria as tabelas automaticamente no startup (`Base.metadata.create_all`)
e roda o seed idempotente do TCE-SP 2026 (`if not exam: ...`), portanto reinícios
não duplicam dados.

### Migração de SQLite -> Postgres (feita uma vez)

O MVP começou em SQLite (`apps/api/passafacil.db`). A migração preservou todos
os dados usando os próprios modelos SQLAlchemy (conversão de tipos entre dialetos
via type processors — UUID, Enum, DateTime, Boolean; não há sequences porque as
PKs são UUID). Procedimento:

1. `sudo systemctl stop passafacil-api` (snapshot consistente);
2. rodar um script que abre dois engines (SQLite origem, Postgres destino), faz
   `Base.metadata.create_all(dst)` e copia cada `Base.metadata.sorted_tables`
   (ordem de FK) do origem para o destino, verificando as contagens;
3. trocar `DATABASE_URL` no `/etc/passafacil.env` para o Postgres;
4. `sudo systemctl start passafacil-api` e validar `/health` + contagens.

O SQLite antigo fica preservado como `apps/api/passafacil.db` (+ backups
`.db.bak.<timestamp>`) para rollback.

## 4. Backend

```bash
cd /home/jussa/FileShare/development/passa_facil/apps/api
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Serviço: `infra/systemd/passafacil-api.service` -> `/etc/systemd/system/`.

## 5. Frontend

```bash
cd /home/jussa/FileShare/development/passa_facil/apps/web
corepack pnpm install --frozen-lockfile
```

**Build (2 passos — importante):**

```bash
export NEXT_PUBLIC_API_URL=https://passafacil.jussa.com.br/api/v1
# 1) build direto pelo binário local (NÃO use `pnpm build`: o corepack tenta
#    invocar um `pnpm` global que não existe no PATH e falha)
./node_modules/.bin/next build
# 2) o modo standalone NÃO copia os assets estáticos — copie manualmente
rm -rf .next/standalone/.next/static
cp -r .next/static .next/standalone/.next/static
```

O servidor de produção fica em `.next/standalone/server.js` (o `public/` está
vazio, então não precisa ser copiado). Serviço:
`infra/systemd/passafacil-web.service`.

## 6. Serviços systemd

```bash
sudo cp infra/systemd/passafacil-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now passafacil-api passafacil-web
```

## 7. Apache + TLS

Dois VirtualHosts (padrão dos outros subdomínios): um `:80` com o desafio ACME
por webroot e redirect para HTTPS, e um `:443` com o proxy reverso.

```bash
sudo cp infra/apache/passafacil.jussa.com.br.conf        /etc/apache2/sites-available/
sudo cp infra/apache/passafacil.jussa.com.br-le-ssl.conf /etc/apache2/sites-available/
sudo mkdir -p /var/www/html/passafacil-acme/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/html/passafacil-acme

sudo a2ensite passafacil.jussa.com.br.conf
sudo apache2ctl configtest && sudo systemctl reload apache2

# Certificado Let's Encrypt via webroot
sudo certbot certonly --webroot -w /var/www/html/passafacil-acme \
  -d passafacil.jussa.com.br --non-interactive --agree-tos -m juscelino.carvalho@gmail.com

sudo a2ensite passafacil.jussa.com.br-le-ssl.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
```

O DNS de `passafacil.jussa.com.br` é gerenciado no Cloudflare em modo **DNS-only**
(cinza), apontando direto para o IP de origem — necessário para o desafio HTTP-01.

## 8. Validações

```bash
curl http://127.0.0.1:9000/health           # {"status":"ok"}
curl -I http://127.0.0.1:9001                # 200
curl https://passafacil.jussa.com.br/health # {"status":"ok"}
curl -I https://passafacil.jussa.com.br/     # 200
curl https://passafacil.jussa.com.br/api/v1/exams
```

## 9. Atualizações

1. obter a versão desejada do repositório;
2. `corepack pnpm install --frozen-lockfile` (se o front mudou);
3. `pip install -r requirements.txt` no `.venv` (se o back mudou);
4. rebuild do front (os 2 passos da seção 5) — se o front mudou;
5. `sudo systemctl restart passafacil-api passafacil-web`;
6. validar `/health` e a home.

Backup do Postgres:

```bash
docker exec passafacil-postgres pg_dump -U passafacil_app passafacil > backup.sql
```

Ainda pendentes antes de escalar para usuários reais: Alembic (migrações),
refresh tokens, rate limiting, backup automatizado e logs estruturados.
