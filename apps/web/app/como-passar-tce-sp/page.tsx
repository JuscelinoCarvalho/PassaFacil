import type { Metadata } from "next";
import Link from "next/link";
import { PubNav, PubFooter } from "../_seo/chrome";

const URL = "https://passafacil.jussa.com.br/como-passar-tce-sp";

export const metadata: Metadata = {
  title: "Como Passar no Concurso TCE-SP 2026 (Auditor de Controle Externo — TI)",
  description:
    "Estratégia de estudo para passar no concurso TCE-SP 2026 (VUNESP): onde focar, como distribuir o tempo entre Português e as específicas de TI, uso de questões comentadas, revisão e a prova de estudo de caso.",
  alternates: { canonical: URL },
  openGraph: { type: "article", url: URL, title: "Como passar no concurso TCE-SP 2026", description: "Estratégia prática de estudo para o TCE-SP 2026 (TI), banca VUNESP." },
};

export default function Page() {
  return (
    <>
      <PubNav />
      <main className="pub">
        <h1>Como passar no concurso TCE-SP 2026 (Auditor de Controle Externo — TI)</h1>
        <p className="lead">
          Passar em um concurso do <strong>TCE-SP</strong> exige método, não só horas de estudo. Abaixo, uma
          estratégia prática para a prova de 2026 (banca <strong>VUNESP</strong>), pensada para quem vai
          disputar a especialidade de <strong>Tecnologia da Informação</strong>.
        </p>

        <h2>1. Priorize onde estão os pontos</h2>
        <p>
          A prova objetiva tem <strong>60 questões de TI</strong> e <strong>20 de conhecimentos gerais</strong>.
          O maior peso está nas específicas — então a maior parte do seu tempo deve ir para elas. Entre as
          gerais, o <strong>Português vale 12 questões</strong> (mais que o dobro das outras somadas): não dá
          para abandoná-lo. Veja a divisão completa no{" "}
          <Link href="/edital-tce-sp-2026">guia do edital TCE-SP 2026</Link>.
        </p>

        <h2>2. Estude por questões, não só por teoria</h2>
        <p>
          A forma mais rápida de aprender o que a VUNESP cobra é resolvendo{" "}
          <Link href="/questoes-comentadas">questões comentadas</Link>. Cada questão mostra o padrão da banca,
          e a correção com explicação fixa o conteúdo. Erros viram material de revisão.
        </p>

        <h2>3. Use revisão espaçada</h2>
        <p>
          Revisar no intervalo certo é o que transforma o estudo em memória de longo prazo. Marque o que
          errou e volte nesses pontos com frequência crescente — é assim que o conteúdo "gruda" até o dia da
          prova.
        </p>

        <h2>4. Treine a prova de estudo de caso</h2>
        <p>
          Além da objetiva, o TCE-SP cobra uma <strong>prova escrita (estudo de caso)</strong> com peso alto e
          nota mínima. Pratique estruturar respostas técnicas: contextualize, aponte a solução correta e
          justifique com base em normas e boas práticas.
        </p>

        <h2>5. Simule as condições da prova</h2>
        <p>
          Faça simulados intercalando as matérias, como na prova real. Isso treina ritmo, foco e o rodízio
          entre assuntos — e mostra, com dados, onde você ainda precisa melhorar.
        </p>

        <div className="cta-box">
          <h3>Comece agora, de graça</h3>
          <p>Faça uma amostra de questões comentadas e sinta o método. Depois, libere o acesso completo com pagamento único.</p>
          <Link href="/">Fazer o teste grátis</Link>
        </div>

        <p>
          Veja também: <Link href="/cronograma-estudos-tce-sp">cronograma de estudos para o TCE-SP 2026</Link>{" "}
          e o <Link href="/edital-tce-sp-2026">guia do edital</Link>.
        </p>
      </main>
      <PubFooter />
    </>
  );
}
