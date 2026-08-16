"use client";

import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";

/** Barra fixa no topo quando o navegador perde a conexão. Funciona 100% offline
 * porque o JS já está carregado — resolve o "cliquei e não aconteceu nada". */
export default function OfflineBanner() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="offline-banner" role="status" aria-live="polite">
      <WifiOff size={16} />
      <span>
        <strong>Sem conexão com a internet.</strong> Suas ações não serão salvas até a rede voltar.
      </span>
    </div>
  );
}
