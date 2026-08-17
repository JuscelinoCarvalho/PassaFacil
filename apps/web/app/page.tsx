"use client";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  BookOpen,
  CalendarDays,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  Database,
  FileUp,
  FileText,
  Filter,
  Gauge,
  Headphones,
  LayoutDashboard,
  ListChecks,
  LoaderCircle,
  Lock,
  LogOut,
  Mail,
  Menu,
  Moon,
  Play,
  RotateCcw,
  ShieldCheck,
  Sun,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    dataLayer?: unknown[];
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:9000/api/v1";
const API_ORIGIN = API_URL.replace(/\/api\/v1$/, "");
const TOKEN_KEY = "pf-token";

// Google Ads — conversão de "Compra" (pagamento Pix confirmado). O rótulo vem da
// ação de conversão criada no Google Ads (config_ads3). A tag base (gtag.js) é
// carregada no layout.tsx. Dispara no máximo uma vez por transaction_id.
const GADS_PURCHASE_SEND_TO = "AW-975500543/YEiMCLvJ5t4cEP_pk9ED";
const firedConversions = new Set<string>();
// Retorna true se o evento foi (ou já havia sido) disparado; false se o gtag
// ainda não carregou — nesse caso NÃO marcamos como reportado, para tentar de novo.
function trackPurchaseConversion(transactionId: string, value = 25.0, currency = "BRL"): boolean {
  if (typeof window === "undefined" || typeof window.gtag !== "function") return false;
  const key = transactionId || "no-id";
  if (firedConversions.has(key)) return true;
  firedConversions.add(key);
  window.gtag("event", "conversion", {
    send_to: GADS_PURCHASE_SEND_TO,
    value,
    currency,
    transaction_id: transactionId,
  });
  return true;
}

type PendingConversion = { transaction_id: string; value: number; currency: string };

// Dispara a conversão pendente vinda do backend e, se de fato enviada, avisa o
// servidor para não reenviar. Espera o gtag (afterInteractive) até ~5s. Se ainda
// não estiver pronto, deixa pendente — a próxima carga do app tenta de novo.
async function reportConversion(conv: PendingConversion | null | undefined) {
  if (!conv) return;
  for (let i = 0; i < 20 && (typeof window === "undefined" || typeof window.gtag !== "function"); i++) {
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  const fired = trackPurchaseConversion(conv.transaction_id, conv.value, conv.currency);
  if (!fired) return;
  try {
    await authFetch(`${API_URL}/billing/conversion/reported`, { method: "POST" });
  } catch {
    /* se falhar, a flag continua pendente e será reportada na próxima carga */
  }
}

// Google Ads — clique de anúncio (gclid). Capturamos da URL na chegada e
// guardamos por 90 dias, para enviar ao backend no cadastro e no checkout
// (conversão server-side, independente do gtag no navegador do comprador).
const GCLID_KEY = "pf_gclid";
const GCLID_MAX_AGE_MS = 90 * 24 * 60 * 60 * 1000;
const ANON_KEY = "pf_anon";
const RESUME_KEY = "pf_resume_q"; // última questão aberta e NÃO respondida no simulado

function captureGclidFromUrl() {
  if (typeof window === "undefined") return;
  try {
    const gclid = new URLSearchParams(window.location.search).get("gclid");
    if (gclid) {
      localStorage.setItem(GCLID_KEY, JSON.stringify({ v: gclid.slice(0, 512), t: Date.now() }));
    }
  } catch {
    /* localStorage indisponível — ignora */
  }
}

function getStoredGclid(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(GCLID_KEY);
    if (!raw) return null;
    const { v, t } = JSON.parse(raw) as { v: string; t: number };
    if (!v || typeof t !== "number" || Date.now() - t > GCLID_MAX_AGE_MS) {
      localStorage.removeItem(GCLID_KEY);
      return null;
    }
    return v;
  } catch {
    return null;
  }
}

// ID ANÔNIMO do visitante (só para telemetria do teste grátis). UUID no navegador,
// não identifica pessoa. Usado para contar acessos/funil do test-drive.
function getAnonId(): string {
  if (typeof window === "undefined") return "";
  try {
    let id = localStorage.getItem(ANON_KEY);
    if (!id) {
      id = (crypto?.randomUUID?.() ?? `a-${Date.now()}-${Math.random().toString(36).slice(2)}`);
      localStorage.setItem(ANON_KEY, id);
    }
    return id;
  } catch {
    return "";
  }
}

