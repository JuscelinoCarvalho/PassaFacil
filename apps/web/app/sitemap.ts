import type { MetadataRoute } from "next";

const SITE_URL = "https://passafacil.jussa.com.br";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: SITE_URL, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE_URL}/questoes-comentadas`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE_URL}/edital-tce-sp-2026`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/como-passar-tce-sp`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/cronograma-estudos-tce-sp`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
  ];
}
