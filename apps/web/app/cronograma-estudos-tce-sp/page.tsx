import type { Metadata } from "next";
import Link from "next/link";
import { PubNav, PubFooter } from "../_seo/chrome";

const URL = "https://passafacil.jussa.com.br/cronograma-estudos-tce-sp";

export const metadata: Metadata = {
  title: "Cronograma de Estudos para o TCE-SP 2026 (especialidade TI)",
  description:
    "Um cronograma de estudos prático para o concurso TCE-SP 2026 (VUNESP), especialidade Tecnologia da Informação: como dividir a semana entre Português, Raciocínio Lógico, legislação e as matérias de TI.",
  alternates: { canonical: URL },
  openGraph: { type: "article", url: URL, title: "Cronograma de estudos para o TCE-SP 2026", description: "Como organizar a semana de estudos para o concurso TCE-SP 2026 (TI)." },
};

export default function Page() {
  return (
    <>
      <PubNav />
      <main className="pub">
        <h1>Cronograma de estudos para o TCE-SP 2026 (especialidade TI)</h1>
        <p className="lead">
          Um modelo de <strong>cronograma de estudos</strong> para o concurso do <strong>TCE-SP 2026</strong>{" "}
          (banca VUNESP), pensado para quem concilia trabalho e estudos e vai disputar a vaga de{" "}
          Auditor de Controle Externo — Tecnologia da Informação. Adapte às suas horas disponíveis.
        </p>

        <h2>Princípio: mais tempo para o que vale mais pontos</h2>
        <p>
          Como as específicas de TI somam 60 das 80 questões, elas devem ocupar a maior fatia da semana.
          Reserve blocos fixos para Português (que sozinho vale 12 questões) e um tempo menor para Raciocínio
          Lógico, Ética e Legislação. Entenda a divisão no{" "}
          <Link href="/edital-tce-sp-2026">guia do edital</Link>.
        </p>

        <h2>Exemplo de semana (ajuste ao seu tempo)</h2>
        <ul>
          <li><strong>Segunda:</strong> TI — Segurança da Informação + 20 questões comentadas.</li>
          <li><strong>Terça:</strong> TI — Redes/Infraestrutura + Português (interpretação).</li>
          <li><strong>Quarta:</strong> TI — Banco de Dados + Raciocínio Lógico.</li>
          <li><strong>Quinta:</strong> TI — Desenvolvimento/Engenharia de Software + Português (gramática).</li>
          <li><strong>Sexta:</strong> TI — Governança/ITIL/COBIT + Legislação e Ética.</li>
          <li><strong>Sábado:</strong> Simulado geral (intercalando matérias) + correção dos erros.</li>
          <li><strong>Domingo:</strong> Revisão dos erros da semana + treino de estudo de caso.</li>
        </ul>

        <h2>Rotina diária que funciona</h2>
        <p>
          Comece revisando rapidamente o que errou nos dias anteriores, estude o tópico do dia por teoria
          curta e vá direto para <Link href="/questoes-comentadas">questões comentadas</Link>. Fechar o dia
          resolvendo questões fixa muito mais do que só ler.
        </p>

        <div className="cta-box">
          <h3>Coloque o cronograma em prática</h3>
          <p>No Passa Fácil você pratica todas as matérias com correção imediata, mini-aula, revisões e caderno de erros.</p>
          <Link href="/">Começar com o teste grátis</Link>
        </div>

        <p>
          Veja também: <Link href="/como-passar-tce-sp">como passar no TCE-SP 2026</Link> e{" "}
          <Link href="/questoes-comentadas">questões comentadas VUNESP</Link>.
        </p>
      </main>
      <PubFooter />
    </>
  );
}