// Envia um evento anônimo do teste grátis. Fire-and-forget — nunca atrapalha a UI.
function trackTrial(eventType: string, payload: Record<string, unknown> = {}) {
  if (typeof window === "undefined") return;
  const anon_id = getAnonId();
  if (!anon_id) return;
  try {
    fetch(`${API_URL}/study/trial/event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anon_id, event_type: eventType, payload }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* ignora — telemetria best-effort */
  }
}

function getToken(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
}
function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}
async function authFetch(input: string, init: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(init.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(input, { ...init, headers });
  // Token expirado/inválido: avisa o app para reabrir o login em vez de
  // exibir erros genéricos ("API não respondeu") ao usuário.
  if (response.status === 401 && token && typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("pf-session-expired"));
  }
  return response;
}

type Me = {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  email_verified: boolean;
  has_access: boolean;
  plan: string;
  conversion?: PendingConversion | null;
};

type Task = {
  id: string;
  title: string;
  description: string;
  activity_type: string;
  duration_minutes: number;
  is_completed: boolean;
};

type DashboardData = {
  user: { full_name: string; plan: string };
  stats: {
    questions_answered: number;
    accuracy: number;
    completed_tasks: number;
    total_tasks: number;
    study_minutes: number;
    answered_today: number;
    distinct_answered: number;
    published_total: number;
    coverage: number;
  };
  tasks: Task[];
  performance: { name: string; attempts: number; accuracy: number }[];
};

type Question = {
  id: string;
  statement: string;
  options: string[];
  topic: string;
  subject: string;
};

type SubjectScope = {
  slug: string;
  name: string;
  category: string;
  specialty: string | null;
  count: number;
};

const SPECIALTY_LABELS: Record<string, string> = {
  ti: "Tecnologia da Informação",
  atuariais: "Ciências Atuariais",
  contabeis: "Ciências Contábeis",
  economicas: "Ciências Econômicas",
  direito: "Direito",
  "engenharia-civil": "Engenharia Civil",
};

function greeting() {
  const hour = new Date().getHours();
  if (hour >= 6 && hour < 12) return "Bom dia";
  if (hour >= 12 && hour < 18) return "Boa tarde";
  return "Boa noite";
}

type MicroLesson = {
  essential?: {
    titulo?: string; regra?: string; aplicacao?: string; pegadinha?: string; macete?: string;
  } | null;
  deep?: string | null;
  mastery?: string | null;
};

type AnswerResult = {
  is_correct: boolean;
  correct_option: number;
  explanation: string;
  micro_aula?: string | null;
  // Fase 2 — feedback adaptativo + microaula em camadas (todos opcionais/retrocompatíveis)
  why_wrong?: string | null;
  misconception?: { code: string; name: string } | null;
  micro_lesson?: MicroLesson | null;
};

type ResultsData = {
  overall: {
    attempts: number;
    correct: number;
    accuracy: number;
    published: number;
    answered_distinct: number;
    coverage: number;
    all_questions_seen: boolean;
  };
  subjects: {
    slug: string;
    name: string;
    published: number;
    answered_distinct: number;
    attempts: number;
    correct: number;
    accuracy: number | null;
    coverage: number;
  }[];
  gaps: { slug: string; name: string; accuracy: number | null; coverage: number; attempts: number }[];
  recommendation: "repeat_all" | "focus_gaps";
};

type DiscCaseItem = {
  id: string;
  slug: string;
  tipo: string;
  disciplina: string;
  tema: string;
  pontuacao_maxima: number;
  limite_linhas: number;
  is_demo: boolean;
};

type DiscCase = DiscCaseItem & {
  enunciado: string;
  texto_apoio: string | null;
  banca_referencia: string;
};

type DiscCriterion = {
  codigo: string;
  descricao: string;
  conteudo_esperado: string;
  pontuacao_maxima: number;
};

type DiscEspelho = {
  model_answer: string;
  micro_aula: string;
  pontuacao_maxima: number;
  criteria: DiscCriterion[];
};

type DiscCorrecao = {
  scores: Record<string, number>;
  feedback: Record<string, string>;
  comentario: string | null;
  total: number;
  provider: string;
};

type TestResult = {
  total: number;
  correct: number;
  accuracy: number;
  by_subject: { subject: string; total: number; correct: number; accuracy: number }[];
  details: {
    question_id: string;
    is_correct: boolean;
    selected_option: number | null;
    correct_option: number;
    explanation: string;
    micro_aula?: string | null;
    topic: string;
    subject: string;
  }[];
};

const taskIcons = {
  theory: BookOpen,
  review: RotateCcw,
  questions: Target,
  audio: Headphones,
};

const nav = [
  ["Hoje", LayoutDashboard, "today", false],
  ["Plano de estudos", CalendarDays, "today", false],
  ["Simulado", Gauge, "questions", false],
  ["Modo teste", ListChecks, "test", false],
  ["Estudo de caso", FileText, "discursive", false],
  ["Meus resultados", TrendingUp, "results", false],
  ["Revisões", RotateCcw, "reviews", false],
  ["Caderno de erros", CircleAlert, "errors", false],
  ["Banco de questões", Database, "bank", true],
  ["Teste grátis", BarChart3, "trial", true],
  ["Áudios", Headphones, "soon", false],
] as const;

const EXAM_DATE = new Date(2026, 9, 11, 12, 0, 0); // 11/10/2026 — prova TCE-SP 2026

function useCountdown() {
  return useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const exam = new Date(EXAM_DATE.getFullYear(), EXAM_DATE.getMonth(), EXAM_DATE.getDate());
    const days = Math.max(0, Math.round((exam.getTime() - today.getTime()) / 86_400_000));
    const fmt = (value: Date) =>
      value.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
    return { days, todayLabel: fmt(today), examLabel: fmt(exam) };
  }, []);
}

// ============================ PORTÃO DE ACESSO ============================

export default function App() {
  const [booting, setBooting] = useState(true);
  const [me, setMe] = useState<Me | null>(null);
  const [showTrial, setShowTrial] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  const loadMe = useCallback(async () => {
    if (!getToken()) {
      setMe(null);
      setBooting(false);
      return;
    }
    try {
      const response = await authFetch(`${API_URL}/auth/me`, { cache: "no-store" });
      if (!response.ok) {
        setToken(null);
        setMe(null);
      } else {
        setMe(await response.json());
      }
    } catch {
      setMe(null);
    }
    setBooting(false);
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  // Guarda o gclid da URL (?gclid=) na chegada, para enviar ao backend no
  // cadastro/checkout e permitir a conversão server-side do Google Ads.
  useEffect(() => {
    captureGclidFromUrl();
  }, []);

  // Conversão Google Ads durável: se o backend marcou um pagamento confirmado
  // ainda não reportado, dispara o gtag agora (mesmo que a aba tenha sido fechada
  // durante o Pix) e limpa a flag no servidor. Roda em toda carga do app.
  useEffect(() => {
    if (me?.conversion) reportConversion(me.conversion);
  }, [me?.conversion?.transaction_id]);

  const onAuthed = useCallback(
    (token: string) => {
      setToken(token);
      setSessionExpired(false);
      setBooting(true);
      loadMe();
    },
    [loadMe]
  );

  const onLogout = useCallback(() => {
    setToken(null);
    setMe(null);
    setShowTrial(false);
  }, []);

  // Sessão expirada (401 em qualquer chamada autenticada): volta ao login
  // com um aviso claro, em vez de mostrar "API não respondeu".
  useEffect(() => {
    const handler = () => {
      setToken(null);
      setMe(null);
      setShowTrial(false);
      setSessionExpired(true);
    };
    window.addEventListener("pf-session-expired", handler);
    return () => window.removeEventListener("pf-session-expired", handler);
  }, []);

  if (booting) {
    return (
      <div className="gate">
        <div className="loading-state">
          <LoaderCircle className="spin" />
          <b>Carregando...</b>
        </div>
      </div>
    );
  }

  if (!me) {
    if (showTrial) return <TrialView onBack={() => setShowTrial(false)} />;
    return (
      <AuthGate
        onAuthed={onAuthed}
        onTrial={() => setShowTrial(true)}
        notice={sessionExpired ? "Sua sessão expirou por inatividade. Entre novamente para continuar." : ""}
      />
    );
  }

  if (!me.email_verified && !me.is_admin) {
    return <VerifyScreen email={me.email} onRefresh={loadMe} onLogout={onLogout} />;
  }

  if (!me.has_access) {
    return <Paywall me={me} onRefresh={loadMe} onLogout={onLogout} />;
  }

  return <StudyApp me={me} onLogout={onLogout} />;
}

// ============================ APP DE ESTUDO (logado + pago) ============================

function StudyApp({ me, onLogout }: { me: Me; onLogout: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [view, setView] = useState<"today" | "questions" | "test" | "discursive" | "results" | "reviews" | "errors" | "bank" | "trial" | "soon">("today");
  const [practiceFocus, setPracticeFocus] = useState<"all" | "gaps">("all");
  const [subjectsList, setSubjectsList] = useState<SubjectScope[]>([]);
  const [specialty, setSpecialty] = useState<string>("ti"); // especialidade escolhida
  const [scope, setScope] = useState<string[] | null>(null); // null = todas as matérias da especialidade
  const [qLoading, setQLoading] = useState(true);
  const countdown = useCountdown();

  const menuItems = useMemo(() => nav.filter(([, , , adminOnly]) => me.is_admin || !adminOnly), [me.is_admin]);

  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem("pf-theme")) as
      | "light"
      | "dark"
      | null;
    const initial =
      saved ??
      (typeof window !== "undefined" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light");
    setTheme(initial);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    if (typeof window !== "undefined") localStorage.setItem("pf-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!profileMenuOpen) return;
    const onDown = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setProfileMenuOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [profileMenuOpen]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [answer, setAnswer] = useState<AnswerResult | null>(null);
  // Id da sessão de estudo (agrupa os LearningEvents desta visita — spec §34/§35).
  const [studySessionId] = useState(() =>
    typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now())
  );
  // Guarda o que já foi marcado/respondido por questão (id → seleção + resultado),
  // para preservar o estado ao navegar Anterior/Próxima entre as questões do lote.
  const [answersMap, setAnswersMap] = useState<Record<string, { selected: number | null; result: AnswerResult | null }>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      const response = await authFetch(`${API_URL}/study/dashboard`, { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível carregar seu plano.");
      setDashboard(await response.json());
      setError("");
    } catch {
      setError("A API não respondeu. Confirme se o serviço da porta 9000 está aberto.");
    } finally {
      setLoading(false);
    }
  }, []);

  // matérias da especialidade escolhida = comuns (specialty null) + as da especialidade
  const specialtySubjects = useMemo(
    () => subjectsList.filter((item) => item.specialty === null || item.specialty === specialty),
    [subjectsList, specialty]
  );
  const allSlugs = useMemo(() => specialtySubjects.map((item) => item.slug), [specialtySubjects]);

  const loadQuestions = useCallback(async () => {
    setQLoading(true);
    try {
      const params = new URLSearchParams({ limit: "5000" });
      const isSubset = scope !== null && scope.length > 0 && scope.length < allSlugs.length;
      if (isSubset) params.set("subjects", scope.join(","));
      else params.set("specialty", specialty);
      if (practiceFocus === "gaps") params.set("focus", "gaps");
      const response = await authFetch(`${API_URL}/study/practice?${params.toString()}`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      const data: Question[] = await response.json();
      // Mantém a ORDEM natural (numeração estável) e apenas ABRE na última questão
      // aberta e não respondida (mesmo ID), se ela ainda estiver no lote.
      let startIndex = 0;
      try {
        const resumeId = localStorage.getItem(RESUME_KEY);
        if (resumeId) {
          const i = data.findIndex((q) => q.id === resumeId);
          if (i >= 0) startIndex = i;
        }
      } catch { /* localStorage indisponível — começa na primeira */ }
      setQuestions(data);
      setAnswersMap({});
      setQuestionIndex(startIndex);
      setSelectedOption(null);
      setAnswer(null);
      setError("");
    } catch {
      setError("Não foi possível carregar as questões.");
    } finally {
      setQLoading(false);
    }
  }, [scope, specialty, allSlugs, practiceFocus]);

  const loadSubjects = useCallback(async () => {
    try {
      const response = await authFetch(`${API_URL}/study/subjects`, { cache: "no-store" });
      if (response.ok) setSubjectsList(await response.json());
    } catch {
      /* silencioso — o seletor apenas não aparece */
    }
  }, []);

  // Restaura especialidade e matérias salvas no navegador (localStorage).
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedSpecialty = localStorage.getItem("pf_specialty");
    if (savedSpecialty) setSpecialty(savedSpecialty);
    const raw = localStorage.getItem("pf_scope");
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.every((item) => typeof item === "string")) {
        setScope(parsed);
      }
    } catch {
      localStorage.removeItem("pf_scope");
    }
  }, []);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    loadDashboard();
    loadQuestions();
  }, [loadDashboard, loadQuestions]);

  // Marca a questão atualmente ABERTA e ainda NÃO respondida no simulado, para
  // retomar exatamente nela ao voltar. (Limpa-se ao responder, em submitAnswer.)
  useEffect(() => {
    if (view !== "questions") return;
    const cq = questions[questionIndex];
    if (cq && answer === null) {
      try { localStorage.setItem(RESUME_KEY, cq.id); } catch { /* ignora */ }
    }
  }, [view, questions, questionIndex, answer]);

  const persistScope = useCallback((next: string[] | null) => {
    setScope(next);
    if (typeof window === "undefined") return;
    if (next && next.length) localStorage.setItem("pf_scope", JSON.stringify(next));
    else localStorage.removeItem("pf_scope");
  }, []);

  const chooseSpecialty = useCallback((slug: string) => {
    setSpecialty(slug);
    setScope(null); // troca de especialidade zera o filtro de matérias
    if (typeof window === "undefined") return;
    localStorage.setItem("pf_specialty", slug);
    localStorage.removeItem("pf_scope");
  }, []);

  const toggleScope = useCallback(
    (slug: string) => {
      const current = scope ?? allSlugs;
      const next = current.includes(slug)
        ? current.filter((item) => item !== slug)
        : [...current, slug];
      if (next.length === 0) return; // mantém ao menos uma matéria ativa
      persistScope(next.length >= allSlugs.length ? null : next);
    },
    [scope, allSlugs, persistScope]
  );

  const resetScope = useCallback(() => persistScope(null), [persistScope]);

  const toggleTask = async (taskId: string) => {
    setDashboard((current) =>
      current
        ? {
            ...current,
            tasks: current.tasks.map((task) =>
              task.id === taskId ? { ...task, is_completed: !task.is_completed } : task
            ),
            stats: {
              ...current.stats,
              completed_tasks:
                current.stats.completed_tasks +
                (current.tasks.find((task) => task.id === taskId)?.is_completed ? -1 : 1),
            },
          }
        : current
    );
    const response = await authFetch(`${API_URL}/study/tasks/${taskId}/toggle`, { method: "PATCH" });
    if (!response.ok) {
      setError("Não foi possível salvar a atividade.");
      await loadDashboard();
    }
  };

  const submitAnswer = async (confidence: string | null) => {
    const question = questions[questionIndex];
    if (!question || selectedOption === null) return;
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setError("Você está sem conexão com a internet. Reconecte para registrar a resposta.");
      return;
    }
    try {
      const response = await authFetch(`${API_URL}/study/questions/${question.id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_option: selectedOption, confidence, session_id: studySessionId }),
      });
      if (!response.ok) {
        setError("Não foi possível registrar a resposta.");
        return;
      }
      setError("");
      const data: AnswerResult = await response.json();
      setAnswer(data);
      // memoriza para preservar ao navegar Anterior/Próxima
      setAnswersMap((current) => ({ ...current, [question.id]: { selected: selectedOption, result: data } }));
      // já respondida → não é mais "aberta e não respondida"; limpa o marcador de retomada.
      try { localStorage.removeItem(RESUME_KEY); } catch { /* ignora */ }
      await loadDashboard();
    } catch {
      // fetch rejeita quando não há rede — evita o "cliquei e nada aconteceu".
      setError("Sem conexão com a internet. Verifique sua rede e tente novamente.");
    }
  };

  // Navega para uma questão pelo índice, salvando o estado da atual e
  // restaurando o estado (seleção/resultado) da questão de destino, se houver.
  const goToIndex = (target: number) => {
    if (target < 0 || target >= questions.length) return;
    const cur = questions[questionIndex];
    if (cur) setAnswersMap((current) => ({ ...current, [cur.id]: { selected: selectedOption, result: answer } }));
    const dest = questions[target];
    const saved = dest ? answersMap[dest.id] : undefined;
    setSelectedOption(saved?.selected ?? null);
    setAnswer(saved?.result ?? null);
    setQuestionIndex(target);
  };

  const nextQuestion = () => {
    if (questionIndex + 1 >= questions.length) {
      loadQuestions(); // fim do lote → busca mais questões
      return;
    }
    goToIndex(questionIndex + 1);
  };

  const prevQuestion = () => goToIndex(questionIndex - 1);

  const currentQuestion = questions[questionIndex];
  const firstName = me.full_name.split(" ")[0] || "Estudante";
  const initials = me.full_name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "PF";
  const planLabel = me.is_admin ? "Proprietário" : me.plan === "pro" ? "Acesso completo" : "Assinante";
  const completed = dashboard?.stats.completed_tasks ?? 0;
  const totalTasks = dashboard?.stats.total_tasks ?? 4;
  const progress = totalTasks ? Math.round((completed / totalTasks) * 100) : 0;
  const remainingMinutes = useMemo(
    () => dashboard?.tasks.filter((task) => !task.is_completed).reduce((sum, task) => sum + task.duration_minutes, 0) ?? 0,
    [dashboard]
  );

  const navigate = (destination: typeof view) => {
    setMenuOpen(false);
    setError("");
    if (destination === "questions") {
      setSelectedOption(null);
      setAnswer(null);
      setQuestionIndex(0);
      setPracticeFocus("all");
      loadQuestions();
    }
    setView(destination);
  };

  // Inicia o simulado em modo geral ou focado nos pontos fracos (P3 → P2/gaps).
  // A mudança de practiceFocus dispara o efeito que recarrega as questões.
  const startPractice = (focus: "all" | "gaps") => {
    setMenuOpen(false);
    setError("");
    setSelectedOption(null);
    setAnswer(null);
    setQuestionIndex(0);
    setPracticeFocus(focus);
    setView("questions");
  };

  return (
    <main className="app-shell">
      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={22} /></div>
          <div><strong>Passa Fácil</strong><span>Estude com direção.</span></div>
        </div>
        <nav className="sidebar-nav">
          <p className="nav-label">PREPARAÇÃO</p>
          {menuItems.map(([label, Icon, destination]) => (
            <button
              className={view === destination ? "nav-item active" : "nav-item"}
              key={label}
              onClick={() => navigate(destination)}
            >
              <Icon size={19} /><span>{label}</span>
              {destination === "soon" && <small className="soon-tag">EM BREVE</small>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-wrap" ref={profileRef}>
            {profileMenuOpen && (
              <div className="profile-menu">
                {me.is_admin && (
                  <button className="profile-menu-item"><Settings size={16} /><span>Configurações</span></button>
                )}
                <button className="profile-menu-item" onClick={onLogout}><LogOut size={16} /><span>Sair</span></button>
              </div>
            )}
            <button
              className={profileMenuOpen ? "profile open" : "profile"}
              onClick={() => setProfileMenuOpen((o) => !o)}
              aria-label="Menu do perfil"
            >
              <div className="avatar">{initials}</div>
              <div><b>{firstName}</b><span>{planLabel}</span></div>
              <ChevronRight size={17} className="profile-caret" />
            </button>
          </div>
        </div>
      </aside>
      {menuOpen && <button aria-label="Fechar menu" className="backdrop" onClick={() => setMenuOpen(false)} />}

      <section className="content">
        <header className="topbar">
          <button className="menu-button" aria-label="Abrir menu" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X /> : <Menu />}
          </button>
          <div className="exam-chip"><span className="live-dot" />TCE-SP 2026 · TI</div>
          <div className="countdown" title={`Hoje ${countdown.todayLabel} · Prova ${countdown.examLabel}`}>
            <CalendarDays size={17} />
            <div className="countdown-text">
              <span>Hoje {countdown.todayLabel} · Prova {countdown.examLabel}</span>
              <b>{countdown.days === 0 ? "É hoje!" : `faltam ${countdown.days} dias`}</b>
            </div>
          </div>
          <button
            className="theme-toggle"
            aria-label={theme === "dark" ? "Ativar modo claro" : "Ativar modo escuro"}
            title={theme === "dark" ? "Modo claro" : "Modo escuro (noturno)"}
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </header>

        <div className="dashboard">
          {error && <div className="error-banner"><CircleAlert size={18} />{error}<button onClick={loadDashboard}>Tentar novamente</button></div>}
          {loading ? (
            <div className="loading-state"><LoaderCircle className="spin" /><b>Preparando seu plano...</b></div>
          ) : view === "questions" ? (
            <>
              <ScopeBar
                subjects={subjectsList}
                specialty={specialty}
                onSpecialty={chooseSpecialty}
                scope={scope}
                onToggle={toggleScope}
                onReset={resetScope}
              />
              {practiceFocus === "gaps" && (
                <div className="focus-banner">
                  <Target size={17} /> Modo <b>pontos fracos</b>: só questões novas ou que você errou.
                  <button onClick={() => startPractice("all")}>Voltar ao simulado completo</button>
                </div>
              )}
              <QuestionsView
                question={currentQuestion}
                index={questionIndex}
                total={questions.length}
                loading={qLoading}
                selected={selectedOption}
                result={answer}
                onSelect={setSelectedOption}
                onSubmit={submitAnswer}
                onNext={nextQuestion}
                onPrev={prevQuestion}
                onJumpNext={() => goToIndex(questionIndex + 1)}
                canPrev={questionIndex > 0}
                canNext={questionIndex + 1 < questions.length}
              />
            </>
          ) : view === "test" ? (
            <TestView
              specialty={specialty}
              subjects={scope && scope.length < allSlugs.length ? scope : null}
            />
          ) : view === "discursive" ? (
            <DiscursiveView />
          ) : view === "results" ? (
            <ResultsView
              specialty={specialty}
              subjects={scope && scope.length < allSlugs.length ? scope : null}
              onFocusGaps={() => startPractice("gaps")}
              onRepeatAll={() => startPractice("all")}
            />
          ) : view === "reviews" ? (
            <ReviewView />
          ) : view === "errors" ? (
            <ErrorNotebook onPractice={() => navigate("questions")} />
          ) : view === "bank" && me.is_admin ? (
            <QuestionBankView />
          ) : view === "trial" && me.is_admin ? (
            <TrialAnalyticsView />
          ) : view === "soon" ? (
            <section className="card empty-state">
              <Sparkles size={34} /><h1>Este módulo é o próximo da fila.</h1>
              <p>Primeiro estamos fechando o ciclo essencial: plano, questões, correção e evolução real.</p>
              <button className="primary compact" onClick={() => navigate("questions")}>Ir para o simulado</button>
            </section>
          ) : (
            <>
              <section className="hero">
                <div>
                  <span className="eyebrow">SEU PLANO ADAPTATIVO</span>
                  <h1>{greeting()}, {firstName}.</h1>
                  <p>Você tem <strong>{remainingMinutes} minutos</strong> restantes no plano de hoje.</p>
                </div>
                <div className="daily-score">
                  <div className="score-ring" style={{ "--progress": `${progress}%` } as React.CSSProperties}><span>{completed}/{totalTasks}</span></div>
                  <div><b>Meta diária</b><span>{completed === totalTasks ? "Fechou o dia!" : `${totalTasks - completed} atividades restantes`}</span></div>
                </div>
              </section>

              <div className="grid">
                <section className="card plan-card">
                  <div className="card-heading">
                    <div><span className="section-kicker">PLANO DE HOJE</span><h2>Atividades salvas no seu perfil</h2></div>
                  </div>
                  <div className="activity-list">
                    {dashboard?.tasks.map((task) => {
                      const Icon = taskIcons[task.activity_type as keyof typeof taskIcons] ?? BookOpen;
                      return (
                        <button className={task.is_completed ? "activity completed" : "activity"} key={task.id} onClick={() => toggleTask(task.id)}>
                          <span className={`activity-icon ${task.activity_type === "audio" ? "green" : task.activity_type === "questions" ? "orange" : task.activity_type === "review" ? "blue" : "purple"}`}><Icon size={20} /></span>
                          <span className="activity-copy"><b>{task.title}</b><small>{task.description}</small></span>
                          <span className="activity-time"><Clock3 size={15} />{task.duration_minutes} min</span>
                          <span className="check">{task.is_completed && <Check size={17} />}</span>
                        </button>
                      );
                    })}
                  </div>
                  <button className="primary" onClick={() => navigate("questions")}><Play size={17} fill="currentColor" />{dashboard?.stats.questions_answered ? "Continuar simulado" : "Iniciar simulado"}</button>
                </section>

                <aside className="right-column">
                  <section className="card readiness-card">
                    <div className="card-heading"><div><span className="section-kicker">RESULTADOS REAIS</span><h2>Seu desempenho</h2></div><Trophy size={22} /></div>
                    <div className="readiness">
                      <div className="big-number">{dashboard?.stats.accuracy ?? 0}<span>%</span></div>
                      <div>
                        <b>{dashboard?.stats.questions_answered
                          ? `${dashboard.stats.distinct_answered} de ${dashboard.stats.published_total} questões vistas`
                          : "Primeiro diagnóstico"}</b>
                        <p>{dashboard?.stats.questions_answered
                          ? `${dashboard.stats.coverage}% do banco percorrido · seu progresso é salvo e continua de onde parou.`
                          : "Responda questões para o sistema identificar seus pontos fortes e fracos."}</p>
                      </div>
                    </div>
                    <div className="mini-stats">
                      <div><span>Estudo hoje</span><b>{dashboard?.stats.study_minutes ?? 0}m</b></div>
                      <div><span>Progresso</span><b>{dashboard?.stats.coverage ?? 0}%</b></div>
                      <div><span>Acertos</span><b>{dashboard?.stats.accuracy ?? 0}%</b></div>
                    </div>
                    <div className="mini-stats" style={{ marginTop: 8 }}>
                      <div><span>Questões hoje</span><b>{dashboard?.stats.answered_today ?? 0}</b></div>
                      <div><span>Respondidas</span><b>{dashboard?.stats.questions_answered ?? 0}</b></div>
                      <div><span>Do banco</span><b>{dashboard?.stats.distinct_answered ?? 0}</b></div>
                    </div>
                  </section>
                  <section className="insight">
                    <span className="insight-icon"><CircleAlert size={20} /></span>
                    <div><span>PRÓXIMA AÇÃO</span><b>Simulado de treino</b><p>Cada resposta atualiza seus indicadores.</p><button onClick={() => navigate("questions")}>Começar agora <ArrowRight size={15} /></button></div>
                  </section>
                </aside>
              </div>

              <section className="card performance">
                <div className="card-heading"><div><span className="section-kicker">DESEMPENHO</span><h2>Resultados por disciplina</h2></div></div>
                {dashboard?.performance.length ? (
                  <div className="subject-grid">
                    {dashboard.performance.map((subject, index) => (
                      <div className="subject" key={subject.name}>
                        <div><span>{subject.name} · {subject.attempts} questões</span><b>{subject.accuracy}%</b></div>
                        <div className="bar"><i style={{ width: `${subject.accuracy}%`, background: ["#7457e8", "#5776e8", "#ee8c43", "#ef5f67"][index % 4] }} /></div>
                      </div>
                    ))}
                  </div>
                ) : <p className="no-data">Seu gráfico aparecerá assim que você responder a primeira questão.</p>}
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function ScopeBar({
  subjects, specialty, onSpecialty, scope, onToggle, onReset,
}: {
  subjects: SubjectScope[];
  specialty: string;
  onSpecialty: (slug: string) => void;
  scope: string[] | null;
  onToggle: (slug: string) => void;
  onReset: () => void;
}) {
  if (!subjects.length) return null;
  // especialidades disponíveis, na ordem de exibição (exclui as comuns)
  const specialties: string[] = [];
  for (const item of subjects) {
    if (item.specialty && !specialties.includes(item.specialty)) specialties.push(item.specialty);
  }
  const mats = subjects.filter((item) => item.specialty === null || item.specialty === specialty);
  const selected = scope ?? mats.map((item) => item.slug);
  const allOn = selected.length >= mats.length;
  const totalQuestions = mats
    .filter((item) => selected.includes(item.slug))
    .reduce((sum, item) => sum + item.count, 0);
  return (
    <section className="card scope-bar">
      <div className="scope-head">
        <span className="scope-title"><Filter size={16} /> Monte seu simulado</span>
      </div>
      <div className="specialty-row" role="radiogroup" aria-label="Especialidade do concurso">
        {specialties.map((slug) => (
          <button
            type="button"
            key={slug}
            role="radio"
            aria-checked={slug === specialty}
            className={slug === specialty ? "specialty-pill on" : "specialty-pill"}
            onClick={() => onSpecialty(slug)}
          >
            {SPECIALTY_LABELS[slug] ?? slug}
          </button>
        ))}
      </div>
      <div className="scope-sub">
        <span className="scope-count">
          {allOn ? "Todas as matérias" : `${selected.length} de ${mats.length} matérias`}
          {" · "}{totalQuestions} questões
        </span>
        {!allOn && (
          <button type="button" className="scope-reset" onClick={onReset}>Selecionar todas</button>
        )}
      </div>
      <div className="scope-chips">
        {mats.map((item) => {
          const on = selected.includes(item.slug);
          const empty = item.count === 0;
          return (
            <button
              type="button"
              key={item.slug}
              className={`scope-chip${on ? " on" : ""}${empty ? " empty" : ""}`}
              aria-pressed={on}
              title={empty ? "Ainda sem questões — em breve" : undefined}
              onClick={() => onToggle(item.slug)}
            >
              {on && <Check size={13} />}
              <span>{item.name}</span>
              <i>{item.count}</i>
            </button>
          );
        })}
      </div>
    </section>
  );
}

// Confiança do modo aprendizagem (spec §6): 1 clique, opcional. Valores casam com o back.
const CONFIDENCE_OPTIONS: { value: string; label: string }[] = [
  { value: "chutei", label: "Chutei" },
  { value: "duvida", label: "Em dúvida" },
  { value: "confiante", label: "Confiante" },
];

// Parte pedagógica do feedback (spec §7/§8): por que a correta está certa, por que a sua
// pode estar errada (misconception) e a microaula em camadas 1/2/3 (2 e 3 colapsadas).
function QuestionTeach({ result }: { result: AnswerResult }) {
  const [showDeep, setShowDeep] = useState(false);
  const [showMastery, setShowMastery] = useState(false);
  const ml = result.micro_lesson || {};
  const ess = ml.essential || null;
  return (
    <>
      {/* Por que a correta está certa */}
      <div className="teach"><span className="teach-label">Por que a correta está certa</span>{result.explanation}</div>

      {/* Por que a SUA resposta pode estar errada (não acusatório) */}
      {!result.is_correct && result.why_wrong && (
        <div className="teach diag">
          <span className="teach-label">Por que sua resposta pode estar errada</span>
          {result.misconception && <b className="mis-tag">{result.misconception.name}</b>}
          <span>{result.why_wrong}</span>
        </div>
      )}

      {/* Camada 1 — essencial (estruturada), quando autorada */}
      {ess && (
        <div className="micro-aula layer1">
          <span className="micro-aula-label"><BookOpen size={13} /> {ess.titulo || "Micro Aula — o essencial"}</span>
          {ess.regra && <p><b>Regra:</b> {ess.regra}</p>}
          {ess.aplicacao && <p><b>Nesta questão:</b> {ess.aplicacao}</p>}
          {ess.pegadinha && <p><b>Pegadinha:</b> {ess.pegadinha}</p>}
          {ess.macete && <p><b>Macete:</b> {ess.macete}</p>}
        </div>
      )}

      {/* Camada 2 — Entender melhor (colapsada) */}
      {ml.deep && (
        <div className="layer-more">
          <button className="ghost compact layer-toggle" onClick={() => setShowDeep((v) => !v)}>
            {showDeep ? "Ocultar" : "Entender melhor"}
          </button>
          {showDeep && <div className="micro-aula layer2">{ml.deep}</div>}
        </div>
      )}

      {/* Camada 3 — Dominar este assunto (colapsada); cai p/ a descrição do tópico */}
      {ml.mastery && (
        <div className="layer-more">
          <button className="ghost compact layer-toggle" onClick={() => setShowMastery((v) => !v)}>
            {showMastery ? "Ocultar" : "Dominar este assunto"}
          </button>
          {showMastery && <div className="micro-aula layer3">{ml.mastery}</div>}
        </div>
      )}
    </>
  );
}

function QuestionsView({
  question, index, total, loading, selected, result, onSelect, onSubmit, onNext,
  onPrev, onJumpNext, canPrev, canNext,
}: {
  question?: Question;
  index: number;
  total: number;
  loading: boolean;
  selected: number | null;
  result: AnswerResult | null;
  onSelect: (value: number) => void;
  onSubmit: (confidence: string | null) => void;
  onNext: () => void;
  onPrev?: () => void;
  onJumpNext?: () => void;
  canPrev?: boolean;
  canNext?: boolean;
}) {
  // Confiança (modo aprendizagem) — local à questão; zera ao trocar de questão.
  const [confidence, setConfidence] = useState<string | null>(null);
  useEffect(() => { setConfidence(null); }, [question?.id]);
  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando questões...</h2></section>;
  if (!question) return (
    <section className="card empty-state">
      <Sparkles size={34} />
      <h1>Nenhuma questão nesse escopo ainda</h1>
      <p>Essa combinação de matérias ainda não tem questões. Escolha outra especialidade ou marque mais matérias acima.</p>
    </section>
  );
  return (
    <section className="question-layout">
      <div className="question-top">
        <div><span className="eyebrow">SIMULADO</span><h1>Treine e aprenda a cada questão</h1><p>Errou? A explicação ensina na hora — assim você fixa rápido.</p></div>
        <div className="question-nav">
          {onPrev && (
            <button className="ghost compact nav-arrow" onClick={onPrev} disabled={!canPrev} aria-label="Questão anterior" title="Questão anterior"><ArrowLeft size={16} /></button>
          )}
          <span className="question-count">{index + 1}<span>/{total}</span></span>
          {onJumpNext && (
            <button className="ghost compact nav-arrow" onClick={onJumpNext} disabled={!canNext} aria-label="Próxima questão" title="Próxima questão"><ArrowRight size={16} /></button>
          )}
        </div>
      </div>
      <article className="card question-card">
        <div className="question-meta"><span>{question.subject}</span><i>{question.topic}</i></div>
        <h2>{question.statement}</h2>
        <div className="options">
          {question.options.map((option, optionIndex) => {
            const isCorrect = result && optionIndex === result.correct_option;
            const isWrong = result && optionIndex === selected && !result.is_correct;
            return (
              <button
                key={option}
                disabled={Boolean(result)}
                onClick={() => onSelect(optionIndex)}
                className={`option ${selected === optionIndex ? "selected" : ""} ${isCorrect ? "correct" : ""} ${isWrong ? "wrong" : ""}`}
              >
                <span>{String.fromCharCode(65 + optionIndex)}</span>{option}
              </button>
            );
          })}
        </div>
        {result && (
          <div className={result.is_correct ? "feedback correct-feedback" : "feedback wrong-feedback"}>
            <b>{result.is_correct ? "✓ Você acertou!" : "✗ Ainda não — vamos fixar isso"}</b>
            {!result.is_correct && selected !== null && (
              <p className="answer-line chosen">
                <span className="tag">Você marcou</span>
                <b>{String.fromCharCode(65 + selected)}</b> {question.options[selected]}
              </p>
            )}
            <p className="answer-line right">
              <span className="tag">Resposta correta</span>
              <b>{String.fromCharCode(65 + result.correct_option)}</b> {question.options[result.correct_option]}
            </p>
            <QuestionTeach result={result} />
          </div>
        )}
        {/* Confiança: aparece após escolher a alternativa e antes de confirmar (1 clique, opcional) */}
        {!result && selected !== null && (
          <div className="confidence-row" role="group" aria-label="Qual sua confiança?">
            <span className="confidence-label">Confiança:</span>
            {CONFIDENCE_OPTIONS.map((c) => (
              <button
                key={c.value}
                type="button"
                className={`confidence-pill ${confidence === c.value ? "on" : ""}`}
                aria-pressed={confidence === c.value}
                onClick={() => setConfidence((cur) => (cur === c.value ? null : c.value))}
              >
                {c.label}
              </button>
            ))}
          </div>
        )}
        <div className="question-actions">
          {!result ? (
            <button className="primary compact" disabled={selected === null} onClick={() => onSubmit(confidence)}>Confirmar resposta</button>
          ) : (
            <button className="primary compact" onClick={onNext}>Próxima questão <ArrowRight size={16} /></button>
          )}
        </div>
      </article>
    </section>
  );
}

// ============================ TEST-DRIVE (público) ============================

function TrialView({ onBack }: { onBack: () => void }) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState<"home" | "quiz" | "results" | "discursive" | "audio">("home");
  const [tally, setTally] = useState<{ subject: string; correct: boolean }[]>([]);

  useEffect(() => {
    trackTrial("trial_start");
    fetch(`${API_URL}/study/trial`, { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data: Question[]) => setQuestions(data))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (stage === "results" && tally.length) {
      const t = tally.length;
      const c = tally.filter((x) => x.correct).length;
      trackTrial("results_viewed", { total: t, correct: c, accuracy: Math.round((c / t) * 100) });
    } else if (stage === "discursive") {
      trackTrial("discursive_opened");
    } else if (stage === "audio") {
      trackTrial("audio_opened");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  const submit = async (confidence: string | null) => {
    const question = questions[index];
    if (!question || selected === null) return;
    const response = await fetch(`${API_URL}/study/trial/${question.id}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_option: selected, confidence }),
    });
    if (response.ok) {
      const data: AnswerResult = await response.json();
      setResult(data);
      setTally((current) => [...current, { subject: question.subject, correct: data.is_correct }]);
      trackTrial("question_answered", { question_id: question.id, subject: question.subject, correct: data.is_correct });
    }
  };

  const next = () => {
    if (index + 1 >= questions.length) {
      setStage("results");
      return;
    }
    setIndex((current) => current + 1);
    setSelected(null);
    setResult(null);
  };

  const LOCKED = [
    "Centenas de questões comentadas de TODAS as matérias do TCE-SP",
    "Seu histórico real e estatísticas que evoluem a cada resposta",
    "Simulados (modo teste) e treino focado nos seus pontos fracos",
    "Revisões espaçadas e caderno de erros",
    "Estudos de caso da prova discursiva, com sua nota salva no histórico",
  ];

  // Resultado da amostra — calculado no navegador, só destas questões (não grava nada).
  const total = tally.length;
  const correct = tally.filter((t) => t.correct).length;
  const accuracy = total ? Math.round((correct / total) * 100) : 0;
  const projected = Math.round((accuracy / 100) * 80);
  const bySubject = Object.values(
    tally.reduce((acc, t) => {
      acc[t.subject] = acc[t.subject] || { name: t.subject, total: 0, correct: 0 };
      acc[t.subject].total += 1;
      if (t.correct) acc[t.subject].correct += 1;
      return acc;
    }, {} as Record<string, { name: string; total: number; correct: number }>)
  );
  const barColors = ["#7457e8", "#5776e8", "#ee8c43", "#ef5f67", "#2fa98a"];

  return (
    <main className="app-shell">
      <section className="content" style={{ marginLeft: 0 }}>
        <header className="topbar">
          <button className="gate-linkbtn" onClick={() => (stage === "home" ? onBack() : setStage("home"))}>
            ← {stage === "home" ? "Voltar" : "Início"}
          </button>
          <div className="exam-chip"><span className="live-dot" />Teste grátis · TCE-SP 2026</div>
          <div style={{ marginLeft: "auto" }} />
        </header>
        <div className="dashboard">
          <div className="trial-notice">
            <Sparkles size={16} /> Você está na <b>versão de demonstração</b>. É uma amostra — escolha o que testar abaixo. Uso <b>anônimo</b> para melhorar o app.
          </div>

          {loading ? (
            <div className="loading-state"><LoaderCircle className="spin" /><b>Carregando o teste grátis...</b></div>
          ) : stage === "home" ? (
            <>
              <div className="question-top">
                <div>
                  <span className="eyebrow">TESTE GRÁTIS · DEMONSTRAÇÃO</span>
                  <h1>O que você pode testar agora</h1>
                  <p>Uma amostra do Passa Fácil. Escolha por onde começar:</p>
                </div>
              </div>
              <div className="trial-menu">
                <button className="trial-menu-card" onClick={() => setStage("quiz")}>
                  <span className="tm-badge on">Disponível</span>
                  <span className="tm-icon purple"><Gauge size={22} /></span>
                  <b>Simulado</b>
                  <small>{questions.length || 8} questões comentadas de matérias diferentes, com correção imediata e Micro Aula.</small>
                </button>
                <button className="trial-menu-card" onClick={() => setStage("discursive")}>
                  <span className="tm-badge on">Disponível</span>
                  <span className="tm-icon amber"><FileText size={22} /></span>
                  <b>Estudo de caso</b>
                  <small>Um exemplo da prova discursiva: responda e revele o espelho da banca com micro-aula.</small>
                </button>
                <button className="trial-menu-card" onClick={() => setStage("results")}>
                  <span className="tm-badge on">Disponível</span>
                  <span className="tm-icon green"><TrendingUp size={22} /></span>
                  <b>Resumo dos avanços</b>
                  <small>{tally.length ? `Sua prévia: ${accuracy}% em ${tally.length} questões.` : "Prévia dos resultados e estimativa — faça o simulado para preencher."}</small>
                </button>
                <button className="trial-menu-card" onClick={() => setStage("audio")}>
                  <span className="tm-badge on">Prévia</span>
                  <span className="tm-icon teal"><Headphones size={22} /></span>
                  <b>Aulas em áudio</b>
                  <small>A voz lê a questão, dá um tempo para pensar e revela a resposta com a explicação. Ideal para estudar no trânsito.</small>
                </button>
              </div>

              <section className="card trial-locks-card">
                <div className="card-heading"><div><span className="section-kicker">TESTE GRÁTIS ≠ ACESSO COMPLETO</span><h2>O que só o acesso completo tem</h2></div><Lock size={20} /></div>
                <ul className="trial-locks">
                  {LOCKED.map((f) => <li key={f}><Lock size={14} /> {f}</li>)}
                </ul>
                <div className="results-actions">
                  <button className="primary compact" onClick={onBack}><Sparkles size={15} /> Criar minha conta</button>
                </div>
              </section>
            </>
          ) : stage === "quiz" ? (
            !questions.length ? (
              <section className="card empty-state">
                <CircleAlert size={30} />
                <h2>Amostra indisponível no momento.</h2>
                <button className="primary compact" onClick={onBack}>Criar minha conta</button>
              </section>
            ) : (
              <>
                <div className="error-banner" style={{ background: "#eef2ff", color: "#4338ca" }}>
                  <Sparkles size={18} /> Amostra grátis — {questions.length} questões de matérias diferentes, com correção e Micro Aula.
                </div>
                <QuestionsView
                  question={questions[index]}
                  index={index}
                  total={questions.length}
                  loading={false}
                  selected={selected}
                  result={result}
                  onSelect={setSelected}
                  onSubmit={submit}
                  onNext={next}
                />
              </>
            )
          ) : stage === "results" ? (
            tally.length === 0 ? (
              <section className="card empty-state">
                <TrendingUp size={34} />
                <h1>Ainda sem dados</h1>
                <p>Faça algumas questões do simulado e volte aqui para ver sua prévia de resultados e a estimativa.</p>
                <button className="primary compact" onClick={() => setStage("quiz")}><Play size={16} fill="currentColor" /> Ir para o simulado</button>
              </section>
            ) : (
            <section className="results-layout">
              <div className="question-top">
                <div>
                  <span className="eyebrow">PRÉVIA DOS SEUS RESULTADOS</span>
                  <h1>Como você foi na amostra</h1>
                  <p>Baseado só nestas {total} questões. No acesso completo, esta tela acompanha todo o seu histórico e evolui a cada resposta.</p>
                </div>
              </div>

              <div className="results-cards">
                <section className="card readiness-card">
                  <div className="card-heading"><div><span className="section-kicker">APROVEITAMENTO</span><h2>Acertos</h2></div><Trophy size={22} /></div>
                  <div className="readiness">
                    <div className="big-number">{accuracy}<span>%</span></div>
                    <div><b>{correct} de {total} respostas certas</b><p>Nesta amostra grátis.</p></div>
                  </div>
                  <div className="mini-stats">
                    <div><span>Respondidas</span><b>{total}</b></div>
                    <div><span>Certas</span><b>{correct}</b></div>
                    <div><span>Erradas</span><b>{total - correct}</b></div>
                  </div>
                </section>

                <section className="insight">
                  <span className="insight-icon"><TrendingUp size={20} /></span>
                  <div>
                    <span>ESTIMATIVA ILUSTRATIVA</span>
                    <b>~{projected} de 80 na objetiva</b>
                    <p>Se mantivesse este aproveitamento na prova toda. É só uma referência — a amostra é curta; com mais questões a estimativa fica precisa.</p>
                  </div>
                </section>
              </div>

              {bySubject.length > 0 && (
                <section className="card performance">
                  <div className="card-heading"><div><span className="section-kicker">DESEMPENHO</span><h2>Acerto por matéria (amostra)</h2></div></div>
                  <div className="subject-grid">
                    {bySubject.map((s, i) => {
                      const acc = Math.round((s.correct / s.total) * 100);
                      return (
                        <div className="subject" key={s.name}>
                          <div><span>{s.name} · {s.correct}/{s.total}</span><b>{acc}%</b></div>
                          <div className="bar"><i style={{ width: `${acc}%`, background: barColors[i % barColors.length] }} /></div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

              <section className="card trial-locks-card">
                <div className="card-heading"><div><span className="section-kicker">TESTE GRÁTIS ≠ ACESSO COMPLETO</span><h2>O que ainda está bloqueado</h2></div><Lock size={20} /></div>
                <ul className="trial-locks">
                  {LOCKED.map((f) => <li key={f}><Lock size={14} /> {f}</li>)}
                </ul>
                <div className="results-actions">
                  <button className="ghost compact" onClick={() => setStage("discursive")}><FileText size={15} /> Ver a prova discursiva (exemplo)</button>
                  <button className="primary compact" onClick={onBack}><Sparkles size={15} /> Criar minha conta</button>
                </div>
              </section>
            </section>
            )
          ) : stage === "discursive" ? (
            <TrialDiscursive onBack={() => setStage("home")} onCreate={onBack} />
          ) : (
            <TrialAudio />
          )}
        </div>
      </section>
    </main>
  );
}

function TrialAudio() {
  const [items, setItems] = useState<{ n: number; title: string; url: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const refs = useRef<(HTMLAudioElement | null)[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/study/trial/audios`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : []))
      .then((d: { n: number; title: string; url: string }[]) => setItems(d))
      .finally(() => setLoading(false));
  }, []);

  const playIndex = (i: number) => {
    if (i < 0 || i >= items.length) return;
    refs.current.forEach((a, j) => { if (a && j !== i) a.pause(); });
    setCurrent(i);
    const el = refs.current[i];
    if (el) {
      el.play().catch(() => { /* autoplay pode ser bloqueado — sem problema */ });
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando as aulas em áudio...</h2></section>;

  return (
    <section className="results-layout">
      <div className="question-top">
        <div>
          <span className="eyebrow">AULAS EM ÁUDIO · PRÉVIA</span>
          <h1>Ouça as questões</h1>
          <p>A voz lê o enunciado, dá um tempo para você pensar e então revela a resposta com o porquê. Toque em Tocar e ele segue de uma para a outra.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <section className="card empty-state"><Headphones size={30} /><p>Nenhuma aula em áudio disponível ainda.</p></section>
      ) : (
        <>
          <div className="audio-controls">
            <button className="ghost compact" onClick={() => playIndex(current - 1)} disabled={current <= 0}><ArrowLeft size={15} /> Anterior</button>
            <button className="primary compact" onClick={() => playIndex(current)}><Play size={15} fill="currentColor" /> Tocar</button>
            <button className="ghost compact" onClick={() => playIndex(current + 1)} disabled={current + 1 >= items.length}>Próxima <ArrowRight size={15} /></button>
            <span className="audio-count">{current + 1} / {items.length}</span>
          </div>
          <div className="trial-audios">
            {items.map((it, idx) => (
              <div className={`trial-audio ${idx === current ? "playing" : ""}`} key={it.n}>
                <div className="ta-head"><span className="ta-num">{it.n}</span><b>{it.title}</b></div>
                <audio
                  controls
                  preload="none"
                  src={it.url}
                  ref={(el) => { refs.current[idx] = el; }}
                  onPlay={() => setCurrent(idx)}
                  onEnded={() => playIndex(idx + 1)}
                />
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

// Painel da correção automática por IA (read-only), reaproveitado no teste grátis
// e na área logada. Mostra a nota de cada critério + a justificativa + o comentário.
// formata nota com no máximo 1 casa, vírgula decimal (ex.: 2 -> "2", 1.3 -> "1,3")
function fmtNota(n: number): string {
  return (Math.round(n * 10) / 10).toString().replace(".", ",");
}

// Correção da IA reaproveitando a MESMA tela/ícones da autoavaliação: os três
// botões (Não completou / Em parte / Completou) agora são marcados pela IA e ficam
// somente-leitura; a nota apurada é realista (soma das notas por critério).
function DiscCorrecaoPanel({ correcao, criteria, max }: { correcao: DiscCorrecao; criteria: DiscCriterion[]; max: number }) {
  const pct = max ? Math.round((correcao.total / max) * 100) : 0;
  return (
    <article className="card">
      <div className="card-heading"><div><span className="section-kicker">CORREÇÃO DA IA</span><h2>Quanto você cobriu de cada critério</h2></div></div>
      <div className="disc-criteria">
        {criteria.map((cr) => {
          const nota = correcao.scores[cr.codigo] ?? 0;
          const just = correcao.feedback[cr.codigo] ?? "";
          const level = nota >= cr.pontuacao_maxima ? "ok" : nota <= 0 ? "no" : "mid";
          return (
            <div className="disc-crit" key={cr.codigo}>
              <div className="disc-crit-head"><b>{cr.codigo} · {cr.descricao}</b><span className={`disc-crit-nota ${level}`}>{fmtNota(nota)} / {fmtNota(cr.pontuacao_maxima)}</span></div>
              <p className="disc-crit-esperado">{cr.conteudo_esperado}</p>
              <div className="disc-crit-buttons ia">
                <button className={level === "no" ? "on no" : ""} disabled>Não completou</button>
                <button className={level === "mid" ? "on mid" : ""} disabled>Em parte</button>
                <button className={level === "ok" ? "on ok" : ""} disabled>Completou</button>
              </div>
              {just && <p className="disc-crit-feedback">{just}</p>}
            </div>
          );
        })}
      </div>
      <div className="disc-total">
        <div className="score-ring big" style={{ "--progress": `${pct}%` } as React.CSSProperties}><span>{fmtNota(correcao.total)}</span></div>
        <div><b>{fmtNota(correcao.total)} de {fmtNota(max)} pontos</b><p>Nota apurada pela IA comparando sua resposta com o espelho da banca.</p></div>
      </div>
      {correcao.comentario && <p className="disc-comentario"><Sparkles size={13} /> {correcao.comentario}</p>}
    </article>
  );
}

// Mostrado quando a IA não conseguiu corrigir (raro) — sem autoavaliação manual.
function DiscCorrecaoIndisponivel() {
  return (
    <article className="card">
      <div className="disc-ia-fail"><CircleAlert size={18} /> <span>Não foi possível gerar a correção automática agora. Volte e envie sua resposta novamente em instantes.</span></div>
    </article>
  );
}

function TrialDiscursive({ onBack, onCreate }: { onBack: () => void; onCreate: () => void }) {
  const [phase, setPhase] = useState<"answer" | "reveal">("answer");
  const [current, setCurrent] = useState<DiscCase | null>(null);
  const [texto, setTexto] = useState("");
  const [espelho, setEspelho] = useState<DiscEspelho | null>(null);
  const [correcao, setCorrecao] = useState<DiscCorrecao | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/discursive/demo`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: DiscCase | null) => setCurrent(d))
      .catch(() => setError("Não foi possível carregar o exemplo."))
      .finally(() => setLoading(false));
  }, []);

  const submit = async () => {
    if (!current) return;
    setBusy(true); setError("");
    try {
      const r = await fetch(`${API_URL}/discursive/demo/submit`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_resposta: texto }),
      });
      if (!r.ok) throw new Error();
      const data = await r.json();
      setEspelho(data.espelho);
      setCorrecao(data.correcao ?? null);
      setPhase("reveal");
      trackTrial("discursive_submitted", { length: texto.length, texto });
    } catch {
      setError("Não foi possível revelar o espelho.");
    } finally { setBusy(false); }
  };

  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando o exemplo...</h2></section>;
  if (!current) return (
    <section className="card empty-state"><FileText size={30} /><h2>Exemplo indisponível no momento.</h2><button className="ghost compact" onClick={onBack}>Voltar aos resultados</button></section>
  );

  if (phase === "answer") {
    const estLinhas = Math.max(1, Math.ceil(texto.length / 75));
    const overLimit = estLinhas > current.limite_linhas;
    return (
      <section className="disc-layout">
        <div className="question-top">
          <div><span className="eyebrow">PROVA DISCURSIVA · EXEMPLO</span><h1>{current.tema}</h1></div>
          <button className="ghost compact" onClick={onBack}>Voltar</button>
        </div>
        <div className="focus-banner"><FileText size={16} /> <b>Prévia da prova escrita.</b> Aqui você experimenta o formato; no acesso completo há estudos de caso de TI e sua nota fica salva no histórico.</div>
        <article className="card">
          <div className="disc-enunciado">{current.enunciado}</div>
          {current.texto_apoio && <div className="disc-apoio">{current.texto_apoio}</div>}
        </article>
        <article className="card">
          <label className="disc-label">Sua resposta</label>
          <textarea className="disc-textarea" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escreva como na prova (introdução, desenvolvimento e conclusão). Depois você revela o espelho da banca." rows={12} />
          <div className="disc-meta-row">
            <span className={overLimit ? "over" : ""}>~{estLinhas} linhas (limite {current.limite_linhas})</span>
            <span>{texto.length} caracteres</span>
          </div>
          {error && <p className="test-error"><CircleAlert size={16} /> {error}</p>}
          <button className="primary" disabled={busy || texto.trim().length < 100} onClick={submit}>
            {busy ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />} Ver resposta comentada
          </button>
          <p className="disc-hint">O espelho só aparece depois que você responde — igual à prova. Sua resposta é registrada de forma <b>anônima</b> e pode ser usada para melhorar o app.</p>
        </article>
      </section>
    );
  }

  return (
    <section className="disc-layout">
      <div className="question-top">
        <div><span className="eyebrow">CORREÇÃO COMENTADA · EXEMPLO</span><h1>{current.tema}</h1><p>Sua resposta foi corrigida pela IA critério a critério — compare com o espelho da banca.</p></div>
        <button className="ghost compact" onClick={onBack}>Voltar</button>
      </div>
      <article className="card">
        <div className="card-heading"><div><span className="section-kicker">SUA RESPOSTA</span><h2>O que você escreveu</h2></div></div>
        <div className="disc-your-answer">{texto}</div>
      </article>
      {correcao ? <DiscCorrecaoPanel correcao={correcao} criteria={espelho!.criteria} max={espelho!.pontuacao_maxima} /> : <DiscCorrecaoIndisponivel />}
      <article className="card">
        <div className="card-heading"><div><span className="section-kicker">ESPELHO DA BANCA</span><h2>Resposta-modelo</h2></div></div>
        <div className="disc-model">{espelho!.model_answer}</div>
      </article>
      <article className="card">
        <div className="micro-aula"><span className="micro-aula-label"><BookOpen size={13} /> Micro Aula — como estruturar</span>{espelho!.micro_aula}</div>
      </article>
      <div className="results-actions">
        <button className="primary compact" onClick={onCreate}><Sparkles size={15} /> Criar minha conta</button>
        <button className="ghost compact" onClick={onBack}>Voltar aos resultados</button>
      </div>
    </section>
  );
}

// ============================ TELAS DE AUTENTICAÇÃO ============================

function AuthGate({ onAuthed, onTrial, notice = "" }: { onAuthed: (token: string) => void; onTrial: () => void; notice?: string }) {
  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);

  const switchMode = (next: "login" | "register" | "forgot") => {
    setMode(next);
    setError("");
    setInfo("");
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setInfo("");
    try {
      if (mode === "forgot") {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await response.json().catch(() => ({}));
        setInfo(data.detail ?? "Se houver uma conta com esse e-mail, enviamos um link para redefinir a senha.");
        setBusy(false);
        return;
      }
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const body =
        mode === "login"
          ? { email, password }
          : { email, password, full_name: fullName, gclid: getStoredGclid() };
      const response = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 422) setError("Verifique os dados. A senha precisa ter ao menos 8 caracteres.");
        else setError(typeof data.detail === "string" ? data.detail : "Não foi possível continuar.");
        setBusy(false);
        return;
      }
      onAuthed(data.access_token);
    } catch {
      setError("Falha de conexão. Tente novamente.");
      setBusy(false);
    }
  };

  const title = mode === "login" ? "Entrar na sua conta" : mode === "register" ? "Criar sua conta" : "Recuperar senha";
  const sub =
    mode === "login"
      ? "Estude para o TCE-SP 2026 com simulados e questões comentadas."
      : mode === "register"
      ? "Comece agora. Você confirmará seu e-mail para ativar a conta."
      : "Informe seu e-mail e enviaremos um link para você criar uma nova senha.";

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="gate-brand"><Sparkles size={22} /> Passa Fácil</div>
        <h1>{title}</h1>
        <p className="sub">{sub}</p>
        <div className="gate-ti-notice">
          <AlertTriangle size={18} />
          <span>
            <strong>Atenção:</strong> o conteúdo pago é focado exclusivamente na especialidade de{" "}
            <strong>Tecnologia da Informação (TI)</strong> do TCE-SP 2026. As demais especialidades
            ainda não têm conteúdo completo.
          </span>
        </div>
        {notice && !error && <div className="gate-ok">{notice}</div>}
        {error && <div className="gate-error">{error}</div>}
        {info && <div className="gate-ok">{info}</div>}
        <form onSubmit={submit}>
          {mode === "register" && (
            <label className="gate-field">
              <span>Nome completo</span>
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} required minLength={2} placeholder="Seu nome" />
            </label>
          )}
          <label className="gate-field">
            <span>E-mail</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="voce@email.com" />
          </label>
          {mode !== "forgot" && (
            <label className="gate-field">
              <span>Senha</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} placeholder="Mínimo 8 caracteres" />
            </label>
          )}
          {mode === "login" && (
            <div style={{ textAlign: "right", marginBottom: 12 }}>
              <button type="button" className="gate-linkbtn" onClick={() => switchMode("forgot")}>Esqueci minha senha</button>
            </div>
          )}
          <button className="primary" type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? <LoaderCircle className="spin" size={17} /> : null}
            {mode === "login" ? "Entrar" : mode === "register" ? "Criar conta" : "Enviar link de recuperação"}
          </button>
        </form>
        {mode !== "forgot" && (
          <button className="gate-secondary" onClick={onTrial}>Experimentar grátis (sem cadastro)</button>
        )}
        <div className="gate-switch">
          {mode === "login" ? (
            <>Ainda não tem conta? <button onClick={() => switchMode("register")}>Criar conta</button></>
          ) : mode === "register" ? (
            <>Já tem conta? <button onClick={() => switchMode("login")}>Entrar</button></>
          ) : (
            <>Lembrou a senha? <button onClick={() => switchMode("login")}>Voltar ao login</button></>
          )}
        </div>
        <nav className="gate-seo-links" aria-label="Conteúdo gratuito">
          <Link href="/questoes-comentadas">Questões comentadas VUNESP</Link>
          <Link href="/edital-tce-sp-2026">Edital TCE-SP 2026</Link>
          <Link href="/como-passar-tce-sp">Como passar no TCE-SP</Link>
          <Link href="/cronograma-estudos-tce-sp">Cronograma de estudos</Link>
        </nav>
      </div>
    </div>
  );
}

function VerifyScreen({ email, onRefresh, onLogout }: { email: string; onRefresh: () => void; onLogout: () => void }) {
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const resend = async () => {
    setBusy(true);
    await fetch(`${API_URL}/auth/resend-verification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }).catch(() => {});
    setSent(true);
    setBusy(false);
  };

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="gate-brand"><Mail size={22} /> Confirme seu e-mail</div>
        <h1>Falta um passo</h1>
        <p className="sub">Enviamos um link de ativação para <strong>{email}</strong>. Clique nele para liberar sua conta e depois volte aqui.</p>
        {sent && <div className="gate-ok">Se a conta ainda não estiver ativada, reenviamos o link.</div>}
        <button className="primary" style={{ width: "100%" }} onClick={onRefresh}>Já confirmei — atualizar</button>
        <button className="gate-secondary" onClick={resend} disabled={busy}>{busy ? "Enviando..." : "Reenviar e-mail de ativação"}</button>
        <div className="gate-switch"><button onClick={onLogout}>Sair</button></div>
      </div>
    </div>
  );
}

type Charge = { qr_image?: string; copy_paste?: string; payment_id?: string; already_active?: boolean };

function Paywall({ me, onRefresh, onLogout }: { me: Me; onRefresh: () => void; onLogout: () => void }) {
  const [cpf, setCpf] = useState("");
  const [charge, setCharge] = useState<Charge | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [checking, setChecking] = useState(false);
  const firstName = me.full_name.split(" ")[0] || "tudo certo";

  const generate = async () => {
    setBusy(true);
    setError("");
    try {
      const response = await authFetch(`${API_URL}/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cpf_cnpj: cpf, gclid: getStoredGclid() }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível gerar o Pix. Tente novamente.");
      } else if (data.already_active) {
        onRefresh();
      } else {
        setCharge(data);
      }
    } catch {
      setError("Falha de conexão. Tente novamente.");
    }
    setBusy(false);
  };

  useEffect(() => {
    if (!charge) return;
    const id = setInterval(async () => {
      try {
        const response = await authFetch(`${API_URL}/billing/status`, { cache: "no-store" });
        if (response.ok) {
          const data = await response.json();
          if (data.has_access) {
            clearInterval(id);
            reportConversion(data.conversion);
            onRefresh();
          }
        }
      } catch {
        /* ignora e tenta de novo */
      }
    }, 4000);
    return () => clearInterval(id);
  }, [charge, onRefresh]);

  const copy = async () => {
    if (!charge?.copy_paste) return;
    try {
      await navigator.clipboard.writeText(charge.copy_paste);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard bloqueado */
    }
  };

  const manualCheck = async () => {
    setChecking(true);
    try {
      const response = await authFetch(`${API_URL}/billing/status`, { cache: "no-store" });
      if (response.ok) {
        const data = await response.json();
        if (data.has_access) {
          reportConversion(data.conversion);
          onRefresh();
          return;
        }
      }
    } catch {
      /* ignora */
    }
    setChecking(false);
  };

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="gate-brand"><ShieldCheck size={22} /> Acesso completo</div>
        {!charge ? (
          <>
            <h1>Olá, {firstName}!</h1>
            <p className="sub">Sua conta está ativa. Libere o acesso completo com um pagamento único via Pix.</p>
            <div className="gate-ti-notice">
              <AlertTriangle size={18} />
              <span>
                <strong>Este acesso cobre apenas a especialidade de Tecnologia da Informação (TI).</strong>{" "}
                As outras especialidades do TCE-SP ainda não têm conteúdo completo — não pague
                esperando material de outra área.
              </span>
            </div>
            <div className="gate-price">R$ 25 <small>· pagamento único · acesso por 2 anos</small></div>
            <ul className="gate-hero-list">
              <li><Check size={18} /> Centenas de questões comentadas no estilo VUNESP</li>
              <li><Check size={18} /> Correção imediata + Micro Aula em cada questão</li>
              <li><Check size={18} /> Todo o conteúdo de TI + as matérias Gerais do TCE-SP 2026</li>
              <li><Check size={18} /> Simulado, revisões e caderno de erros</li>
              <li><Check size={18} /> Acesso válido por 2 anos a partir do pagamento</li>
            </ul>
            {error && <div className="gate-error">{error}</div>}
            <label className="gate-field">
              <span>CPF ou CNPJ (exigido pelo Pix)</span>
              <input value={cpf} onChange={(event) => setCpf(event.target.value)} inputMode="numeric" placeholder="Somente números" />
            </label>
            <button className="primary" style={{ width: "100%" }} disabled={busy || cpf.replace(/\D/g, "").length < 11} onClick={generate}>
              {busy ? <LoaderCircle className="spin" size={17} /> : null}
              Gerar Pix de R$ 25
            </button>
          </>
        ) : (
          <>
            <h1>Pague com Pix para liberar</h1>
            <p className="sub">Escaneie o QR Code no app do seu banco. O acesso é liberado <strong>automaticamente</strong> assim que o pagamento cair.</p>
            {charge.qr_image && (
              <img
                alt="QR Code Pix"
                src={`data:image/png;base64,${charge.qr_image}`}
                style={{ width: 220, height: 220, display: "block", margin: "10px auto", borderRadius: 8 }}
              />
            )}
            <label className="gate-field">
              <span>Pix copia e cola</span>
              <input readOnly value={charge.copy_paste ?? ""} onFocus={(event) => event.currentTarget.select()} />
            </label>
            <button className="gate-secondary" onClick={copy}>{copied ? "Copiado! ✓" : "Copiar código Pix"}</button>
            <p className="gate-note" style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "center" }}>
              <LoaderCircle className="spin" size={13} /> Aguardando o pagamento… esta tela libera sozinha.
            </p>
            <button className="primary" style={{ width: "100%", marginTop: 6 }} onClick={manualCheck} disabled={checking}>
              {checking ? "Verificando..." : "Já paguei — verificar agora"}
            </button>
          </>
        )}
        <div className="gate-switch"><button onClick={onLogout}>Sair</button></div>
      </div>
    </div>
  );
}

type ReviewQuestion = Question & {
  review_id: string;
  correct_option: number;
  explanation: string;
  due_date: string;
  interval_days: number;
};

function scopeParams(specialty: string, subjects: string[] | null): string {
  const params = new URLSearchParams();
  if (subjects && subjects.length) params.set("subjects", subjects.join(","));
  else params.set("specialty", specialty);
  return params.toString();
}

// =============================== P3 — RESULTADOS ===============================
function ResultsView({
  specialty, subjects, onFocusGaps, onRepeatAll,
}: {
  specialty: string;
  subjects: string[] | null;
  onFocusGaps: () => void;
  onRepeatAll: () => void;
}) {
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await authFetch(`${API_URL}/study/results?${scopeParams(specialty, subjects)}`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      setData(await response.json());
      setError("");
    } catch {
      setError("Não foi possível carregar seus resultados.");
    } finally {
      setLoading(false);
    }
  }, [specialty, subjects]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Calculando seus resultados...</h2></section>;
  if (error) return <section className="card empty-state"><CircleAlert size={30} /><h2>{error}</h2><button className="primary compact" onClick={load}>Tentar de novo</button></section>;
  if (!data) return null;

  const { overall } = data;
  if (!overall.attempts) {
    return (
      <section className="card empty-state">
        <TrendingUp size={34} />
        <h1>Ainda sem dados para mostrar</h1>
        <p>Responda algumas questões no simulado e volte aqui: vou mapear seus acertos por matéria e apontar onde focar.</p>
        <button className="primary compact" onClick={onRepeatAll}><Play size={16} fill="currentColor" /> Ir para o simulado</button>
      </section>
    );
  }
  const barColors = ["#7457e8", "#5776e8", "#ee8c43", "#ef5f67", "#2fa98a"];
  return (
    <section className="results-layout">
      <div className="question-top">
        <div>
          <span className="eyebrow">MEUS RESULTADOS</span>
          <h1>Onde você está e o que atacar</h1>
          <p>Com base nas suas respostas neste escopo de matérias.</p>
        </div>
      </div>

      <div className="results-cards">
        <section className="card readiness-card">
          <div className="card-heading"><div><span className="section-kicker">APROVEITAMENTO</span><h2>Acertos</h2></div><Trophy size={22} /></div>
          <div className="readiness">
            <div className="big-number">{overall.accuracy}<span>%</span></div>
            <div><b>{overall.correct} de {overall.attempts} respostas certas</b><p>Contando todas as tentativas registradas.</p></div>
          </div>
          <div className="mini-stats">
            <div><span>Respondidas</span><b>{overall.answered_distinct}</b></div>
            <div><span>Disponíveis</span><b>{overall.published}</b></div>
            <div><span>Cobertura</span><b>{overall.coverage}%</b></div>
          </div>
        </section>

        <section className="insight">
          <span className="insight-icon"><Target size={20} /></span>
          <div>
            <span>RECOMENDAÇÃO</span>
            {overall.all_questions_seen ? (
              <>
                <b>Você já viu todas as questões</b>
                <p>Hora de fixar: repita tudo para reforçar ou ataque só os pontos fracos.</p>
                <div className="results-actions">
                  <button className="primary compact" onClick={onFocusGaps}><Target size={15} /> Focar nos pontos fracos</button>
                  <button className="ghost compact" onClick={onRepeatAll}><RotateCcw size={15} /> Repetir tudo</button>
                </div>
              </>
            ) : (
              <>
                <b>Faltam {100 - overall.coverage}% das questões</b>
                <p>Você ainda não viu tudo. Avance no simulado ou foque agora nos seus pontos fracos.</p>
                <div className="results-actions">
                  <button className="primary compact" onClick={onFocusGaps}><Target size={15} /> Focar nos pontos fracos</button>
                  <button className="ghost compact" onClick={onRepeatAll}><Play size={15} fill="currentColor" /> Continuar simulado</button>
                </div>
              </>
            )}
          </div>
        </section>
      </div>

      {data.gaps.length > 0 && (
        <section className="card">
          <div className="card-heading"><div><span className="section-kicker">PRIORIDADE</span><h2>Seus maiores gaps</h2></div><AlertTriangle size={20} /></div>
          <div className="gap-list">
            {data.gaps.map((gap) => (
              <div className="gap-row" key={gap.slug}>
                <div className="gap-name">
                  <b>{gap.name}</b>
                  <small>
                    {gap.attempts >= 3 && gap.accuracy !== null
                      ? `${gap.accuracy}% de acerto`
                      : gap.attempts > 0
                        ? `poucas respostas (${gap.attempts})`
                        : "ainda não iniciada"}
                    {" · "}cobertura {gap.coverage}%
                  </small>
                </div>
                <span className={`gap-badge ${gap.accuracy !== null && gap.accuracy < 60 ? "low" : "mid"}`}>
                  {gap.accuracy !== null && gap.attempts >= 3 ? `${gap.accuracy}%` : "novo"}
                </span>
              </div>
            ))}
          </div>
          <button className="primary compact" onClick={onFocusGaps}><Target size={16} /> Treinar meus pontos fracos</button>
        </section>
      )}

      <section className="card performance">
        <div className="card-heading"><div><span className="section-kicker">DESEMPENHO</span><h2>Acerto por matéria</h2></div></div>
        <div className="subject-grid">
          {data.subjects.map((subject, index) => (
            <div className="subject" key={subject.slug}>
              <div>
                <span>{subject.name} · {subject.attempts} resp. · cob. {subject.coverage}%</span>
                <b>{subject.accuracy === null ? "—" : `${subject.accuracy}%`}</b>
              </div>
              <div className="bar"><i style={{ width: `${subject.accuracy ?? 0}%`, background: barColors[index % barColors.length] }} /></div>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}

// ================================ P4 — MODO TESTE ================================
function TestView({ specialty, subjects }: { specialty: string; subjects: string[] | null }) {
  const [phase, setPhase] = useState<"config" | "running" | "done">("config");
  const [mode, setMode] = useState<"random" | "fixed">("random");
  const [size, setSize] = useState(20);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const start = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams(scopeParams(specialty, subjects));
      params.set("mode", mode);
      params.set("size", String(size));
      const response = await authFetch(`${API_URL}/study/test?${params.toString()}`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      const body = await response.json();
      if (!body.questions?.length) { setError("Não há questões suficientes nesse escopo."); return; }
      setQuestions(body.questions);
      setAnswers({});
      setIndex(0);
      setResult(null);
      setPhase("running");
    } catch {
      setError("Não foi possível montar o teste.");
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = { answers: questions.map((q) => ({ question_id: q.id, selected_option: answers[q.id] ?? null })) };
      const response = await authFetch(`${API_URL}/study/test/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error();
      setResult(await response.json());
      setPhase("done");
    } catch {
      setError("Não foi possível corrigir o teste.");
    } finally {
      setLoading(false);
    }
  };

  if (phase === "config") {
    return (
      <section className="test-layout">
        <div className="question-top">
          <div>
            <span className="eyebrow">MODO TESTE</span>
            <h1>Simulado curto, correção no fim</h1>
            <p>Responda sem ver o gabarito; a correção comentada sai só quando você finaliza — como na prova.</p>
          </div>
        </div>
        <article className="card">
          <div className="test-config">
            <div className="config-block">
              <span className="config-label">Quantas questões</span>
              <div className="chip-row">
                {[10, 20, 40, 80].map((n) => (
                  <button key={n} className={`chip ${size === n ? "on" : ""}`} onClick={() => setSize(n)}>{n}{n === 80 ? " (prova)" : ""}</button>
                ))}
              </div>
            </div>
            <div className="config-block">
              <span className="config-label">Seleção</span>
              <div className="chip-row">
                <button className={`chip ${mode === "random" ? "on" : ""}`} onClick={() => setMode("random")}>Aleatórias</button>
                <button className={`chip ${mode === "fixed" ? "on" : ""}`} onClick={() => setMode("fixed")}>Fixas</button>
              </div>
              <small className="config-hint">{mode === "fixed" ? "Sempre o mesmo conjunto — bom para medir evolução." : "Sorteio novo a cada teste, priorizando questões que você ainda não respondeu."} Espelha a proporção da prova: 75% TI, 25% Gerais.</small>
            </div>
          </div>
          {error && <p className="test-error"><CircleAlert size={16} /> {error}</p>}
          <button className="primary" disabled={loading} onClick={start}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />} Iniciar teste
          </button>
        </article>
      </section>
    );
  }

  if (phase === "running") {
    const q = questions[index];
    const answeredCount = Object.keys(answers).length;
    return (
      <section className="test-layout">
        <div className="question-top">
          <div><span className="eyebrow">MODO TESTE</span><h1>Responda com calma</h1><p>Você pode voltar e mudar antes de finalizar.</p></div>
          <div className="question-count">{index + 1}<span>/{questions.length}</span></div>
        </div>
        <div className="test-progress"><i style={{ width: `${(answeredCount / questions.length) * 100}%` }} /></div>
        <article className="card question-card">
          <div className="question-meta"><span>{q.subject}</span><i>{q.topic}</i></div>
          <h2>{q.statement}</h2>
          <div className="options">
            {q.options.map((option, optionIndex) => (
              <button
                key={option}
                onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: optionIndex }))}
                className={`option ${answers[q.id] === optionIndex ? "selected" : ""}`}
              >
                <span>{String.fromCharCode(65 + optionIndex)}</span>{option}
              </button>
            ))}
          </div>
          <div className="question-actions test-nav">
            <button className="ghost compact" disabled={index === 0} onClick={() => setIndex((i) => Math.max(0, i - 1))}>Anterior</button>
            {index + 1 < questions.length ? (
              <button className="primary compact" onClick={() => setIndex((i) => Math.min(questions.length - 1, i + 1))}>Próxima <ArrowRight size={16} /></button>
            ) : (
              <button className="primary compact" disabled={loading} onClick={submit}>{loading ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />} Finalizar</button>
            )}
          </div>
          <div className="test-jump">
            {questions.map((qq, i) => (
              <button
                key={qq.id}
                className={`jump ${i === index ? "current" : ""} ${answers[qq.id] !== undefined ? "done" : ""}`}
                onClick={() => setIndex(i)}
                aria-label={`Ir para questão ${i + 1}`}
              >{i + 1}</button>
            ))}
          </div>
          {answeredCount < questions.length && (
            <button className="finish-early" disabled={loading} onClick={submit}>Finalizar mesmo com {questions.length - answeredCount} em branco</button>
          )}
          {error && <p className="test-error"><CircleAlert size={16} /> {error}</p>}
        </article>
      </section>
    );
  }

  // phase === "done"
  const r = result!;
  const qById: Record<string, Question> = Object.fromEntries(questions.map((q) => [q.id, q]));
  return (
    <section className="test-layout">
      <div className="question-top">
        <div><span className="eyebrow">RESULTADO DO TESTE</span><h1>Você acertou {r.correct} de {r.total}</h1><p>As tentativas já entraram nos seus resultados e revisões.</p></div>
        <div className="score-ring big" style={{ "--progress": `${r.accuracy}%` } as React.CSSProperties}><span>{r.accuracy}%</span></div>
      </div>
      {r.by_subject.length > 0 && (
        <section className="card performance">
          <div className="card-heading"><div><span className="section-kicker">POR MATÉRIA</span><h2>Como você foi</h2></div></div>
          <div className="subject-grid">
            {r.by_subject.map((s, i) => (
              <div className="subject" key={s.subject}>
                <div><span>{s.subject} · {s.correct}/{s.total}</span><b>{s.accuracy}%</b></div>
                <div className="bar"><i style={{ width: `${s.accuracy}%`, background: ["#7457e8", "#5776e8", "#ee8c43", "#ef5f67"][i % 4] }} /></div>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="card">
        <div className="card-heading"><div><span className="section-kicker">CORREÇÃO COMENTADA</span><h2>Revise cada questão</h2></div></div>
        <div className="review-list">
          {r.details.map((d, i) => {
            const q = qById[d.question_id];
            return (
              <article className={`review-item ${d.is_correct ? "ok" : "no"}`} key={d.question_id}>
                <div className="review-head">
                  <span className="review-num">{i + 1}</span>
                  <span className="review-tag">{d.subject} · {d.topic}</span>
                  <span className={`review-badge ${d.is_correct ? "ok" : "no"}`}>{d.is_correct ? "Acertou" : "Errou"}</span>
                </div>
                {q && <p className="review-statement">{q.statement}</p>}
                {q && (
                  <p className="answer-line">
                    <span className="tag">Correta</span>
                    <b>{String.fromCharCode(65 + d.correct_option)}</b> {q.options[d.correct_option]}
                  </p>
                )}
                {q && !d.is_correct && (
                  <p className="answer-line chosen">
                    <span className="tag">Você marcou</span>
                    {d.selected_option === null ? <em>em branco</em> : <><b>{String.fromCharCode(65 + d.selected_option)}</b> {q.options[d.selected_option]}</>}
                  </p>
                )}
                <div className="teach"><span className="teach-label">Por quê</span>{d.explanation}</div>
              </article>
            );
          })}
        </div>
        <button className="primary compact" onClick={() => setPhase("config")}><RotateCcw size={16} /> Novo teste</button>
      </section>
    </section>
  );
}

// ============================ P5 — ESTUDO DE CASO (discursivas) ============================
function DiscursiveView() {
  const [phase, setPhase] = useState<"list" | "answer" | "reveal">("list");
  const [cases, setCases] = useState<DiscCaseItem[]>([]);
  const [current, setCurrent] = useState<DiscCase | null>(null);
  const [texto, setTexto] = useState("");
  const [espelho, setEspelho] = useState<DiscEspelho | null>(null);
  const [correcao, setCorrecao] = useState<DiscCorrecao | null>(null);
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const r = await authFetch(`${API_URL}/discursive/cases`, { cache: "no-store" });
      if (!r.ok) throw new Error();
      setCases(await r.json());
      setError("");
    } catch {
      setError("Não foi possível carregar os estudos de caso.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadList(); }, [loadList]);

  const openCase = async (id: string) => {
    setBusy(true); setError("");
    try {
      const r = await authFetch(`${API_URL}/discursive/cases/${id}`, { cache: "no-store" });
      if (!r.ok) throw new Error();
      setCurrent(await r.json());
      setTexto(""); setEspelho(null); setCorrecao(null); setSubmissionId(null);
      setPhase("answer");
    } catch {
      setError("Não foi possível abrir o caso.");
    } finally { setBusy(false); }
  };

  const submit = async () => {
    if (!current) return;
    setBusy(true); setError("");
    try {
      const r = await authFetch(`${API_URL}/discursive/cases/${current.id}/submit`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_resposta: texto }),
      });
      if (!r.ok) throw new Error();
      const data = await r.json();
      setSubmissionId(data.submission_id);
      setEspelho(data.espelho);
      setCorrecao(data.correcao ?? null);
      setPhase("reveal");
    } catch {
      setError("Não foi possível registrar sua resposta.");
    } finally { setBusy(false); }
  };

  // ---- LISTA ----
  if (phase === "list") {
    if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando estudos de caso...</h2></section>;
    return (
      <section className="disc-layout">
        <div className="question-top">
          <div><span className="eyebrow">PROVA DISCURSIVA</span><h1>Estudos de caso</h1><p>Responda como na prova; depois revele o espelho da banca e a micro-aula de como estruturar.</p></div>
        </div>
        {error && <p className="test-error"><CircleAlert size={16} /> {error}</p>}
        {cases.length === 0 ? (
          <section className="card empty-state"><FileText size={30} /><p>Nenhum estudo de caso disponível ainda.</p></section>
        ) : (
          <div className="disc-grid">
            {cases.map((c) => (
              <button className="disc-card" key={c.id} disabled={busy} onClick={() => openCase(c.id)}>
                <div className="disc-card-top">
                  <span className={`disc-badge ${c.tipo === "estudo_caso" ? "case" : c.tipo === "dissertativa" ? "diss" : "parecer"}`}>
                    {c.tipo === "estudo_caso" ? "Estudo de caso" : c.tipo === "dissertativa" ? "Dissertativa" : "Parecer"}
                  </span>
                  {c.is_demo && <span className="disc-badge demo">Exemplo de método</span>}
                </div>
                <b>{c.tema}</b>
                <small>{c.disciplina} · {c.pontuacao_maxima} pts · até {c.limite_linhas} linhas</small>
              </button>
            ))}
          </div>
        )}
      </section>
    );
  }

  // ---- RESPONDER ----
  if (phase === "answer" && current) {
    const estLinhas = Math.max(1, Math.ceil(texto.length / 75));
    const overLimit = estLinhas > current.limite_linhas;
    return (
      <section className="disc-layout">
        <div className="question-top">
          <div><span className="eyebrow">{current.disciplina.toUpperCase()}</span><h1>{current.tema}</h1></div>
          <button className="ghost compact" onClick={() => setPhase("list")}>Voltar</button>
        </div>
        {current.is_demo && (
          <div className="focus-banner"><FileText size={16} /> Este é um <b>exemplo de método</b> (não é conteúdo de TI) — serve para treinar como se estrutura e raciocina a resposta.</div>
        )}
        <article className="card">
          <div className="disc-enunciado">{current.enunciado}</div>
          {current.texto_apoio && <div className="disc-apoio">{current.texto_apoio}</div>}
        </article>
        <article className="card">
          <label className="disc-label">Sua resposta</label>
          <textarea
            className="disc-textarea"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escreva sua resposta como na prova (introdução, desenvolvimento e conclusão). Depois você revela o espelho da banca."
            rows={12}
          />
          <div className="disc-meta-row">
            <span className={overLimit ? "over" : ""}>~{estLinhas} linhas (limite {current.limite_linhas})</span>
            <span>{texto.length} caracteres</span>
          </div>
          {error && <p className="test-error"><CircleAlert size={16} /> {error}</p>}
          <button className="primary" disabled={busy || texto.trim().length < 100} onClick={submit}>
            {busy ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />} Ver resposta comentada
          </button>
          <p className="disc-hint">O espelho só aparece depois que você responde — igual à prova, sem espiar o gabarito antes.</p>
        </article>
      </section>
    );
  }

  // ---- REVELAR (espelho + autoavaliação + micro-aula) ----
  if (phase === "reveal" && current && espelho) {
    return (
      <section className="disc-layout">
        <div className="question-top">
          <div><span className="eyebrow">CORREÇÃO COMENTADA</span><h1>{current.tema}</h1><p>Sua resposta foi corrigida pela IA critério a critério; a nota fica salva no seu histórico.</p></div>
          <button className="ghost compact" onClick={() => setPhase("list")}>Outros casos</button>
        </div>

        <article className="card">
          <div className="card-heading"><div><span className="section-kicker">SUA RESPOSTA</span><h2>O que você escreveu</h2></div></div>
          <div className="disc-your-answer">{texto}</div>
        </article>

        {correcao ? <DiscCorrecaoPanel correcao={correcao} criteria={espelho.criteria} max={espelho.pontuacao_maxima} /> : <DiscCorrecaoIndisponivel />}

        <article className="card">
          <div className="card-heading"><div><span className="section-kicker">ESPELHO DA BANCA</span><h2>Resposta-modelo</h2></div></div>
          <div className="disc-model">{espelho.model_answer}</div>
        </article>

        <article className="card">
          <div className="micro-aula"><span className="micro-aula-label"><BookOpen size={13} /> Micro Aula — como estruturar</span>{espelho.micro_aula}</div>
        </article>
      </section>
    );
  }

  return null;
}

// ===================== ADMIN — painel do teste grátis (telemetria anônima) =====================
type TrialAnalytics = {
  visitors: number;
  events: number;
  first: string | null;
  last: string | null;
  funnel: { key: string; label: string; count: number; pct: number }[];
  questions: { subject: string; total: number; correct: number; accuracy: number }[];
  discursive: { count: number; avg_length: number; items: { created_at: string; length: number; texto: string }[] };
};

function TrialAnalyticsView() {
  const [data, setData] = useState<TrialAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await authFetch(`${API_URL}/study/trial/analytics${days ? `?days=${days}` : ""}`, { cache: "no-store" });
      if (!r.ok) throw new Error();
      setData(await r.json());
      setError("");
    } catch {
      setError("Não foi possível carregar o painel.");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  const periods: [string, number | null][] = [["Tudo", null], ["30 dias", 30], ["7 dias", 7]];
  const barColors = ["#7457e8", "#5776e8", "#ee8c43", "#ef5f67", "#2fa98a"];

  const header = (
    <div className="question-top">
      <div>
        <span className="eyebrow">ADMIN · TESTE GRÁTIS</span>
        <h1>Quem está simulando</h1>
        <p>Telemetria anônima do test-drive: funil, questões acessadas e as dissertativas escritas.</p>
      </div>
      <div className="chip-row trial-period">
        {periods.map(([label, d]) => (
          <button key={label} className={days === d ? "chip on" : "chip"} onClick={() => setDays(d)}>{label}</button>
        ))}
      </div>
    </div>
  );

  if (loading) return <section className="results-layout">{header}<section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando o painel...</h2></section></section>;
  if (error) return <section className="results-layout">{header}<section className="card empty-state"><CircleAlert size={30} /><h2>{error}</h2><button className="primary compact" onClick={load}>Tentar de novo</button></section></section>;
  if (!data) return null;

  return (
    <section className="results-layout">
      {header}

      {data.events === 0 ? (
        <section className="card empty-state">
          <BarChart3 size={34} />
          <h1>Ainda sem dados neste período</h1>
          <p>Quando visitantes usarem o teste grátis, o funil, as questões e as dissertativas aparecem aqui.</p>
        </section>
      ) : (
        <>
          <div className="results-cards">
            <section className="card readiness-card">
              <div className="card-heading"><div><span className="section-kicker">ALCANCE</span><h2>Visitantes</h2></div><TrendingUp size={22} /></div>
              <div className="readiness">
                <div className="big-number">{data.visitors}</div>
                <div><b>{data.events} eventos registrados</b><p>{data.first ? `desde ${new Date(data.first).toLocaleDateString("pt-BR")}` : ""}</p></div>
              </div>
            </section>
            <section className="insight">
              <span className="insight-icon"><FileText size={20} /></span>
              <div>
                <span>DISSERTATIVAS</span>
                <b>{data.discursive.count} escritas</b>
                <p>{data.discursive.count ? `tamanho médio de ${data.discursive.avg_length} caracteres` : "ninguém escreveu ainda"}</p>
              </div>
            </section>
          </div>

          <section className="card performance">
            <div className="card-heading"><div><span className="section-kicker">FUNIL</span><h2>Até onde os visitantes vão</h2></div></div>
            <div className="subject-grid">
              {data.funnel.map((f, i) => (
                <div className="subject" key={f.key}>
                  <div><span>{f.label} · {f.count} visit.</span><b>{f.pct}%</b></div>
                  <div className="bar"><i style={{ width: `${f.pct}%`, background: barColors[i % barColors.length] }} /></div>
                </div>
              ))}
            </div>
          </section>

          {data.questions.length > 0 && (
            <section className="card performance">
              <div className="card-heading"><div><span className="section-kicker">QUESTÕES</span><h2>Acessos e acerto na amostra</h2></div></div>
              <div className="subject-grid">
                {data.questions.map((q, i) => (
                  <div className="subject" key={`${q.subject}-${i}`}>
                    <div><span>{q.subject} · {q.total} resp.</span><b>{q.accuracy}%</b></div>
                    <div className="bar"><i style={{ width: `${q.accuracy}%`, background: barColors[i % barColors.length] }} /></div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {data.discursive.items.length > 0 && (
            <section className="card">
              <div className="card-heading"><div><span className="section-kicker">DISSERTATIVAS</span><h2>O que escreveram ({data.discursive.count})</h2></div></div>
              <div className="trial-subs">
                {data.discursive.items.map((s, i) => (
                  <div className="trial-sub" key={i}>
                    <div className="trial-sub-head"><b>#{data.discursive.items.length - i}</b><span>{new Date(s.created_at).toLocaleString("pt-BR")} · {s.length} caracteres</span></div>
                    <p className="trial-sub-text">{s.texto || "(vazio)"}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </section>
  );
}

function ReviewView() {
  const [items, setItems] = useState<ReviewQuestion[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<(AnswerResult & { next_review: string }) | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const response = await authFetch(`${API_URL}/reviews/due`, { cache: "no-store" });
    setItems(response.ok ? await response.json() : []);
    setSelected(null);
    setResult(null);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  const item = items[0];

  const answerReview = async () => {
    if (!item || selected === null) return;
    const response = await authFetch(`${API_URL}/reviews/${item.review_id}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_option: selected }),
    });
    if (response.ok) setResult(await response.json());
  };

  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Buscando revisões...</h2></section>;
  if (!item) return (
    <section className="card empty-state success-state">
      <Check size={38} /><h1>Revisões em dia.</h1><p>Quando uma questão precisar ser reforçada, ela aparecerá aqui automaticamente.</p>
    </section>
  );
  return (
    <section className="question-layout">
      <div className="question-top"><div><span className="eyebrow">REPETIÇÃO ESPAÇADA</span><h1>Revisão de hoje</h1><p>{items.length} {items.length === 1 ? "item pendente" : "itens pendentes"}.</p></div><div className="question-count">{items.length}</div></div>
      <article className="card question-card">
        <div className="question-meta"><span>{item.subject}</span><i>Intervalo atual: {item.interval_days} dia(s)</i></div>
        <h2>{item.statement}</h2>
        <div className="options">
          {item.options.map((option, index) => (
            <button
              key={option}
              disabled={Boolean(result)}
              onClick={() => setSelected(index)}
              className={`option ${selected === index ? "selected" : ""} ${result && index === result.correct_option ? "correct" : ""} ${result && index === selected && !result.is_correct ? "wrong" : ""}`}
            ><span>{String.fromCharCode(65 + index)}</span>{option}</button>
          ))}
        </div>
        {result && <div className={result.is_correct ? "feedback correct-feedback" : "feedback wrong-feedback"}><b>{result.is_correct ? "Memória reforçada." : "Vamos rever novamente amanhã."}</b><p>{result.explanation}</p><small>Próxima revisão: {new Date(`${result.next_review}T12:00:00`).toLocaleDateString("pt-BR")}</small></div>}
        <div className="question-actions">
          {result ? <button className="primary compact" onClick={load}>Próxima revisão</button> : <button className="primary compact" disabled={selected === null} onClick={answerReview}>Verificar memória</button>}
        </div>
      </article>
    </section>
  );
}

type ErrorItem = Question & {
  attempt_id: string;
  selected_option: number;
  correct_option: number;
  explanation: string;
  answered_at: string;
};

function ErrorNotebook({ onPractice }: { onPractice: () => void }) {
  const [items, setItems] = useState<ErrorItem[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    authFetch(`${API_URL}/reviews/errors`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);
  if (loading) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Montando seu caderno...</h2></section>;
  return (
    <section>
      <div className="question-top"><div><span className="eyebrow">CADERNO DE ERROS</span><h1>Aprenda com seus tropeços</h1><p>Uma questão aparece uma vez, mesmo que você tenha errado mais de uma tentativa.</p></div><div className="question-count">{items.length}</div></div>
      {!items.length ? (
        <section className="card empty-state success-state"><Check size={38} /><h2>Nenhum erro registrado.</h2><p>Responda questões para iniciar seu diagnóstico.</p><button className="primary compact" onClick={onPractice}>Praticar agora</button></section>
      ) : (
        <div className="error-grid">
          {items.map((item) => (
            <article className="card error-card" key={item.attempt_id}>
              <div className="question-meta"><span>{item.subject}</span><i>{item.topic}</i></div>
              <h2>{item.statement}</h2>
              <p className="your-answer"><b>Sua resposta:</b> {item.options[item.selected_option]}</p>
              <p className="right-answer"><b>Resposta correta:</b> {item.options[item.correct_option]}</p>
              <div className="explanation">{item.explanation}</div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

type ImportJob = {
  id: string;
  filename: string;
  source_name: string;
  document_type: string;
  rights_status: string;
  status: string;
  page_count: number | null;
  candidate_count: number;
};

type DraftQuestion = {
  id: string;
  exam_job_id: string;
  source_name: string | null;
  question_number: number;
  statement: string;
  options: string[];
  correct_option: number | null;
  confidence: string;
  status: string;
  topic_id: string | null;
  reviewer_note: string | null;
  page_number: number | null;
  image_url: string | null;
};

type TopicOption = { id: string; name: string; slug: string };

function QuestionBankView() {
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("Prova oficial");
  const [documentType, setDocumentType] = useState("exam");
  const [rightsStatus, setRightsStatus] = useState("owner_only");
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [examJob, setExamJob] = useState("");
  const [keyJob, setKeyJob] = useState("");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [drafts, setDrafts] = useState<DraftQuestion[]>([]);
  const [topics, setTopics] = useState<TopicOption[]>([]);
  const [selectedDraftId, setSelectedDraftId] = useState("");
  const [savingDraft, setSavingDraft] = useState(false);

  const loadJobs = useCallback(() => {
    authFetch(`${API_URL}/question-bank/pdf/jobs`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then(setJobs);
  }, []);
  useEffect(() => { loadJobs(); }, [loadJobs]);
  const loadDrafts = useCallback(() => {
    authFetch(`${API_URL}/question-bank/drafts?status=pending`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then((items: DraftQuestion[]) => {
        setDrafts(items);
        setSelectedDraftId((current) => current || items[0]?.id || "");
      });
  }, []);
  useEffect(() => {
    loadDrafts();
    authFetch(`${API_URL}/question-bank/topics`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then(setTopics);
  }, [loadDrafts]);
  const selectedDraft = drafts.find((draft) => draft.id === selectedDraftId) ?? null;

  const changeDraft = (patch: Partial<DraftQuestion>) => {
    setDrafts((current) => current.map((draft) => (
      draft.id === selectedDraftId ? { ...draft, ...patch } : draft
    )));
  };

  const saveDraft = async (status: "pending" | "reviewed" | "rejected") => {
    if (!selectedDraft) return;
    setSavingDraft(true);
    const response = await authFetch(`${API_URL}/question-bank/drafts/${selectedDraft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        statement: selectedDraft.statement,
        options: selectedDraft.options,
        correct_option: selectedDraft.correct_option,
        topic_id: selectedDraft.topic_id,
        reviewer_note: selectedDraft.reviewer_note,
        status,
      }),
    });
    const data = await response.json();
    if (response.ok) {
      setMessage(status === "reviewed" ? "Questão revisada e pronta para o banco." : status === "rejected" ? "Questão descartada." : "Rascunho salvo.");
      setSelectedDraftId("");
      loadDrafts();
    } else {
      setMessage(typeof data.detail === "string" ? data.detail : "Não foi possível salvar a revisão.");
    }
    setSavingDraft(false);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setMessage("");
    const body = new FormData();
    body.append("file", file);
    body.append("source_name", sourceName);
    body.append("document_type", documentType);
    body.append("rights_status", rightsStatus);
    const response = await authFetch(`${API_URL}/question-bank/pdf/inspect`, { method: "POST", body });
    const data = await response.json();
    if (response.ok) {
      setMessage(`PDF inspecionado: ${data.page_count} página(s) e ${data.candidate_count} questão(ões) candidata(s). Nada foi publicado.`);
      setFile(null);
      loadJobs();
    } else {
      setMessage(data.detail ?? "Não foi possível inspecionar o PDF.");
    }
    setUploading(false);
  };

  const associate = async () => {
    if (!examJob || !keyJob) return;
    setUploading(true);
    const response = await authFetch(`${API_URL}/question-bank/pdf/associate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exam_job_id: examJob, answer_key_job_id: keyJob }),
    });
    const data = await response.json();
    if (response.ok) {
      setMessage(`${data.matched_answers} respostas associadas; ${data.ready_for_review} questões prontas para revisão.`);
      loadJobs();
    } else {
      setMessage(typeof data.detail === "string" ? data.detail : "Não foi possível associar os documentos.");
    }
    setUploading(false);
  };

  return (
    <section>
      <div className="question-top">
        <div><span className="eyebrow">ÁREA PROPRIETÁRIA</span><h1>Banco de questões</h1><p>Envie provas e gabaritos para inspeção. A publicação sempre exige uma etapa posterior.</p></div>
        <div className="question-count">{jobs.reduce((sum, job) => sum + job.candidate_count, 0)}</div>
      </div>
      <div className="bank-grid">
        <section className="card upload-card">
          <div className="sim-icon"><FileUp size={29} /></div>
          <h2>Inspecionar novo PDF</h2>
          <p>O arquivo fica privado, o texto é extraído e as questões são apenas sugeridas para revisão.</p>
          <label>Fonte<input value={sourceName} onChange={(event) => setSourceName(event.target.value)} /></label>
          <div className="form-row">
            <label>Documento<select value={documentType} onChange={(event) => setDocumentType(event.target.value)}><option value="exam">Prova</option><option value="answer_key">Gabarito</option></select></label>
            <label>Uso permitido<select value={rightsStatus} onChange={(event) => setRightsStatus(event.target.value)}><option value="owner_only">Somente proprietário</option><option value="research_only">Somente pesquisa</option><option value="licensed">Licenciado</option><option value="public_domain">Domínio público</option><option value="authorial">Autoral</option></select></label>
          </div>
          <label className="file-field"><input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /><span>{file ? file.name : "Selecionar PDF"}</span></label>
          <button className="primary" disabled={!file || uploading || !sourceName.trim()} onClick={upload}>{uploading ? <LoaderCircle className="spin" size={17} /> : <FileUp size={17} />}{uploading ? "Analisando..." : "Inspecionar sem publicar"}</button>
          {message && <div className="import-message">{message}</div>}
        </section>
        <section className="card jobs-card">
          <div className="card-heading"><div><span className="section-kicker">HISTÓRICO</span><h2>Arquivos inspecionados</h2></div></div>
          <div className="association-box">
            <b>Associar prova e gabarito</b>
            <div className="form-row">
              <select value={examJob} onChange={(event) => setExamJob(event.target.value)}>
                <option value="">Selecione a prova</option>
                {jobs.filter((job) => job.document_type === "exam" && job.status === "review").map((job) => <option key={job.id} value={job.id}>{job.filename}</option>)}
              </select>
              <select value={keyJob} onChange={(event) => setKeyJob(event.target.value)}>
                <option value="">Selecione o gabarito</option>
                {jobs.filter((job) => job.document_type === "answer_key" && job.status === "review").map((job) => <option key={job.id} value={job.id}>{job.filename}</option>)}
              </select>
            </div>
            <button className="secondary" disabled={!examJob || !keyJob || uploading} onClick={associate}>Cruzar documentos</button>
          </div>
          {!jobs.length ? <p className="no-data">Nenhum PDF enviado ainda.</p> : jobs.map((job) => (
            <div className="job" key={job.id}>
              <span className="job-icon"><Database size={17} /></span>
              <div><b>{job.filename}</b><small>{job.source_name} · {job.document_type === "exam" ? "Prova" : "Gabarito"}</small></div>
              <div className="job-stats"><b>{job.candidate_count}</b><span>candidatas</span></div>
              <i className={`status ${job.status}`}>{job.status}</i>
            </div>
          ))}
        </section>
      </div>
      <section className="card review-workspace">
        <div className="card-heading">
          <div><span className="section-kicker">REVISÃO HUMANA</span><h2>Oficina de questões</h2></div>
          <span className="review-count">{drafts.length} pendentes</span>
        </div>
        {!selectedDraft ? <p className="no-data">Não há questões pendentes para revisar.</p> : (
          <div className="review-grid">
            <aside className="draft-list">
              {drafts.map((draft) => (
                <button key={draft.id} className={draft.id === selectedDraftId ? "active" : ""} onClick={() => setSelectedDraftId(draft.id)}>
                  <b>Questão {draft.question_number}</b>
                  <span>{draft.source_name}</span>
                  <i>{draft.image_url ? "visual disponível" : draft.confidence}</i>
                </button>
              ))}
            </aside>
            <div className="draft-editor">
              <div className="draft-source">
                <b>Questão {selectedDraft.question_number}</b>
                <span>{selectedDraft.source_name}{selectedDraft.page_number ? ` · página ${selectedDraft.page_number}` : ""}</span>
              </div>
              {selectedDraft.image_url && (
                <details className="visual-reference">
                  <summary>Comparar com o recorte original</summary>
                  <img src={`${API_ORIGIN}${selectedDraft.image_url}`} alt={`Questão ${selectedDraft.question_number} no PDF original`} />
                </details>
              )}
              <label>Enunciado<textarea value={selectedDraft.statement} onChange={(event) => changeDraft({ statement: event.target.value })} /></label>
              <div className="draft-options">
                {selectedDraft.options.map((option, index) => (
                  <label key={index}>
                    <input type="radio" name="correct-option" checked={selectedDraft.correct_option === index} onChange={() => changeDraft({ correct_option: index })} />
                    <span>{String.fromCharCode(65 + index)}</span>
                    <textarea value={option} onChange={(event) => changeDraft({ options: selectedDraft.options.map((item, itemIndex) => itemIndex === index ? event.target.value : item) })} />
                  </label>
                ))}
              </div>
              <div className="form-row">
                <label>Tópico<select value={selectedDraft.topic_id ?? ""} onChange={(event) => changeDraft({ topic_id: event.target.value || null })}><option value="">Classificar...</option>{topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.name}</option>)}</select></label>
                <label>Nota editorial<input value={selectedDraft.reviewer_note ?? ""} onChange={(event) => changeDraft({ reviewer_note: event.target.value })} placeholder="Comentário ou correção necessária" /></label>
              </div>
              <div className="review-actions">
                <button className="secondary reject" disabled={savingDraft} onClick={() => saveDraft("rejected")}>Descartar</button>
                <button className="secondary" disabled={savingDraft} onClick={() => saveDraft("pending")}>Salvar rascunho</button>
                <button className="primary compact" disabled={savingDraft || !selectedDraft.topic_id || selectedDraft.correct_option === null} onClick={() => saveDraft("reviewed")}>{savingDraft ? "Salvando..." : "Aprovar revisão"}</button>
              </div>
            </div>
          </div>
        )}
      </section>
    </section>
  );
}
