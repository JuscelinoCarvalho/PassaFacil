import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import HelpWidget from "./_components/HelpWidget";
import OfflineBanner from "./_components/OfflineBanner";
import PwaUpdater from "./_components/PwaUpdater";

const SITE_URL = "https://passafacil.jussa.com.br";
// Google Ads (gtag.js) — medição de conversões. ID da conta AW-975500543.
const GADS_ID = "AW-975500543";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Passa Fácil — Simulados e Questões Comentadas para Concursos (TCE-SP 2026)",
    template: "%s | Passa Fácil",
  },
  description:
    "Plataforma de estudo para concursos com simulados, questões comentadas no estilo VUNESP e micro aulas. Prepare-se para o TCE-SP 2026 (Auditor de Controle Externo — TI e Conhecimentos Gerais) com correção imediata, explicação e mini-aula em cada questão.",
  keywords: [
    "concurso TCE-SP 2026",
    "simulado TCE-SP",
    "questões VUNESP",
    "questões comentadas VUNESP",
    "Auditor de Controle Externo",
    "concurso TCE-SP TI",
    "simulado concurso público",
    "banco de questões TCE-SP",
    "estudar para concurso TCE-SP",
    "preparatório TCE-SP",
    "questões comentadas concurso",
    "Passa Fácil",
  ],
  authors: [{ name: "Passa Fácil" }],
  creator: "Passa Fácil",
  publisher: "Passa Fácil",
  applicationName: "Passa Fácil",
  category: "education",
  alternates: { canonical: SITE_URL },
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Passa Fácil",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/icons/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: SITE_URL,
    siteName: "Passa Fácil",
    title: "Passa Fácil — Simulados e Questões Comentadas para o TCE-SP 2026",
    description:
      "Simulados e questões comentadas no estilo VUNESP para o concurso TCE-SP 2026, com correção imediata e mini-aula em cada questão. Faça um teste grátis.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Passa Fácil — Simulados e Questões Comentadas (TCE-SP 2026)",
    description:
      "Estude para o TCE-SP 2026 com simulados e questões comentadas no estilo VUNESP. Correção imediata e mini-aula. Teste grátis.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  // Para o Google Search Console: peça ao dev para preencher o token aqui,
  // OU (mais fácil) verifique via registro DNS TXT no Cloudflare.
  // verification: { google: "SEU_TOKEN_DO_SEARCH_CONSOLE" },
};

export const viewport: Viewport = {
  themeColor: "#5f40dd",
  // Ocupa a tela toda quando instalado como app (atrás do "notch" no iOS).
  viewportFit: "cover",
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: "Passa Fácil",
      inLanguage: "pt-BR",
      description:
        "Simulados e questões comentadas para concursos, com correção imediata e mini-aula.",
    },
    {
      "@type": "EducationalOrganization",
      "@id": `${SITE_URL}/#org`,
      name: "Passa Fácil",
      url: SITE_URL,
      description:
        "Plataforma de estudo para concursos públicos com simulados e questões comentadas no estilo VUNESP.",
    },
    {
      "@type": "Course",
      name: "Preparatório TCE-SP 2026 — Auditor de Controle Externo (TI e Conhecimentos Gerais)",
      description:
        "Banco de questões comentadas e simulados para o concurso do Tribunal de Contas do Estado de São Paulo (TCE-SP) 2026, cobrindo Português, Raciocínio Lógico, Legislação, Ética e as específicas de Tecnologia da Informação.",
      inLanguage: "pt-BR",
      provider: { "@id": `${SITE_URL}/#org` },
      offers: {
        "@type": "Offer",
        category: "Preparação para concurso",
        priceCurrency: "BRL",
        price: "0",
      },
    },
    {
      "@type": "FAQPage",
      mainEntity: [
        {
          "@type": "Question",
          name: "O Passa Fácil tem simulado para o concurso TCE-SP 2026?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Sim. O Passa Fácil oferece simulados e centenas de questões comentadas no estilo VUNESP para o TCE-SP 2026 (Auditor de Controle Externo), com correção imediata e mini-aula em cada questão.",
          },
        },
        {
          "@type": "Question",
          name: "As questões são comentadas?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Sim. Cada questão traz a resposta correta, uma explicação do porquê e uma mini-aula que ensina o conteúdo, para você acertar mesmo que a pergunta mude.",
          },
        },
        {
          "@type": "Question",
          name: "O acesso é pago?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "No momento o acesso está liberado gratuitamente enquanto a plataforma evolui. Basta criar uma conta para usar tudo — simulados, questões comentadas e correção imediata.",
          },
        },
        {
          "@type": "Question",
          name: "Quais matérias estão cobertas?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Português, Raciocínio Lógico, Legislação e Ética, além das específicas de TI: Segurança da Informação, Redes, Banco de Dados, Desenvolvimento, Engenharia de Software, Governança, LGPD, Infraestrutura e Contratações de TI.",
          },
        },
      ],
    },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <PwaUpdater />
        <OfflineBanner />
        {/* Google tag (gtag.js) — Google Ads / conversões */}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GADS_ID}`}
          strategy="afterInteractive"
        />
        <Script id="gtag-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GADS_ID}');
          `}
        </Script>
        {children}
        <footer className="seo-footer" aria-label="Sobre o Passa Fácil">
          <div className="seo-footer-inner">
            <h2>Simulados e questões comentadas para o concurso TCE-SP 2026</h2>
            <p>
              O <strong>Passa Fácil</strong> é uma plataforma de estudo para concursos públicos com{" "}
              <strong>simulados</strong> e <strong>questões comentadas no estilo VUNESP</strong>. Cada
              questão tem <strong>correção imediata</strong>, explicação da resposta e uma{" "}
              <strong>mini-aula</strong> que ensina o conteúdo — ideal para quem vai prestar o concurso
              do <strong>Tribunal de Contas do Estado de São Paulo (TCE-SP) 2026</strong>, cargo de
              Auditor de Controle Externo (Conhecimentos Gerais e especialidade de Tecnologia da
              Informação).
            </p>
            <h3>Matérias cobertas</h3>
            <p>
              Português (interpretação, gramática, crase, concordância), Raciocínio Lógico, Legislação
              e Ética (LC 709/93, Regimento Interno do TCE-SP, arts. 70–75 da CF, Lei 10.261/68) e as
              específicas de TI: Segurança da Informação, Redes, Banco de Dados, Desenvolvimento,
              Engenharia de Software, Governança (ITIL, COBIT, PMBOK), LGPD, Infraestrutura,
              Containers/Docker/Kubernetes e Contratações de TI (Lei 14.133, Lei 13.303).
            </p>
            <h3>Perguntas frequentes</h3>
            <p>
              <strong>O acesso é pago?</strong> No momento não — o acesso está liberado gratuitamente
              enquanto a plataforma evolui; basta criar uma conta.{" "}
              <strong>As questões são comentadas?</strong> Sim, todas trazem explicação e mini-aula.
            </p>
            <p>
              Veja também: <a href="/questoes-comentadas">questões comentadas VUNESP (amostra grátis)</a>{" "}
              e o <a href="/edital-tce-sp-2026">guia do edital TCE-SP 2026</a>.
            </p>
            <p className="seo-footer-copy">
              Passa Fácil · Estudo para concursos · TCE-SP 2026
            </p>
          </div>
        </footer>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <HelpWidget />
      </body>
    </html>
  );
}
