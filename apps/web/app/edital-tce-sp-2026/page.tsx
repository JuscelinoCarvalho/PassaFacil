import type { Metadata } from "next";
import Link from "next/link";
import { PubNav, PubFooter } from "../_seo/chrome";

const URL = "https://passafacil.jussa.com.br/edital-tce-sp-2026";

export const metadata: Metadata = {
  title: "Edital TCE-SP 2026: Guia do Concurso (Auditor de Controle Externo — TI)",
  description:
    "Guia do concurso TCE-SP 2026: cargo de Auditor de Controle Externo (Tecnologia da Informação), banca VUNESP, estrutura da prova (20 gerais + 60 de TI + estudo de caso) e todas as matérias. Estude com simulados e questões comentadas.",
  alternates: { canonical: URL },
  openGraph: {
    type: "article",
    url: URL,
    title: "Edital TCE-SP 2026: Guia do Concurso (Auditor de Controle Externo — TI)",
    description:
      "Estrutura da prova, matérias e como estudar para o concurso do TCE-SP 2026 (especialidade TI), banca VUNESP.",
  },
};

export default function Page() {
  return (
    <>
      <PubNav />
      <main className="pub">
        <h1>Edital TCE-SP 2026: guia do concurso de Auditor de Controle Externo (TI)</h1>
        <p className="lead">
          Um resumo prático do concurso do <strong>Tribunal de Contas do Estado de São Paulo (TCE-SP)</strong>{" "}
          para o cargo de <strong>Auditor de Controle Externo</strong>, especialidade{" "}
          <strong>Tecnologia da Informação</strong>, organizado pela banca <strong>VUNESP</strong> — com a
          estrutura da prova, as matérias cobradas e uma sugestão de como estudar.
        </p>

        <h2>Sobre o concurso</h2>
        <ul>
          <li><strong>Órgão:</strong> Tribunal de Contas do Estado de São Paulo (TCE-SP).</li>
          <li><strong>Cargo:</strong> Auditor de Controle Externo — especialidade Tecnologia da Informação.</li>
          <li><strong>Banca:</strong> VUNESP.</li>
          <li><strong>Prova objetiva:</strong> prevista para <strong>11 de outubro de 2026</strong>, em São Paulo.</li>
          <li><strong>Escolaridade:</strong> nível superior.</li>
        </ul>

        <h2>Como é a prova</h2>
        <p>
          A seleção tem uma <strong>prova objetiva</strong> e uma <strong>prova escrita (estudo de caso)</strong>.
          A objetiva combina <strong>20 questões de Conhecimentos Gerais</strong> e{" "}
          <strong>60 questões específicas de Tecnologia da Informação</strong> — ou seja, o peso está fortemente
          nas específicas de TI. A prova escrita cobra a produção de estudo(s) de caso, com nota mínima de corte.
        </p>

        <h2>Conhecimentos Gerais (20 questões)</h2>
        <p>Segundo o edital, a distribuição das gerais dá grande peso ao Português:</p>
        <ul>
          <li><strong>Língua Portuguesa (12 questões):</strong> interpretação de texto, classes de palavras,
            concordância e regência, colocação pronominal, crase, pontuação e vocabulário.</li>
          <li><strong>Raciocínio Lógico-Matemático (4 questões):</strong> proposições e conectivos,
            equivalências e negações, quantificadores, sequências e problemas.</li>
          <li><strong>Ética no Serviço Público (2 questões):</strong> Código de Ética do TCE-SP, conflito de
            interesses, integridade e compliance no setor público.</li>
          <li><strong>Legislação / Controle Externo (2 questões):</strong> Lei Orgânica e Regimento Interno do
            TCE-SP (LC 709/93), arts. 70 a 75 da Constituição Federal e normas correlatas.</li>
        </ul>

        <h2>Conhecimentos Específicos de TI (60 questões)</h2>
        <p>O conteúdo de tecnologia é extenso. Os principais blocos são:</p>
        <ul>
          <li><strong>Sistemas operacionais, virtualização e nuvem</strong> (Linux, Windows Server, VMware, IaaS/PaaS/SaaS).</li>
          <li><strong>Contêineres e DevOps</strong> (Docker, Kubernetes, CI/CD).</li>
          <li><strong>Redes de computadores</strong> (TCP/IP, roteamento, protocolos, segurança de rede).</li>
          <li><strong>Banco de dados</strong> (modelagem, normalização, SQL, transações, NoSQL, Big Data/ETL).</li>
          <li><strong>Desenvolvimento e engenharia de software</strong> (POO, padrões, UML, ágil, testes, APIs REST, SOLID).</li>
          <li><strong>Segurança da informação</strong> (CID, criptografia, ISO 27001/27002, gestão de vulnerabilidades).</li>
          <li><strong>Governança e gestão de TI</strong> (ITIL v4, COBIT, PMBOK 7, ISO 20000).</li>
          <li><strong>LGPD e legislação de TI</strong> (Lei 13.709, Lei de Acesso à Informação, Lei do Software).</li>
          <li><strong>Contratações de TI</strong> (Lei 14.133, Lei 13.303, IN SGD/ME 94/2022).</li>
          <li><strong>Inteligência artificial</strong> (conceitos de ML, LLMs, prompt engineering).</li>
        </ul>

        <div className="cta-box">
          <h3>Estude com simulados e questões comentadas</h3>
          <p>Pratique todas essas matérias no estilo VUNESP, com correção imediata e mini-aula. Comece pela amostra grátis.</p>
          <Link href="/">Fazer o teste grátis</Link>
        </div>

        <h2>Como se preparar para o TCE-SP 2026</h2>
        <p>
          Como o peso está nas específicas de TI, concentre a maior parte do tempo nelas — mas não abandone o
          Português, que sozinho vale 12 das 20 questões gerais. A prática constante de{" "}
          <Link href="/questoes-comentadas">questões comentadas da VUNESP</Link> ajuda a fixar o conteúdo e a
          reconhecer os padrões da banca. Reserve também um tempo para treinar a{" "}
          <strong>prova escrita (estudo de caso)</strong>, que tem peso alto na nota final.
        </p>
        <p>
          O <strong>Passa Fácil</strong> reúne centenas de questões de todas as matérias do concurso, com
          correção imediata, explicação e mini-aula em cada uma — além de simulado, revisões e caderno de erros.{" "}
          <Link href="/">Crie sua conta</Link> e comece hoje.
        </p>
      </main>
      <PubFooter />
    </>
  );
}
