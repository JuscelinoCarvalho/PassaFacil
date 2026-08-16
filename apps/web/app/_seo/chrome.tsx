import Link from "next/link";
import { Sparkles } from "lucide-react";

export function PubNav() {
  return (
    <nav className="pub-nav">
      <Link href="/" className="brand-link"><Sparkles size={20} /> Passa Fácil</Link>
      <div className="nav-links">
        <Link href="/questoes-comentadas">Questões comentadas</Link>
        <Link href="/edital-tce-sp-2026">Edital 2026</Link>
        <Link href="/como-passar-tce-sp">Como passar</Link>
        <Link href="/" className="cta">Entrar / Criar conta</Link>
      </div>
    </nav>
  );
}

export function PubFooter() {
  return (
    <footer className="pub-foot">
      Passa Fácil · Simulados e questões comentadas para o concurso TCE-SP 2026 ·{" "}
      <Link href="/">Fazer o teste grátis</Link>
    </footer>
  );
}
