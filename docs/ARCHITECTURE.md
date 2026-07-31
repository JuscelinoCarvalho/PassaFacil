# Arquitetura

## Visão

Monorepo modular com aplicação web Next.js, API FastAPI e PostgreSQL. O backend
é a fonte de verdade; a interface consome endpoints versionados em `/api/v1`.

```text
Navegador -> Next.js -> FastAPI -> PostgreSQL
                           |
                           +-> serviços futuros: filas, IA, áudio e pagamentos
```

## Domínios

- **Identidade:** usuário, credenciais, perfil e sessão.
- **Comercial:** assinatura, plano, provedor e estado de cobrança.
- **Catálogo:** concurso, disciplina, tópico e questão.
- **Aprendizagem:** tentativa, acerto, tempo e revisões futuras.

Todas as tentativas pertencem a um usuário. Disciplinas pertencem a um concurso;
tópicos pertencem a disciplinas. Isso permite vários concursos sem duplicar a
identidade do aluno.

## Segurança

- senhas usando Argon2;
- access tokens JWT curtos;
- CORS configurável;
- segredos apenas em variáveis de ambiente;
- e-mails normalizados e únicos;
- IDs UUID não sequenciais;
- assinatura separada do usuário para receber webhooks idempotentes.

Antes da produção: refresh token rotativo em cookie `httpOnly`, verificação de
e-mail, recuperação de senha, rate limit, logs de auditoria, CSP, backup testado
e gestão externa de segredos.

## Decisões

- FastAPI favorece APIs tipadas e recursos futuros de IA.
- SQLAlchemy mantém o domínio independente do PostgreSQL.
- Next.js permite produto público e área autenticada no mesmo frontend.
- Docker Compose reproduz o ambiente local e simplifica a publicação inicial.
- Redis e filas ficam fora do MVP até existir processamento assíncrono real.

## Produção

Apache termina HTTPS para `passafacil.jussa.com.br`, roteia `/api` à API e o
restante ao frontend. Next.js e FastAPI são serviços independentes gerenciados
pelo `systemd`. PostgreSQL é instalado diretamente no Debian e não é exposto
publicamente.

As portas internas reservadas para o produto são `9000` para a API e `9001`
para o frontend.

Docker Compose permanece exclusivamente como opção de desenvolvimento local no
Windows. A configuração de produção está em `docs/DEPLOY_DEBIAN.md`.
