"""Estudos de caso REAIS da prova VUNESP TCE-SP 2026 (TI), aplicada em 11.10.2026.

Fonte: EstudoCaso2026.pdf (caderno oficial — 2 temas). Os ENUNCIADOS e TEXTOS DE
APOIO são transcritos fielmente do caderno. O ESPELHO (model_answer) e a GRADE de
critérios são PROVISÓRIOS, redigidos aqui com base no conteúdo técnico esperado —
serão SUBSTITUÍDOS pelo padrão de resposta OFICIAL da VUNESP quando disponível
(é o padrão oficial que faz a correção por IA ficar precisa; ver services/grading.py).

Idempotente por slug: re-rodar atualiza texto/critérios, não duplica. Toda citação
de artigo nomeia a lei ([[citar-artigo-com-a-lei]]).

Uso (produção): DATABASE_URL=... PYTHONPATH=. .venv/bin/python -m scripts.seed_prova2026_casos
"""

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import DiscursiveCase, DiscursiveCriterion

PROVISORIO = (
    "\n\n[ESPELHO PROVISÓRIO: será substituído pelo padrão de resposta OFICIAL da "
    "VUNESP. Use como referência de conteúdo esperado.]"
)

CASES: list[dict] = [
    # =====================================================================
    # CASO 1 (2026) — Modelagem relacional de títulos/movimentações + nuvem + TR
    # =====================================================================
    {
        "slug": "prova2026-caso1-modelagem-dados-tic",
        "disciplina": "TI — Banco de Dados e Contratações (Prova 2026)",
        "tema": "Modelagem relacional, integridade de dados, nuvem e Termo de Referência",
        "display_order": 8,
        "texto_apoio": (
            "Sistema web (PHP) de controle de pagamentos e recebimentos. Cada conta a pagar ou a "
            "receber (ambas chamadas de \"títulos\") pode ser quitada em uma única movimentação "
            "bancária ou em várias (pagamentos parciais). Não há documentação da modelagem. "
            "Registros encontrados no ambiente de produção (nomes/CPFs/CNPJs fictícios):\n\n"
            "pessoa(id_pessoa, tipo_pessoa, nome_pessoa, cpf_cnpj):\n"
            "  1 F Fulano de Tal da Silva; 2 J Soluções Tecnológicas Empresariais Ltda.; "
            "3 J Distribuidor de Mercadorias Ltda.; 4 J Fornecedor de Sistemas Ltda.; "
            "5 J Escritório de Contabilidade Ltda.; 6 F Funcionário Exemplar de Souza.\n\n"
            "conta_bancaria(id_conta, nome_banco, agencia, numero_conta):\n"
            "  1 Super Banco Regional S/A 1234 3333-3; 2 Cooperativa Bancária do Município S/A 5678 4444-4.\n\n"
            "titulo(id_titulo, id_pessoa, tipo_titulo, descricao, data_vencimento, valor_titulo):\n"
            "  1 | 2 | R | Prestação de serviços de consultoria | 10/01/2026 | 20.000,00\n"
            "  2 | 3 | P | Compra de equipamentos | 12/01/2026 | 10.000,00\n"
            "  3 | 4 | P | Assinatura de software Jan/2026 | 15/01/2026 | 500,00\n"
            "  4 | 1 | R | Venda de ativos usados (móveis) | 18/01/2026 | 800,00\n"
            "  5 | 5 | P | Serviço de contabilidade Jan/2026 | 20/01/2026 | 3.600,00\n"
            "  7 | 6 | R | Pagamento de salário a funcionário | 05/02/2026 | 3.500,00\n\n"
            "meio_pagamento(id_meio_pagamento, nome_meio_pagamento): 1 Pix; 2 Boleto Bancário.\n\n"
            "movimentacao_bancaria(id_movimentacao, id_conta, id_titulo, id_meio_pagamento, "
            "data_movimentacao, valor_movimentacao):\n"
            "  1 | 1 | 1 | 2 | 10/01/2026 | 20.000,00\n"
            "  2 | 1 | 2 | 2 | 12/01/2026 | 5.000,00\n"
            "  3 | 2 | 3 | 2 | 15/01/2026 | 500,00\n"
            "  4 | 1 | 2 | 2 | 15/01/2026 | 3.000,00\n"
            "  5 | 2 | 2 | 2 | 20/01/2026 | 2.000,00\n"
            "  6 | 2 | 4 | 1 | 18/01/2026 | 200,00\n"
            "  7 | 2 | 5 | 2 | 20/01/2026 | 3.600,00\n"
            "  8 | 1 | 6 | 1 | 20/01/2026 | 200,00\n"
            "  9 | 1 | 4 | 1 | 19/01/2026 | 200,00\n"
            "  10 | 1 | 5 | 1 | 22/01/2026 | 3.600,00\n"
            "  11 | 1 | 4 | 1 | 25/01/2026 | 200,00\n\n"
            "Observação do enunciado: títulos ainda não quitados ou quitados parcialmente NÃO são "
            "incoerências, e sim situação normal, ainda que em atraso."
        ),
        "enunciado": (
            "O Auditor de Controle Externo – TI foi apresentado ao sistema acima. Responda:\n"
            "a) Identifique cada uma das entidades da modelagem e explique o significado de cada uma "
            "no contexto da aplicação.\n"
            "b) Indique 3 (três) situações de problemas de integridade, incoerências ou suspeitas nos "
            "dados — tanto do ponto de vista de banco de dados quanto financeiro/administrativo — e "
            "explique cada uma. (Lembre-se: título não quitado ou quitado parcialmente é normal.)\n"
            "c) O modelo não permite uma única movimentação bancária que quite vários títulos do mesmo "
            "cliente/fornecedor (recurso desejado). Apresente uma modelagem alternativa (diagrama ou "
            "texto) que ofereça essa possibilidade e explique a solução.\n"
            "d) O sistema está on-premises (arquivos PHP + banco de dados) e deseja-se migrá-lo para a "
            "nuvem. Cite e explique pelo menos 2 (dois) serviços típicos de provedores de nuvem que "
            "podem compor o ambiente de execução desse sistema.\n"
            "e) Supondo que a organização seja da Administração Pública sujeita à Lei nº 14.133/2021 e "
            "deva elaborar um Termo de Referência para contratar serviços de atualizações por escopo, "
            "explique o que é Termo de Referência e cite 2 (dois) parâmetros/elementos que o compõem."
        ),
        "model_answer": (
            "a) ENTIDADES. 'pessoa' representa os agentes (físicos F ou jurídicos J) credores ou "
            "devedores — clientes, fornecedores e funcionários. 'conta_bancaria' são as contas da "
            "organização usadas nas movimentações. 'titulo' é a conta a pagar (P) ou a receber (R), "
            "com vencimento e valor. 'meio_pagamento' é a forma de quitação (Pix, boleto). "
            "'movimentacao_bancaria' é cada liquidação (total ou parcial) de um título por uma conta e "
            "um meio de pagamento — relação 1:N entre título e movimentações.\n\n"
            "b) PROBLEMAS (3). (1) Integridade referencial: a movimentação id 8 aponta id_titulo = 6, "
            "mas não existe título com id 6 (há 1,2,3,4,5,7) — é uma chave estrangeira órfã, que uma "
            "FK bem definida impediria. (2) Incoerência financeira: o título 5 (R$ 3.600,00) é quitado "
            "pelas movimentações id 7 (3.600,00) e id 10 (3.600,00), somando R$ 7.200,00 — pagamento "
            "ACIMA do valor do título, sem constraint que impeça o excesso. (3) Incoerência semântica/"
            "administrativa: o título 7, 'Pagamento de salário a funcionário', está classificado como "
            "tipo R (a receber), quando salário é despesa a PAGAR (tipo P) — além de ausência de "
            "domínio controlado para tipo_titulo e de datas gravadas como texto livre (ex.: 'Jan/2026').\n\n"
            "c) MODELAGEM ALTERNATIVA. Substituir a ligação direta título↔movimentação por uma entidade "
            "ASSOCIATIVA 'movimentacao_titulo' (N:N) com os campos (id_movimentacao, id_titulo, "
            "valor_aplicado). Assim, uma única movimentação pode ratear seu valor entre vários títulos "
            "do mesmo cliente/fornecedor (um registro por título quitado), e um título continua podendo "
            "receber várias movimentações. A soma de valor_aplicado por título passa a controlar a "
            "quitação, e o valor_movimentacao deve igualar a soma dos rateios.\n\n"
            "d) SERVIÇOS DE NUVEM (2). (1) Máquina virtual em IaaS (ex.: compute/VM) para hospedar a "
            "aplicação PHP, com o sistema operacional e o servidor web sob gestão do contratante. "
            "(2) Banco de dados gerenciado (DBaaS/PaaS, ex.: instância relacional gerenciada) para o "
            "banco, com backup, alta disponibilidade e pat/atualização pelo provedor. Alternativas "
            "válidas: hospedagem PaaS da aplicação, armazenamento de objetos para anexos e balanceador "
            "de carga.\n\n"
            "e) TERMO DE REFERÊNCIA. É o documento da fase preparatória que define o objeto e as "
            "condições da contratação, necessário para licitação/contratação de bens e serviços (Lei nº "
            "14.133/2021, art. 6º, XXIII, e art. 40). Dois elementos que o compõem, entre outros: a "
            "definição do objeto (com requisitos da contratação); e o modelo de execução do objeto com "
            "os critérios de medição e de pagamento (também: estimativa do valor, modelo de gestão do "
            "contrato e requisitos de sustentabilidade)."
        ),
        "micro_aula": (
            "Estruture por item (a–e), um bloco para cada comando, começando pela resposta direta. "
            "No item b, mostre que você leu os DADOS: aponte a FK órfã (movimentação → título 6 "
            "inexistente), o pagamento acima do valor (título 5 somando 7.200 > 3.600) e o salário "
            "classificado como 'a receber'. No item c, a palavra-chave é ENTIDADE ASSOCIATIVA (N:N) com "
            "valor_aplicado. No item e, cite a Lei nº 14.133/2021 (art. 6º, XXIII) e dois elementos do "
            "TR. Vocabulário que pontua: integridade referencial, constraint, cardinalidade, IaaS/DBaaS, "
            "Termo de Referência." + PROVISORIO
        ),
        "criteria": [
            ("N1", "Identificação das entidades (comando a).",
             "Identifica e explica as 5 entidades (pessoa, conta_bancaria, titulo, meio_pagamento, "
             "movimentacao_bancaria) e a relação título 1:N movimentações no contexto de contas a pagar/receber.", 5),
            ("N2", "Problemas de integridade/incoerências (comando b).",
             "Aponta 3 problemas reais e explicados, idealmente: FK órfã (movimentação id 8 → título 6 inexistente); "
             "pagamento acima do valor (título 5 = 7.200 > 3.600); salário classificado como 'a receber' (ou outra "
             "incoerência válida de domínio/data). Não conta como erro título em aberto/parcial.", 5),
            ("N3", "Modelagem alternativa N:N (comando c).",
             "Propõe entidade associativa entre movimentacao_bancaria e titulo (ex.: movimentacao_titulo com "
             "valor_aplicado) permitindo uma movimentação quitar vários títulos; explica a solução e o controle de valores.", 4),
            ("N4", "Serviços de nuvem (comando d).",
             "Cita e explica ao menos 2 serviços típicos (ex.: IaaS/VM para a aplicação PHP e banco de dados gerenciado "
             "DBaaS/PaaS; ou PaaS, armazenamento de objetos, balanceador), adequados a hospedar app + BD.", 3),
            ("N5", "Termo de Referência (comando e).",
             "Explica o que é o Termo de Referência (documento da fase preparatória, Lei nº 14.133/2021, art. 6º, XXIII) "
             "e cita 2 elementos (ex.: definição do objeto/requisitos; modelo de execução com critérios de medição e pagamento).", 3),
        ],
    },
    # =====================================================================
    # CASO 2 (2026) — Auditoria de contrato de administração de servidores Linux
    # =====================================================================
    {
        "slug": "prova2026-caso2-admin-linux-contrato",
        "disciplina": "TI — Segurança/Linux e Fiscalização de Contratos (Prova 2026)",
        "tema": "Auditoria de servidores Ubuntu: privilégios, contas e uso de disco (Lei 14.133)",
        "display_order": 9,
        "texto_apoio": (
            "Órgão público estadual contratou empresa de suporte e administração de servidores. Os "
            "sistemas institucionais são hospedados em servidores com sistema operacional Ubuntu. Um "
            "auditor foi designado para acompanhar e avaliar a execução do contrato, verificando a "
            "observância das condições previstas e a conformidade com a Lei Federal nº 14.133/2021."
        ),
        "enunciado": (
            "Na condição de auditor, responda:\n"
            "a) Constatou-se que TODOS os usuários cadastrados nos servidores possuíam privilégios "
            "administrativos plenos. Apresente uma análise dos riscos decorrentes dessa situação.\n"
            "b) Verificou-se grande número de contas, com contas de ex-funcionários ainda ativas. "
            "Apresente um comando de terminal para verificar a data do último acesso de cada usuário e "
            "explique o procedimento para remover essas contas.\n"
            "c) Os Requisitos da Contratação não previam como a empresa deveria gerenciar os sistemas de "
            "arquivos (monitoramento do consumo de disco e medidas para consumo anormal). Apresente um "
            "comando de terminal para verificar o uso de espaço em disco do servidor e explique o "
            "procedimento para sanar essa deficiência nos requisitos da contratação."
        ),
        "model_answer": (
            "a) RISCOS DO PRIVILÉGIO PLENO GENERALIZADO. A concessão de privilégios administrativos "
            "(root/sudo) a todos os usuários viola o princípio do MENOR PRIVILÉGIO e da segregação de "
            "funções. Riscos: (i) qualquer conta comprometida dá controle total do servidor, ampliando a "
            "superfície de ataque e o movimento lateral; (ii) perda de rastreabilidade/responsabilização "
            "(accountability), pois ações críticas não ficam vinculadas a um responsável; (iii) maior "
            "chance de erro operacional e de alterações indevidas de configuração; (iv) impacto elevado de "
            "malware/ransomware, que herda privilégios máximos. Recomenda-se conceder privilégios mínimos "
            "necessários, uso de sudo nominal e auditado, e revisão periódica de acessos.\n\n"
            "b) ÚLTIMO ACESSO E REMOÇÃO DE CONTAS. Para verificar o último login de cada usuário: "
            "`lastlog` (lista todos os usuários e a data do último acesso; alternativamente `last` lê o "
            "/var/log/wtmp). Procedimento de remoção: primeiro DESABILITAR a conta para investigação e "
            "evitar novo acesso (`usermod -L usuario` e/ou `usermod -s /usr/sbin/nologin usuario`, ou "
            "expirar com `chage -E 0 usuario`); preservar/backup dos dados necessários; e então remover "
            "com `userdel -r usuario` (o -r remove também o diretório home e a spool de e-mail). O "
            "procedimento deve seguir rotina formal de gestão de identidades (desprovisionamento no "
            "desligamento) e trilha de auditoria.\n\n"
            "c) USO DE DISCO E CORREÇÃO DOS REQUISITOS. Para verificar o uso de espaço em disco: `df -h` "
            "(uso por sistema de arquivos, em formato legível; para localizar diretórios que mais "
            "consomem, `du -h --max-depth=1 /caminho` ou `du -sh *`). Para sanar a deficiência, deve-se "
            "ALTERAR/COMPLEMENTAR os Requisitos da Contratação no Termo de Referência (Lei nº 14.133/2021, "
            "art. 6º, XXIII, e art. 40), incluindo um procedimento objetivo de gestão dos sistemas de "
            "arquivos: monitoramento contínuo do consumo (com ferramenta/limiar de alerta), definição de "
            "níveis de serviço (SLA), e medidas para consumo anormal (análise de causa, rotação/expurgo de "
            "logs, quotas de disco, ampliação de capacidade e escalonamento). Como fiscal, cabe registrar a "
            "falha, exigir o plano de ação e acompanhar a execução contratual."
        ),
        "micro_aula": (
            "Item a: ancore em MENOR PRIVILÉGIO, segregação de funções e accountability — liste riscos "
            "concretos (conta comprometida = controle total; perda de rastreabilidade; impacto de "
            "ransomware). Itens b e c pedem COMANDO + PROCEDIMENTO: b) `lastlog`/`last` + desabilitar "
            "(usermod -L / chage -E 0) antes de `userdel -r`; c) `df -h` (e `du` para achar o vilão) + "
            "corrigir o Termo de Referência (Lei nº 14.133/2021) com rotina de monitoramento, limiares, "
            "quotas e plano de ação. Mostre a dupla competência: técnica (Linux) e de fiscalização de "
            "contrato." + PROVISORIO
        ),
        "criteria": [
            ("N1", "Análise de riscos do privilégio pleno (comando a).",
             "Relaciona a violação do menor privilégio/segregação de funções e aponta riscos concretos: conta "
             "comprometida = controle total, perda de rastreabilidade/accountability, erro operacional, impacto de malware.", 7),
            ("N2", "Último acesso + remoção de contas (comando b).",
             "Apresenta comando correto para último acesso (`lastlog` ou `last`) e procedimento de remoção: desabilitar antes "
             "(usermod -L / nologin / chage -E 0), backup, depois `userdel -r`; menciona desprovisionamento formal/auditoria.", 7),
            ("N3", "Uso de disco + correção dos requisitos (comando c).",
             "Apresenta comando de uso de disco (`df -h`, e `du` para diretórios) e explica a correção dos Requisitos da "
             "Contratação/Termo de Referência (Lei nº 14.133/2021) com monitoramento, limiares/alertas, quotas e plano de ação.", 6),
        ],
    },
]


