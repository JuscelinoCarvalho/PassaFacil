"use client";

import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  Database,
  FileUp,
  Gauge,
  Headphones,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  NotebookPen,
  Play,
  RotateCcw,
  Settings,
  Sparkles,
  Target,
  Trophy,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:9000/api/v1";
const API_ORIGIN = API_URL.replace(/\/api\/v1$/, "");

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

type AnswerResult = {
  is_correct: boolean;
  correct_option: number;
  explanation: string;
};

const taskIcons = {
  theory: BookOpen,
  review: RotateCcw,
  questions: Target,
  audio: Headphones,
};

const nav = [
  ["Hoje", LayoutDashboard, "today"],
  ["Plano de estudos", CalendarDays, "today"],
  ["Questões", NotebookPen, "questions"],
  ["Simulados", Gauge, "simulations"],
  ["Revisões", RotateCcw, "reviews"],
  ["Caderno de erros", CircleAlert, "errors"],
  ["Banco de questões", Database, "bank"],
  ["Áudios", Headphones, "soon"],
] as const;

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [view, setView] = useState<"today" | "questions" | "reviews" | "errors" | "simulations" | "bank" | "soon">("today");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [answer, setAnswer] = useState<AnswerResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/study/dashboard`, { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível carregar seu plano.");
      setDashboard(await response.json());
      setError("");
    } catch {
      setError("A API não respondeu. Confirme se o serviço da porta 9000 está aberto.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadQuestions = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/study/questions?limit=20`, { cache: "no-store" });
      if (!response.ok) throw new Error();
      setQuestions(await response.json());
      setQuestionIndex(0);
      setSelectedOption(null);
      setAnswer(null);
      setError("");
    } catch {
      setError("Não foi possível carregar as questões.");
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    loadQuestions();
  }, [loadDashboard, loadQuestions]);

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
    const response = await fetch(`${API_URL}/study/tasks/${taskId}/toggle`, { method: "PATCH" });
    if (!response.ok) {
      setError("Não foi possível salvar a atividade.");
      await loadDashboard();
    }
  };

  const submitAnswer = async () => {
    const question = questions[questionIndex];
    if (!question || selectedOption === null) return;
    const response = await fetch(`${API_URL}/study/questions/${question.id}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_option: selectedOption }),
    });
    if (!response.ok) {
      setError("Não foi possível registrar a resposta.");
      return;
    }
    setAnswer(await response.json());
    await loadDashboard();
  };

  const nextQuestion = () => {
    if (questionIndex + 1 >= questions.length) {
      loadQuestions();
      return;
    }
    setQuestionIndex((current) => current + 1);
    setSelectedOption(null);
    setAnswer(null);
  };

  const currentQuestion = questions[questionIndex];
  const firstName = dashboard?.user.full_name.split(" ")[0] ?? "Juscelino";
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
      loadQuestions();
    }
    setView(destination);
  };

  return (
    <main className="app-shell">
      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={22} /></div>
          <div><strong>Passa Fácil</strong><span>Estude com direção.</span></div>
        </div>
        <nav>
          <p className="nav-label">PREPARAÇÃO</p>
          {nav.map(([label, Icon, destination]) => (
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
          <button className="nav-item"><Settings size={19} /><span>Configurações</span></button>
          <div className="profile"><div className="avatar">JC</div><div><b>{firstName}</b><span>Acesso proprietário</span></div><ChevronRight size={17} /></div>
        </div>
      </aside>
      {menuOpen && <button aria-label="Fechar menu" className="backdrop" onClick={() => setMenuOpen(false)} />}

      <section className="content">
        <header className="topbar">
          <button className="menu-button" aria-label="Abrir menu" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X /> : <Menu />}
          </button>
          <div className="exam-chip"><span className="live-dot" />TCE-SP 2026 · TI</div>
          <div className="countdown"><CalendarDays size={17} /><span>Prova em</span><b>73 dias</b></div>
        </header>

        <div className="dashboard">
          {error && <div className="error-banner"><CircleAlert size={18} />{error}<button onClick={loadDashboard}>Tentar novamente</button></div>}
          {loading ? (
            <div className="loading-state"><LoaderCircle className="spin" /><b>Preparando seu plano...</b></div>
          ) : view === "questions" ? (
            <QuestionsView
              question={currentQuestion}
              index={questionIndex}
              total={questions.length}
              selected={selectedOption}
              result={answer}
              onSelect={setSelectedOption}
              onSubmit={submitAnswer}
              onNext={nextQuestion}
            />
          ) : view === "reviews" ? (
            <ReviewView />
          ) : view === "errors" ? (
            <ErrorNotebook onPractice={() => navigate("questions")} />
          ) : view === "simulations" ? (
            <SimulationView onDashboard={loadDashboard} />
          ) : view === "bank" ? (
            <QuestionBankView />
          ) : view === "soon" ? (
            <section className="card empty-state">
              <Sparkles size={34} /><h1>Este módulo é o próximo da fila.</h1>
              <p>Primeiro estamos fechando o ciclo essencial: plano, questões, correção e evolução real.</p>
              <button className="primary compact" onClick={() => navigate("questions")}>Praticar questões agora</button>
            </section>
          ) : (
            <>
              <section className="hero">
                <div>
                  <span className="eyebrow">SEU PLANO ADAPTATIVO</span>
                  <h1>Bom dia, {firstName}.</h1>
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
                  <button className="primary" onClick={() => navigate("questions")}><Play size={17} fill="currentColor" />Iniciar questões</button>
                </section>

                <aside className="right-column">
                  <section className="card readiness-card">
                    <div className="card-heading"><div><span className="section-kicker">RESULTADOS REAIS</span><h2>Seu desempenho</h2></div><Trophy size={22} /></div>
                    <div className="readiness">
                      <div className="big-number">{dashboard?.stats.accuracy ?? 0}<span>%</span></div>
                      <div><b>{dashboard?.stats.questions_answered ? "Dados das suas respostas" : "Primeiro diagnóstico"}</b><p>Responda questões para o sistema identificar seus pontos fortes e fracos.</p></div>
                    </div>
                    <div className="mini-stats">
                      <div><span>Estudo hoje</span><b>{dashboard?.stats.study_minutes ?? 0}m</b></div>
                      <div><span>Acertos</span><b>{dashboard?.stats.accuracy ?? 0}%</b></div>
                      <div><span>Questões</span><b>{dashboard?.stats.questions_answered ?? 0}</b></div>
                    </div>
                  </section>
                  <section className="insight">
                    <span className="insight-icon"><CircleAlert size={20} /></span>
                    <div><span>PRÓXIMA AÇÃO</span><b>Diagnóstico por questões</b><p>Cada resposta atualiza seus indicadores.</p><button onClick={() => navigate("questions")}>Começar agora <ArrowRight size={15} /></button></div>
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

function QuestionsView({
  question, index, total, selected, result, onSelect, onSubmit, onNext,
}: {
  question?: Question;
  index: number;
  total: number;
  selected: number | null;
  result: AnswerResult | null;
  onSelect: (value: number) => void;
  onSubmit: () => void;
  onNext: () => void;
}) {
  if (!question) return <section className="card empty-state"><LoaderCircle className="spin" /><h2>Carregando questões...</h2></section>;
  return (
    <section className="question-layout">
      <div className="question-top">
        <div><span className="eyebrow">MODO QUESTÕES</span><h1>Diagnóstico inteligente</h1><p>Cada resposta fica salva e atualiza o painel.</p></div>
        <div className="question-count">{index + 1}<span>/{total}</span></div>
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
            <b>{result.is_correct ? "Resposta correta." : "Ainda não. Vamos fixar isso."}</b>
            <p>{result.explanation}</p>
          </div>
        )}
        <div className="question-actions">
          {!result ? (
            <button className="primary compact" disabled={selected === null} onClick={onSubmit}>Confirmar resposta</button>
          ) : (
            <button className="primary compact" onClick={onNext}>Próxima questão <ArrowRight size={16} /></button>
          )}
        </div>
      </article>
    </section>
  );
}

type ReviewQuestion = Question & {
  review_id: string;
  correct_option: number;
  explanation: string;
  due_date: string;
  interval_days: number;
};

function ReviewView() {
  const [items, setItems] = useState<ReviewQuestion[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<(AnswerResult & { next_review: string }) | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const response = await fetch(`${API_URL}/reviews/due`, { cache: "no-store" });
    setItems(response.ok ? await response.json() : []);
    setSelected(null);
    setResult(null);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  const item = items[0];

  const answerReview = async () => {
    if (!item || selected === null) return;
    const response = await fetch(`${API_URL}/reviews/${item.review_id}/answer`, {
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
    fetch(`${API_URL}/reviews/errors`, { cache: "no-store" })
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

type SimulationData = {
  id: string;
  title: string;
  status: string;
  duration_minutes: number;
  started_at: string;
  answered: number;
  total: number;
  questions: (Question & { question_id: string; selected_option: number | null })[];
};

function SimulationView({ onDashboard }: { onDashboard: () => Promise<void> }) {
  const [simulation, setSimulation] = useState<SimulationData | null>(null);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<{ total: number; answered: number; correct: number; accuracy: number } | null>(null);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/simulations/latest`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => {
        if (data?.status === "in_progress") {
          setSimulation(data);
          setSeconds(Math.max(0, data.duration_minutes * 60 - Math.floor((Date.now() - new Date(data.started_at).getTime()) / 1000)));
        }
      });
  }, []);
  useEffect(() => {
    if (!simulation || result) return;
    const timer = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [simulation, result]);

  const start = async () => {
    const response = await fetch(`${API_URL}/simulations`, { method: "POST" });
    if (response.ok) {
      const data = await response.json();
      setSimulation(data);
      setSeconds(data.duration_minutes * 60);
      setIndex(0);
      setResult(null);
    }
  };
  const saveAndNext = async () => {
    const question = simulation?.questions[index];
    if (!simulation || !question || selected === null) return;
    await fetch(`${API_URL}/simulations/${simulation.id}/questions/${question.question_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_option: selected }),
    });
    setSimulation({ ...simulation, answered: simulation.answered + (question.selected_option === null ? 1 : 0), questions: simulation.questions.map((item, itemIndex) => itemIndex === index ? { ...item, selected_option: selected } : item) });
    setSelected(null);
    if (index + 1 < simulation.questions.length) setIndex(index + 1);
  };
  const finish = async () => {
    if (!simulation) return;
    const response = await fetch(`${API_URL}/simulations/${simulation.id}/finish`, { method: "POST" });
    if (response.ok) {
      setResult(await response.json());
      await onDashboard();
    }
  };

  if (!simulation) return (
    <section className="card simulation-intro">
      <div className="sim-icon"><Gauge size={30} /></div><span className="eyebrow">SIMULADO DIAGNÓSTICO</span>
      <h1>Treine sob pressão, sem adivinhação.</h1>
      <p>O primeiro simulado usa as questões disponíveis, salva cada resposta e mantém o cronômetro mesmo se você atualizar a página.</p>
      <div className="sim-features"><span><Check />{5} questões iniciais</span><span><Clock3 />3 minutos por questão</span><span><Target />Resultado automático</span></div>
      <button className="primary compact" onClick={start}>Começar simulado</button>
    </section>
  );
  if (result) return (
    <section className="card simulation-result">
      <Trophy size={40} /><span className="eyebrow">RESULTADO</span><h1>{result.accuracy}% de acertos</h1>
      <p>Você acertou {result.correct} de {result.total} questões e respondeu {result.answered}.</p>
      <div className="result-number">{result.correct}<span>/{result.total}</span></div>
      <button className="primary compact" onClick={start}>Fazer novo simulado</button>
    </section>
  );
  const question = simulation.questions[index];
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const secs = (seconds % 60).toString().padStart(2, "0");
  return (
    <section className="question-layout">
      <div className="simulation-bar"><div><b>{simulation.title}</b><span>{simulation.answered}/{simulation.total} respondidas</span></div><div className={seconds < 60 ? "timer danger" : "timer"}><Clock3 />{minutes}:{secs}</div></div>
      <article className="card question-card">
        <div className="question-meta"><span>{question.subject}</span><i>Questão {index + 1} de {simulation.total}</i></div>
        <h2>{question.statement}</h2>
        <div className="options">
          {question.options.map((option, optionIndex) => (
            <button key={option} onClick={() => setSelected(optionIndex)} className={`option ${selected === optionIndex ? "selected" : ""}`}><span>{String.fromCharCode(65 + optionIndex)}</span>{option}</button>
          ))}
        </div>
        <div className="simulation-actions">
          <button className="secondary" onClick={finish}>Finalizar agora</button>
          <button className="primary compact" disabled={selected === null} onClick={saveAndNext}>{index + 1 === simulation.total ? "Salvar resposta" : "Salvar e avançar"} <ArrowRight size={16} /></button>
        </div>
      </article>
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
    fetch(`${API_URL}/question-bank/pdf/jobs`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then(setJobs);
  }, []);
  useEffect(() => { loadJobs(); }, [loadJobs]);
  const loadDrafts = useCallback(() => {
    fetch(`${API_URL}/question-bank/drafts?status=pending`, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then((items: DraftQuestion[]) => {
        setDrafts(items);
        setSelectedDraftId((current) => current || items[0]?.id || "");
      });
  }, []);
  useEffect(() => {
    loadDrafts();
    fetch(`${API_URL}/question-bank/topics`, { cache: "no-store" })
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
    const response = await fetch(`${API_URL}/question-bank/drafts/${selectedDraft.id}`, {
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
    const response = await fetch(`${API_URL}/question-bank/pdf/inspect`, { method: "POST", body });
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
    const response = await fetch(`${API_URL}/question-bank/pdf/associate`, {
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
