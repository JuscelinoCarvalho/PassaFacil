import type { MetadataRoute } from "next";

/**
 * Manifest do PWA — é o que torna o Passa Fácil "instalável" no celular
 * (Adicionar à tela de início, no Android e no iOS). Servido em /manifest.webmanifest.
 * O app NÃO empacota o código: ele carrega o site ao vivo, então toda vez que
 * abre já pega a última versão publicada (ver sw.js + PwaUpdater).
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Passa Fácil — Concursos",
    short_name: "Passa Fácil",
    description:
      "Simulados e questões comentadas para concursos, com correção imediata e mini-aula em cada questão.",
    id: "/",
    start_url: "/?source=pwa",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#191b28",
    theme_color: "#5f40dd",
    lang: "pt-BR",
    dir: "ltr",
    categories: ["education"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
