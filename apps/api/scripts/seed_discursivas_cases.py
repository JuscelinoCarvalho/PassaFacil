"""Estudos de caso REAIS da discursiva TCE-SP (idempotente).

Fonte: transcricao_2discursivas.txt (2 casos VUNESP resolvidos por professor) +
fasttrack-tcesp-ti.pdf, Parte IV (5 arquétipos de caso de TI).

Estrutura de resposta = método CIDA (Contextualizar / Identificar / Dispositivo /
Ação), sempre com lei + artigo e na voz de um Auditor de Controle Externo.

Cada caso vira um DiscursiveCase publicado + a grade de critérios (DiscursiveCriterion),
que alimenta a correção por IA item-a-item (services/grading.py). Toda citação de
artigo nomeia a lei ([[citar-artigo-com-a-lei]]).

Uso (produção): DATABASE_URL=... PYTHONPATH=. .venv/bin/python -m scripts.seed_discursivas_cases

Idempotente por slug: re-rodar atualiza texto/critérios, não duplica.
"""

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import DiscursiveCase, DiscursiveCriterion

# Cada caso: dict do DiscursiveCase + lista de critérios (codigo, descricao, conteudo_esperado, pontos).
CASES: list[dict] = [
    # =====================================================================
    # MÉTODO 1 — Dispensa/inexigibilidade (VUNESP, resolvido em aula) — Lei 14.133 + STF
    # =====================================================================
    {
        "slug": "metodo-dispensa-inexigibilidade-14133",
        "disciplina": "Método — Licitações (VUNESP)",
        "tema": "Dispensa e inexigibilidade de licitação + cautelar do TCE",
        "display_order": 1,
        "texto_apoio": (
            "Em decorrência de chuvas torrenciais no início de 2024, o prefeito do município de Beta "
            "decretou estado de calamidade pública e contratou emergencialmente, por dispensa de licitação, "
            "a Construtora Alfa para obras de contenção de encostas pelo prazo de 12 meses. Em janeiro de 2025, "
            "com o encerramento do contrato, o prefeito formalizou nova dispensa para recontratar a MESMA "
            "Construtora Alfa por mais 6 meses, sob alegação de que os efeitos da mesma calamidade persistiam. "
            "Em paralelo, para a defesa do município em ação judicial de alta complexidade, o gestor contratou "
            "diretamente, por inexigibilidade, o escritório do Dr. Melo (notória especialização), desprezando "
            "parecer do órgão jurídico que atestava a plena capacidade da Procuradoria Municipal para a causa. "
            "Diante disso, o Tribunal de Contas do Estado de São Paulo expediu medida cautelar suspendendo os "
            "pagamentos da recontratação e assinou prazo para manifestação do gestor."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, "
            "com fundamento legal, aos seguintes tópicos:\n"
            "a) avalie a legalidade da recontratação da Construtora Alfa por dispensa de licitação, à luz das "
            "vedações da Lei de Licitações e do entendimento do STF;\n"
            "b) analise a viabilidade jurídica da contratação direta do escritório por inexigibilidade, "
            "considerando os requisitos cumulativos fixados pelo STF;\n"
            "c) explicite os prazos e procedimentos da medida cautelar do Tribunal de Contas e situe a função "
            "do controle externo no modelo de governança em linhas de defesa."
        ),
        "model_answer": (
            "A recontratação da Construtora Alfa é ILEGAL. Nos termos da Lei nº 14.133/2021, a contratação "
            "direta por emergência ou calamidade restringe-se a obras e serviços pelo prazo máximo de 1 ano, "
            "sendo vedadas a prorrogação e a recontratação da mesma empresa sob o mesmo fundamento (art. 75, VIII). "
            "O STF, na ADI 6.890/2024, fixou que a vedação incide sobre recontratação fundada na mesma situação "
            "que ultrapassa 12 meses; como o contrato inicial já durou um ano e a nova avença decorre do mesmo "
            "evento de 2024, a conduta viola o ordenamento.\n"
            "A contratação do escritório por inexigibilidade também é irregular. A Lei nº 14.133/2021 admite a "
            "contratação de serviços técnicos especializados de natureza intelectual por inexigibilidade quando "
            "houver notória especialização e inviabilidade de competição (art. 74). Todavia, o STF (Tema 309) "
            "exige, cumulativamente, notória especialização, preço compatível e a inadequação/impossibilidade de "
            "prestação pelos quadros efetivos. Como a Procuradoria Municipal tinha plena capacidade, faltou o "
            "requisito da inadequação do corpo próprio, o que invalida a contratação direta.\n"
            "Por fim, a atuação do TCE-SP encontra amparo na fiscalização das contratações. Ao suspender "
            "cautelarmente o ato, a Corte de Contas deve assinar prazo para o órgão prestar informações e "
            "deliberar sobre o mérito nos prazos regimentais. No modelo de governança em linhas de defesa, o "
            "controle externo integra a TERCEIRA linha, atuando após os controles primários dos gestores (1ª "
            "linha) e da assessoria jurídica/controle interno (2ª linha), podendo determinar o saneamento dos "
            "vícios ou a anulação dos contratos irregulares."
        ),
        "micro_aula": (
            "ESTRUTURA (CIDA, um parágrafo por comando): comece cada parágrafo pela CONCLUSÃO (ilegal/irregular) "
            "— dá previsibilidade ao corretor — e depois fundamente. Cite sempre LEI + ARTIGO (Lei nº 14.133/2021, "
            "art. 75, VIII; art. 74) e a jurisprudência pedida (ADI 6.890; Tema 309). Use conectivos de coesão "
            "('em primeiro lugar', 'ademais', 'por conseguinte') e sinônimos para não repetir 'Tribunal de Contas' "
            "('Corte de Contas'). A tese central da inexigibilidade é o requisito CUMULATIVO da inadequação do corpo "
            "próprio de procuradores — sem ele, não há contratação direta."
        ),
        "criteria": [
            ("N1", "Legalidade da recontratação por dispensa (comando a).",
             "Conclui pela ILEGALIDADE; cita a Lei nº 14.133/2021 (contratação emergencial/calamidade limitada a 1 ano, "
             "vedada recontratação da mesma empresa sob o mesmo fundamento — art. 75, VIII) e o entendimento do STF (ADI 6.890).", 7),
            ("N2", "Viabilidade da inexigibilidade da advocacia (comando b).",
             "Conclui pela IRREGULARIDADE; aponta os requisitos da inexigibilidade (notória especialização + inviabilidade de "
             "competição, Lei nº 14.133/2021, art. 74) e os requisitos CUMULATIVOS do STF (Tema 309), destacando a capacidade "
             "da Procuradoria (falta a inadequação do corpo próprio).", 7),
            ("N3", "Cautelar do TCE + linhas de defesa (comando c).",
             "Explicita que a Corte de Contas assina prazo para informações e delibera nos prazos regimentais; situa o controle "
             "externo como TERCEIRA linha de defesa (após gestores e controle interno) e menciona saneamento/anulação.", 6),
        ],
    },
    # =====================================================================
    # MÉTODO 2 — LRF / ano eleitoral (VUNESP, resolvido em aula) — LC 101/2000 + CF
    # =====================================================================
    {
        "slug": "metodo-lrf-ano-eleitoral",
        "disciplina": "Método — Direito Financeiro (VUNESP)",
        "tema": "LRF: fim de mandato, estatal dependente e limitação de empenho",
        "display_order": 2,
        "texto_apoio": (
            "No município de Serra Dourada (SP), a 120 dias do fim do mandato, o prefeito editou ato que "
            "reestruturou a carreira dos fiscais de tributos, com reajuste e parcelas escalonadas (imediata, "
            "maio/2026 e novembro/2026), e nomeou 20 aprovados em concurso homologado para auditor fiscal. "
            "O município mantém repasses mensais à ORBS — empresa de desenvolvimento urbano, sociedade de "
            "economia mista sob controle municipal — exclusivamente para despesas de capital (obras), sem "
            "aporte para despesa de pessoal e sem decorrer de aumento de participação acionária. Ao fim do "
            "3º bimestre de 2025, a arrecadação ficou abaixo da meta; transcorridos 30 dias sem que a Câmara "
            "promovesse a limitação de suas dotações, o prefeito editou decreto limitando unilateralmente os "
            "empenhos e a movimentação financeira do Poder Legislativo."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) avalie a validade dos atos de reestruturação de carreira e de nomeação praticados pelo prefeito, "
            "considerando o período de edição e o cronograma dos efeitos financeiros;\n"
            "b) analise se a ORBS se enquadra como empresa estatal dependente perante a LRF e se seus empregados "
            "se sujeitam ao teto remuneratório constitucional;\n"
            "c) discorra sobre a constitucionalidade do decreto do Executivo que limitou o empenho e a "
            "movimentação financeira do Legislativo municipal."
        ),
        "model_answer": (
            "Os atos são NULOS. A Lei Complementar nº 101/2000 (LRF) veda, nos 180 dias anteriores ao fim do "
            "mandato, ato que resulte aumento de despesa com pessoal (art. 21), o que alcança a reestruturação de "
            "carreira e a nomeação de aprovados que ampliem o gasto. A previsão de parcelas para 2026, posteriores "
            "ao mandato, também padece de nulidade por violar o art. 21 da LRF. Assim, tanto a reestruturação quanto "
            "as nomeações feitas a 120 dias do término são inválidas.\n"
            "A ORBS caracteriza-se como estatal DEPENDENTE, mas seus empregados NÃO se sujeitam ao teto. A LRF "
            "(art. 2º, III) define estatal dependente como a controlada que recebe do ente recursos para pagamento "
            "de despesas de pessoal ou de custeio em geral (excluídos, no caso de capital, os valores de aumento de "
            "participação acionária). Como a ORBS recebe repasses e integra os orçamentos, é dependente. Contudo, a "
            "Constituição (art. 37, § 9º) só aplica o teto às estatais que recebam recursos para despesas de pessoal "
            "ou custeio geral; como aqui os repasses destinam-se apenas a despesa de capital, não incide o teto.\n"
            "O decreto é INCONSTITUCIONAL. Pela LRF (art. 9º), verificado o risco de não cumprimento das metas, "
            "cada Poder e o Ministério Público promovem, por ato PRÓPRIO, a limitação de empenho. O STF firmou que "
            "é inconstitucional dispositivo que autorize o Executivo a limitar unilateralmente a execução "
            "orçamentária dos demais Poderes, por violar a separação de Poderes e a autonomia financeira. Cabe ao "
            "prefeito apenas alertar o Legislativo, sendo ilegítimo o contingenciamento compulsório por decreto."
        ),
        "micro_aula": (
            "CIDA de novo: conclua no início de cada parágrafo (nulo / dependente mas sem teto / inconstitucional) "
            "e fundamente com LEI + ARTIGO — LC nº 101/2000 (LRF), arts. 21, 2º, III e 9º; CF, art. 37, § 9º. Saber o "
            "número exato do artigo ajuda, mas citar 'a LRF' já pontua; o essencial é a TESE certa. Cuidado com a "
            "pegadinha do teto: estatal dependente ≠ sujeição automática ao teto — depende da natureza do repasse "
            "(capital × pessoal/custeio)."
        ),
        "criteria": [
            ("N1", "Validade dos atos de fim de mandato (comando a).",
             "Conclui pela NULIDADE; fundamenta na LC nº 101/2000 (LRF, art. 21 — vedação de aumento de despesa com "
             "pessoal nos 180 dias que antecedem o fim do mandato), alcançando também as parcelas com efeito em 2026.", 7),
            ("N2", "Estatal dependente e teto remuneratório (comando b).",
             "Enquadra a ORBS como estatal DEPENDENTE (LRF, art. 2º, III) mas afasta o teto porque os repasses são só para "
             "despesa de capital (CF, art. 37, § 9º só alcança recursos para despesa de pessoal/custeio geral).", 7),
            ("N3", "Constitucionalidade da limitação de empenho (comando c).",
             "Conclui pela INCONSTITUCIONALIDADE; cada Poder limita empenho por ato próprio (LRF, art. 9º) e o STF veda ao "
             "Executivo limitar unilateralmente os demais Poderes (separação de Poderes/autonomia financeira).", 6),
        ],
    },
    # =====================================================================
    # TI 1 — Contratação irregular de solução de TIC — Lei 14.133
    # =====================================================================
    {
        "slug": "ti-contratacao-irregular-tic",
        "disciplina": "TI — Contratações de TIC",
        "tema": "Contratação de software por inexigibilidade sem planejamento",
        "display_order": 3,
        "texto_apoio": (
            "Determinada Secretaria municipal contratou, por inexigibilidade de licitação, um sistema integrado "
            "de gestão de um fornecedor único, sob a justificativa de 'exclusividade da solução'. Não houve "
            "Estudo Técnico Preliminar nem análise de riscos; o termo de referência foi elaborado após a "
            "escolha do fornecedor e reproduziu características proprietárias que só aquela empresa atende. O "
            "contrato prevê renovação automática de licenças e migração de dados em formato proprietário, sem "
            "cláusulas de interoperabilidade ou de saída. A área de controle interno alertou para dependência "
            "tecnológica e custos crescentes de manutenção."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) identifique as irregularidades da contratação quanto ao planejamento e à modalidade escolhida;\n"
            "b) discuta se a hipótese de inexigibilidade se sustenta e o risco de aprisionamento tecnológico "
            "(lock-in) diante dos princípios da licitação;\n"
            "c) proponha o encaminhamento do Tribunal de Contas e as medidas corretivas, situando o papel do "
            "controle externo nas linhas de defesa."
        ),
        "model_answer": (
            "A contratação é IRREGULAR por falha de planejamento. A Lei nº 14.133/2021 exige, na fase "
            "preparatória, o Estudo Técnico Preliminar, a análise de riscos e o termo de referência (art. 18), "
            "elaborados ANTES da definição da solução. Elaborar o termo de referência após escolher o fornecedor "
            "e reproduzir características proprietárias direciona indevidamente a contratação e viola os "
            "princípios do planejamento e da competitividade.\n"
            "A inexigibilidade NÃO se sustenta. Ela pressupõe inviabilidade de competição por fornecedor "
            "exclusivo ou notória especialização (Lei nº 14.133/2021, art. 74). A 'exclusividade' fabricada por "
            "especificação proprietária não é exclusividade real de mercado; havendo soluções concorrentes "
            "capazes de atender à necessidade, a competição é viável. A ausência de cláusulas de "
            "interoperabilidade e de saída agrava o risco de aprisionamento tecnológico (lock-in), com custos "
            "crescentes e perda de economicidade — contrariando a busca da proposta mais vantajosa.\n"
            "Cabe ao Tribunal de Contas, no exercício da fiscalização das contratações, expedir determinação "
            "para saneamento (exigir ETP e análise de riscos, revisar o termo de referência, incluir cláusulas "
            "de interoperabilidade/portabilidade de dados) e, persistindo o vício, sustar o ato ou determinar a "
            "anulação, sem prejuízo da responsabilização. No modelo em linhas de defesa (art. 169), o controle "
            "externo é a TERCEIRA linha, atuando após os gestores (1ª) e o controle interno (2ª)."
        ),
        "micro_aula": (
            "CIDA: Contextualize ('trata-se de contratação de solução de TIC sob o regime da Lei nº 14.133/2021'), "
            "Identifique a irregularidade com precisão técnica (falta de ETP; inexigibilidade forjada por "
            "especificação proprietária), aponte o Dispositivo (arts. 18, 74 e 169 da Lei nº 14.133/2021; princípio "
            "da competitividade) e proponha a Ação (determinação de saneamento; sustação/anulação; cláusulas de "
            "interoperabilidade). Termos que impressionam: ETP, lock-in, interoperabilidade, portabilidade de dados."
        ),
        "criteria": [
            ("N1", "Falhas de planejamento e modalidade (comando a).",
             "Identifica a ausência de ETP/análise de riscos e o termo de referência elaborado após a escolha do "
             "fornecedor; cita a fase preparatória da Lei nº 14.133/2021 (art. 18) e o direcionamento por especificação proprietária.", 7),
            ("N2", "Inexigibilidade e lock-in (comando b).",
             "Afasta a inexigibilidade (art. 74 da Lei nº 14.133/2021 exige inviabilidade REAL de competição), aponta o risco de "
             "aprisionamento tecnológico (lock-in) e a violação dos princípios da competitividade/economicidade.", 7),
            ("N3", "Encaminhamento do TCE e linhas de defesa (comando c).",
             "Propõe determinação de saneamento (ETP, revisão do TR, cláusulas de interoperabilidade/portabilidade) e, se "
             "necessário, sustação/anulação e responsabilização; situa o controle externo como 3ª linha de defesa (art. 169).", 6),
        ],
    },
    # =====================================================================
    # TI 2 — Vazamento de dados em sistema municipal — LGPD
    # =====================================================================
    {
        "slug": "ti-vazamento-dados-lgpd",
        "disciplina": "TI — Proteção de Dados (LGPD)",
        "tema": "Exposição de dados pessoais em portal público",
        "display_order": 4,
        "texto_apoio": (
            "Um portal municipal de um programa social passou a exibir, em página pública e indexável por "
            "buscadores, o nome completo, o CPF e o endereço dos beneficiários, além de informações de saúde que "
            "justificavam o benefício. Não havia Relatório de Impacto à Proteção de Dados, o órgão não havia "
            "designado encarregado (DPO) e não existiam controles de acesso ou registro das operações de "
            "tratamento. Após denúncia, o vazamento permaneceu ativo por semanas sem comunicação às autoridades "
            "ou aos titulares."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) identifique os princípios e deveres da LGPD violados pelo tratamento realizado, indicando a base "
            "legal correta para o tratamento de dados pelo Poder Público;\n"
            "b) analise as providências que o órgão deveria ter adotado (segurança, encarregado, relatório de "
            "impacto e comunicação de incidente);\n"
            "c) proponha o encaminhamento do Tribunal de Contas e as sanções/medidas cabíveis."
        ),
        "model_answer": (
            "O tratamento VIOLA a LGPD (Lei nº 13.709/2018). Foram desrespeitados, entre outros, os princípios da "
            "finalidade, da necessidade, da segurança e da prevenção (art. 6º), pois a publicação de nome, CPF, "
            "endereço e dados de saúde extrapola o mínimo necessário e expõe dados sensíveis (art. 11). Cabe "
            "corrigir a base legal: a Administração não trata dados com fundamento em consentimento, mas na "
            "execução de políticas públicas (art. 7º, III, c/c art. 23), o que não autoriza publicidade "
            "irrestrita de dados pessoais.\n"
            "O órgão descumpriu deveres essenciais. Deveria ter adotado medidas de segurança técnicas e "
            "administrativas (art. 46) e controles de acesso, mantido o registro das operações de tratamento "
            "(art. 37), elaborado o Relatório de Impacto à Proteção de Dados (art. 38), designado o encarregado "
            "(DPO), obrigatório também no Poder Público (art. 41), e, ocorrido o incidente, comunicado à ANPD e "
            "aos titulares (art. 48) — o que não fez.\n"
            "Cabe ao Tribunal de Contas determinar a imediata retirada dos dados do ar, a designação de "
            "encarregado, a elaboração do RIPD e a implantação de controles de segurança, além de recomendar a "
            "comunicação à ANPD e apurar responsabilidades. Embora as sanções administrativas da LGPD (art. 52 — "
            "advertência, multa de até 2% do faturamento limitada a R$ 50 milhões por infração, entre outras) "
            "sejam aplicadas pela ANPD, o controle externo, como terceira linha de defesa, fiscaliza a "
            "conformidade e determina o saneamento."
        ),
        "micro_aula": (
            "O erro que ZERA o embasamento aqui é dizer que a base legal é o consentimento: para o Poder Público é "
            "execução de políticas públicas (art. 7º, III, c/c art. 23 da LGPD). Depois é decorar os artigos-âncora: "
            "6º (princípios), 46 (segurança), 37 (registro), 38 (RIPD), 41 (DPO), 48 (incidente) e 52 (sanções). CIDA: "
            "identifique a violação, ancore no artigo e proponha a Ação concreta do auditor (retirar do ar, RIPD, DPO, "
            "comunicar ANPD)."
        ),
        "criteria": [
            ("N1", "Princípios/deveres violados e base legal correta (comando a).",
             "Aponta violação de princípios da LGPD (art. 6º — finalidade/necessidade/segurança/prevenção) e o tratamento de "
             "dados sensíveis (art. 11); CORRIGE a base legal para execução de políticas públicas (art. 7º, III, c/c art. 23), não consentimento.", 7),
            ("N2", "Providências devidas (comando b).",
             "Indica medidas de segurança (art. 46), registro (art. 37), Relatório de Impacto — RIPD (art. 38), encarregado/DPO "
             "obrigatório no Poder Público (art. 41) e comunicação de incidente à ANPD e aos titulares (art. 48).", 7),
            ("N3", "Encaminhamento do TCE e sanções (comando c).",
             "Propõe determinações (retirar dados do ar, designar DPO, elaborar RIPD, implantar controles), menciona as sanções "
             "do art. 52 (multa até 2%/R$ 50 mi) e situa o controle externo como 3ª linha, distinguindo o papel da ANPD.", 6),
        ],
    },
    # =====================================================================
    # TI 3 — Responsabilização por decisão técnica — LINDB + Improbidade
    # =====================================================================
    {
        "slug": "ti-responsabilizacao-decisao-tecnica",
        "disciplina": "TI — Responsabilização (LINDB)",
        "tema": "Auditar decisão técnica de arquitetura que gerou prejuízo",
        "display_order": 5,
        "texto_apoio": (
            "O gestor de TI de um órgão optou, com base em parecer técnico fundamentado e nas orientações "
            "vigentes à época, por uma arquitetura de nuvem que depois se mostrou mais custosa do que uma "
            "alternativa surgida posteriormente. Não houve desvio de recursos, favorecimento ou má-fé; a escolha "
            "seguiu estudo técnico e as dificuldades reais de contratação existentes no momento. A equipe de "
            "auditoria discorda tecnicamente da decisão e cogita responsabilizar pessoalmente o gestor pelo "
            "sobrecusto."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) avalie se o gestor pode ser responsabilizado pessoalmente pela decisão técnica, à luz da LINDB;\n"
            "b) discuta a incidência da Lei de Improbidade após a Lei nº 14.230/2021 e o parâmetro de aferição "
            "que o auditor deve adotar;\n"
            "c) proponha a conduta adequada do controle externo diante de decisões técnicas discricionárias."
        ),
        "model_answer": (
            "A responsabilização pessoal NÃO se justifica. A LINDB dispõe que o agente público responde "
            "pessoalmente por suas decisões ou opiniões técnicas somente em caso de DOLO ou ERRO GROSSEIRO "
            "(art. 28). Além disso, a interpretação deve considerar os obstáculos e as dificuldades reais do "
            "gestor (art. 22) e a orientação geral da época (não se avalia a decisão passada com a lente do "
            "conhecimento posterior). Uma escolha respaldada em parecer técnico e nas orientações vigentes, sem "
            "má-fé, não configura erro grosseiro.\n"
            "A Lei de Improbidade também não incide. Após a Lei nº 14.230/2021, a Lei nº 8.429/1992 exige DOLO "
            "específico (não há mais improbidade culposa) e tornou taxativo o rol do art. 11, em coerência com o "
            "art. 28 da LINDB. O parâmetro do auditor não é discordar tecnicamente do mérito da escolha, e sim "
            "aferir a existência de dolo ou erro grosseiro, a razoabilidade do processo decisório e a "
            "proporcionalidade.\n"
            "Diante de decisões técnicas discricionárias, cabe ao controle externo examinar o PROCESSO (motivação, "
            "estudos, aderência às normas da época) e não substituir o gestor no juízo de conveniência. Não "
            "havendo dolo ou erro grosseiro, a conduta recomendada é orientar/expedir recomendações de melhoria "
            "para contratações futuras, preservando a segurança jurídica (LINDB, art. 30), sem responsabilização."
        ),
        "micro_aula": (
            "A tese-chave é o art. 28 da LINDB: 'dolo ou erro grosseiro' — o auditor NÃO responsabiliza só por "
            "discordar tecnicamente. Combine com os arts. 22 (mundo real do gestor) e 24 (orientações da época) e "
            "com a mudança da Lei nº 14.230/2021 na improbidade (exige dolo; rol taxativo do art. 11). CIDA: "
            "conclua (não cabe responsabilizar), fundamente nos dispositivos e proponha a Ação proporcional "
            "(recomendação de melhoria, não punição)."
        ),
        "criteria": [
            ("N1", "Responsabilização pessoal à luz da LINDB (comando a).",
             "Conclui que NÃO cabe responsabilização; fundamenta no art. 28 da LINDB (dolo ou erro grosseiro) e nos arts. 22 "
             "(dificuldades reais) e 24 (orientação da época), afastando o erro grosseiro na escolha respaldada em parecer.", 7),
            ("N2", "Improbidade pós-14.230/2021 e parâmetro do auditor (comando b).",
             "Aponta que a Lei nº 8.429/1992, após a Lei nº 14.230/2021, exige DOLO e tornou taxativo o rol do art. 11; define "
             "que o auditor afere dolo/erro grosseiro e razoabilidade, não o mérito técnico.", 7),
            ("N3", "Conduta adequada do controle externo (comando c).",
             "Defende o exame do PROCESSO decisório (motivação/estudos/normas da época) sem substituir o gestor; recomenda "
             "orientação/recomendações de melhoria e preservação da segurança jurídica (LINDB, art. 30) quando não há dolo/erro grosseiro.", 6),
        ],
    },
    # =====================================================================
    # TI 4 — Governança e gestão de TI deficientes — COBIT / art. 169
    # =====================================================================
    {
        "slug": "ti-governanca-deficiente",
        "disciplina": "TI — Governança de TI",
        "tema": "Órgão sem PDTI, sem comitê de TI e sem gestão de riscos",
        "display_order": 6,
        "texto_apoio": (
            "Auditoria constatou que um órgão da Administração municipal não possui Plano Diretor de Tecnologia "
            "da Informação (PDTI), não instituiu comitê de governança de TI, não realiza gestão de riscos nem "
            "gestão de continuidade de serviços, e não mantém indicadores nem monitoramento dos contratos de TI. "
            "As contratações de tecnologia ocorrem de forma reativa, sem alinhamento ao planejamento "
            "institucional, e o controle interno não acompanha os investimentos da área."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) aponte as deficiências de governança e gestão de TI e os riscos que geram para a Administração;\n"
            "b) indique os instrumentos e referenciais aplicáveis (planejamento, comitê, gestão de riscos), "
            "distinguindo governança de gestão, e a base normativa/principiológica;\n"
            "c) proponha as recomendações do controle externo e situe o papel das linhas de defesa."
        ),
        "model_answer": (
            "Há grave deficiência de governança e gestão de TI. A ausência de PDTI, de comitê de governança de "
            "TI, de gestão de riscos e de continuidade, e de indicadores/monitoramento, leva a decisões "
            "desalinhadas do planejamento institucional, a desperdício de recursos e a vulnerabilidade dos "
            "serviços, em afronta ao princípio da eficiência (art. 37 da CF) e à busca de resultados.\n"
            "É preciso distinguir GOVERNANÇA de GESTÃO: no COBIT 2019, a governança AVALIA, DIRIGE e MONITORA "
            "(domínio EDM), enquanto a gestão PLANEJA, CONSTRÓI, ENTREGA e MONITORA (APO, BAI, DSS, MEA). "
            "Aplicam-se o PDTI (planejamento), o comitê de TI (direção) e a gestão de riscos (ISO 31000/COSO), "
            "à luz do Referencial de Governança do TCU e do modelo das três linhas de defesa (art. 169 da Lei "
            "nº 14.133/2021).\n"
            "Cabe ao Tribunal de Contas recomendar a instituição do PDTI e do comitê de governança de TI, a "
            "implantação de gestão de riscos e de continuidade e a definição de indicadores e monitoramento dos "
            "contratos. No modelo em linhas de defesa, os gestores atuam na 1ª linha, o controle interno "
            "supervisiona na 2ª e o controle externo, como 3ª linha, audita e determina o aprimoramento da "
            "governança."
        ),
        "micro_aula": (
            "O ponto que vale ponto é NÃO confundir governança (EDM — avalia/dirige/monitora) com gestão "
            "(planeja/constrói/entrega/monitora). CIDA: Contextualize (governança de TI sob os referenciais "
            "aplicáveis), Identifique as lacunas (sem PDTI/comitê/riscos), ancore no Dispositivo (art. 37 da CF — "
            "eficiência; art. 169 da Lei nº 14.133/2021; Referencial do TCU; COBIT/ISO 31000) e proponha a Ação "
            "(recomendações de PDTI, comitê, gestão de riscos, indicadores)."
        ),
        "criteria": [
            ("N1", "Deficiências e riscos (comando a).",
             "Aponta a ausência de PDTI, comitê de TI, gestão de riscos/continuidade e indicadores, e os riscos (desalinhamento, "
             "desperdício, vulnerabilidade), relacionando ao princípio da eficiência (art. 37 da CF).", 7),
            ("N2", "Instrumentos/referenciais e governança × gestão (comando b).",
             "Distingue governança (EDM — avalia/dirige/monitora) de gestão (planeja/constrói/entrega/monitora) no COBIT 2019; "
             "cita PDTI, comitê, gestão de riscos (ISO 31000/COSO), Referencial de Governança do TCU e o art. 169 da Lei nº 14.133/2021.", 7),
            ("N3", "Recomendações e linhas de defesa (comando c).",
             "Propõe recomendações concretas (PDTI, comitê, gestão de riscos/continuidade, indicadores) e situa o controle externo "
             "como 3ª linha de defesa, após gestores (1ª) e controle interno (2ª).", 6),
        ],
    },
    # =====================================================================
    # TI 5 — Transparência e dados abertos — LAI + Governo Digital
    # =====================================================================
    {
        "slug": "ti-transparencia-dados-abertos",
        "disciplina": "TI — Transparência e Dados Abertos",
        "tema": "Portal da transparência incompleto e não legível por máquina",
        "display_order": 7,
        "texto_apoio": (
            "O portal da transparência de um município publica dados apenas em PDF de imagem (não pesquisável), "
            "com defasagem de meses, sem formato aberto/legível por máquina e sem série histórica. Parte das "
            "informações só é fornecida mediante pedido formal, e não há publicação proativa de contratos e "
            "despesas. O órgão alega cumprir a transparência por 'disponibilizar quando solicitado'."
        ),
        "enunciado": (
            "Na condição de Auditor de Controle Externo, redija texto dissertativo que responda, com fundamento "
            "legal, aos seguintes tópicos:\n"
            "a) avalie a conformidade da conduta com a transparência ativa e com os requisitos de dados abertos;\n"
            "b) fundamente na Lei de Acesso à Informação e na legislação de governo digital, indicando os "
            "dispositivos e princípios;\n"
            "c) proponha o encaminhamento do controle externo."
        ),
        "model_answer": (
            "A conduta é IRREGULAR. A Lei nº 12.527/2011 (LAI) impõe a transparência ATIVA — o dever de publicar "
            "informações de interesse coletivo independentemente de pedido (art. 8º) —, de modo que 'disponibilizar "
            "só quando solicitado' não a cumpre. Publicar em PDF de imagem, defasado e sem série histórica também "
            "viola o princípio da publicidade (art. 37 da CF), pilar do controle social.\n"
            "Quanto aos dados abertos, a Lei nº 14.129/2021 (Governo Digital) consagra os dados abertos por "
            "padrão, o formato legível por máquina e a interoperabilidade, além do 'once only' (não reexigir do "
            "cidadão dado que a Administração já possui). A regra é a publicidade; o sigilo é exceção e, quando "
            "cabível, observa os graus e prazos da LAI (art. 24 — 25/15/5 anos).\n"
            "Cabe ao Tribunal de Contas determinar a publicação proativa de contratos, despesas e demais dados "
            "obrigatórios em formato aberto, atualizado e legível por máquina, com série histórica, fixando prazo "
            "para saneamento e acompanhando o cumprimento; persistindo a omissão, apura responsabilidades."
        ),
        "micro_aula": (
            "Transparência ATIVA (publicar sem pedir, LAI art. 8º) × passiva (responder a pedido) é a chave. "
            "Some os dados abertos por padrão e o formato legível por máquina da Lei nº 14.129/2021, e a "
            "publicidade como regra (art. 37 da CF; sigilo é exceção — LAI art. 24). CIDA: identifique a omissão, "
            "ancore no dispositivo e proponha a Ação (publicar proativamente em formato aberto, com prazo)."
        ),
        "criteria": [
            ("N1", "Transparência ativa e dados abertos (comando a).",
             "Conclui pela irregularidade; aponta o descumprimento da transparência ATIVA (publicar independe de pedido) e a "
             "impropriedade do PDF-imagem defasado sem formato aberto/legível por máquina.", 7),
            ("N2", "Fundamentação LAI + Governo Digital (comando b).",
             "Fundamenta na LAI (Lei nº 12.527/2011, art. 8º — transparência ativa; art. 24 — sigilo excepcional) e na Lei nº "
             "14.129/2021 (dados abertos por padrão, formato legível por máquina, interoperabilidade), com a publicidade do art. 37 da CF.", 7),
            ("N3", "Encaminhamento do controle externo (comando c).",
             "Propõe determinação de publicação proativa em formato aberto/atualizado com série histórica, prazo para saneamento, "
             "acompanhamento e apuração de responsabilidades pela omissão.", 6),
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
            case.limite_linhas = 30
            case.banca_referencia = "VUNESP"
            case.is_demo = False
            case.is_published = True
            case.display_order = spec["display_order"]
            db.flush()

            # Recria a grade (idempotente): remove critérios antigos e insere os atuais.
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
        print(f"OK — casos: {created} criados, {updated} atualizados. Total de estudos de caso: {total}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
