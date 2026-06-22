import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const INTENT_STYLE = {
  interested: "bg-green-100 text-green-700",
  question: "bg-blue-100 text-blue-700",
  needs_info: "bg-indigo-100 text-indigo-700",
  objection: "bg-amber-100 text-amber-700",
  not_interested: "bg-red-100 text-red-700",
  ambiguous: "bg-slate-100 text-slate-600",
};
const SENT_STYLE = { positive: "text-green-600", neutral: "text-slate-500", negative: "text-red-600" };
const STAGES = ["Reading your site…", "Understanding your company…", "Configuring the agent…", "Writing the first message…"];

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.12 } } };
const item = { hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } };

function Background() {
  const blob = (cls, dur, delay) => (
    <motion.div className={`absolute rounded-full blur-3xl opacity-20 ${cls}`}
      animate={{ x: [0, 40, -20, 0], y: [0, -30, 20, 0], scale: [1, 1.1, 0.95, 1] }}
      transition={{ duration: dur, repeat: Infinity, ease: "easeInOut", delay }} />
  );
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {blob("w-96 h-96 bg-indigo-300 -top-10 -left-10", 18, 0)}
      {blob("w-96 h-96 bg-emerald-200 -bottom-16 -right-10", 22, 2)}
      {blob("w-80 h-80 bg-sky-200 top-1/3 right-1/4", 26, 4)}
    </div>
  );
}

function Chips({ items, className = "" }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {(items || []).map((it, i) => (
        <motion.span key={i} variants={item} className={`px-2 py-0.5 rounded-full text-xs ${className}`}>{it}</motion.span>
      ))}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center px-3 py-2">
      {[0, 1, 2].map((i) => (
        <motion.span key={i} className="w-1.5 h-1.5 bg-indigo-400 rounded-full"
          animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }} />
      ))}
    </div>
  );
}

const gcalUrl = (title, s, details) =>
  `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${s.start_iso}/${s.end_iso}&details=${encodeURIComponent(details)}`;

