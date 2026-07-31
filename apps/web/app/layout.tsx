import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Passa Fácil — Seu plano de aprovação",
  description: "Estudo adaptativo para concursos, começando pelo TCE-SP 2026.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
