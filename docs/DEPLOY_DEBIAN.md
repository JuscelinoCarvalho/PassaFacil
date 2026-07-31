# Publicação nativa — Debian 13 e Apache

Esta é a estratégia de produção do Passa Fácil. Docker Compose continua
disponível somente para desenvolvimento local no Windows.

## Arquitetura

```text
Internet
   |
Apache :443
   |-- /api/*  -> FastAPI 127.0.0.1:9000
   `-- /*      -> Next.js 127.0.0.1:9001
                         |
FastAPI -----------------+-> PostgreSQL 127.0.0.1:5432
```

Somente as portas 80 e 443 devem ficar públicas. Aplicação, API e banco escutam
na interface local.

## 1. Pacotes do servidor

Instale Apache, PostgreSQL, Python, ambiente virtual e as ferramentas necessárias
para compilar a aplicação. Node.js deve ser instalado em uma versão LTS
compatível com o `package.json`.

Módulos necessários do Apache:

```bash
sudo a2enmod proxy proxy_http headers rewrite ssl
```

## 2. Usuário e diretórios

Recomendação:

```text
/srv/passafacil/app       código da aplicação
/srv/passafacil/venv      ambiente Python
/etc/passafacil/api.env   segredos da API
/etc/passafacil/web.env   configuração do frontend
```

Use um usuário de serviço sem login interativo, por exemplo `passafacil`. Não
execute a aplicação como `root` nem mantenha segredos no repositório.

## 3. PostgreSQL

Crie um banco e um usuário exclusivos. A senha deve ser longa e diferente das
credenciais de administração.

```sql
CREATE USER passafacil_app WITH PASSWORD 'substitua-por-uma-senha-forte';
CREATE DATABASE passafacil OWNER passafacil_app;
```

Em `/etc/passafacil/api.env`, configure:

```dotenv
DATABASE_URL=postgresql+psycopg://passafacil_app:SENHA@127.0.0.1:5432/passafacil
JWT_SECRET=SEGREDO_ALEATORIO_LONGO
CORS_ORIGINS=https://passafacil.jussa.com.br
```

O arquivo deve pertencer ao usuário do serviço e ter permissão de leitura
restrita.

## 4. Backend

Na primeira instalação:

```bash
python3 -m venv /srv/passafacil/venv
/srv/passafacil/venv/bin/pip install -r /srv/passafacil/app/apps/api/requirements.txt
```

Instale `infra/systemd/passafacil-api.service` em `/etc/systemd/system/`,
ajustando usuário e caminhos se necessário.

## 5. Frontend

Compile o frontend com a URL pública da API:

```bash
cd /srv/passafacil/app/apps/web
corepack enable
pnpm install --frozen-lockfile
NEXT_PUBLIC_API_URL=https://passafacil.jussa.com.br/api/v1 pnpm build
```

O modo `standalone` gera o servidor de produção. Instale
`infra/systemd/passafacil-web.service` e ajuste os caminhos conforme o conteúdo
gerado pela versão usada do Next.js.

## 6. Apache

Copie `infra/apache/passafacil.conf` para
`/etc/apache2/sites-available/passafacil.conf`, substitua os caminhos dos
certificados e habilite o site:

```bash
sudo a2ensite passafacil
sudo apache2ctl configtest
sudo systemctl reload apache2
```

O certificado poderá ser obtido pelo método já utilizado no servidor, inclusive
Certbot, desde que os arquivos apontados no VirtualHost existam.

## 7. Serviços

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now passafacil-api passafacil-web
sudo systemctl status passafacil-api passafacil-web
```

Validações locais:

```bash
curl http://127.0.0.1:9000/health
curl -I http://127.0.0.1:9001
curl https://passafacil.jussa.com.br/health
```

## 8. Atualizações

Uma atualização segura deve:

1. obter a versão desejada do repositório;
2. instalar dependências travadas;
3. executar testes;
4. aplicar migrações do banco;
5. compilar o frontend;
6. reiniciar os dois serviços;
7. validar `/health`;
8. permitir retorno à versão anterior.

Antes de publicar para usuários reais, ainda serão adicionados Alembic,
refresh tokens, limites de requisição, backup automatizado e logs estruturados.