function ScheduleCard({ schedule }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
      className="mt-3 border border-indigo-200 bg-indigo-50/70 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1 flex-wrap">
        <span className="text-xs font-semibold text-indigo-700">⚡ Agent action · schedule_call</span>
        <span className="text-[10px] text-slate-400">(simulated — nothing is sent to the candidate)</span>
      </div>
      <div className="text-sm font-medium">{schedule.title}</div>
      <div className="text-xs text-slate-500 mb-3">{schedule.agenda}</div>
      <div className="space-y-1.5">
        {schedule.slots.map((s, i) => (
          <div key={i} className="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-slate-200">
            <span className="text-sm">{s.label}</span>
            <a href={gcalUrl(schedule.title, s, schedule.agenda)} target="_blank" rel="noreferrer"
              className="text-xs text-indigo-600 font-medium hover:underline">Add to Google Calendar →</a>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function Modal({ children, onClose, title }) {
  return (
    <motion.div className="fixed inset-0 z-20 bg-black/40 flex items-center justify-center p-4"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="bg-white rounded-2xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto"
        initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>
        {children}
      </motion.div>
    </motion.div>
  );
}

export default function App() {
  const [source, setSource] = useState("");
  const [candidateRole, setCandidateRole] = useState("");
  const [inferred, setInferred] = useState(null);
  const [persona, setPersona] = useState(null);
  const [plan, setPlan] = useState(null);
  const [state, setState] = useState(null);
  const [turns, setTurns] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(null);
  const [configuring, setConfiguring] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  const [srcA, setSrcA] = useState("PSVIEW — autonomous AI recruiting agents for IT staffing firms; fast, ambitious, no BS");
  const [srcB, setSrcB] = useState("Meridian Trust — a 120-year-old private wealth bank; formal, precise, discreet");
  const [abReply, setAbReply] = useState("I'm happy where I am, why should I move?");
  const [abResult, setAbResult] = useState(null);
  const [abBusy, setAbBusy] = useState(false);
  const [critique, setCritique] = useState(null);
  const [critiqueBusy, setCritiqueBusy] = useState(false);

  useEffect(() => {
    if (!configuring) return;
    setStageIdx(0);
    const id = setInterval(() => setStageIdx((i) => Math.min(i + 1, STAGES.length - 1)), 1300);
    return () => clearInterval(id);
  }, [configuring]);

  async function post(path, body) {
    const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error((await r.json()).detail || "Request failed");
    return r.json();
  }

  async function configure() {
    if (!source.trim()) return;
    setError(""); setConfiguring(true); setTurns([]); setSchedule(null);
    try {
      const data = await post("/api/configure", { source, candidate_role: candidateRole });
      setInferred(data.company); setPersona(data.persona); setPlan(data.plan); setState(data.state);
    } catch (e) { setError(e.message); } finally { setConfiguring(false); }
  }

  async function sendReply() {
    if (!reply.trim() || !state) return;
    setError(""); setBusy(true);
    const r = reply; setReply(""); setPending(r);
    try {
      const turn = await post("/api/reply", { state, reply: r });
      setState(turn.state); setPending(null);
      setTurns((t) => [...t, { ...turn.analysis, ...turn.decision }]);
      if (turn.schedule) setSchedule(turn.schedule);
    } catch (e) {
      setError(e.message); setPending(null); setReply(r);
    } finally { setBusy(false); }
  }

  async function runAB() {
    setAbBusy(true); setAbResult(null); setError("");
    try {
      const r = abReply.trim() || "I'm happy where I am, why should I move?";
      const run = async (src) => {
        const cfg = await post("/api/configure", { source: src });
        const turn = await post("/api/reply", { state: cfg.state, reply: r });
        return { company: cfg.company, persona: cfg.persona, intent: turn.analysis.intent, action: turn.decision.action, message: turn.message };
      };
      const [a, b] = await Promise.all([run(srcA), run(srcB)]);
      setAbResult({ a, b });
    } catch (e) { setError(e.message); } finally { setAbBusy(false); }
  }

  async function runCritique() {
    const lastAgent = [...(state?.history || [])].reverse().find((m) => m.sender === "agent");
    if (!lastAgent) return;
    setCritiqueBusy(true); setCritique(null); setError("");
    try {
      const res = await post("/api/critique", { state, draft: lastAgent.text });
      setCritique({ draft: lastAgent.text, ...res });
    } catch (e) { setError(e.message); } finally { setCritiqueBusy(false); }
  }

  function reset() { setPersona(null); setPlan(null); setState(null); setTurns([]); setSchedule(null); setInferred(null); setError(""); }

  const messages = state?.history || [];
  const lastTurn = turns[turns.length - 1];

  return (
    <div className="min-h-screen text-slate-800 relative">
      <Background />
      <div className="max-w-6xl mx-auto px-6 py-8">
        <header className="mb-6 flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-bold">Engagement Agent</h1>
            <p className="text-slate-500 text-sm">Give it your company URL. It figures out who you are, builds its own personality, and runs the conversation.</p>
          </div>
          {persona && <button onClick={reset} className="text-sm text-slate-500 hover:underline">Start over</button>}
        </header>

        {error && <div className="mb-4 text-red-600 text-sm">Error: {error}</div>}

        <AnimatePresence mode="wait">
          {!persona ? (
            <motion.div key="form" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              className="bg-white/80 backdrop-blur p-6 rounded-2xl border border-slate-200 max-w-xl">
              <h2 className="font-semibold mb-1">Tell the agent about your company</h2>
              <p className="text-xs text-slate-500 mb-4">Paste a URL, or just a line — it works either way.</p>
              <input value={source} onChange={(e) => setSource(e.target.value)} onKeyDown={(e) => e.key === "Enter" && configure()}
                placeholder="https://yourcompany.com  —  or  “a fast AI startup hiring engineers”"
                className="w-full p-3 border border-slate-300 rounded-xl text-sm bg-white/70 mb-3" />
              <input value={candidateRole} onChange={(e) => setCandidateRole(e.target.value)}
                placeholder="(optional) who are you hiring? e.g. senior backend engineer"
                className="w-full p-3 border border-slate-300 rounded-xl text-sm bg-white/70 mb-4" />
              <button onClick={configure} disabled={configuring || !source.trim()}
                className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-medium disabled:opacity-40 min-w-[200px]">
                {configuring ? (
                  <AnimatePresence mode="wait">
                    <motion.span key={stageIdx} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}>
                      {STAGES[stageIdx]}
                    </motion.span>
                  </AnimatePresence>
                ) : "Build the agent"}
              </button>
            </motion.div>
          ) : (
            <motion.div key="workspace" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3 space-y-4">
                <div className="bg-white/80 backdrop-blur p-5 rounded-xl border border-slate-200 flex flex-col">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="font-semibold text-sm">Conversation preview</h2>
                    <motion.span key={state.stage} initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                      className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">stage: {state.stage}</motion.span>
                  </div>
                  <div className="flex-1 space-y-3 overflow-y-auto max-h-[400px] pr-1">
                    <AnimatePresence initial={false}>
                      {messages.map((m, i) => (
                        <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                          transition={{ type: "spring", stiffness: 260, damping: 22 }}
                          className={`flex ${m.sender === "agent" ? "justify-start" : "justify-end"}`}>
                          <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${m.sender === "agent" ? "bg-indigo-50 text-slate-800 rounded-tl-sm" : "bg-slate-800 text-white rounded-tr-sm"}`}>
                            <div className={`text-[10px] mb-1 ${m.sender === "agent" ? "text-indigo-400" : "text-slate-300"}`}>{m.sender === "agent" ? persona.agent_name : "candidate"}</div>
                            {m.text}
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                    {pending && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
                        <div className="max-w-[80%] p-3 rounded-2xl text-sm bg-slate-800 text-white rounded-tr-sm opacity-80">
                          <div className="text-[10px] mb-1 text-slate-300">candidate</div>
                          {pending}
                        </div>
                      </motion.div>
                    )}
                    {busy && <div className="flex justify-start"><div className="bg-indigo-50 rounded-2xl rounded-tl-sm"><TypingDots /></div></div>}
                    {schedule && <ScheduleCard schedule={schedule} />}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <input value={reply} onChange={(e) => setReply(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendReply()}
                      placeholder="Type a candidate reply to simulate…" className="flex-1 p-2.5 border border-slate-300 rounded-lg text-sm bg-white/70" />
                    <button onClick={sendReply} disabled={busy || !reply.trim()} className="px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium disabled:opacity-40">Send</button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button onClick={() => setModal("ab")} className="flex-1 px-4 py-2.5 bg-white/80 backdrop-blur border border-indigo-200 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-50">
                    ⚖️ Compare two companies (A/B)
                  </button>
                  <button onClick={() => { setModal("critique"); runCritique(); }} className="flex-1 px-4 py-2.5 bg-white/80 backdrop-blur border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50">
                    🔍 Self-critique last message
                  </button>
                </div>
              </div>

              <div className="lg:col-span-2 space-y-4">
                {inferred && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="bg-white/80 backdrop-blur p-5 rounded-xl border border-slate-200">
                    <h3 className="font-semibold text-sm mb-1">What the agent understood</h3>
                    <div className="text-sm font-medium">{inferred.name}</div>
                    <p className="text-xs text-slate-500 mb-2">{inferred.description}</p>
                    <div className="text-[10px] text-slate-400">Culture: <span className="text-slate-600">{inferred.culture}</span></div>
                    <div className="text-[10px] text-slate-400">Hires: <span className="text-slate-600">{inferred.hiring_profiles}</span></div>
                    <div className="text-[10px] text-slate-400">Tone: <span className="text-slate-600">{inferred.tone}</span></div>
                  </motion.div>
                )}

                <motion.div variants={stagger} initial="hidden" animate="show" className="bg-white/80 backdrop-blur p-5 rounded-xl border border-slate-200">
                  <motion.div variants={item} className="flex items-center gap-2 mb-2">
                    <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">{persona.agent_name?.[0] || "A"}</div>
                    <div>
                      <div className="font-semibold text-sm">{persona.agent_name}</div>
                      <div className="text-xs text-slate-500">{persona.role}</div>
                    </div>
                  </motion.div>
                  <motion.p variants={item} className="text-xs text-slate-600 mb-3">{persona.voice}</motion.p>
                  <motion.div variants={item} className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">Values</motion.div>
                  <Chips items={persona.values} className="bg-green-50 text-green-700" />
                  <motion.div variants={item} className="text-[10px] uppercase tracking-wide text-slate-400 mt-3 mb-1">Signature vocabulary</motion.div>
                  <Chips items={persona.vocabulary} className="bg-indigo-50 text-indigo-700" />
                  <motion.div variants={item} className="text-[10px] uppercase tracking-wide text-slate-400 mt-3 mb-1">Boundaries</motion.div>
                  <Chips items={persona.boundaries} className="bg-red-50 text-red-700" />
                </motion.div>

                <div className="bg-white/80 backdrop-blur p-5 rounded-xl border border-slate-200">
                  <h3 className="font-semibold text-sm mb-3">Agent reasoning <span className="font-normal text-slate-400">(latest turn)</span></h3>
                  {!lastTurn ? (
                    <p className="text-xs text-slate-400">Simulate a candidate reply to watch the agent perceive, decide, and act.</p>
                  ) : (
                    <motion.div key={turns.length} variants={stagger} initial="hidden" animate="show" className="space-y-3">
                      <motion.div variants={item}>
                        <div className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">1 · Perceive</div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs ${INTENT_STYLE[lastTurn.intent] || "bg-slate-100"}`}>{lastTurn.intent}</span>
                          <span className={`text-xs ${SENT_STYLE[lastTurn.sentiment] || ""}`}>● {lastTurn.sentiment}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{lastTurn.reasoning}</p>
                      </motion.div>
                      <motion.div variants={item}>
                        <div className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">2 · Decide <span className="text-slate-300">(policy)</span></div>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-slate-800 text-white">{lastTurn.action}</span>
                        <p className="text-xs text-slate-500 mt-1">{lastTurn.strategy}</p>
                      </motion.div>
                      <motion.div variants={item}>
                        <div className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">3 · Act</div>
                        <p className="text-xs text-slate-500">Generated the in-persona message →</p>
                      </motion.div>
                    </motion.div>
                  )}
                </div>

                {plan && (
                  <div className="bg-white/80 backdrop-blur p-5 rounded-xl border border-slate-200">
                    <h3 className="font-semibold text-sm mb-1">Outreach plan</h3>
                    <p className="text-xs text-slate-500 mb-2">{plan.goal}</p>
                    <ol className="space-y-1">
                      {(plan.steps || []).map((s, i) => (
                        <li key={i} className="text-xs text-slate-600"><span className="font-medium">{s.order}.</span> {s.objective} <span className="text-slate-400">— {s.angle}</span></li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {modal === "ab" && (
          <Modal title="Compare two companies — same reply, different agents" onClose={() => setModal(null)}>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <div className="text-xs font-semibold mb-1">Company A (URL or a line)</div>
                <textarea value={srcA} onChange={(e) => setSrcA(e.target.value)} className="w-full h-20 p-2.5 border border-slate-300 rounded-lg text-sm" />
              </div>
              <div>
                <div className="text-xs font-semibold mb-1">Company B (URL or a line)</div>
                <textarea value={srcB} onChange={(e) => setSrcB(e.target.value)} className="w-full h-20 p-2.5 border border-slate-300 rounded-lg text-sm" />
              </div>
            </div>
            <div className="text-xs font-semibold mb-1">Candidate reply (same for both)</div>
            <textarea value={abReply} onChange={(e) => setAbReply(e.target.value)} className="w-full h-16 p-2.5 border border-slate-300 rounded-lg text-sm mb-3" />
            <button onClick={runAB} disabled={abBusy} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium disabled:opacity-40">
              {abBusy ? "Running both agents…" : "Compare"}
            </button>
            {abResult && (
              <div className="grid grid-cols-2 gap-3 mt-4">
                {[abResult.a, abResult.b].map((r, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                    className="border border-slate-200 rounded-xl p-3">
                    <div className="font-semibold text-sm">{r.persona.agent_name} <span className="font-normal text-slate-400">· {r.company.name}</span></div>
                    <div className="text-xs text-slate-500 mb-2">{r.persona.voice}</div>
                    <div className="flex gap-1 mb-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${INTENT_STYLE[r.intent] || "bg-slate-100"}`}>{r.intent}</span>
                      <span className="px-2 py-0.5 rounded-full text-xs bg-slate-800 text-white">{r.action}</span>
                    </div>
                    <div className="text-sm bg-slate-50 rounded-lg p-2">{r.message}</div>
                  </motion.div>
                ))}
              </div>
            )}
          </Modal>
        )}

        {modal === "critique" && (
          <Modal title="Self-critique — the agent reviews its own draft" onClose={() => setModal(null)}>
            {critiqueBusy && <p className="text-sm text-slate-500">Agent reflecting on its last message…</p>}
            {critique && (
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">Original draft</div>
                  <div className="text-sm bg-slate-50 border border-slate-200 rounded-lg p-3">{critique.draft}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">Critique</div>
                  <p className="text-sm text-slate-600">{critique.critique}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(critique.issues || []).map((it, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700">{it}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-green-600 mb-1">Revised</div>
                  <div className="text-sm bg-green-50 border border-green-200 rounded-lg p-3">{critique.revised}</div>
                </div>
              </div>
            )}
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}