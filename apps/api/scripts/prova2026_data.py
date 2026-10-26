# -*- coding: utf-8 -*-
"""Transcrição MANUAL e FIEL da prova objetiva VUNESP TCE-SP 2026 (TI),
aplicada em 11.10.2026 (caderno 006, Versão 2). Fonte: ProvaMarqueX2026.pdf.

- `statement`/`options` transcritos à mão do caderno (preservando trechos
  destacados com **asteriscos**, lacunas com ____ e formatação de código).
- O gabarito oficial (GabaritoMarqueX2026.pdf, Versão 2) é aplicado pelo gerador,
  nunca derivado aqui.
- Textos de leitura (interpretação) ficam em constantes e são prefixados no
  enunciado das questões que os citam, para que fiquem autossuficientes no app.

Matérias (subject_slug): portugues, logica, etica, legislacao e as de TI
(seguranca, governanca, redes, banco-dados, engenharia-software, desenvolvimento, lgpd).
"""

TEXT_I = (
    "Texto I — IA e as tendências do futuro\n\n"
    "O uso da inteligência artificial (IA) já é uma realidade em todo o mundo, provocando "
    "mudanças profundas em todos os ramos da atividade humana, incluindo os negócios. Além "
    "disso, trata-se de uma ferramenta à disposição de qualquer pessoa que possua um smartphone "
    "ou notebook.\n"
    "Constatar essa realidade implica também reconhecer que nenhum exercício de futurologia "
    "conseguirá prever todas as consequências dessas mudanças. Porém, essas possibilidades têm "
    "de ser estudadas de modo a identificar tendências e preparar governos e empresas para "
    "conviver com a revolução tecnológica.\n"
    "Relatório da Organização para a Cooperação e Desenvolvimento Econômico (OCDE), de maio de "
    "2025, anota o seguinte: “A obtenção de taxas mais elevadas de adoção de IA pode aumentar "
    "a produtividade do trabalho e gerar outros resultados desejáveis, como menores taxas de "
    "defeitos na produção, reduzindo a necessidade de insumos materiais. As informações para "
    "políticas públicas provenientes deste e de outros estudos comparáveis provavelmente se "
    "tornarão mais importantes à medida que mais empresas buscarem se tornar usuárias ativas de "
    "IA”.\n"
    "Esses temas serão debatidos no Futura Trend, evento que terá em pauta o processo acelerado "
    "de transformação digital e os impactos da inteligência artificial generativa na "
    "reconfiguração da sociedade, na educação e na economia. Será debatida, também e de forma "
    "aprofundada, a questão do letramento digital e da educação, a partir da primeira infância, "
    "para o acesso à tecnologia, o que evitará mais uma geração de excluídos da era digital, como "
    "aconteceu nos anos 1990 e início do ano 2000.\n"
    "O seminário, portanto, está inserido no grande debate que hoje mobiliza países de todo o "
    "mundo para estudar as tendências que regularão a sociedade permeada pela inteligência "
    "artificial.\n"
    "(Editorial, 06.08.2026. Disponível em: www.opovo.com.br. Adaptado)"
)

TEXT_II = (
    "Texto II — A conta que a IA não fechou\n\n"
    "A corrida pela inteligência artificial levou muitas empresas a acreditar que seria possível "
    "substituir profissionais por tecnologia de forma rápida e com redução de custos. Contudo, a "
    "realidade começa a mostrar que essa decisão nem sempre produz os resultados esperados.\n"
    "Começamos a ver as organizações recontratando funcionários que haviam sido dispensados após "
    "a adoção de sistemas de IA. O movimento, conhecido como AI boomerang, evidencia que "
    "eficiência não depende apenas de velocidade, mas também de conhecimento, contexto e "
    "capacidade de decisão.\n"
    "A inteligência artificial é extremamente competente para automatizar tarefas repetitivas, "
    "organizar grandes volumes de dados e apoiar processos. No entanto, ainda apresenta "
    "limitações quando precisa interpretar cenários complexos, compreender nuances, lidar com "
    "situações inesperadas ou construir relações de confiança com clientes e parceiros.\n"
    "O caso da Ford ilustra bem essa realidade. Após ampliar o uso da IA em determinadas "
    "operações, a empresa percebeu que a tecnologia não conseguia entregar, sozinha, o padrão de "
    "qualidade esperado e trouxe de volta especialistas técnicos para atuar em conjunto com "
    "sistemas automatizados.\n"
    "(Sílvia Letícia, Artigos, 06.08.2026. Disponível em: www.opovo.com.br/)"
)

TEXT_CRONICA = (
    "Texto — Minhas fila (crônica)\n\n"
    "A fila é um sofrimento. É mesmo? Depende de como você encara uma fila. Em primeiro lugar, "
    "você não pode levar a fila a sério. Existem filas e filas. Uma fila de banco, por exemplo, é "
    "completamente diferente de uma fila de padaria.\n"
    "A pior fila, por consenso, é a fila do banco. Sim, você começa a sofrer com ela no dia "
    "anterior. Amanhã vou ter de ir ao banco. E você já dorme com aquela fila na cabeça. Sonha com "
    "ela. Ela vai até à rua. Ninguém está feliz na fila do banco, já notou? O sujeito que está ali "
    "está sofrendo. Já chega sofrendo. Ele sabe que vai sair dali um pouco mais pobre, no mínimo.\n"
    "Mas o pior na fila do banco é que a gente, que está mais atrás, olha a quantidade de "
    "papelzinho que o da frente tem na mão e logo pensa: isso vai longe. E quando a menina do caixa "
    "pede licença e sai para obter uma orientação do gerente lá na outra sala? Todo mundo olha a "
    "relógio. E a inveja que a gente fica do segundo da fila? Dá vontade de matar o sujeito. E "
    "aquele que disfarça? Está só com um papelzinho na mão. Mas quando chega na vez dele, abre uma "
    "pasta. Uma pasta!\n"
    "Mas toda fila tem seus encantos (basta saber curtir). Menos a fila da fome, esperando comida. "
    "Não dá para olhar para a foto (na primeira página dos jornais) daqueles brasileiros e fazer "
    "brincadeira. Aquela fila é uma coisa muito séria, gente.\n"
    "(Mário Prata, Minhas tudo. Adaptado)"
)

