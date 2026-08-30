"""Cartões de recordação ativa do NÚCLEO DURO da discursiva TCE-SP (idempotente).

Fonte: fasttrack-tcesp-ti.pdf (Parte II — núcleo duro; Parte III — governança de TI).
Cada cartão é frente (deixa p/ o aluno tentar lembrar) → verso (resposta a decorar).
Toda citação de artigo nomeia a lei/norma ([[citar-artigo-com-a-lei]]).

Uso (produção): DATABASE_URL=... PYTHONPATH=. .venv/bin/python -m scripts.seed_discursivas_flashcards

Idempotente por (deck, ordem): re-rodar atualiza o texto, não duplica.
"""

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import FlashCard

DECK_LEIS = "nucleo-duro-leis"
DECK_GOV = "governanca-ti"
DECK_PRAZOS = "prazos-e-procedimentos"
DECK_JURIS = "jurisprudencia"
DECK_TCESP = "sumulas-tce-sp"

# (deck, ordem, frente, verso, lei_ref, mnemonic)
CARDS: list[tuple] = [
    # ---------------- LIMPE / princípios ----------------
    (DECK_LEIS, 1, "Princípios da Administração Pública — mnemônico e quais são?",
     "LIMPE: Legalidade, Impessoalidade, Moralidade, Publicidade, Eficiência.",
     "CF, art. 37, caput", "LIMPE"),
    (DECK_LEIS, 2, "Princípios que a VUNESP cobra JUNTO do LIMPE (processo administrativo)?",
     "Razoabilidade, proporcionalidade, motivação, interesse público e eficiência.",
     "Lei nº 9.784/1999, art. 2º", None),

    # ---------------- LINDB (Decreto-Lei 4.657/1942, arts 20-30) ----------------
    (DECK_LEIS, 10, "LINDB — mnemônico dos blocos dos arts. 20 a 30?",
     "C-R-C-R-P: Consequências (20-21), Realidade (22-24), Consenso (26-27), Responsabilidade (28), Previsibilidade (29-30).",
     "LINDB — Decreto-Lei nº 4.657/1942", "C-R-C-R-P"),
    (DECK_LEIS, 11, "LINDB — consequencialismo (decidir olhando as consequências práticas)?",
     "Art. 20: não se decide com base em valores jurídicos abstratos sem considerar as consequências práticas.",
     "LINDB, art. 20", None),
    (DECK_LEIS, 12, "LINDB — a decisão que INVALIDA um ato deve fazer o quê?",
     "Art. 21: indicar expressamente suas consequências jurídicas e administrativas.",
     "LINDB, art. 21", None),
    (DECK_LEIS, 13, "LINDB — 'mundo real do gestor' (obstáculos e dificuldades reais)?",
     "Art. 22: a interpretação considera os obstáculos e as dificuldades reais do gestor.",
     "LINDB, art. 22", None),
    (DECK_LEIS, 14, "LINDB — nova interpretação de norma exige o quê?",
     "Art. 23: regime de transição quando a nova interpretação impuser novo dever/condicionamento.",
     "LINDB, art. 23", None),
    (DECK_LEIS, 15, "LINDB — como se revê ato/conduta do passado?",
     "Art. 24: pela orientação geral da ÉPOCA (não se aplica interpretação nova retroativamente).",
     "LINDB, art. 24", None),
    (DECK_LEIS, 16, "LINDB — qual artigo foi VETADO? (pegadinha clássica)",
     "Art. 25 — foi vetado.",
     "LINDB, art. 25 (vetado)", None),
    (DECK_LEIS, 17, "LINDB — solução consensual/negociada?",
     "Art. 26: a autoridade pode celebrar compromisso para eliminar irregularidade/incerteza.",
     "LINDB, art. 26", None),
    (DECK_LEIS, 18, "LINDB — compensação por benefícios indevidos ou prejuízos anormais?",
     "Art. 27: a decisão pode impor compensação por benefícios indevidos ou prejuízos anormais.",
     "LINDB, art. 27", None),
    (DECK_LEIS, 19, "LINDB — quando o agente público responde PESSOALMENTE? (o mais citável em TI)",
     "Art. 28: somente em caso de DOLO ou ERRO GROSSEIRO. Não basta o auditor discordar tecnicamente.",
     "LINDB, art. 28", "dolo ou erro grosseiro"),
    (DECK_LEIS, 20, "LINDB — consulta pública antes do ato?",
     "Art. 29: pode-se submeter minuta a consulta pública para editar atos normativos.",
     "LINDB, art. 29", None),
    (DECK_LEIS, 21, "LINDB — dever de aumentar a segurança jurídica?",
     "Art. 30: autoridades devem atuar para aumentar a segurança jurídica (regulamentos, súmulas, respostas a consultas — caráter vinculante).",
     "LINDB, art. 30", None),

    # ---------------- Controle Externo (CF arts 70-75) ----------------
    (DECK_LEIS, 30, "Controle externo — as 5 espécies de fiscalização (mnemônico)?",
     "COFOP: Contábil, Financeira, Orçamentária, Operacional e Patrimonial.",
     "CF, art. 70", "COFOP"),
    (DECK_LEIS, 31, "Controle externo — os 3 critérios de fiscalização (mnemônico)?",
     "LLE: Legalidade, Legitimidade e Economicidade (+ aplicação das subvenções e renúncia de receitas).",
     "CF, art. 70", "LLE"),
    (DECK_LEIS, 32, "Competências do Tribunal de Contas — mnemônico A-J-A-R-F-S?",
     "Apreciar contas do Chefe do Executivo (parecer prévio); Julgar contas dos administradores; Apreciar legalidade de admissões/aposentadorias (registro); Realizar inspeções e auditorias; Fiscalizar contas e repasses; Sustar ato impugnado / aplicar sanções.",
     "CF, art. 71", "A-J-A-R-F-S"),
    (DECK_LEIS, 33, "Por que posso citar jurisprudência do TCU numa prova do TCE-SP?",
     "Art. 75: por simetria, as normas do TCU aplicam-se aos Tribunais de Contas estaduais.",
     "CF, art. 75", "simetria"),
    (DECK_LEIS, 34, "Quem sabe de irregularidade e não comunica ao Tribunal de Contas?",
     "Responde SOLIDARIAMENTE (dever do controle interno de dar ciência ao TC).",
     "CF, art. 74, §1º", None),

    # ---------------- LGPD (Lei 13.709/2018) ----------------
    (DECK_LEIS, 40, "LGPD — os 10 princípios (mnemônico)?",
     "FAN-LQT-SP-NR: Finalidade, Adequação, Necessidade / Livre acesso, Qualidade, Transparência / Segurança, Prevenção / Não discriminação, Responsabilização e prestação de contas.",
     "Lei nº 13.709/2018 (LGPD), art. 6º", "FAN-LQT-SP-NR"),
    (DECK_LEIS, 41, "LGPD — base legal da Administração p/ executar políticas públicas? (NÃO é consentimento!)",
     "Art. 7º, III c/c art. 23: execução de políticas públicas pelo Poder Público. O consentimento não é a base natural da Administração.",
     "Lei nº 13.709/2018 (LGPD), arts. 7º, III e 23", None),
    (DECK_LEIS, 42, "LGPD — artigo das definições (dado pessoal, sensível, controlador, operador, encarregado)?",
     "Art. 5º — definições.",
     "Lei nº 13.709/2018 (LGPD), art. 5º", None),
    (DECK_LEIS, 43, "LGPD — dados sensíveis?",
     "Art. 11: origem racial/étnica, convicção religiosa, opinião política, saúde, vida sexual, dado genético ou biométrico.",
     "Lei nº 13.709/2018 (LGPD), art. 11", None),
    (DECK_LEIS, 44, "LGPD — direitos do titular?",
     "Art. 18 (9 incisos): confirmação, acesso, correção, anonimização/bloqueio/eliminação, portabilidade, eliminação, informação sobre compartilhamento, informação sobre não consentir, revogação.",
     "Lei nº 13.709/2018 (LGPD), art. 18", None),
    (DECK_LEIS, 45, "LGPD — registro das operações de tratamento?",
     "Art. 37.",
     "Lei nº 13.709/2018 (LGPD), art. 37", None),
    (DECK_LEIS, 46, "LGPD — Relatório de Impacto à Proteção de Dados (RIPD)?",
     "Art. 38.",
     "Lei nº 13.709/2018 (LGPD), art. 38", "RIPD"),
    (DECK_LEIS, 47, "LGPD — encarregado (DPO): obrigatório no Poder Público?",
     "Art. 41: sim, o encarregado (DPO) é obrigatório também no Poder Público.",
     "Lei nº 13.709/2018 (LGPD), art. 41", "DPO"),
    (DECK_LEIS, 48, "LGPD — medidas de segurança, técnicas e administrativas?",
     "Art. 46.",
     "Lei nº 13.709/2018 (LGPD), art. 46", None),
    (DECK_LEIS, 49, "LGPD — comunicação de incidente de segurança?",
     "Art. 48: comunicar à ANPD e ao titular.",
     "Lei nº 13.709/2018 (LGPD), art. 48", None),
    (DECK_LEIS, 50, "LGPD — sanções (inclusive o teto da multa)?",
     "Art. 52: advertência; multa de até 2% do faturamento, limitada a R$ 50 milhões por infração; bloqueio; eliminação; suspensão; proibição.",
     "Lei nº 13.709/2018 (LGPD), art. 52", "2% / R$ 50 mi"),

    # ---------------- Lei 14.133/2021 (Licitações) ----------------
    (DECK_LEIS, 60, "Lei 14.133 — fases do processo licitatório (ordem importa)?",
     "P-D-A-J-H-R-H: Preparatória → Divulgação do edital → Apresentação de propostas/lances → Julgamento → Habilitação → Recursal → Homologação. Novidade: julgamento ANTES da habilitação.",
     "Lei nº 14.133/2021, art. 17", "P-D-A-J-H-R-H"),
    (DECK_LEIS, 61, "Lei 14.133 — modalidades de licitação (mnemônico)?",
     "PC²LD: Pregão, Concorrência, Concurso, Leilão, Diálogo competitivo. (Tomada de preços e convite foram extintas.)",
     "Lei nº 14.133/2021, art. 28", "PC²LD"),
    (DECK_LEIS, 62, "Lei 14.133 — as três linhas de defesa? (altíssima probabilidade em TI/controle)",
     "1ª: servidores/agentes na execução (quem faz); 2ª: assessoria jurídica e controle interno (quem supervisiona); 3ª: controle interno central e Tribunal de Contas (quem audita independentemente).",
     "Lei nº 14.133/2021, art. 169", "3 linhas de defesa"),
    (DECK_LEIS, 63, "Lei 14.133 — o que compõe a fase preparatória (planejamento)?",
     "Art. 18: ETP (Estudo Técnico Preliminar), termo de referência, análise de riscos e orçamento estimado.",
     "Lei nº 14.133/2021, art. 18", "ETP"),
    (DECK_LEIS, 64, "Lei 14.133 — inexigibilidade × dispensa (e como cai em TI)?",
     "Inexigibilidade (art. 74) = INVIABILIDADE de competição (fornecedor exclusivo, notória especialização). Dispensa (art. 75) = competição é viável, mas a lei dispensa (valor, emergência). Em TI: renovação de licença de software proprietário, fabricante único, lock-in.",
     "Lei nº 14.133/2021, arts. 74 e 75", None),
    (DECK_LEIS, 65, "Contratação emergencial/calamidade — prazo e vedação?",
     "Prazo máximo de 1 ano, sem prorrogação; vedada a recontratação da mesma empresa sob o mesmo fundamento (STF, ADI 6.890/2024).",
     "Lei nº 14.133/2021, art. 75, VIII", None),

    # ---------------- LAI (Lei 12.527/2011) ----------------
    (DECK_LEIS, 70, "LAI — transparência ativa?",
     "Art. 8º: dever de publicar informações independentemente de pedido.",
     "Lei nº 12.527/2011 (LAI), art. 8º", None),
    (DECK_LEIS, 71, "LAI — graus de sigilo e prazos (mnemônico)?",
     "25-15-5: Ultrassecreta 25 anos, Secreta 15 anos, Reservada 5 anos. Publicidade é a regra; sigilo é exceção.",
     "Lei nº 12.527/2011 (LAI), art. 24", "25-15-5"),

    # ---------------- Improbidade (Lei 8.429/1992, alt. 14.230/2021) ----------------
    (DECK_LEIS, 80, "Improbidade — as 3 modalidades e seus artigos?",
     "Art. 9º enriquecimento ilícito; art. 10 prejuízo ao erário; art. 11 atenta contra princípios (rol agora TAXATIVO).",
     "Lei nº 8.429/1992, arts. 9º, 10 e 11", None),
    (DECK_LEIS, 81, "O que a Lei 14.230/2021 mudou na improbidade? (a banca adora)",
     "Passou a exigir DOLO (não existe mais improbidade culposa) e tornou taxativo o rol do art. 11. Conecta direto com o art. 28 da LINDB.",
     "Lei nº 8.429/1992 (alt. pela Lei nº 14.230/2021)", None),

    # ---------------- Estatuto do Servidor SP (Lei 10.261/1968) ----------------
    (DECK_LEIS, 90, "Estatuto do Servidor de SP — artigos de deveres, proibições e penalidades?",
     "Art. 241 deveres; art. 242 proibições; art. 251 penalidades.",
     "Lei estadual nº 10.261/1968 (Estatuto SP)", None),
    (DECK_LEIS, 91, "Estatuto do Servidor de SP — penalidades (mnemônico)?",
     "R-S-M-D-D-C: Repreensão, Suspensão, Multa, Demissão, Demissão a bem do serviço público, Cassação de aposentadoria/disponibilidade.",
     "Lei estadual nº 10.261/1968, art. 251", "R-S-M-D-D-C"),

    # ---------------- Marco Civil (Lei 12.965/2014) ----------------
    (DECK_LEIS, 100, "Marco Civil — guarda de registros de conexão × de aplicação?",
     "Conexão = 1 ano (art. 13) [Calendário]; acesso a aplicações = 6 meses (art. 15) [meiA]. Art. 7º direitos do usuário; art. 19 responsabilidade do provedor mediante ordem judicial.",
     "Lei nº 12.965/2014 (Marco Civil), arts. 13 e 15", "Conexão=1 ano / Aplicação=6 meses"),

    # ---------------- Governo Digital (Lei 14.129/2021) ----------------
    (DECK_LEIS, 110, "Governo Digital — princípios de destaque?",
     "Interoperabilidade, dados abertos por padrão, once only (vedação de exigir do cidadão dado que a Administração já possui), governo como plataforma, linguagem simples.",
     "Lei nº 14.129/2021 (Governo Digital)", "once only"),

    # =========================================================
    # DECK GOVERNANÇA DE TI
    # =========================================================
    (DECK_GOV, 1, "COBIT 2019 — os 5 domínios (mnemônico)?",
     "EDM (Evaluate, Direct, Monitor) = Governança; APO (Align, Plan, Organize), BAI (Build, Acquire, Implement), DSS (Deliver, Service, Support), MEA (Monitor, Evaluate, Assess) = Gestão. Frase: 'Eu Dirijo e Monitoro; Alinho, Construo, Entrego e Avalio.'",
     "COBIT 2019", "EDM-APO-BAI-DSS-MEA"),
    (DECK_GOV, 2, "COBIT — diferença GOVERNANÇA × GESTÃO (vale ponto)?",
     "Governança AVALIA, DIRIGE e MONITORA (EDM). Gestão PLANEJA, CONSTRÓI, EXECUTA e MONITORA as atividades. Confundir os dois é erro clássico.",
     "COBIT 2019", None),
    (DECK_GOV, 3, "Três linhas (IIA) — como casam com o art. 169 da Lei 14.133?",
     "Operação → Supervisão/conformidade → Auditoria independente (o Tribunal de Contas é a 3ª linha).",
     "Modelo das 3 Linhas (IIA) ↔ Lei nº 14.133/2021, art. 169", None),
    (DECK_GOV, 4, "Segurança da informação — a tríade e o que se acrescenta?",
     "CID: Confidencialidade, Integridade, Disponibilidade (+ autenticidade, irretratabilidade/não repúdio, legalidade).",
     "Tríade CID", "CID"),
    (DECK_GOV, 5, "Gestão de riscos — etapas e as respostas ao risco (mnemônico)?",
     "Identificar → Analisar → Avaliar → Tratar. Respostas A-T-M-C: Aceitar, Transferir, Mitigar, Compartilhar/evitar.",
     "ISO 31000 / COSO ERM", "A-T-M-C"),

    # =========================================================
    # DECK LEIS — modalidades (QUANDO usar cada uma)
    # =========================================================
    (DECK_LEIS, 66, "Lei 14.133 — quando usar PREGÃO?",
     "Para aquisição de BENS e SERVIÇOS COMUNS (padrões de qualidade objetivamente definidos por especificações usuais), julgamento por menor preço ou maior desconto. VEDADO para serviços técnicos de natureza predominantemente intelectual.",
     "Lei nº 14.133/2021, art. 6º, XLI, e art. 29", None),
    (DECK_LEIS, 67, "Lei 14.133 — quando usar CONCORRÊNCIA e CONCURSO?",
     "Concorrência: bens/serviços ESPECIAIS e obras/serviços de engenharia (admite vários critérios de julgamento). Concurso: escolha de trabalho técnico, científico ou artístico, mediante prêmio ou remuneração.",
     "Lei nº 14.133/2021, art. 6º, XXXVIII e XXXIX", None),
    (DECK_LEIS, 68, "Lei 14.133 — quando usar LEILÃO e DIÁLOGO COMPETITIVO?",
     "Leilão: ALIENAÇÃO de bens (imóveis ou móveis inservíveis/apreendidos), por MAIOR LANCE. Diálogo competitivo: objetos de INOVAÇÃO ou de alta complexidade em que a Administração dialoga com licitantes para desenvolver a solução.",
     "Lei nº 14.133/2021, art. 6º, XL e XLII", None),

    # =========================================================
    # DECK LEIS — legalidade dos atos (é legal? sim/não) — aplicação
    # =========================================================
    (DECK_LEIS, 120, "É LEGAL recontratar a MESMA empresa, por dispensa, sob o mesmo fundamento emergencial, além de 12 meses?",
     "NÃO — ILEGAL. A contratação emergencial/calamidade tem prazo máximo de 1 ano e veda prorrogação e recontratação da mesma empresa sob o mesmo fundamento (STF, ADI 6.890).",
     "Lei nº 14.133/2021, art. 75, VIII", None),
    (DECK_LEIS, 121, "É VÁLIDA a inexigibilidade para contratar advocacia quando a Procuradoria tem capacidade para a causa?",
     "NÃO — IRREGULAR. O STF (Tema 309) exige, CUMULATIVAMENTE, notória especialização, preço compatível e a inadequação/impossibilidade de atuação dos quadros próprios. Havendo procuradoria capaz, falta esse requisito.",
     "Lei nº 14.133/2021, art. 74 + STF, Tema 309", None),
    (DECK_LEIS, 122, "É VÁLIDO aumentar despesa com pessoal nos 180 dias finais do mandato?",
     "NÃO — o ato é NULO (reestruturação, reajuste ou nomeação que amplie o gasto), mesmo que as parcelas só produzam efeito após o mandato.",
     "LC nº 101/2000 (LRF), art. 21", None),
    (DECK_LEIS, 123, "É CONSTITUCIONAL o Executivo limitar por decreto o empenho dos demais Poderes?",
     "NÃO — INCONSTITUCIONAL. Cada Poder e o MP limitam empenho por ATO PRÓPRIO (LRF, art. 9º); o Executivo só pode alertar, sob pena de violar a separação de Poderes e a autonomia financeira (STF).",
     "LC nº 101/2000 (LRF), art. 9º", None),
    (DECK_LEIS, 124, "A Administração pode tratar dados pessoais com base no CONSENTIMENTO do titular?",
     "Em regra NÃO é a base adequada: o Poder Público trata para execução de políticas públicas (LGPD, art. 7º, III, c/c art. 23). Apontar consentimento é erro grave no estudo de caso.",
     "Lei nº 13.709/2018 (LGPD), arts. 7º, III e 23", None),

    # =========================================================
    # DECK PRAZOS E PROCEDIMENTOS — o que a banca adora (prazos entre fases)
    # =========================================================
    (DECK_PRAZOS, 1, "Lei 14.133 — o que caracteriza a INVERSÃO de fases como regra?",
     "O JULGAMENTO das propostas ocorre ANTES da habilitação (só se habilita o vencedor). A habilitação pode, excepcionalmente e por ato motivado, anteceder o julgamento.",
     "Lei nº 14.133/2021, arts. 17 e 62", None),
    (DECK_PRAZOS, 2, "Lei 14.133 — prazo para IMPUGNAR o edital ou pedir esclarecimento?",
     "Até 3 dias úteis ANTES da data de abertura do certame; a Administração responde em até 3 dias úteis.",
     "Lei nº 14.133/2021, art. 164", "impugnação: 3 dias úteis"),
    (DECK_PRAZOS, 3, "Lei 14.133 — prazo do RECURSO administrativo e das contrarrazões?",
     "3 dias úteis para o recurso e 3 dias úteis para as contrarrazões, contados da intimação. A fase recursal é ÚNICA (após habilitação e julgamento).",
     "Lei nº 14.133/2021, art. 165", "recurso: 3 dias úteis"),
    (DECK_PRAZOS, 4, "Lei 14.133 — prazos mínimos de DIVULGAÇÃO do edital (exemplos-chave)?",
     "Contados da publicação até a apresentação de propostas (art. 55). Exemplos: bens/serviços comuns por menor preço = 8 dias úteis; obras/serviços comuns de engenharia = 10 dias úteis; leilão = 15 dias úteis; concurso e melhor técnica/técnica e preço = 35 dias úteis.",
     "Lei nº 14.133/2021, art. 55", None),
    (DECK_PRAZOS, 5, "Lei 14.133 — duração dos contratos de serviços/fornecimento CONTÍNUOS?",
     "Até 5 anos (art. 106), prorrogáveis até o limite de 10 anos (art. 107). Contratos de escopo duram até a entrega do objeto.",
     "Lei nº 14.133/2021, arts. 106 e 107", "5 anos → até 10"),
    (DECK_PRAZOS, 6, "Cautelar do Tribunal de Contas nas contratações — prazos?",
     "A Corte de Contas assina 10 dias úteis para o órgão prestar informações e delibera sobre o mérito em 25 dias úteis, prorrogável uma única vez por igual período.",
     "Lei nº 14.133/2021, art. 171", "10 / 25 dias úteis"),
    (DECK_PRAZOS, 7, "LAI — prazo para responder ao pedido de acesso à informação?",
     "Resposta imediata; não sendo possível, em até 20 dias, prorrogáveis por mais 10 dias mediante justificativa.",
     "Lei nº 12.527/2011 (LAI), art. 11", "20 + 10 dias"),
    (DECK_PRAZOS, 8, "LAI — prazo de recurso diante da negativa de acesso?",
     "10 dias a contar da ciência da negativa, dirigido à autoridade hierarquicamente superior à que negou.",
     "Lei nº 12.527/2011 (LAI), art. 15", "10 dias"),
    (DECK_PRAZOS, 9, "LRF — prazo para LIMITAR EMPENHO quando a receita frustra as metas?",
     "30 dias após verificado, ao fim de um bimestre, que a arrecadação pode não comportar as metas fiscais; cada Poder e o MP limitam por ato próprio.",
     "LC nº 101/2000 (LRF), art. 9º", "30 dias"),
    (DECK_PRAZOS, 10, "LRF — vedação de despesa com pessoal no FIM DE MANDATO?",
     "É nulo o ato que resulte aumento de despesa com pessoal nos 180 dias anteriores ao fim do mandato do titular do Poder.",
     "LC nº 101/2000 (LRF), art. 21", "180 dias"),
    (DECK_PRAZOS, 11, "LRF — periodicidade dos relatórios fiscais?",
     "Relatório Resumido da Execução Orçamentária (RREO): BIMESTRAL (art. 52). Relatório de Gestão Fiscal (RGF): QUADRIMESTRAL (art. 54).",
     "LC nº 101/2000 (LRF), arts. 52 e 54", "RREO bimestral / RGF quadrimestral"),
    (DECK_PRAZOS, 12, "LGPD — prazo para comunicar incidente de segurança?",
     "A lei exige comunicação 'em prazo razoável' à ANPD e ao titular (art. 48); a ANPD regulamentou o prazo em dias úteis — confira o número vigente antes da prova.",
     "Lei nº 13.709/2018 (LGPD), art. 48", None),
    (DECK_PRAZOS, 13, "Improbidade — prazo de prescrição após a Lei 14.230/2021?",
     "8 anos, contados da ocorrência do fato ou, na infração permanente, do dia em que cessou.",
     "Lei nº 8.429/1992, art. 23 (red. Lei nº 14.230/2021)", "8 anos"),
    (DECK_PRAZOS, 14, "Marco Civil — prazos de GUARDA de registros?",
     "Registros de CONEXÃO: 1 ano (art. 13). Registros de acesso a APLICAÇÕES: 6 meses (art. 15).",
     "Lei nº 12.965/2014, arts. 13 e 15", "Conexão 1 ano / Aplicação 6 meses"),

    # =========================================================
    # DECK JURISPRUDÊNCIA — súmulas/teses do STF e do TCU que a VUNESP cobra
    # (paráfrase — confira o texto oficial antes de decorar)
    # =========================================================
    (DECK_JURIS, 1, "STF — a súmula-chave dos Tribunais de Contas (contraditório)?",
     "SÚMULA VINCULANTE 3: assegura-se contraditório e ampla defesa nos processos do Tribunal de Contas quando a decisão puder anular/revogar ato que beneficie o interessado — EXCETO na apreciação da legalidade do ato de concessão INICIAL de aposentadoria, reforma e pensão.",
     "STF, Súmula Vinculante 3", "SV 3"),
    (DECK_JURIS, 2, "STF — prazo do Tribunal de Contas para julgar o registro de aposentadoria?",
     "TEMA 445: os Tribunais de Contas têm 5 anos, a contar da chegada do processo à Corte, para julgar a legalidade da concessão inicial de aposentadoria/reforma/pensão; ultrapassado o prazo, exige-se contraditório antes da anulação.",
     "STF, Tema 445 (RE 636.553)", "5 anos"),
    (DECK_JURIS, 3, "STF — autotutela: a Administração pode desfazer os próprios atos?",
     "SÚMULA 473: a Administração pode ANULAR seus atos ilegais e REVOGAR os inconvenientes/inoportunos, respeitados os direitos adquiridos e ressalvada a apreciação judicial.",
     "STF, Súmula 473", "autotutela"),
    (DECK_JURIS, 4, "STF — a Administração pode declarar a nulidade dos próprios atos?",
     "SÚMULA 346: sim — a Administração Pública pode declarar a nulidade dos seus próprios atos (par com a Súmula 473).",
     "STF, Súmula 346", None),
    (DECK_JURIS, 5, "STF — vedação ao nepotismo?",
     "SÚMULA VINCULANTE 13: é vedado nomear cônjuge, companheiro ou parente até o 3º grau da autoridade nomeante (ou de servidor de direção da mesma pessoa jurídica) para cargo em comissão/função de confiança, inclusive o nepotismo cruzado.",
     "STF, Súmula Vinculante 13", "SV 13"),
    (DECK_JURIS, 6, "STF — falta de advogado no processo administrativo disciplinar (PAD)?",
     "SÚMULA VINCULANTE 5: a falta de defesa técnica por advogado no PAD não ofende a Constituição.",
     "STF, Súmula Vinculante 5", "SV 5"),
    (DECK_JURIS, 7, "STF — cláusula de reserva de plenário?",
     "SÚMULA VINCULANTE 10: viola a reserva de plenário (art. 97 da CF) a decisão de órgão fracionário que afasta a incidência de lei, no todo ou em parte, sem declarar expressamente a inconstitucionalidade.",
     "STF, Súmula Vinculante 10", "SV 10"),
    (DECK_JURIS, 8, "STF — exigir depósito prévio para recorrer na via administrativa?",
     "SÚMULA VINCULANTE 21: é inconstitucional exigir depósito ou arrolamento prévio de dinheiro/bens como condição de admissibilidade de recurso administrativo.",
     "STF, Súmula Vinculante 21", "SV 21"),
    (DECK_JURIS, 9, "STF — o Tribunal de Contas pode apreciar a constitucionalidade de leis/atos?",
     "SÚMULA 347: o Tribunal de Contas pode apreciar a constitucionalidade de leis e atos do Poder Público no exercício de suas atribuições. ⚠️ O STF tem RELATIVIZADO esse entendimento em decisões recentes — cite com cautela.",
     "STF, Súmula 347", None),
    (DECK_JURIS, 10, "STF — proteção de dados pessoais é direito fundamental?",
     "Sim: o STF reconheceu a proteção de dados pessoais como direito fundamental autônomo (ADI 6.387) e a EC 115/2022 a inseriu no art. 5º, LXXIX, da CF. Reforça a LGPD nos estudos de caso de TI.",
     "STF, ADI 6.387 + EC 115/2022 (CF, art. 5º, LXXIX)", None),
    (DECK_JURIS, 11, "STF — requisitos da contratação direta de advocacia por inexigibilidade?",
     "TEMA 309: exige-se, CUMULATIVAMENTE, notória especialização, preço compatível com o mercado e a inadequação/impossibilidade de prestação pelos quadros efetivos do poder público.",
     "STF, Tema 309", None),
    (DECK_JURIS, 12, "STF — recontratação emergencial da mesma empresa além de 12 meses?",
     "ADI 6.890 (2024): é vedada a recontratação, por dispensa emergencial/calamidade, da mesma empresa sob o mesmo fundamento que ultrapasse o limite de 12 meses.",
     "STF, ADI 6.890/2024", None),

    # =========================================================
    # DECK SÚMULAS DO PRÓPRIO TCE-SP (texto oficial — tce.sp.gov.br)
    # =========================================================
    (DECK_TCESP, 1, "TCE-SP — o preço ofertado na licitação deve incluir o quê?",
     "Súmula 10: o preço final do produto ofertado pelos proponentes deve incluir os tributos e demais encargos a serem suportados pelo ofertante.",
     "Súmula TCE-SP nº 10", None),
    (DECK_TCESP, 2, "TCE-SP — o tabelamento de um produto dispensa a licitação?",
     "Súmula 11: NÃO. O simples tabelamento não dispensa a Administração de adquirir o produto mediante o competente certame licitatório.",
     "Súmula TCE-SP nº 11", None),
    (DECK_TCESP, 3, "TCE-SP — a aquisição de combustíveis e derivados de petróleo depende de licitação?",
     "Súmula 12: SIM, depende de licitação (órgãos e entidades estaduais e municipais, da administração direta e indireta).",
     "Súmula TCE-SP nº 12", None),
    (DECK_TCESP, 4, "TCE-SP — pode-se exigir documento que configure compromisso de terceiro alheio à disputa?",
     "Súmula 15: é VEDADA, em procedimento licitatório, a exigência de qualquer documento que configure compromisso de terceiro alheio à disputa.",
     "Súmula TCE-SP nº 15", None),
    (DECK_TCESP, 5, "TCE-SP — como se comprova a capacidade técnico-profissional em obras/serviços de engenharia?",
     "Súmula 23: mediante apresentação da CAT (Certidão de Acervo Técnico).",
     "Súmula TCE-SP nº 23", "CAT"),
    (DECK_TCESP, 6, "TCE-SP — é legal exigir recibo da taxa de retirada do edital para participar?",
     "Súmula 26: é ILEGAL a exigência de recibo de recolhimento da taxa de retirada do edital como condição para participação no certame.",
     "Súmula TCE-SP nº 26", None),
    (DECK_TCESP, 7, "TCE-SP — pode-se usar registro de preços para serviços de natureza continuada?",
     "Súmula 31: é VEDADA a utilização do sistema de registro de preços para contratação de serviços de natureza continuada.",
     "Súmula TCE-SP nº 31", None),
    (DECK_TCESP, 8, "TCE-SP — pode-se designar agente político como responsável por adiantamento?",
     "Súmula 46: é VEDADO designar agente político como responsável por adiantamento (art. 68 da Lei federal nº 4.320/1964).",
     "Súmula TCE-SP nº 46", None),
    (DECK_TCESP, 9, "TCE-SP — é permitido pagar sessões extraordinárias ou verbas de gabinete a Vereadores?",
     "Súmula 52: é VEDADO o pagamento de sessões extraordinárias ou de verbas de gabinete a Vereadores.",
     "Súmula TCE-SP nº 52", None),
]


def main() -> None:
    db = SessionLocal()
    created = updated = 0
    try:
        existing = {
            (c.deck, c.ordem): c
            for c in db.scalars(select(FlashCard)).all()
        }
        for deck, ordem, frente, verso, lei_ref, mnemonic in CARDS:
            card = existing.get((deck, ordem))
            if card is None:
                db.add(FlashCard(
                    deck=deck, ordem=ordem, frente=frente, verso=verso,
                    lei_ref=lei_ref, mnemonic=mnemonic, is_published=True,
                ))
                created += 1
            else:
                card.frente, card.verso = frente, verso
                card.lei_ref, card.mnemonic = lei_ref, mnemonic
                card.is_published = True
                updated += 1
        db.commit()
        total = db.scalar(select(func.count(FlashCard.id)))
        print(f"OK — cartões: {created} criados, {updated} atualizados. Total no banco: {total}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
