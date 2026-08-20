"use client";

import { useEffect } from "react";

/**
 * Registra o service worker e garante a ATUALIZAÇÃO AUTOMÁTICA:
 * toda vez que o app é aberto ou volta ao foco, ele checa se saiu versão nova
 * e, se saiu, ativa e recarrega uma única vez — o usuário sempre roda o código
 * mais recente publicado, sem precisar reinstalar nada.
 *
 * A navegação já é network-first (ver sw.js), então em abertura "fria" o HTML
 * novo já vem do servidor. Este componente cobre o SW em si e o retorno ao app
 * quando ele ficou aberto em segundo plano.
 */
export default function PwaUpdater() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;
    // Só registra sob HTTPS (ou localhost em dev).
    if (location.protocol !== "https:" && location.hostname !== "localhost") return;

    let reloading = false;
    const reloadOnce = () => {
      if (reloading) return;
      reloading = true;
      window.location.reload();
    };

    // Quando o SW novo assume o controle, recarrega para pegar o código novo.
    navigator.serviceWorker.addEventListener("controllerchange", reloadOnce);

    let reg: ServiceWorkerRegistration | null = null;

    const promoteWaiting = (r: ServiceWorkerRegistration) => {
      if (r.waiting) r.waiting.postMessage("SKIP_WAITING");
    };

    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((r) => {
        reg = r;
        // Se já havia um SW esperando, ativa de imediato.
        promoteWaiting(r);
        // Novo SW encontrado durante uma checagem → ativa quando instalar.
        r.addEventListener("updatefound", () => {
          const sw = r.installing;
          if (!sw) return;
          sw.addEventListener("statechange", () => {
            // "installed" + já existe controller = é uma ATUALIZAÇÃO (não a 1ª vez).
            if (sw.state === "installed" && navigator.serviceWorker.controller) {
              promoteWaiting(r);
            }
          });
        });
      })
      .catch(() => {});

    // Checa por atualização toda vez que o app volta ao foco / é reaberto.
    const checkForUpdate = () => {
      if (document.visibilityState === "visible" && reg) {
        reg.update().catch(() => {});
      }
    };
    document.addEventListener("visibilitychange", checkForUpdate);
    window.addEventListener("focus", checkForUpdate);

    return () => {
      navigator.serviceWorker.removeEventListener("controllerchange", reloadOnce);
      document.removeEventListener("visibilitychange", checkForUpdate);
      window.removeEventListener("focus", checkForUpdate);
    };
  }, []);

  return null;
}