QUESTIONS: list[dict] = [
    # ============== LÍNGUA PORTUGUESA (Q1–12) ==============
    {
        "n": 1, "subject": "portugues", "topic": "portugues-1", "text": TEXT_I,
        "statement": "Ao analisar a inteligência artificial no cotidiano da sociedade contemporânea, o editorial deixa claro que",
        "options": [
            "a crítica que se faz à sua adoção em áreas sensíveis, como a educação digital, é justificada pelo risco de desinformação.",
            "a IA é uma ferramenta indispensável e acessível, ainda que seus efeitos negativos deixem de ser combatidos pela sociedade.",
            "a preparação precoce para acesso à tecnologia é matéria de discussão, à vista de sua importância para a inclusão digital.",
            "as mudanças tecnológicas superaram desafios para sua implementação graças a políticas públicas eficientes para enfrentá-los.",
            "a performance dela já está demonstrada, não se justificando especulações acerca de eventuais efeitos das mudanças na sociedade.",
        ],
    },
    {
        "n": 2, "subject": "portugues", "topic": "portugues-2", "text": TEXT_I,
        "statement": "A construção entre parênteses que substitui o trecho destacado, em conformidade com a norma-padrão de regência e de crase, é:",
        "options": [
            "… grande debate que hoje **mobiliza** países de todo o mundo para estudar as tendências… (conclama à muitos)",
            "… preparar governos e empresas para **conviver com a** revolução tecnológica. (adaptar-se à)",
            "… essas possibilidades têm de ser estudadas de modo a **identificar** tendências… (reconhecer à todas as)",
            "… ferramenta à disposição de qualquer pessoa **que possua um** smartphone… (tenha acesso à qualquer)",
            "Constatar essa realidade **implica** (…) reconhecer que nenhum exercício de futurologia… (leva à)",
        ],
    },
    {
        "n": 3, "subject": "portugues", "topic": "portugues-2", "text": TEXT_I,
        "statement": "Assinale a alternativa em que o trecho entre parênteses substitui o trecho destacado, de acordo com a norma-padrão e com sentido compatível com o original.",
        "options": [
            "Esses temas serão debatidos no Futura Trend, evento que **terá em pauta** o processo acelerado de transformação digital e os impactos da inteligência artificial… (em cuja pauta estarão)",
            "… grande debate **que hoje mobiliza países de todo o mundo** para estudar as tendências que regularão a sociedade permeada pela inteligência artificial. (cujos países de todo o mundo são mobilizados)",
            "… educação, a partir da primeira infância, para o acesso à tecnologia, **o que evitará** mais uma geração de excluídos da era digital… (a qual poupará)",
            "As informações para políticas públicas **provenientes deste e de outros** estudos comparáveis provavelmente se tornarão mais importantes… (nas quais provieram este e outros)",
            "… provocando mudanças profundas em todos os ramos da atividade humana, **incluindo** os negócios. (em que abrange)",
        ],
    },
    {
        "n": 4, "subject": "portugues", "topic": "portugues-2",
        "statement": (
            "A IA é uma ferramenta acessível a ____________ cidadãos que ____________ de um smartphone ou um "
            "notebook. Hoje, mais de um brasileiro a ____________ em seu cotidiano, e o uso irrestrito dessa "
            "tecnologia se consolidará quando se ____________ as consequências de sua adoção.\n\n"
            "De acordo com a norma-padrão de emprego dos verbos e de concordância, as lacunas devem ser "
            "preenchidas, correta e respectivamente, com:"
        ),
        "options": [
            "quaisquer … disporem … utilizam … previrem",
            "quaisquer … dispuserem … utiliza … previrem",
            "quaisquer … disporem … utilizam … preverem",
            "qualquer … dispuserem … utilizam … previr",
            "qualquer … dispuserem … utiliza … prever",
        ],
    },
    {
        "n": 5, "subject": "portugues", "topic": "portugues-1", "text": TEXT_I + "\n\n" + TEXT_II,
        "statement": "Constata-se que os textos I e II são tematicamente vinculados. Um aspecto que se destaca no tratamento que eles dão ao tema é:",
        "options": [
            "texto II aponta certo ceticismo da autora em relação à ideia, no texto I, de que o uso da IA direcionará a definição de políticas públicas.",
            "o texto I aponta dados de utilização da IA na formação de crianças e jovens, dados esses que são contraditados pelo texto II.",
            "ambos os textos passam ao largo de questionamentos que possam colocar em xeque a necessidade da IA para a sociedade.",
            "o texto II suscita uma discussão ausente no texto I, ao apresentar fatos que já representam restrições no uso da IA.",
            "ambos os textos enfatizam a importância da aplicação da IA e reconhecem sua autossuficiência insuperável.",
        ],
    },
    {
        "n": 6, "subject": "portugues", "topic": "portugues-1", "text": TEXT_II,
        "statement": "A expressão destacada que, no contexto, está empregada em sentido figurado é:",
        "options": [
            "… **eficiência** não depende apenas de velocidade, mas também de conhecimento… (2º parágrafo)",
            "… essa **decisão** nem sempre produz os resultados esperados. (1º parágrafo)",
            "A inteligência artificial é extremamente competente para automatizar **tarefas** repetitivas… (3º parágrafo)",
            "… a empresa percebeu que a tecnologia não conseguia entregar, sozinha, o **padrão** de qualidade esperado… (4º parágrafo)",
            "… ainda apresenta limitações quando precisa interpretar **cenários** complexos… (3º parágrafo)",
        ],
    },
    {
        "n": 7, "subject": "portugues", "topic": "portugues-2", "text": TEXT_II,
        "statement": (
            "Observe os termos em destaque nas passagens:\n"
            "… eficiência não depende apenas de velocidade, **mas também** de conhecimento, contexto e capacidade de decisão. (2º parágrafo)\n"
            "… a empresa percebeu que a tecnologia não conseguia entregar, sozinha, o padrão de qualidade esperado **e** trouxe de volta especialistas técnicos… (4º parágrafo)\n\n"
            "Esses termos relacionam as afirmações em sequência, introduzindo entre elas aspectos semânticos compatíveis com as ideias, respectivamente, de"
        ),
        "options": [
            "contraste e conclusão.",
            "oposição e acréscimo.",
            "acréscimo e consequência.",
            "acréscimo e contraste.",
            "restrição e efeito.",
        ],
    },
    {
        "n": 8, "subject": "portugues", "topic": "portugues-1", "text": TEXT_CRONICA,
        "statement": "A leitura do relato acerca da fila de banco leva a reconhecer que o narrador",
        "options": [
            "imagina-se no lugar de quem aguarda na fila e disfarça a insatisfação de ser obrigado a estar naquele local, esperando a fila andar.",
            "expressa, em tom irônico, como se habituar a situações que causam sofrimento antecipado, rendendo-se ao inevitável.",
            "recomenda ao leitor adotar alguns comportamentos que permitem evitar a ansiedade, tais como ficar alheio ao ambiente.",
            "revela-se inconformado por ver como as pessoas são submetidas a longa espera para atendimento, mesmo pagando pelo serviço.",
            "representa de forma bem-humorada sentimentos e expectativas de quem enfrenta a espera, colocando-se, com o leitor, na situação.",
        ],
    },
    {
        "n": 9, "subject": "portugues", "topic": "portugues-1", "text": TEXT_CRONICA,
        "statement": "Tal como empregada no contexto, a palavra “consenso” (2º parágrafo) tem sinônimo e antônimo, respectivamente, em:",
        "options": [
            "acordo e dissensão.",
            "certeza e desacordo.",
            "concordância e distorção.",
            "anuência e menosprezo.",
            "conforto e desconforto.",
        ],
    },
    {
        "n": 10, "subject": "portugues", "topic": "portugues-2", "text": TEXT_CRONICA,
        "statement": "Assinale a alternativa em que a colocação dos pronomes está em conformidade com a norma-padrão.",
        "options": [
            "E quando a moça do caixa sai de fininho e vai afastando-se para outra sala?",
            "Em primeiro lugar, você não pode levar a fila a sério. Nunca pode-se mesmo levar uma fila a sério.",
            "Amanhã vou ter de ir ao banco; infelizmente sujeitarei-me a essa tortura inevitável.",
            "Me dá vontade de matar o sujeito, dá vontade de esmagá-lo ali mesmo.",
            "O sujeito tinha só um papelzinho na mão, mas tinha enganado-nos e abriu uma pasta.",
        ],
    },
    {
        "n": 11, "subject": "portugues", "topic": "portugues-2", "text": TEXT_CRONICA,
        "statement": (
            "Considere as passagens a seguir:\n"
            "• E aquele que disfarça? Está **só** com um papelzinho na mão… (3º parágrafo)\n"
            "• **Mas toda** fila tem seus encantos (basta saber curtir). **Menos** a fila da fome, esperando comida. (4º parágrafo)\n\n"
            "Os termos destacados podem ser substituídos, correta e respectivamente, por:"
        ),
        "options": [
            "isolado … Além disso, seja qual for a … Afora",
            "sozinho … No entanto, cada … Não muito",
            "apenas … Entretanto qualquer … Exceto",
            "somente … Portanto, a … Salvo",
            "unicamente … Pois uma … Tirante",
        ],
    },
    {
        "n": 12, "subject": "portugues", "topic": "portugues-2",
        "statement": "A alternativa redigida de acordo com a norma-padrão de concordância verbal e de pontuação é:",
        "options": [
            "Filas, é um sofrimento e sempre podem haver filas e filas, para cada um de nós enfrentarmos no dia a dia.",
            "Com a demora do atendente, as pessoas que havia na fila do banco se cansaram, e a maior parte delas protestou.",
            "Já não basta: as horas de espera, na fila do banco, e ainda, é necessário a apresentação de documento!",
            "Não se enfrenta filas, com mau-humor, e o sujeito que as levam a sério acabam sofrendo.",
            "Ultimamente, eu me pergunto se não se vê mais filas de banco será porque nem existe mais agências bancárias?",
        ],
    },
    # ============== RACIOCÍNIO LÓGICO (Q13–16) ==============
    {
        "n": 13, "subject": "logica", "topic": "logica-1",
        "statement": (
            "Considere a afirmação: “Todos os funcionários fizeram o treinamento e pelo menos um deles fez o "
            "treinamento de maneira remota”.\n\n"
            "Uma negação dessa afirmação é equivalente a:"
        ),
        "options": [
            "pelo menos um funcionário não fez o treinamento ou todos os funcionários fizeram o treinamento de maneira remota.",
            "nenhum funcionário fez o treinamento ou todos os funcionários fizeram o treinamento de maneira remota.",
            "nenhum funcionário fez o treinamento ou pelo menos um funcionário fez o treinamento de maneira remota.",
            "algum funcionário não fez o treinamento ou nenhum funcionário fez o treinamento de maneira remota.",
            "pelo menos um funcionário não fez o treinamento e apenas um funcionário fez o treinamento de maneira remota.",
        ],
    },
    {
        "n": 14, "subject": "logica", "topic": "logica-1",
        "statement": (
            "Marina decidiu que em sua festa haverá, no máximo, 4 tipos de doces. Para ajudar em sua decisão, ela "
            "selecionou os 5 doces que mais gosta e depois escreveu 4 afirmações que precisam ser todas verdadeiras:\n"
            "• Se tiver cajuzinho, então não haverá quindim.\n"
            "• Haverá brigadeiro ou churros, mas não ambos.\n"
            "• Haverá quindim se e somente se houver churros.\n"
            "• Se houver pudim, então haverá cajuzinho ou não haverá brigadeiro.\n\n"
            "Em seguida, Marina decidiu que haverá brigadeiro, portanto, os únicos tipos de doce em sua festa serão"
        ),
        "options": [
            "brigadeiro e cajuzinho.",
            "brigadeiro, quindim e cajuzinho.",
            "brigadeiro e churros.",
            "brigadeiro, pudim e cajuzinho.",
            "brigadeiro e quindim.",
        ],
    },
    {
        "n": 15, "subject": "logica", "topic": "logica-2",
        "statement": (
            "Considere o padrão de formação da sequência ilimitada:\n"
            "1, 0, 1, 2, 0, 0, 1, 2, 3, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0, …\n\n"
            "Nessa sequência, a 1ª ocorrência do termo 0 (zero) ocorre na 2ª posição e a 1.000ª ocorrência do termo "
            "0 (zero) ocorre na"
        ),
        "options": [
            "1.995ª posição.",
            "3.150ª posição.",
            "2.955ª posição.",
            "2.035ª posição.",
            "2.450ª posição.",
        ],
    },
    {
        "n": 16, "subject": "logica", "topic": "logica-1",
        "statement": (
            "Seis irmãos nasceram, respectivamente, nos anos de 1990, 1992, 1994, 1996, 1998 e 2000.\n"
            "Considere as seguintes afirmações proferidas por eles:\n"
            "Abel: eu sou o mais novo entre os irmãos.\n"
            "Abel: Denis não é o mais velho entre os irmãos.\n"
            "Beto: Eder é mais novo do que Fábio\n"
            "Caio: Denis é o terceiro mais velho.\n"
            "Denis: eu sou mais velho do que Beto.\n"
            "Denis: eu não nasci em 2000.\n"
            "Eder: Caio é um dos dois irmãos mais velhos.\n"
            "Fábio: Beto nasceu em 1998.\n\n"
            "Apenas três desses irmãos fizeram afirmações verdadeiras. Entre os três irmãos que mentiram em suas "
            "afirmações, dois são os mais velhos entre todos.\n"
            "Os irmãos que nasceram em 1992 e 1996 foram, não necessariamente nessa ordem,"
        ),
        "options": [
            "Eder e Fábio.",
            "Caio e Denis.",
            "Beto e Fábio.",
            "Abel e Denis.",
            "Caio e Eder.",
        ],
    },
    # ============== ÉTICA PÚBLICA E INTEGRIDADE (Q17–18) ==============
    {
        "n": 17, "subject": "etica", "topic": "etica-1",
        "statement": (
            "Mário Mariano é servidor público vinculado ao Tribunal de Contas do Estado de São Paulo e encontra-se "
            "licenciado do cargo para tratar de assuntos particulares. Durante o período de licença, Mário tem "
            "oferecido, por meio de plataformas digitais, serviços de “mentoria” na área de contratações públicas "
            "e utilizado suas redes sociais para tecer comentários depreciativos sobre precedentes da Corte.\n"
            "Após ser alertado de que suas condutas poderiam ser questionadas à luz do Código de Conduta Ética do "
            "TCE/SP, o servidor afirmou acreditar que não estaria praticando qualquer ato ilícito. Ainda assim, para "
            "sanar eventuais dúvidas, decidiu formular consulta à Presidência do TCE/SP, a fim de esclarecer se sua "
            "conduta é compatível com as normas éticas aplicáveis.\n\n"
            "Com base na situação hipotética e no disposto no Código de Conduta Ética do TCE/SP, é correto afirmar que"
        ),
        "options": [
            "cabe à Presidência disciplinar a aplicação do Código de Conduta Ética e, consequentemente, responder à consulta.",
            "o servidor somente poderá ser responsabilizado por opiniões depreciativas caso se identifique, na publicação, como servidor do TCE/SP.",
            "Mário Mariano não pode ser responsabilizado, pois o Código de Conduta Ética se aplica a atos que não estejam relacionados ao exercício de suas atribuições funcionais.",
            "o Código de Conduta Ética não se aplica aos servidores licenciados, motivo pelo qual não houve a prática de ato ilícito.",
            "a autoridade competente para responder à consulta é a Comissão de Ética do TCE/SP, órgão colegiado vinculado ao Gabinete da Presidência, que tem natureza pedagógica, consultiva e deliberativa.",
        ],
    },
    {
        "n": 18, "subject": "etica", "topic": "etica-2",
        "statement": (
            "Equipe técnica do Tribunal de Contas do Estado de São Paulo (TCE/SP), durante auditoria realizada em "
            "autarquia estadual, identificou a ocorrência de fraudes relacionadas à celebração e à execução de "
            "contratos administrativos, que resultaram em elevados prejuízos para a Administração Pública.\n"
            "Diante da gravidade das irregularidades constatadas, a equipe técnica, em reunião com agentes públicos "
            "vinculados à autarquia, formulou questionamentos acerca da implantação e do funcionamento do programa de "
            "integridade na entidade. As respostas apresentadas revelaram, contudo, que os agentes desconheciam as "
            "disposições do Decreto Estadual nº 67.683/2023.\n\n"
            "Com base na situação hipotética e no disposto no referido Decreto, é correto afirmar:"
        ),
        "options": [
            "cabe à Controladoria Geral do Estado a orientação e a supervisão técnica para a elaboração e execução dos programas de integridade, sem prejuízo da subordinação hierárquica ou vinculação administrativa.",
            "o plano deve ser criado pela entidade e deve ter como eixo, dentre outros, o comprometimento da alta administração do órgão ou entidade, a instituição de instância responsável por sua implantação e gestão e a gestão de riscos à integridade.",
            "o Decreto ordena que todas as empresas que contratem com a Administração Pública estadual possuam programas de integridade em funcionamento, a serem fiscalizados pela Controladoria Geral do Estado.",
            "o plano é implantado e fiscalizado pela Controladoria Geral do Estado, a quem cabe sanar eventuais dúvidas envolvendo o tema.",
            "compete ao Secretário titular da Pasta a que está vinculada a autarquia indicar o titular da Unidade de Gestão de Integridade, a quem cabe coordenar a elaboração, a execução, a comunicação, a implantação e o monitoramento do programa de integridade.",
        ],
    },
    # ============== LEGISLAÇÃO (Q19–20) ==============
    {
        "n": 19, "subject": "legislacao", "topic": "legislacao-1",
        "statement": (
            "O Tribunal de Contas do Estado do Estado de São Paulo recebeu, para apreciação, as contas anuais "
            "prestadas pelo prefeito do Município Y, relativas ao último exercício financeiro. Durante a instrução, a "
            "unidade técnica identificou preliminarmente irregularidades relevantes na execução orçamentária e na "
            "aplicação dos recursos destinados à manutenção e ao desenvolvimento do ensino. Concluída a instrução, "
            "surgiu divergência interna quanto ao órgão competente para deliberar sobre o processo, bem como sobre o "
            "rito que deve ser seguido no procedimento de emissão do parecer prévio.\n\n"
            "Com base na situação hipotética e no Regimento Interno do Tribunal de Contas do Estado do Estado de São "
            "Paulo, é correto afirmar que"
        ),
        "options": [
            "compete privativamente às Câmaras emitir parecer prévio, que será passível de pedido de reexame, formulado uma única vez e com efeito suspensivo.",
            "os processos de emissão de parecer prévio são distribuídos automaticamente para a Presidência, que poderá redistribuí-los, de acordo com ato interno.",
            "nos processos desta natureza não são admitidas decisões monocráticas que suspendam a sua análise ou ordenem a adoção de diligências complementares.",
            "a competência para a emissão do parecer prévio é privativa do Plenário.",
            "cabe ao juiz singular emitir parecer prévio sobre as contas do prefeito, admitida a possibilidade de interposição de embargos de declaração e recurso de revisão para a Câmara, nas hipóteses previstas no Regimento Interno.",
        ],
    },
    {
        "n": 20, "subject": "legislacao", "topic": "legislacao-1",
        "statement": (
            "Considere que o Tribunal de Contas do Estado de São Paulo recebeu denúncia acerca de possíveis "
            "irregularidades em procedimento licitatório promovido pelo Município X para a contratação de empresa "
            "destinada à prestação dos serviços de coleta, transporte e destinação final de resíduos sólidos "
            "domiciliares. Segundo o denunciante, determinadas exigências do instrumento convocatório teriam sido "
            "estabelecidas com o objetivo de direcionar a contratação em favor de empresa específica.\n"
            "A denúncia sustenta, ainda, que a empresa supostamente beneficiada pertence ao empresário que teria "
            "realizado expressivas doações não contabilizadas à campanha eleitoral do atual chefe do Poder Executivo "
            "municipal e que o favorecimento na licitação, inclusive mediante contratação por valores superiores aos "
            "praticados no mercado, constituiria contrapartida ao apoio financeiro anteriormente prestado.\n\n"
            "Com base na situação hipotética, no disposto na Lei Complementar Estadual nº 709/1993 e no Regimento "
            "Interno do Tribunal de Contas do Estado de São Paulo, assinale a alternativa correta."
        ),
        "options": [
            "A denúncia pode ser apresentada por pessoa jurídica desde que, com base na situação narrada, ela não seja utilizada para atender interesse subjetivo próprio.",
            "A denúncia não pode ser autuada em caráter sigiloso, salvo em situações em que seja necessária a preservação da intimidade dos envolvidos ou de interesse público.",
            "A denúncia pode ser apresentada de forma anônima, cabendo ao relator do processo avaliar se deve ou não ser recebida, de acordo com a natureza das circunstâncias reveladas na sua apresentação.",
            "O relator poderá, após recebida a denúncia, decretar a suspensão liminar do procedimento licitatório, estando a decisão sujeita a referendo do Plenário.",
            "A denúncia, para ser recebida, precisa conter, além do relato do ilícito, o nome legível, a qualificação e o endereço do denunciante e estar acompanhada de prova ou indício concernente ao fato denunciado.",
        ],
    },
    # ============== CONHECIMENTOS ESPECÍFICOS — TI (Q21–80) ==============
    {
        "n": 21, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Considere um sistema operacional com três processos (P1, P2 e P3) e três recursos (R1, R2 e R3). Cada "
            "recurso possui uma única instância, e nenhum dos recursos pode ser retirado à força do processo que o "
            "possui. Em determinado momento, o estado do sistema é:\n"
            "• P1 possui R1 e solicita R2;\n"
            "• P2 possui R2 e solicita R3;\n"
            "• P3 possui R3 e solicita R1.\n\n"
            "Com base nas condições de Coffman, assinale a alternativa que apresenta a conclusão correta sobre esse "
            "estado do sistema."
        ),
        "options": [
            "O enunciado não apresenta a ordem em que P1, P2 e P3 foram criados, não sendo possível determinar a ocorrência de deadlock.",
            "A espera circular caracteriza deadlock somente quando há dois processos envolvidos. Como a situação apresenta três processos, não existe deadlock.",
            "Como há três processos e cada um deles possui um recurso, não existe deadlock. Pelo menos um processo pode liberar um recurso, evitando impasses.",
            "Os três processos formam uma espera circular e estão presentes simultaneamente as condições de exclusão mútua, posse e espera e não preempção, existindo deadlock.",
            "Os recursos possuem uma única instância, o que por si só caracteriza a exclusão mútua, determinando a ocorrência de deadlock. Se houvesse mais de uma instância de cada recurso, a espera circular deixaria de existir.",
        ],
    },
    {
        "n": 22, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Em um sistema operacional, um dispositivo de entrada gera caracteres de forma contínua. Para otimizar o "
            "fluxo e evitar a perda de dados, o kernel utiliza o mecanismo de double buffering (Buffer 1 e Buffer 2). "
            "Considere a seguinte sequência de eventos:\n"
            "• O Buffer 1 atinge sua capacidade máxima, e o kernel inicia a transferência de seu conteúdo para a "
            "memória do processo do usuário.\n"
            "• Durante essa transferência, ocorre uma falha de página (page fault), bloqueando a conclusão da cópia "
            "até que a página necessária seja trazida do disco.\n"
            "• O dispositivo de hardware continua a enviar novos dados ininterruptamente.\n\n"
            "Assinale a alternativa que descreve a conduta correta do sistema operacional segundo o conceito de "
            "double buffering."
        ),
        "options": [
            "Manter a recepção de dados no Buffer 1 simultaneamente à transferência para o usuário, permitindo o acesso concorrente ao mesmo buffer.",
            "Redirecionar os novos caracteres diretamente para o espaço do usuário via Memory-Mapped I/O, liberando os buffers do núcleo para a paginação do disco.",
            "Redirecionar a gravação dos novos caracteres recebidos para o Buffer 2, enquanto a transferência do Buffer 1 permanece suspensa aguardando o tratamento do page fault.",
            "Transferir o conteúdo dos dois buffers paralelamente para o espaço do usuário, dobrando a largura de banda da transferência de entrada.",
            "Interromper imediatamente a leitura do dispositivo de entrada (gerando hardware stall) até que o tratamento da falha de página seja concluído.",
        ],
    },
    {
        "n": 23, "subject": "redes", "topic": "redes-2",
        "statement": (
            "O sistema operacional Windows 11 possui uma conta local interna denominada Administrador, destinada à "
            "administração do sistema.\n\n"
            "Assinale a alternativa correta associada a essa conta."
        ),
        "options": [
            "O uso da conta local (não administrador) para entrar no computador é uma prática recomendada de segurança, utilizando-se a elevação de privilégios quando forem necessárias tarefas administrativas.",
            "A associação de um usuário ao grupo Administradores faz com que todos os aplicativos executados por esse usuário sejam automaticamente executados com privilégios administrativos completos.",
            "Após a instalação do Windows 11, pode-se excluir a conta Administrador.",
            "Uma prática recomendada é utilizar a conta Administrador interna para atividades cotidianas, pois isso dificulta o acesso de usuários mal-intencionados ao computador.",
            "A conta Administrador não pode ser renomeada ou desabilitada.",
        ],
    },
    {
        "n": 24, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Um usuário de um computador com o sistema operacional Windows 11 formatou um pendrive com capacidade de "
            "128 GB. Em seguida, tentou copiar para esse pendrive um arquivo de tamanho 6 GB e não conseguiu, recebendo "
            "uma mensagem informando que o arquivo é muito grande para o sistema de arquivos de destino.\n\n"
            "Assinale a alternativa correta quanto à explicação sobre o que ocorreu e uma possível solução."
        ),
        "options": [
            "Arquivos maiores que 1 GiB em pendrives não são permitidos no Windows 11, por questões de segurança. Uma solução é desabilitar esse bloqueio automático no Gerenciador de dispositivos do Windows 11.",
            "O pendrive provavelmente está formatado em exFAT, e nesse padrão existe um limite máximo de 2 GiB por arquivo gravado. Uma solução é reformatá-lo em outro padrão, por exemplo, o FAT32 que suporta arquivos de tamanho significativamente maior que 6 GiB.",
            "O Windows 11 permite pendrives com capacidade de até 64 GiB, podendo apresentar erros em pendrives de maior capacidade. Uma solução seria particioná-lo em duas partes de 64 GB.",
            "O pendrive provavelmente está formatado em FAT32, e nesse padrão existe um limite máximo de 4 GiB - 1 byte por arquivo gravado. Uma solução é reformatá-lo em outro padrão, por exemplo, o NTFS, que suporta arquivos de tamanho significativamente maior que 6 GiB.",
            "A Tabela de Alocação de Arquivos do pendrive deve estar defeituosa. A solução é executar o utilitário de teste do Windows 11 para localizar e isolar as partes defeituosas do pendrive.",
        ],
    },
    {
        "n": 25, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Analise o seguinte código HTML, que utiliza JavaScript.\n\n"
            "<!DOCTYPE html>\n"
            "<body>\n"
            "<div id=\"valor\"></div>\n"
            "<script>\n"
            "    var a = 1;\n"
            "    var b = 2;\n"
            "    if (true) {\n"
            "        var a = 2;\n"
            "        var b = b + 1;\n"
            "        let c = 2;\n"
            "    }\n"
            "    const resultado = document.getElementById(\"valor\");\n"
            "    valor.innerHTML =\n"
            "        \"<p>a = \" + a + \"</p>\" +\n"
            "        \"<p>b = \" + b + \"</p>\" +\n"
            "        \"<p>Tipo da variável c = \" + typeof c + \"</p>\";\n"
            "</script>\n"
            "</body></html>\n\n"
            "Ao abrir essa página em um navegador, inicialmente será exibido:"
        ),
        "options": [
            "a = 2\nb = 3\nTipo da variável c = 2",
            "a = 2\nb = 1\nTipo da variável c = undefined",
            "a = 1\nb = 2\nTipo da variável c = undefined",
            "a = 1\nb = 2\nTipo da variável c = 2",
            "a = 2\nb = 3\nTipo da variável c = undefined",
        ],
    },
    {
        "n": 26, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considere o seguinte código HTML, que utiliza JavaScript.\n\n"
            "<!DOCTYPE html>\n"
            "<html><body>\n"
            "<p id=\"nome\">Página da Empresa</p>\n"
            "<button onclick=\"mudar()\">Modificar texto</button>\n"
            "<script>\n"
            "    function mudar() {\n"
            "        const elemento = document.getElementById(\"nome\");\n"
            "        elemento.style.fontWeight = \"bold\";\n"
            "        elemento.style.fontStyle = \"italic\";\n"
            "    }\n"
            "</script>\n"
            "</body></html>\n\n"
            "Ao abrir essa página em um navegador, inicialmente será exibido o texto “Página da Empresa” e um botão "
            "“Modificar texto”. Assinale a alternativa correta sobre esse programa."
        ),
        "options": [
            "Ao clicar o botão, o texto Página da Empresa será exibido em negrito e itálico. Ao clicar o botão novamente, o texto será exibido no formato anterior.",
            "Ao clicar o botão pela primeira vez, o texto “Página da Empresa” será exibido em negrito e itálico. Ao clicar o botão novamente, nada irá ocorrer.",
            "Ao clicar o botão aparecerá uma janela com uma mensagem de confirmação de alteração da forma do texto “Página da Empresa”.",
            "Ao passar o cursor do mouse no botão, o texto Página da Empresa será exibido em negrito e itálico. Ao retirar o cursor do mouse do botão, o texto continuará a ser exibido em negrito e itálico.",
            "Ao passar o cursor do mouse no botão, o texto Página da Empresa será exibido em negrito e itálico. Ao retirar o cursor do mouse do botão, o texto será exibido no formato anterior.",
        ],
    },
    {
        "n": 27, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considere o seguinte código HTML, que utiliza JavaScript.\n\n"
            "<!DOCTYPE html>\n"
            "<body>\n"
            "<button id=\"botao\">\n"
            "    <span id=\"texto\">Clique nesse botão</span>\n"
            "</button>\n"
            "<p id=\"valor\"></p>\n"
            "<script>\n"
            "    const botao = document.getElementById(\"botao\");\n"
            "    const texto = document.getElementById(\"texto\");\n"
            "    const valor = document.getElementById(\"valor\");\n"
            "    botao.addEventListener(\"click\", function () {\n"
            "        valor.textContent += \"casa \";\n"
            "    });\n"
            "    texto.addEventListener(\"click\", function (event) {\n"
            "        valor.textContent += \"bola \";\n"
            "        event.stopPropagation();\n"
            "    });\n"
            "</script>\n"
            "</body></html>\n\n"
            "Ao abrir essa página em um navegador,"
        ),
        "options": [
            "é exibido um botão que, a cada clique sobre o texto “Clique nesse botão”, exibe a palavra bola.",
            "é exibido um botão que, a cada clique sobre o texto “Clique nesse botão”, exibe a palavra casa.",
            "é exibido um botão que, ao se clicar em uma área do botão fora do texto “Clique nesse botão”, exibe a palavra bola.",
            "é exibida a palavra casa.",
            "é exibida a palavra bola.",
        ],
    },
    {
        "n": 28, "subject": "lgpd", "topic": "lgpd-1",
        "statement": (
            "Um órgão público (controlador) possui um sistema que armazena dados pessoais. Em determinado momento, "
            "constata a necessidade de contratar uma empresa especializada (operador) para realizar a manutenção desse "
            "sistema. Durante a vigência do contrato, a empresa utilizou os dados pessoais para testar um novo produto "
            "que ela desenvolveu. A empresa não recebeu autorização ou instrução do órgão público para utilizar os "
            "dados nessa nova finalidade nem informou os titulares dos dados. De acordo com a Lei Geral de Proteção de "
            "Dados Pessoais (LGPD) nº 13.709/2018, a utilização dos dados"
        ),
        "options": [
            "é permitida para fins de pesquisa e aprimoramento de produtos da empresa, independentemente de autorização do controlador, pois o operador pode utilizar os dados para finalidades relacionadas ao desenvolvimento tecnológico, desde que não os divulgue publicamente.",
            "é permitida, sem necessidade de autorização, desde que a empresa utilize os dados exclusivamente em ambiente interno e não os divulgue a terceiros.",
            "pode caracterizar tratamento incompatível com a atuação do operador (empresa), pois este deve realizar o tratamento segundo as instruções fornecidas pelo controlador (órgão público). A empresa não pode utilizar os dados livremente para outras finalidades.",
            "é permitida, sem necessidade de autorização, pois a empresa possui acesso legítimo aos dados durante a execução do contrato e pode utilizá-los para qualquer finalidade relacionada às suas atividades comerciais.",
            "é permitida, sem necessidade de autorização, não caracterizando tratamento incompatível com a atuação do operador (empresa), desde que o novo produto possa ser utilizado também pelo controlador (órgão público).",
        ],
    },
    {
        "n": 29, "subject": "governanca", "topic": "governanca-2",
        "statement": (
            "Uma empresa comercializou a licença de uso de um de seus programas de computador (software) para um órgão "
            "público. A empresa informou que será concedido ao órgão o direito de utilizar o software, mas não serão "
            "transferidos a ele os direitos patrimoniais sobre o software nem será fornecido o código-fonte.\n\n"
            "Assinale a alternativa correta, com base na Lei nº 9.609/1998."
        ),
        "options": [
            "A licença de uso pode autorizar a utilização do programa pelo órgão público sem, contudo, transferir a ele a titularidade dos direitos patrimoniais sobre o software.",
            "A comercialização não foi realizada da forma correta, pois pela citada lei, órgãos públicos devem sempre receber a titularidade dos direitos patrimoniais sobre o software juntamente com a licença de uso.",
            "A informação não foi fornecida da forma correta, pois, pela citada lei, órgãos públicos recebem automaticamente a titularidade dos direitos patrimoniais sobre o software após cinco anos da compra da licença de uso.",
            "A informação fornecida pela empresa não tem valor legal, pois pela citada lei os softwares, quando comercializados, automaticamente transferem a titularidade dos direitos patrimoniais.",
            "Segundo a citada lei, o órgão público tem direito de alterar o código-fonte desde que não comercialize ou forneça essas alterações para outras empresas.",
        ],
    },
    {
        "n": 30, "subject": "governanca", "topic": "governanca-2",
        "statement": (
            "Uma pessoa solicita a um órgão público federal a cópia integral de um documento interno que contém, no "
            "mesmo arquivo, informações que são públicas e, em algumas partes do documento, informações de acesso "
            "restrito, que é amparado pela legislação. Considerando a Lei Federal nº 12.527/2011, caso o órgão público "
            "federal não atenda o pedido da pessoa, com a alegação de que a presença de informações protegidas impede a "
            "divulgação do documento, ele está"
        ),
        "options": [
            "em desacordo com a citada lei, pois como o documento tem partes públicas, ele pode ser fornecido integralmente.",
            "em desacordo com a citada lei, pois ele deverá possibilitar o acesso à parte não sigilosa, por meio de certidão, extrato ou cópia, com ocultação ou exclusão da parte sob sigilo.",
            "de acordo com a citada lei, pois o órgão público federal tem a obrigação de tornar o documento inacessível desde a existência de uma parte protegida, que torna todo o documento inacessível.",
            "de acordo com a citada lei, pois só um juiz poderá obrigá-lo a exibir um documento que apresente algumas partes sob sigilo.",
            "de acordo com a citada lei, pois o órgão público federal só poderá divulgar o documento após expirar o período de 10 anos de sigilo.",
        ],
    },
    {
        "n": 31, "subject": "redes", "topic": "redes-2",
        "statement": "Assinale a alternativa que apresenta uma afirmação correta sobre uma arquitetura de computação em nuvem do tipo multi-tenancy.",
        "options": [
            "Arquiteturas desse tipo são utilizadas em soluções SaaS e PaaS, mas não em IaaS.",
            "Esse tipo de arquitetura permite exclusivamente o escalonamento vertical.",
            "Não é possível implementar esse tipo de arquitetura em uma nuvem pública.",
            "O compartilhamento de recursos nesse tipo de arquitetura contribui para a redução do custo operacional.",
            "Uma das vantagens desse tipo de arquitetura é a redução da necessidade de mecanismos de isolamento e controle de acesso entre os diferentes tenants.",
        ],
    },
    {
        "n": 32, "subject": "redes", "topic": "redes-2",
        "statement": (
            "PaaS e IaaS são dois modelos de computação em nuvem.\n\n"
            "Assinale a alternativa que apresenta uma vantagem do PaaS em relação ao IaaS."
        ),
        "options": [
            "Existe um acesso facilitado ao hardware físico do sistema utilizado.",
            "A latência das operações é maior.",
            "O cliente pode instalar e gerenciar o sistema operacional do sistema utilizado.",
            "O cliente pode focar no desenvolvimento da aplicação.",
            "As chamadas de sistema (syscalls) são configuradas pelo cliente.",
        ],
    },
    {
        "n": 33, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Um dos recursos disponíveis no VMware vSphere 8.x é o Quick Boot.\n\n"
            "A principal vantagem desse recurso é permitir reiniciar o hipervisor ESXi sem reinicializar o"
        ),
        "options": [
            "vCenter Server.",
            "Sistema operacional hospedeiro.",
            "Cluster vSphere.",
            "Datastore VMFS.",
            "Hardware do servidor.",
        ],
    },
    {
        "n": 34, "subject": "redes", "topic": "redes-1",
        "statement": (
            "No terminal de um sistema Ubuntu, foi executado o seguinte comando:\n\n"
            "cut -d: -f6 /etc/passwd\n\n"
            "É correto afirmar que as informações retornadas pelo comando correspondem ao"
        ),
        "options": [
            "nome de cada usuário.",
            "identificador de cada usuário (UID).",
            "diretório home de cada usuário.",
            "shell padrão de cada usuário.",
            "senha de cada usuário.",
        ],
    },
    {
        "n": 35, "subject": "redes", "topic": "redes-1",
        "statement": (
            "Considere o seguinte comando chmod, executado no terminal de um sistema Ubuntu:\n\n"
            "chmod g-wx,o-rw,u=xrw,g+r,go+x file.sh\n\n"
            "Um comando equivalente ao apresentado é:"
        ),
        "options": [
            "chmod 751 file.sh",
            "chmod 731 file.sh",
            "chmod 711 file.sh",
            "chmod 733 file.sh",
            "chmod 755 file.sh",
        ],
    },
    {
        "n": 36, "subject": "redes", "topic": "redes-2",
        "statement": (
            "O Docker pode ser instalado em um sistema Ubuntu por meio do gerenciador de pacotes apt.\n\n"
            "Em uma instalação padrão, os dados persistentes do Docker são armazenados no diretório"
        ),
        "options": [
            "/usr/local/docker",
            "/var/lib/docker",
            "/usr/lib/docker",
            "/srv/docker",
            "/etc/docker",
        ],
    },
    {
        "n": 37, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "Na linguagem JavaScript, a propriedade Number.MAX_SAFE_INTEGER indica o maior valor inteiro que pode ser "
            "representado com segurança.\n\n"
            "Assinale a alternativa que apresenta o valor correto dessa propriedade, considerando o símbolo ^ como "
            "operador de exponenciação."
        ),
        "options": [
            "2^32 - 1",
            "2^52 - 1",
            "2^51 - 1",
            "2^53 - 1",
            "2^31 - 1",
        ],
    },
    {
        "n": 38, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "Considere o seguinte trecho de código na linguagem PHP 8.x:\n\n"
            "$n = 6;\n"
            "unset($n);\n\n"
            "Após a execução da função unset($n), é correto afirmar que a variável $n"
        ),
        "options": [
            "deixa de ser definida.",
            "passa a assumir valor VOID.",
            "passa a assumir valor 0.",
            "passa a assumir valor de string vazia.",
            "permanece armazenando o valor 6.",
        ],
    },
    {
        "n": 39, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "Os tipos double, float e long são utilizados na linguagem C# para representar números.\n\n"
            "Assinale a alternativa que apresenta, respectivamente, os tamanhos desses tipos de dados."
        ),
        "options": [
            "4 bytes, 4 bytes e 4 bytes.",
            "8 bytes, 8 bytes e 8 bytes.",
            "8 bytes, 4 bytes e 8 bytes.",
            "4 bytes, 8 bytes e 8 bytes.",
            "4 bytes, 8 bytes e 4 bytes.",
        ],
    },
    {
        "n": 40, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Requisições HTTP (HTTP Requests) são realizadas por meio de métodos. Esses métodos podem ser "
            "classificados como seguros e/ou idempotentes.\n\n"
            "Assinale a alternativa que apresenta um método que é idempotente, mas não seguro."
        ),
        "options": ["PUT", "GET", "POST", "CONNECT", "HEAD"],
    },
    {
        "n": 41, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "Um usuário utilizou o seguinte prompt para interagir com um LLM:\n\n"
            "Explique qual é o papel de um auditor.\n\n"
            "Com base nas técnicas de engenharia de prompts, é correto afirmar que o usuário utilizou uma abordagem do tipo"
        ),
        "options": [
            "Few-shot prompting.",
            "One-shot prompting.",
            "Chain prompting.",
            "Multi-shot prompting.",
            "Zero-shot prompting.",
        ],
    },
    {
        "n": 42, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "LLMs são modelos capazes de processar solicitações escritas em linguagem natural.\n\n"
            "Nesse tipo de modelo, o conceito de token representa"
        ),
        "options": [
            "um Transformer que compõe o modelo.",
            "uma resposta retornada pelo modelo.",
            "uma consulta à web realizada pelo modelo.",
            "uma unidade de texto processada pelo modelo.",
            "um prompt processado pelo modelo.",
        ],
    },
    {
        "n": 43, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": (
            "Uma das tarefas em que o aprendizado de máquina não supervisionado é utilizado é a detecção de anomalias. "
            "Nesse tipo de tarefa, alguns modelos possuem um hiperparâmetro denominado contamination.\n\n"
            "A função desse hiperparâmetro é"
        ),
        "options": [
            "habilitar o bootstraping.",
            "indicar a proporção esperada de anomalias nos dados.",
            "ajustar o número de features válidas.",
            "definir a proporção dos dados de treinamento utilizada pelo modelo.",
            "configurar a função de perda do modelo.",
        ],
    },
    {
        "n": 44, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Analise o algoritmo apresentado a seguir, na forma de uma pseudolinguagem (português estruturado), que no "
            "seu início lê dois valores.\n\n"
            "Início\n"
            "    Inteiro: va1, va2, va3, cont;\n"
            "    va1 ← 8;\n"
            "    Leia (va2, va3);\n"
            "    Para cont de 1 até 5 faça\n"
            "    [\n"
            "        va1 ← va1 + va2 − va3;\n"
            "        Se (va1 ≥ 10)\n"
            "            Então\n"
            "                va3 ← va2+1;\n"
            "            Senão\n"
            "                va2 ← va3-1;\n"
            "    ]\n"
            "    Imprima va1;\n"
            "Fim.\n\n"
            "Caso os valores lidos para as variáveis va2 e va3 tenham sido, respectivamente, 5 e 3, o valor da variável "
            "va1 impresso ao final do programa será:"
        ),
        "options": ["8", "9", "10", "7", "6"],
    },
    {
        "n": 45, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Deseja-se executar o seguinte programa, elaborado na forma de uma pseudolinguagem (português estruturado).\n\n"
            "Início\n"
            "    Inteiro: i, j;\n"
            "    Inteiro: M[1..3], N[1..3];\n"
            "    Para i de 1 até 3 faça\n"
            "    [\n"
            "        M[i] ← 0;\n"
            "        N[i] ← 0;\n"
            "    ]\n"
            "    Para i de 1 até 3 faça\n"
            "    [\n"
            "        M[i] ← M[i] + i;\n"
            "        Para j de 1 até 3 faça\n"
            "        [\n"
            "            N[j] ← N[j] + 2*j;\n"
            "        ]\n"
            "    ]\n"
            "Fim.\n\n"
            "Ao final da execução desse programa, a soma de todos os valores dos vetores M e N será igual a:"
        ),
        "options": ["24", "30", "42", "48", "54"],
    },
    {
        "n": 46, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Uma estrutura de dados do tipo pilha, em um determinado instante, encontra-se com os seguintes dados "
            "armazenados, conforme ilustrado na figura, em que SP é o Stack Pointer atual da pilha. Do topo (apontado "
            "por SP) para a base, os valores são: 30, 14, 17, 20.\n\n"
            "Considere as operações padrão PUSH e POP associadas a essa estrutura de dados, e assuma x, y e z como "
            "variáveis. As operações a seguir, na ordem apresentada, foram executadas sobre essa estrutura de dados.\n\n"
            "POP x\n"
            "POP y\n"
            "POP z\n"
            "PUSH x\n"
            "PUSH z\n"
            "PUSH y\n"
            "POP x\n"
            "POP y\n"
            "POP z\n\n"
            "Ao final dessa execução, os valores presentes nas variáveis x, y e z, respectivamente, serão:"
        ),
        "options": [
            "14, 17 e 30.",
            "14, 30 e 17.",
            "17, 30 e 14.",
            "17, 14 e 30.",
            "30, 17 e 14.",
        ],
    },
    {
        "n": 47, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Ao desenvolver um programa considerando o paradigma da programação estruturada, pode-se chamar uma "
            "sub-rotina passando parâmetros por valor ou por referência.\n\n"
            "Assinale a alternativa correta a respeito."
        ),
        "options": [
            "Na chamada por referência, a passagem de uma estrutura de dados grande para a sub-rotina é facilitada por ser necessária a passagem do endereço da estrutura, e não de todo o seu conteúdo.",
            "Na chamada por valor, a sub-rotina recebe o endereço de memória onde se encontra a variável original no programa chamador.",
            "Na chamada por referência, a sub-rotina recebe uma cópia do valor da variável, deixando esse processo mais seguro, sem risco de se alterar a variável original no programa chamador.",
            "Tanto na chamada por valor quanto na chamada por referência, uma modificação efetuada no parâmetro dentro da sub-rotina não altera o valor da variável original no programa chamador.",
            "Na chamada por valor, uma eventual modificação efetuada no parâmetro dentro da sub-rotina altera o valor da variável original no programa chamador.",
        ],
    },
    {
        "n": 48, "subject": "redes", "topic": "redes-1",
        "statement": (
            "No contexto do sistema operacional Windows Server 2022, considere o seguinte comando do PowerShell:\n\n"
            "Install-WindowsFeature -Name Web-Server -Source \\\\server2\\winsxs\n\n"
            "Ele tem como objetivo instalar o"
        ),
        "options": [
            "AD DS no computador de nome server2, dentro da pasta compartilhada winsxs, tornando server2 um controlador de domínio.",
            "AD DS no computador local, tornando-o um controlador de domínio que armazena seu banco de dados no compartilhamento designado por \\\\server2\\winsxs.",
            "IIS no computador local, especificando que a origem dos arquivos do recurso para instalação está no compartilhamento winsxs do computador de nome server2, caso não estejam disponíveis no computador local.",
            "IIS no computador de nome server2, dentro da pasta compartilhada winsxs.",
            "IIS no VHD (Virtual Hard Disk) offline designado por \\\\server2\\winsxs, que deve conter uma instalação do Windows Server.",
        ],
    },
    {
        "n": 49, "subject": "redes", "topic": "redes-2",
        "statement": "No Kubernetes, a relação ou diferença entre um Deployment e um ReplicaSet é que",
        "options": [
            "enquanto Deployments servem para manter réplicas de Pods ativas, ReplicaSets servem para manter réplicas de Jobs permanentemente ativas.",
            "Deployments executam exclusivamente em ambientes Linux, enquanto ReplicaSets executam em ambientes Windows.",
            "um Deployment é um tipo específico de ReplicaSet com quantidade máxima de réplicas permitidas igual a 1, possuindo um gerenciamento mais fácil para casos de uso mais simples.",
            "o Deployment atua em um nível hierárquico superior, criando e gerenciando ReplicaSets.",
            "um ReplicaSet determina quantas réplicas de um Deployment devem estar ativas em um determinado momento.",
        ],
    },
    {
        "n": 50, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Considere a seguinte definição de um Pod do Kubernetes:\n\n"
            "apiVersion: v1\n"
            "kind: Pod\n"
            "metadata:\n"
            "  name: test-pd\n"
            "spec:\n"
            "  containers:\n"
            "  - image: registry.k8s.io/test-webserver\n"
            "    name: test-container\n"
            "    volumeMounts:\n"
            "    - mountPath: /cache\n"
            "      name: cache-volume\n"
            "  - image: alpine\n"
            "    name: test-container2\n"
            "    volumeMounts:\n"
            "    - mountPath: /app-cache\n"
            "      name: cache-volume\n"
            "  volumes:\n"
            "  - name: cache-volume\n"
            "    emptyDir:\n"
            "      sizeLimit: 500Mi\n\n"
            "Assinale a alternativa correta a respeito."
        ),
        "options": [
            "Cada container no Pod acessa um volume próprio chamado cache-volume, que é independente e isolado dos volumes de mesmo nome dos outros containers do mesmo Pod.",
            "Todos os containers no Pod podem ler e escrever os mesmos arquivos no volume cache-volume.",
            "O volume cache-volume é montado como um sistema de arquivos em memória RAM.",
            "O container test-container enxerga o volume cache-volume na pasta /test-webserver.",
            "O Pod apresentado possui 3 containers: test-container, test-container2 e cache-volume.",
        ],
    },
    {
        "n": 51, "subject": "engenharia-software", "topic": "engenharia-software-2",
        "statement": "A Entrega Contínua (Continuous Delivery) em DevOps propõe que",
        "options": [
            "versões específicas do código-fonte de um software devem existir, de forma separada, para os ambientes de testes, homologação e produção, adequando-se às especificidades e escala de cada um.",
            "todo o código-fonte enviado ao repositório que passa com sucesso pelos builds, testes automatizados e validações estão prontos para implantação em ambiente de produção, mas essa implantação depende de uma decisão humana para ocorrer.",
            "operações de merge em sistemas de controle de versão de código-fonte não podem ser feitas por ferramentas automatizadas, sob o risco de introdução de conflitos que podem passar despercebidos mesmo quando a operação aparenta sucesso.",
            "sejam utilizadas exclusivamente linguagens de programação interpretadas no desenvolvimento de software, eliminando etapas de compilação que existiriam com linguagens compiladas e, assim, promovendo maior continuidade entre o envio de código-fonte para o repositório e a disponibilização do mesmo em ambiente de produção.",
            "os testes unitários sejam a única camada de validação do pipeline, eliminando completamente a necessidade de testes de integração, de aceitação ou testes manuais exploratórios.",
        ],
    },
    {
        "n": 52, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considere o seguinte código JavaScript em uma página HTML:\n\n"
            "<script>\n"
            "mb1 = document.getElementById(\"mb1\");\n"
            "mb1.addEventListener(\"click\",f1);\n"
            "mb1.addEventListener(\"click\",f2);\n"
            "mb1.addEventListener(\"click\",f3);\n"
            "mb1.removeEventListener(\"click\",f3);\n"
            "function f1( ) { console.log(\"a\"); }\n"
            "function f2( ) { console.log(\"b\"); }\n"
            "function f3( ) { console.log(\"c\"); }\n"
            "</script>\n\n"
            "em que mb1 corresponde a um elemento do tipo button declarado da seguinte maneira:\n\n"
            "<button id=\"mb1\">mb1</button>\n\n"
            "Após a carga completa da página, quando o usuário clicar no botão mb1, a saída gerada no console será:"
        ),
        "options": ["a\nb", "nenhuma (saída vazia).", "a", "a\nb\nc", "a\nb\nc\nc"],
    },
    {
        "n": 53, "subject": "desenvolvimento", "topic": "desenvolvimento-2",
        "statement": "O CLR (Common Language Runtime) da plataforma .NET 10",
        "options": [
            "é capaz de executar bytecode Java nativamente.",
            "é capaz de interpretar código-fonte C# diretamente, oferecendo ganho de desempenho por dispensar o uso do compilador Just-In-Time (JIT).",
            "funciona exclusivamente em ambientes Windows, sendo parte do ecossistema da Microsoft.",
            "embora suporte os sistemas operacionais Linux e Windows, não pode ser usado para aplicações web.",
            "está disponível para arquiteturas de máquina x64 e Arm64.",
        ],
    },
    {
        "n": 54, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "A especificação do Jakarta EE (evolução do Java EE e J2EE) que provê suporte para a criação de web "
            "services RESTful é historicamente conhecida como"
        ),
        "options": ["JNDI.", "JAX-WS.", "JAX-RS.", "JAXP.", "JDBC."],
    },
    {
        "n": 55, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": "No contexto de servlets Java, considerando a classe HttpServlet, assinale a alternativa correta.",
        "options": [
            "Toda vez que uma requisição é recebida, com base em seu cabeçalho, o container de servlets deve decidir se chama o método service() ou doPost(), ou um ou outro, para processá-la.",
            "O método init() é chamado toda vez que uma requisição é recebida.",
            "A implementação dos métodos doPut() e doPost() em uma classe derivada de HttpServlet são mutuamente exclusivas, não podendo existir simultaneamente.",
            "A implementação padrão do método doHead() chama o método doGet() internamente.",
            "O método destroy() é chamado toda vez que uma requisição termina de ser processada, e pode ser usado para fechar conexões com banco de dados.",
        ],
    },
    {
        "n": 56, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Em uma aplicação do tipo Minimal API desenvolvida em ASP.Net Core, foi encontrada a seguinte linha de "
            "código, onde builder é um WebApplicationBuilder:\n\n"
            "builder.Services.AddOpenApi();\n\n"
            "A intenção dessa linha de código é"
        ),
        "options": [
            "registrar um serviço de compatibilidade com a linguagem Java, permitindo que seja possível encaminhar automaticamente certas requisições recebidas pela API a contêineres de servlets.",
            "registrar um serviço de geração de documentação no padrão OpenAPI, por meio da extração de metadados dos endpoints.",
            "informar que devem ser aceitas requisições HTTP (sem criptografia) e não devem ser aceitas requisições HTTPS (criptografadas).",
            "inicializar o servidor web que responderá às requisições recebidas pela API, por meio da abertura (open) das portas TCP associadas ao protocolo HTTP e HTTPS (80 e 443 por padrão).",
            "abrir (open) as portas TCP associadas ao protocolo HTTP e HTTPS (80 e 443 por padrão) no firewall do sistema operacional, permitindo que conexões provenientes de outros computadores na rede ou na Internet sejam aceitas.",
        ],
    },
    {
        "n": 57, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considere o seguinte conteúdo em formato XML:\n\n"
            "<raiz>\n"
            "<tag1>XYZ</tag1>\n"
            "<tag2><![CDATA[\n"
            "<p><strong>Link</p></strong><br>\n"
            "<a href=\"https://exemplo.com\">Clique aqui</a>\n"
            "]]>\n"
            "</tag2>\n"
            "</raiz>\n\n"
            "O conteúdo completo apresentado foi enviado para um validador sintático de XML que informa se a entrada "
            "é válida, ou indica o número da linha em que detecta o primeiro erro, sendo que a primeira linha é "
            "considerada a linha de número 1.\n\n"
            "Assinale a alternativa que corresponde ao resultado obtido no validador."
        ),
        "options": [
            "XML válido.",
            "Erro na linha 3.",
            "Erro na linha 4.",
            "Erro na linha 6.",
            "Erro na linha 5.",
        ],
    },
    {
        "n": 58, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considere a seguinte requisição a uma API REST, baseada no protocolo HTTP, que trafega via HTTPS:\n\n"
            "GET /v1/users/123 HTTP/1.1\n"
            "Accept-Encoding: deflate, gzip\n"
            "Authorization: Bearer 3c9d480d62ba89c6d50b34a7dd\n"
            "Host: exemplo.com\n"
            "Accept: application/json\n\n"
            "Assinale a alternativa correta a respeito."
        ),
        "options": [
            "A string 3c9d480d62ba89c6d50b34a7dd corresponde a um token do tipo JWT assinado em sua forma compacta.",
            "A string 3c9d480d62ba89c6d50b34a7dd codifica um usuário e senha, separados por dois-pontos, em Base64.",
            "O cliente informa que suporta receber uma resposta compactada e define os formatos suportados.",
            "O endpoint acessado é application/json dentro do host exemplo.com.",
            "A requisição usa o esquema Basic Auth para autenticação.",
        ],
    },
    {
        "n": 59, "subject": "engenharia-software", "topic": "engenharia-software-1",
        "statement": (
            "No contexto de desenvolvimento de software, como orientação do princípio SOLID conhecido como "
            "Aberto/Fechado (Open/Closed Principle), deve-se"
        ),
        "options": [
            "fazer com que módulos de mais alto nível dependam de módulos de mais baixo nível.",
            "adicionar novas funcionalidades em um software por meio da extensão de suas classes e funções, adicionando código, e não por meio da modificação do código previamente existente.",
            "fazer com que módulos de mais baixo nível dependam de módulos de mais alto nível.",
            "abrir a possibilidade de novos membros ingressarem em um time de desenvolvimento entre um sprint e outro, mas fechar essa possibilidade enquanto o sprint estiver em execução.",
            "construir métodos que suportem trabalhar com objetos de qualquer subtipo da classe esperada como parâmetro, mesmo sem conhecer esses subtipos especificamente.",
        ],
    },
    {
        "n": 60, "subject": "redes", "topic": "redes-2",
        "statement": (
            "Uma empresa (contratante) utiliza um software de gestão empresarial contratado no modelo SaaS, pagando um "
            "valor mensal ao fornecedor (contratada) pelo uso. Embora os detalhes exatos de fornecimento dependam do "
            "contrato firmado, com base nas características desse modelo, é correto presumir que"
        ),
        "options": [
            "do ponto de vista da contratante, a infraestrutura de servidor e banco de dados é on-premises.",
            "outras empresas concorrentes da contratante não utilizam o mesmo software.",
            "a equipe técnica da contratante possui acesso direto ao banco de dados utilizado pela aplicação, via linha de comandos ou aplicativo client específico.",
            "a equipe técnica da contratante possui acesso direto à infraestrutura de computação utilizada, como por exemplo Virtual Private Servers (VPS) que hospedam o servidor de aplicação, por meio de protocolos como SSH ou RDP.",
            "a integração com outras ferramentas e sistemas da contratante pode ser disponibilizada por meio de APIs e Webhooks.",
        ],
    },
    {
        "n": 61, "subject": "redes", "topic": "redes-1",
        "statement": "Provedores de serviços de nuvem costumam oferecer um serviço designado pela sigla VPC. Esse serviço consiste em",
        "options": [
            "uma máquina virtual (Virtual Machine).",
            "um motor de execução de contêineres Docker.",
            "um interpretador de código Python, que permite executar programas escritos nessa linguagem em um ambiente virtual.",
            "uma versão virtual de uma rede física, que oferece recursos de segurança e conectividade.",
            "um PABX virtual baseado no protocolo SIP, que permite criar ramais e números integrados à rede telefônica convencional.",
        ],
    },
    {
        "n": 62, "subject": "seguranca", "topic": "seguranca-2",
        "statement": (
            "Assinale a alternativa que corresponde a uma boa prática de programação segura (secure coding) para "
            "aplicações web, conforme recomendações do OWASP (Open Web Application Security Project)."
        ),
        "options": [
            "O instante (data e hora) do último uso de uma conta de usuário deve ser reportado a esse usuário em seu próximo login bem sucedido.",
            "Enviar identificadores de sessão em parâmetros de URLs, deixando-os visíveis publicamente.",
            "Gerar mensagens de erros e logs visíveis ao usuário bem detalhadas, incluindo detalhes do sistema, versões e identificadores de sessão, possibilitando que eventual problema seja rapidamente entendido e resolvido.",
            "Em código que executa no lado do servidor (server side), não validar as entradas de dados que já foram validadas no cliente por meio de JavaScript, obtendo-se melhor desempenho em relação a sempre validar todas as entradas.",
            "Utilizar o mesmo identificador de sessão em caso de reautenticação do usuário.",
        ],
    },
    {
        "n": 63, "subject": "seguranca", "topic": "seguranca-2",
        "statement": (
            "Programas antivírus contemporâneos devem estar preparados para detectar e intervir contra tipos de "
            "ameaças cada vez mais sofisticadas. Nesse contexto, a técnica de ciberataque conhecida como Process "
            "Hollowing consiste"
        ),
        "options": [
            "na adoção do ícone de um aplicativo legítimo em um executável de malware, enganando o usuário, fazendo-o pensar que se trata de um aplicativo inofensivo e legítimo.",
            "na criação de um processo legítimo suspenso, cujo código original em memória é desalocado e substituído por código malicioso.",
            "no carregamento de uma DLL em memória sem usar a API padrão do sistema operacional Windows (LoadLibrary).",
            "na tradução de código de máquina, em tempo real, de uma arquitetura para outra (ex. x64 para Arm64), para que o malware possa atacar plataformas distintas.",
            "na exclusão deliberada de arquivos DLL ou outras dependências requeridas por programas antivírus, impedindo que os mesmos funcionem.",
        ],
    },
    {
        "n": 64, "subject": "seguranca", "topic": "seguranca-2",
        "statement": (
            "Em um firewall de borda de uma empresa, foi encontrada a seguinte regra:\n"
            "• Bloquear qualquer tráfego destinado às portas UDP/TCP 53 e TCP 853, da LAN para a Internet, exceto se "
            "proveniente de um endereço IP específico.\n\n"
            "Ainda que não cubra 100% das possibilidades para a intenção pretendida, considerando os números das "
            "portas padrões da Internet, é correto afirmar que essa configuração tem a intenção de"
        ),
        "options": [
            "impedir acesso direto a websites externos via protocolo HTTP, liberando apenas o HTTPS, exceto se partir de uma estação de trabalho específica.",
            "bloquear o compartilhamento de arquivos na rede local via protocolo SMB, exceto se compartilhado por um determinado servidor de arquivos.",
            "impedir o uso direto de servidores externos de telefonia baseada no protocolo SIP, permitindo apenas que o PABX digital interno da empresa tenha esse acesso.",
            "funcionar como anti-bypass de DNS Global, permitindo que apenas um servidor DNS interno da empresa efetue consultas a servidores externos.",
            "impedir o funcionamento de servidores DHCP quaisquer dentro da rede, exceto um previamente autorizado.",
        ],
    },
    {
        "n": 65, "subject": "governanca", "topic": "governanca-2",
        "statement": "A Auditoria Baseada em Riscos (Risk-Based Audit) é uma metodologia que",
        "options": [
            "direciona o foco para a conformidade passada, checando se regras históricas foram cumpridas, sem cobrir ameaças futuras ou mudanças no cenário tecnológico.",
            "audita todos os processos com o mesmo nível de profundidade, buscando oferecer tratamento isonômico a todas as áreas.",
            "segue uma lista fixa de verificação de riscos (checklist do tipo sim/não), o que permite acelerar bastante o trabalho do auditor e gerar cronogramas curtos.",
            "define o que será auditado principalmente com base no orçamento disponível e na facilidade de acesso aos dados, o que permite atender budgets bem reduzidos.",
            "direciona o foco, o escopo e a intensidade dos trabalhos do auditor para as áreas de maior risco da organização.",
        ],
    },
    {
        "n": 66, "subject": "governanca", "topic": "governanca-2",
        "statement": "Com relação à Lei Federal nº 14.133/2021, assinale a alternativa correta.",
        "options": [
            "Na contratação que previr a conclusão de escopo predefinido, quando essa conclusão não ocorrer dentro do prazo por culpa do contratado, a Administração não poderá optar pela extinção do contrato até que o contratado entregue o escopo faltante.",
            "Aplica-se às sociedades de economia mista e às suas subsidiárias por completo, inclusive no que tange a normas penais.",
            "Contratos que previrem a operação continuada de sistemas estruturantes de tecnologia da informação poderão ter vigência de 15 anos.",
            "Contratos que tenham por objeto operação de crédito e gestão de dívida pública são subordinados a essa Lei.",
            "Aplica-se a compras, inclusive por encomenda, mas não a locações de bens móveis, como equipamentos de informática.",
        ],
    },
    {
        "n": 67, "subject": "governanca", "topic": "governanca-1",
        "statement": (
            "No contexto do Guia de Boas Práticas em Contratação de Soluções de Tecnologia da Informação – Riscos e "
            "controles para o planejamento da contratação – versão 1.0, assinale a alternativa correta."
        ),
        "options": [
            "As contratações de TI de um órgão podem ser influenciadas pelos planos elaborados pelo órgão governante superior.",
            "Normas relativas à segurança da informação publicadas pelo Gabinete de Segurança Institucional (GSI) não precisam ser observadas no planejamento de outros órgãos governantes.",
            "O único artefato a ser gerado pelo processo de planejamento da contratação de soluções de TI é o plano de trabalho.",
            "Se os artefatos do planejamento da contratação tiverem sido documentados adequadamente pela equipe de planejamento, não há mais necessidade de interação dessa equipe com aquela da gestão do contrato, economizando custos.",
            "Basear a elaboração dos artefatos necessários ao planejamento da contratação em listas de verificação (checklists) não é considerada uma boa prática, haja vista a simplicidade e limitações dessa técnica.",
        ],
    },
    {
        "n": 68, "subject": "governanca", "topic": "governanca-1",
        "statement": (
            "Um Contrato Público para Solução Inovadora (CPSI), no contexto do art. 14 da Lei Complementar nº "
            "182/2021, que é celebrado pela administração pública após a homologação do resultado da licitação, pode "
            "ter valor máximo a ser pago à contratada de"
        ),
        "options": [
            "R$ 800.000,00 por CPSI.",
            "R$ 600.000,00 por CPSI.",
            "R$ 1.200.000,00 por CPSI.",
            "R$ 1.000.000,00 por CPSI.",
            "R$ 1.600.000,00 por CPSI.",
        ],
    },
    {
        "n": 69, "subject": "seguranca", "topic": "seguranca-1",
        "statement": (
            "De acordo com o Decreto Federal nº 10.540/2020, assinale a alternativa que apresenta um mecanismo de "
            "autenticação de usuários explicitamente previsto para o Siafic."
        ),
        "options": [
            "CPF e senha.",
            "E-mail corporativo governamental e senha.",
            "Reconhecimento facial.",
            "Login alfanumérico e senha.",
            "Biometria das mãos.",
        ],
    },
    {
        "n": 70, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": (
            "Considerando a programação orientada a objetos e o conceito de classes, é correto afirmar que, em um "
            "programa que utilize esse tipo de programação,"
        ),
        "options": [
            "cada classe possui uma limitação teórica de comportar até dez objetos.",
            "as classes existentes devem todas serem compostas pelo mesmo tipo de atributos.",
            "as classes existentes devem todas ter o mesmo número de atributos.",
            "não há limitação teórica quanto ao número de classes existentes em um programa.",
            "o nome de cada uma das classes implementadas não pode conter atributos numéricos.",
        ],
    },
    {
        "n": 71, "subject": "desenvolvimento", "topic": "desenvolvimento-1",
        "statement": "O conceito de sobrecarga presente na orientação a objetos significa, especificamente, que",
        "options": [
            "uma mesma classe não pode ter o mesmo tipo de parâmetros em quaisquer dois de seus métodos.",
            "os métodos de uma mesma classe podem ter o mesmo nome, porém esses métodos devem possuir assinaturas diferentes.",
            "o número de métodos declarados em cada classe possui uma limitação teórica de até vinte métodos.",
            "duas ou mais classes podem possuir o mesmo nome.",
            "uma mesma classe não pode possuir mais de um método com o mesmo número de parâmetros.",
        ],
    },
    {
        "n": 72, "subject": "banco-dados", "topic": "banco-dados-2",
        "statement": (
            "Considere a seguinte tabela de um banco de dados relacional:\n\n"
            "Escritório (Número, Tipo, Andar, Fone)   [Número é a chave primária]\n\n"
            "A consulta do PL/SQL para obter a quantidade de escritórios do tipo ‘Sala de Reunião’ é:"
        ),
        "options": [
            "SELECT SUM(Tipo)\nFROM Escritório\nWHERE Tipo = ‘Sala de Reunião’;",
            "SELECT COUNT(‘Sala de Reunião’)\nFROM Escritório;",
            "SELECT COUNT(Tipo)\nFROM Escritório\nWHERE Tipo = ‘Sala de Reunião’;",
            "SELECT COUNT(Tipo=’Sala de Reunião’)\nFROM Escritório;",
            "SELECT SUM(Tipo: ‘Sala de Reunião’)\nFROM Escritório;",
        ],
    },
    {
        "n": 73, "subject": "banco-dados", "topic": "banco-dados-2",
        "statement": (
            "Considere a seguinte tabela de um banco de dados relacional:\n\n"
            "Aluno (ID, Nome, Sala)   [ID é a chave primária]\n\n"
            "A consulta do PL/SQL para obter o nome dos alunos que comecem com a letra M é:"
        ),
        "options": [
            "SELECT Nome\nFROM Aluno\nWHERE Nome LIKE ‘M%’;",
            "SELECT Nome\nFROM Aluno (‘M%’);",
            "SELECT Nome\nFROM Aluno\nWHERE Nome EQUAL ‘M%’;",
            "SELECT Aluno.Nome\nWHERE Nome = ‘M%’;",
            "SELECT Nome\nFROM Aluno\nWHERE Nome IN ‘M%’;",
        ],
    },
    {
        "n": 74, "subject": "engenharia-software", "topic": "engenharia-software-1",
        "statement": "O BPMN (Business Process Model and Notation) versão 2.0 define os seguintes três tipos de processos:",
        "options": [
            "Normativo, Estratégico e Explicativo.",
            "Estratégico, Normativo e Operacional.",
            "Operacional, Explicativo e Estratégico.",
            "Normativo, Operacional e Explicativo.",
            "Privado Não Executável, Privado Executável e Público.",
        ],
    },
    {
        "n": 75, "subject": "engenharia-software", "topic": "engenharia-software-1",
        "statement": (
            "Considere os seguintes tipos de gateway utilizados pela notação do BPMN (Business Process Model and "
            "Notation) versão 2.0:\n"
            "(a) um losango com um “X” em seu interior;\n"
            "(b) um losango com um “+” em seu interior.\n\n"
            "Esses elementos representam, correta e respectivamente, os símbolos de gateway dos tipos:"
        ),
        "options": [
            "(a) Direto, (b) Invertido.",
            "(a) Temporário, (b) Permanente.",
            "(a) Exclusivo, (b) Paralelo.",
            "(a) Inclusivo, (b) Complexo.",
            "(a) Simples, (b) Padrão.",
        ],
    },
    {
        "n": 76, "subject": "governanca", "topic": "governanca-2",
        "statement": (
            "O ITIL v.4 define a Cadeia de Valor de Serviço. Essa cadeia é composta por seis atividades, sendo "
            "correto afirmar que, especificamente, duas dessas atividades são:"
        ),
        "options": [
            "reunir e distribuir.",
            "contratar e supervisionar.",
            "especificar e documentar.",
            "planejar e engajar.",
            "precificar e finalizar.",
        ],
    },
    {
        "n": 77, "subject": "governanca", "topic": "governanca-2",
        "statement": (
            "O modelo de melhoria contínua do ITIL v.4 define algumas práticas e tipos de gerenciamento incluídos em "
            "cada prática, sendo correto afirmar que o Gerenciamento de"
        ),
        "options": [
            "Implantação está incluído nas Práticas de Gerenciamento Técnico.",
            "Arquitetura está incluído nas Práticas de Gerenciamento Técnico.",
            "Conhecimento está incluído nas Práticas de Gerenciamento de Serviço.",
            "Disponibilidade está incluído nas Práticas Gerais de Gerenciamento.",
            "Nível de Serviço está incluído nas Práticas Gerais de Gerenciamento.",
        ],
    },
    {
        "n": 78, "subject": "governanca", "topic": "governanca-1",
        "statement": (
            "O PMBOK 7ª edição define oito domínios de desempenho de projetos, sendo correto afirmar que, "
            "especificamente, dois desses domínios são:"
        ),
        "options": [
            "Orçamento e Finalização.",
            "Preparação e Iniciação.",
            "Agendamento e Simulação.",
            "Inclusão e Distribuição.",
            "Equipe e Planejamento.",
        ],
    },
    {
        "n": 79, "subject": "banco-dados", "topic": "banco-dados-1",
        "statement": (
            "Ao se proceder ao processo de normalização das tabelas de um banco de dados relacional, obtém-se como "
            "efeito principal dessa operação a"
        ),
        "options": [
            "reunião de todos atributos de todas tabelas em uma única tabela.",
            "redução, ou mesmo eliminação, de redundâncias desnecessárias que possam estar presentes nessas tabelas.",
            "eliminação de atributos do tipo data dessas tabelas.",
            "inserção de um tipo de atributo especial nessas tabelas, denominado atributo normal.",
            "eliminação de todas chaves estrangeiras presentes nas tabelas.",
        ],
    },
    {
        "n": 80, "subject": "banco-dados", "topic": "banco-dados-1",
        "statement": "Considerando os processos conhecidos pelas siglas ETL e ELT, é correto afirmar que",
        "options": [
            "no processo ETL a fase de transformação dos dados é feita anteriormente à fase de carga dos dados.",
            "no processo ELT a fase de transformação é substituída pela fase de temporização.",
            "em ambos os processos, ELT e ETL, a fase de carga é feita após a realização da fase de transformação dos dados.",
            "em ambos os processos, ELT e ETL, a última fase do ciclo consiste na extração dos dados.",
            "no processo ELT a fase de transformação dos dados é feita em sequência à fase de carga dos dados.",
        ],
    },
]
