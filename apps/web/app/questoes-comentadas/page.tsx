import type { Metadata } from "next";
import Link from "next/link";
import { PubNav, PubFooter } from "../_seo/chrome";

export const revalidate = 3600;
const SERVER_API = "http://127.0.0.1:9000/api/v1";
const URL = "https://passafacil.jussa.com.br/questoes-comentadas";

export const metadata: Metadata = {
  title: "Questões Comentadas VUNESP — TCE-SP 2026 (amostra grátis)",
  description:
    "Amostra grátis de questões comentadas no estilo VUNESP para o concurso TCE-SP 2026, com gabarito, explicação e mini-aula em cada questão: Português, Raciocínio Lógico, Legislação e específicas de TI.",
  alternates: { canonical: URL },
  openGraph: {
    type: "article",
    url: URL,
    title: "Questões Comentadas VUNESP — TCE-SP 2026 (amostra grátis)",
    description:
      "Questões no estilo VUNESP para o TCE-SP 2026 com gabarito, explicação e mini-aula. Faça a amostra grátis.",
  },
};

type Q = {
  id: string;
  statement: string;
  options: string[];
  correct_option: number;
  explanation: string;
  micro_aula?: string | null;
  topic: string;
  subject: string;
};

async function getQuestions(): Promise<Q[]> {
  try {
    const res = await fetch(`${SERVER_API}/study/trial/full`, { next: { revalidate: 3600 } });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function Page() {
  const questions = await getQuestions();
  return (
    <>
      <PubNav />
      <main className="pub">
        <h1>Questões comentadas VUNESP para o TCE-SP 2026</h1>
        <p className="lead">
          Amostra grátis de questões no estilo da banca <strong>VUNESP</strong> para o concurso do{" "}
          <strong>Tribunal de Contas do Estado de São Paulo (TCE-SP) 2026</strong>, cargo de Auditor de
          Controle Externo. Cada questão traz o <strong>gabarito</strong>, a <strong>explicação</strong>{" "}
          e uma <strong>mini-aula</strong> que ensina o conteúdo — para você acertar mesmo que a pergunta
          mude na prova.
        </p>

        {questions.length === 0 ? (
          <p>As questões de amostra estão sendo carregadas. Enquanto isso, <Link href="/">faça o teste grátis no app</Link>.</p>
        ) : (
          questions.map((q, index) => (
            <article className="pub-q" key={q.id}>
              <div className="q-meta">{q.subject} <i>· {q.topic}</i></div>
              <div className="q-statement">{index + 1}. {q.statement}</div>
              {q.options.map((option, optionIndex) => (
                <div key={optionIndex} className={`pub-opt ${optionIndex === q.correct_option ? "correct" : ""}`}>
                  <b>{String.fromCharCode(65 + optionIndex)})</b> {option}
                </div>
              ))}
              <p className="pub-answer">✓ Resposta correta: {String.fromCharCode(65 + q.correct_option)}</p>
              <div className="pub-expl"><span className="lbl">Por quê</span>{q.explanation}</div>
              {q.micro_aula && <div className="pub-micro"><span className="lbl">Micro aula</span>{q.micro_aula}</div>}
            </article>
          ))
        )}

        <div className="cta-box">
          <h3>Quer centenas de questões como essas?</h3>
          <p>Todas as matérias do TCE-SP 2026, com correção imediata e mini-aula. Pagamento único, acesso vitalício.</p>
          <Link href="/">Criar conta e fazer o simulado</Link>
        </div>

        <h2>Por que estudar com questões comentadas</h2>
        <p>
          Resolver <strong>questões comentadas</strong> é a forma mais eficiente de se preparar para
          concursos da <strong>VUNESP</strong>: você aprende o conteúdo no contexto em que ele é cobrado,
          entende o porquê de cada alternativa e fixa os pontos que a banca costuma repetir. No Passa
          Fácil, além da explicação, cada questão tem uma <strong>mini-aula</strong> que resume o tema —
          ideal para revisar rápido antes da prova do TCE-SP 2026.
        </p>
        <h2>Matérias do concurso TCE-SP 2026</h2>
        <p>
          O banco de questões cobre as <strong>disciplinas gerais</strong> (Português, Raciocínio Lógico,
          Ética e Legislação/Controle Externo) e as <strong>específicas de Tecnologia da Informação</strong>{" "}
          (Segurança da Informação, Redes, Banco de Dados, Desenvolvimento, Engenharia de Software,
          Governança de TI, LGPD, Infraestrutura, Contêineres e Contratações de TI). Veja também o{" "}
          <Link href="/edital-tce-sp-2026">guia do edital TCE-SP 2026</Link>.
        </p>
      </main>
      <PubFooter />
    </>
  );
}
