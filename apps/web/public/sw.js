/*
 * Service worker do Passa Fácil (PWA instalável no celular).
 *
 * Objetivo nº1: SEMPRE carregar a última versão publicada ao abrir o app.
 * Por isso a navegação (o HTML da página) é NETWORK-FIRST: com internet, busca
 * sempre o servidor; o cache só entra como rede de segurança quando está offline.
 * Os assets do Next (/_next/static/*) têm hash no nome, então cache-first neles
 * é seguro — quando sai deploy novo, os nomes mudam e o navegador baixa os novos.
 *
 * Nunca intercepta chamadas de API (/api/*) nem outros domínios (gtag): essas
 * passam direto, sem cache, pra não quebrar login/dados dinâmicos.
 */
const CACHE = "passafacil-v1";
const OFFLINE_URL = "/";

self.addEventListener("install", (event) => {
  // Assume o controle imediatamente — não espera a aba antiga fechar.
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then((c) => c.add(OFFLINE_URL)).catch(() => {})
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // Limpa caches de versões antigas do SW.
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

// Permite que a página peça ativação imediata do SW novo.
self.addEventListener("message", (event) => {
  if (event.data === "SKIP_WAITING") self.skipWaiting();
});

function isStaticAsset(url) {
  return (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    /\.(?:js|css|woff2?|png|jpg|jpeg|svg|gif|ico|webp)$/.test(url.pathname)
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return; // POST/PUT etc. passam direto

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // gtag e outros domínios
  if (url.pathname.startsWith("/api/")) return; // API nunca é cacheada

  // Assets imutáveis (hash no nome): cache-first, rápido e seguro.
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        if (hit) return hit;
        const res = await fetch(req);
        if (res.ok) cache.put(req, res.clone());
        return res;
      })
    );
    return;
  }

  // Navegação (HTML) e o resto: NETWORK-FIRST — sempre a versão mais nova.
  event.respondWith(
    (async () => {
      try {
        const res = await fetch(req);
        if (res.ok && req.mode === "navigate") {
          const cache = await caches.open(CACHE);
          cache.put(OFFLINE_URL, res.clone()); // atualiza a rede de segurança
        }
        return res;
      } catch {
        // Sem internet: devolve o último HTML que deu certo.
        const cache = await caches.open(CACHE);
        const cached = (await cache.match(req)) || (await cache.match(OFFLINE_URL));
        if (cached) return cached;
        throw new Error("offline e sem cache");
      }
    })()
  );
});
