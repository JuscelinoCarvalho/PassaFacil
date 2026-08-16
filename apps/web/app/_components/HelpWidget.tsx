"use client";

import { useEffect, useState } from "react";
import { LifeBuoy, X, Send, CheckCircle2, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";
const TOKEN_KEY = "pf-token";

type Category = "ajuda" | "reclamacao" | "sugestao" | "elogio" | "outro";

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "ajuda", label: "Preciso de ajuda" },
  { value: "reclamacao", label: "Reclamação" },
  { value: "sugestao", label: "Sugestão" },
  { value: "elogio", label: "Elogio" },
  { value: "outro", label: "Outro assunto" },
];

export default function HelpWidget() {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<Category>("ajuda");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error" | "offline">("idle");

  // Fecha com Esc.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const reset = () => {
    setCategory("ajuda");
    setMessage("");
    setEmail("");
    setState("idle");
  };

  const close = () => {
    setOpen(false);
    // dá tempo da animação antes de limpar (se enviado)
    if (state === "done") setTimeout(reset, 250);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim().length < 5) {
      setState("error");
      return;
    }
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setState("offline");
      return;
    }
    setState("sending");
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          category,
          message: message.trim(),
          contact_email: email.trim() || null,
          page: typeof window !== "undefined" ? window.location.pathname : null,
        }),
      });
      if (!res.ok) throw new Error(String(res.status));
      setState("done");
    } catch {
      setState(typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "error");
    }
  };

  return (
    <>
      <button
        type="button"
        className="help-fab"
        aria-label="Ajuda ou reclamação"
        onClick={() => setOpen(true)}
      >
        <LifeBuoy size={20} />
        <span>Ajuda</span>
      </button>

      {open && (
        <div className="help-overlay" role="dialog" aria-modal="true" aria-label="Fale conosco">
          <button type="button" className="help-backdrop" aria-label="Fechar" onClick={close} />
          <div className="help-card">
            <button type="button" className="help-close" aria-label="Fechar" onClick={close}>
              <X size={18} />
            </button>

            {state === "done" ? (
              <div className="help-done">
                <CheckCircle2 size={44} />
                <h3>Recebemos sua mensagem!</h3>
                <p>Obrigado pelo contato. Se você deixou um e-mail, respondemos por lá.</p>
                <button type="button" className="help-submit" onClick={close}>Fechar</button>
              </div>
            ) : (
              <form onSubmit={submit}>
                <div className="help-head">
                  <LifeBuoy size={20} />
                  <div>
                    <h3>Fale conosco</h3>
                    <p>Precisa de ajuda, quer reclamar ou sugerir algo? É só escrever.</p>
                  </div>
                </div>

                <label className="help-label">Assunto</label>
                <select
                  className="help-select"
                  value={category}
                  onChange={(e) => setCategory(e.target.value as Category)}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>

                <label className="help-label">Sua mensagem</label>
                <textarea
                  className="help-textarea"
                  rows={4}
                  placeholder="Conte o que aconteceu ou o que você precisa…"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  autoFocus
                />

                <label className="help-label">
                  Seu e-mail <span>(opcional, para respondermos)</span>
                </label>
                <input
                  className="help-input"
                  type="email"
                  placeholder="voce@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />

                {state === "error" && (
                  <p className="help-error">
                    Escreva pelo menos algumas palavras e tente novamente. Se persistir,
                    escreva para jussa@jussa.com.br.
                  </p>
                )}
                {state === "offline" && (
                  <p className="help-error">
                    Você está sem conexão com a internet. Reconecte e toque em Enviar novamente —
                    sua mensagem continua escrita aqui.
                  </p>
                )}

                <button type="submit" className="help-submit" disabled={state === "sending"}>
                  {state === "sending" ? (
                    <><Loader2 size={17} className="help-spin" /> Enviando…</>
                  ) : (
                    <><Send size={16} /> Enviar</>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
