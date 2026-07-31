# Fontes e importação de questões

## Objetivo

Construir um banco amplo, rastreável e sustentável. Volume sem qualidade não é
meta: toda questão deve ter assunto, resposta, proveniência e estado de direitos.

## Fontes prioritárias

1. Provas e gabaritos publicados nos portais oficiais das bancas.
2. Provas divulgadas pelos próprios órgãos públicos.
3. Questões autorais revisadas editorialmente.
4. Conteúdo licenciado por parceiros.

Materiais de cursinhos, plataformas pagas e bancos de terceiros não devem ser
copiados sem autorização.

## Estados de direitos

- `authorial`: criado e revisado para o Passa Fácil;
- `licensed`: licença contratual permite uso;
- `public_domain`: domínio público confirmado;
- `owner_only`: uso local pelo proprietário, não publicável;
- `research_only`: catalogado para pesquisa, sem publicação.

Somente itens `authorial`, `licensed` ou `public_domain` entram automaticamente
no catálogo publicado.

## Deduplicação

O importador calcula SHA-256 do enunciado e alternativas normalizados. Também
aceita uma chave externa da fonte. Uma coincidência em qualquer identificador
impede a duplicação.

## Formato

O endpoint `POST /api/v1/question-bank/import` recebe lotes JSON de até 5.000
itens. Cada lote informa fonte, URL, órgão, banca, ano, direitos e identificador.

Antes de automatizar PDFs, o pipeline deve separar:

1. descoberta da prova;
2. download do documento oficial;
3. extração;
4. associação com o gabarito definitivo;
5. classificação por tópico;
6. revisão humana;
7. publicação conforme direitos.

## Implementação atual

A área proprietária "Banco de questões" aceita PDFs de até 50 MB, preserva o
arquivo de origem, extrai texto página a página e identifica questões e
alternativas candidatas. O resultado fica no estado `review`: nenhuma questão é
publicada durante a inspeção.

O próximo estágio associará a prova ao gabarito definitivo e permitirá revisar,
classificar e aprovar cada item individualmente.

## Primeira coleção recomendada

- [TCM-SP — Auditor de Controle Externo, Tecnologia da Informação, VUNESP](https://www.vunesp.com.br/TCMU1901);
- [Prefeitura de São Paulo — Auditor Fiscal Tributário Municipal, TI, VUNESP](https://www.vunesp.com.br/SMGE2304);
- [SP Regula — Analista de Regulação, TI, VUNESP](https://www.vunesp.com.br/SPRE2301);
- concursos de Analista de TI e Auditoria de TI organizados pela VUNESP;
- provas de TCEs e tribunais de contas de outras bancas para assuntos raros.

Os portais oficiais disponibilizam áreas de provas e gabaritos, mas a própria
VUNESP informa reserva de direitos. Antes de usar esse material em um produto
comercial, o status jurídico/licenciamento deve ser confirmado. Até lá, a fonte
pode ser catalogada como `owner_only` ou `research_only`.