def main() -> None:
    db = SessionLocal()
    created = updated = 0
    try:
        for spec in CASES:
            case = db.scalar(select(DiscursiveCase).where(DiscursiveCase.slug == spec["slug"]))
            if case is None:
                case = DiscursiveCase(slug=spec["slug"])
                db.add(case)
                created += 1
            else:
                updated += 1
            case.tipo = "estudo_caso"
            case.disciplina = spec["disciplina"]
            case.tema = spec["tema"]
            case.enunciado = spec["enunciado"]
            case.texto_apoio = spec["texto_apoio"]
            case.model_answer = spec["model_answer"]
            case.micro_aula = spec["micro_aula"]
            case.pontuacao_maxima = 20
            case.limite_linhas = 60
            case.banca_referencia = "VUNESP"
            case.is_demo = False
            case.is_published = True
            case.display_order = spec["display_order"]
            db.flush()

            for c in list(case.criteria):
                db.delete(c)
            db.flush()
            for ordem, (codigo, descricao, esperado, pts) in enumerate(spec["criteria"], start=1):
                db.add(DiscursiveCriterion(
                    case_id=case.id, codigo=codigo, descricao=descricao,
                    conteudo_esperado=esperado, pontuacao_maxima=pts, ordem=ordem,
                ))
            db.commit()
        total = db.scalar(select(func.count(DiscursiveCase.id)))
        print(f"OK — casos 2026: {created} criados, {updated} atualizados. Total de estudos de caso: {total}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
