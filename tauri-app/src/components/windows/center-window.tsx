import { useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useCenterStore } from "@/stores/center-store";
import {
  Building2,
  AlertTriangle,
  Users,
  Clock,
  MessageSquare,
  Zap,
  CheckCircle2,
  Phone,
  Play,
  Square,
  Send,
  ChevronLeft,
  RefreshCw,
} from "lucide-react";

const severityColors: Record<string, string> = {
  low: "border-l-blue-400 bg-blue-900/10",
  moderate: "border-l-yellow-400 bg-yellow-900/10",
  high: "border-l-orange-400 bg-orange-900/10",
  critical: "border-l-red-400 bg-red-900/10",
};

const categoryIcons: Record<string, string> = {
  accesibilidad: "♿", equipamiento: "🔧", infraestructura: "🏗️",
  paciente: "🤒", administrativo: "📋", bioseguridad: "🦠", emergencia: "🚨", otro: "⚠️",
};

const statusColors: Record<string, string> = {
  scheduled: "text-blue-400", in_progress: "text-amber-400",
  completed: "text-green-400", cancelled: "text-red-400",
  rescheduled: "text-purple-400", no_show: "text-gray-400",
};

const statusLabels: Record<string, string> = {
  scheduled: "Pendiente", in_progress: "En atención", completed: "Completado",
  cancelled: "Cancelado", rescheduled: "Reagendado", no_show: "No asistió",
};

type View = "overview" | "box" | "inject" | "meeting" | "chat";

export function CenterWindow() {
  const role = useAuthStore((s) => s.role);
  const isStaff = role === "admin" || role === "docente" || role === "instructor";

  const {
    boxes, incidents, meetings, chatMessages, templates, isActive, scheduledIncidents,
    initCenter, stopCenter, refreshBoxes,
    createBoxes, assignStudentToBox, injectIncident, resolveIncident, discussIncident,
    callMeeting, startMeeting, endMeeting,
    sendChatMessage, startPatientAttention, endPatientAttention, loadTemplates,
    scheduleIncidents,
  } = useCenterStore();

  const [view, setView] = useState<View>("overview");
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [setupSessionId, setSetupSessionId] = useState("");
  const [setupBoxCount, setSetupBoxCount] = useState(4);

  // Inject form
  const [injectCategory, setInjectCategory] = useState("");
  const [injectBox, setInjectBox] = useState<number | undefined>();
  const [customTitle, setCustomTitle] = useState("");
  const [customDesc, setCustomDesc] = useState("");
  const [customSeverity, setCustomSeverity] = useState("moderate");

  // Schedule form
  const [schedTemplate, setSchedTemplate] = useState("");
  const [schedMinutes, setSchedMinutes] = useState(15);

  // Meeting form
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingAgenda, setMeetingAgenda] = useState("");

  // Chat
  const [chatInput, setChatInput] = useState("");

  // Resolve
  const [resolveNotes, setResolveNotes] = useState("");

  // Assign student
  const [assignInput, setAssignInput] = useState("");

  const selectedBox = boxes.find((b) => b.id === selectedBoxId);
  const activeIncidents = incidents.filter((i) => i.status === "active");
  const filteredTemplates = injectCategory
    ? templates.filter((t) => t.category === injectCategory)
    : templates;

  // ─── Sin sesión activa ────────────────────────────
  if (!isActive) {
    return (
      <div className="flex h-full flex-col items-center justify-center ls-bg p-6 text-center">
        <Building2 className="w-16 h-16 ls-text-muted mb-4 opacity-30" />
        <h2 className="text-lg font-semibold ls-text mb-2">Modalidad Centro</h2>
        <p className="text-sm ls-text-muted max-w-md mb-4">
          Simula un día de trabajo completo en un centro clínico.
          Cada estudiante en su box con agenda propia, incidentes y reuniones clínicas.
        </p>

        {isStaff ? (
          <div className="w-full max-w-xs space-y-3">
            <div>
              <label className="text-xs ls-text-muted block mb-1">ID de sesión práctica</label>
              <input
                type="text"
                value={setupSessionId}
                onChange={(e) => setSetupSessionId(e.target.value)}
                placeholder="Pegar ID de sesión..."
                className="w-full px-3 py-2 text-sm rounded ls-bg-input border ls-border ls-text"
              />
            </div>
            <div>
              <label className="text-xs ls-text-muted block mb-1">Cantidad de boxes</label>
              <input
                type="number"
                min={1}
                max={20}
                value={setupBoxCount}
                onChange={(e) => setSetupBoxCount(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded ls-bg-input border ls-border ls-text"
              />
            </div>
            <button
              onClick={async () => {
                if (!setupSessionId) return;
                await initCenter(setupSessionId);
                await createBoxes(setupBoxCount);
              }}
              disabled={!setupSessionId}
              className="w-full px-4 py-2 text-sm rounded bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40"
            >
              Iniciar Centro
            </button>
          </div>
        ) : (
          <p className="text-xs ls-text-muted">
            El docente debe activar la sesión en modo centro.
          </p>
        )}
      </div>
    );
  }

  // ─── Vista: Inyectar Incidente ────────────────────
  if (view === "inject") {
    return (
      <div className="h-full overflow-auto ls-bg p-4">
        <button onClick={() => setView("overview")} className="text-sm ls-text-muted hover:ls-text mb-3 flex items-center gap-1">
          <ChevronLeft className="w-3 h-3" /> Volver
        </button>
        <h2 className="text-lg font-semibold ls-text mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-red-400" /> Inyectar Incidente
        </h2>

        <div className="flex gap-2 mb-3 flex-wrap">
          <button onClick={() => setInjectCategory("")} className={`px-2 py-1 text-xs rounded ${!injectCategory ? "bg-indigo-600 text-white" : "ls-bg-input ls-text-muted"}`}>Todos</button>
          {Object.keys(categoryIcons).map((cat) => (
            <button key={cat} onClick={() => setInjectCategory(cat)} className={`px-2 py-1 text-xs rounded ${injectCategory === cat ? "bg-indigo-600 text-white" : "ls-bg-input ls-text-muted"}`}>
              {categoryIcons[cat]} {cat}
            </button>
          ))}
        </div>

        {injectBox != null && (
          <p className="text-xs text-amber-400 mb-2">Afecta: Box {injectBox}</p>
        )}
        <div className="flex gap-2 mb-3">
          <select value={injectBox ?? ""} onChange={(e) => setInjectBox(e.target.value ? Number(e.target.value) : undefined)}
            className="px-2 py-1 text-xs rounded ls-bg-input border ls-border ls-text">
            <option value="">Todos los boxes</option>
            {boxes.map((b) => <option key={b.id} value={b.box_number}>Box {b.box_number}</option>)}
          </select>
        </div>

        <div className="space-y-1.5 mb-4">
          {filteredTemplates.map((tpl) => (
            <div key={tpl.id} className={`border-l-2 rounded p-2 cursor-pointer hover:opacity-80 transition ${severityColors[tpl.severity]}`}
              onClick={() => injectIncident(tpl.id, undefined, injectBox)}>
              <div className="flex items-center gap-2">
                <span>{categoryIcons[tpl.category]}</span>
                <span className="text-sm font-medium ls-text">{tpl.title}</span>
                <span className={`text-[10px] px-1 py-0.5 rounded ${
                  tpl.severity === "critical" ? "bg-red-900/40 text-red-300" : "bg-gray-800 ls-text-muted"
                }`}>{tpl.severity}</span>
              </div>
              <p className="text-xs ls-text-muted mt-0.5 line-clamp-2">{tpl.description}</p>
            </div>
          ))}
        </div>

        <div className="border-t ls-border pt-3">
          <h4 className="text-xs font-semibold ls-text-muted mb-2">O crear incidente personalizado:</h4>
          <input type="text" value={customTitle} onChange={(e) => setCustomTitle(e.target.value)} placeholder="Título" className="w-full px-2 py-1.5 text-sm rounded ls-bg-input border ls-border ls-text mb-2" />
          <textarea value={customDesc} onChange={(e) => setCustomDesc(e.target.value)} placeholder="Descripción..." rows={3} className="w-full px-2 py-1.5 text-sm rounded ls-bg-input border ls-border ls-text mb-2" />
          <div className="flex gap-2">
            <select value={customSeverity} onChange={(e) => setCustomSeverity(e.target.value)} className="px-2 py-1 text-xs rounded ls-bg-input border ls-border ls-text">
              <option value="low">Baja</option>
              <option value="moderate">Moderada</option>
              <option value="high">Alta</option>
              <option value="critical">Crítica</option>
            </select>
            <button
              onClick={() => {
                if (customTitle && customDesc) {
                  injectIncident(undefined, { title: customTitle, description: customDesc, category: injectCategory || "otro", severity: customSeverity }, injectBox);
                  setCustomTitle(""); setCustomDesc("");
                }
              }}
              disabled={!customTitle || !customDesc}
              className="px-3 py-1 text-xs rounded bg-red-600 text-white disabled:opacity-40"
            >
              Inyectar
            </button>
          </div>
        </div>

        {/* Programar inyección automática */}
        <div className="border-t ls-border pt-3 mt-3">
          <h4 className="text-xs font-semibold ls-text-muted mb-2 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Programar inyección automática
          </h4>
          <select
            value={schedTemplate}
            onChange={(e) => setSchedTemplate(e.target.value)}
            className="w-full px-2 py-1.5 text-xs rounded ls-bg-input border ls-border ls-text mb-2"
          >
            <option value="">Seleccionar incidente...</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.title} ({t.severity})</option>
            ))}
          </select>
          <div className="flex gap-2 items-center mb-2">
            <label className="text-xs ls-text-muted">Activar en:</label>
            <input
              type="number"
              min={1}
              max={120}
              value={schedMinutes}
              onChange={(e) => setSchedMinutes(Number(e.target.value))}
              className="w-20 px-2 py-1 text-xs rounded ls-bg-input border ls-border ls-text"
            />
            <span className="text-xs ls-text-muted">min desde inicio</span>
          </div>
          <button
            onClick={() => {
              const tpl = templates.find((t) => t.id === schedTemplate);
              if (tpl) {
                scheduleIncidents([...scheduledIncidents, { ...tpl, trigger_time_minutes: schedMinutes }]);
                setSchedTemplate("");
                setSchedMinutes(15);
              }
            }}
            disabled={!schedTemplate}
            className="px-3 py-1 text-xs rounded bg-amber-600 text-white disabled:opacity-40"
          >
            Programar
          </button>

          {scheduledIncidents.length > 0 && (
            <div className="mt-3 space-y-1">
              <h5 className="text-[10px] font-semibold ls-text-muted uppercase">
                Programados ({scheduledIncidents.length})
              </h5>
              {scheduledIncidents.map((inc, i) => (
                <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded ls-bg-input">
                  <Clock className="w-3 h-3 text-amber-400" />
                  <span className="ls-text flex-1">{inc.title}</span>
                  <span className="ls-text-muted">@{inc.trigger_time_minutes}min</span>
                  <button
                    onClick={() => scheduleIncidents(scheduledIncidents.filter((_, j) => j !== i))}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    x
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── Vista: Reunión ───────────────────────────────
  if (view === "meeting") {
    return (
      <div className="h-full overflow-auto ls-bg p-4">
        <button onClick={() => setView("overview")} className="text-sm ls-text-muted hover:ls-text mb-3 flex items-center gap-1">
          <ChevronLeft className="w-3 h-3" /> Volver
        </button>
        <h2 className="text-lg font-semibold ls-text mb-3 flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-400" /> Reuniones Clínicas
        </h2>

        {isStaff && (
          <div className="ls-card border ls-border rounded p-3 mb-4">
            <h4 className="text-xs font-semibold ls-text mb-2">Convocar reunión</h4>
            <input type="text" value={meetingTitle} onChange={(e) => setMeetingTitle(e.target.value)} placeholder="Tema de la reunión" className="w-full px-2 py-1.5 text-sm rounded ls-bg-input border ls-border ls-text mb-2" />
            <textarea value={meetingAgenda} onChange={(e) => setMeetingAgenda(e.target.value)} placeholder="Puntos a tratar..." rows={2} className="w-full px-2 py-1.5 text-sm rounded ls-bg-input border ls-border ls-text mb-2" />
            <button
              onClick={() => {
                if (meetingTitle) {
                  const pendingIncidents = activeIncidents.filter((i) => i.status === "active").map((i) => i.id);
                  callMeeting(meetingTitle, meetingAgenda, pendingIncidents);
                  setMeetingTitle(""); setMeetingAgenda("");
                }
              }}
              disabled={!meetingTitle}
              className="px-3 py-1.5 text-xs rounded bg-indigo-600 text-white disabled:opacity-40"
            >
              Convocar
            </button>
          </div>
        )}

        <div className="space-y-2">
          {meetings.map((m) => (
            <div key={m.id} className="ls-card border ls-border rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium ls-text">{m.title}</span>
                <span className={`text-xs ${m.status === "in_progress" ? "text-green-400" : m.status === "completed" ? "ls-text-muted" : "text-blue-400"}`}>
                  {m.status === "in_progress" ? "En curso" : m.status === "completed" ? "Finalizada" : "Programada"}
                </span>
              </div>
              <p className="text-[10px] ls-text-muted">{m.participant_count} participantes · {m.incident_count} incidentes</p>
              {isStaff && m.status === "scheduled" && (
                <button onClick={() => startMeeting(m.id)} className="mt-2 px-2 py-1 text-[10px] rounded bg-green-700 text-white flex items-center gap-0.5">
                  <Play className="w-2.5 h-2.5" /> Iniciar
                </button>
              )}
              {isStaff && m.status === "in_progress" && (
                <button onClick={() => endMeeting(m.id)} className="mt-2 px-2 py-1 text-[10px] rounded bg-amber-700 text-white flex items-center gap-0.5">
                  <Square className="w-2.5 h-2.5" /> Finalizar
                </button>
              )}
            </div>
          ))}
          {meetings.length === 0 && <p className="text-xs ls-text-muted text-center py-6">No hay reuniones</p>}
        </div>
      </div>
    );
  }

  // ─── Vista: Chat del Centro ───────────────────────
  if (view === "chat") {
    return (
      <div className="flex h-full flex-col ls-bg">
        <div className="flex items-center gap-2 p-3 border-b ls-border">
          <button onClick={() => setView("overview")} className="ls-text-muted hover:ls-text"><ChevronLeft className="w-4 h-4" /></button>
          <MessageSquare className="w-4 h-4 text-green-400" />
          <span className="text-sm font-medium ls-text">Chat del Centro</span>
        </div>
        <div className="flex-1 overflow-auto p-3 space-y-2">
          {chatMessages.map((msg) => (
            <div key={msg.id} className={`max-w-[80%] ${msg.message_type === "system" || msg.message_type === "meeting_call" ? "mx-auto text-center" : ""}`}>
              {msg.message_type === "system" || msg.message_type === "meeting_call" ? (
                <p className="text-[10px] ls-text-muted bg-indigo-900/20 rounded px-2 py-1">{msg.message}</p>
              ) : (
                <div className="ls-card border ls-border rounded p-2">
                  <p className="text-[10px] font-semibold text-indigo-400">{msg.sender_name ?? msg.sender_username}</p>
                  <p className="text-sm ls-text">{msg.message}</p>
                </div>
              )}
            </div>
          ))}
          {chatMessages.length === 0 && <p className="text-xs ls-text-muted text-center py-8">Sin mensajes</p>}
        </div>
        <div className="flex gap-2 p-3 border-t ls-border">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && chatInput.trim()) { sendChatMessage(chatInput.trim()); setChatInput(""); } }}
            placeholder="Escribir mensaje..."
            className="flex-1 px-3 py-1.5 text-sm rounded ls-bg-input border ls-border ls-text"
          />
          <button
            onClick={() => { if (chatInput.trim()) { sendChatMessage(chatInput.trim()); setChatInput(""); } }}
            className="px-3 py-1.5 rounded bg-indigo-600 text-white"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  // ─── Vista: Detalle de Box ────────────────────────
  if (view === "box" && selectedBox) {
    return (
      <div className="h-full overflow-auto ls-bg p-4">
        <button onClick={() => { setView("overview"); setSelectedBoxId(null); }} className="text-sm ls-text-muted hover:ls-text mb-3 flex items-center gap-1">
          <ChevronLeft className="w-3 h-3" /> Volver al centro
        </button>

        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold ls-text">{selectedBox.name}</h2>
          <span className="text-xs ls-text-muted">{selectedBox.student_name ?? "Sin asignar"}</span>
        </div>

        {/* Asignar estudiante */}
        {isStaff && !selectedBox.student_id && (
          <div className="flex gap-2 mb-3 items-center">
            <input
              type="text"
              value={assignInput}
              onChange={(e) => setAssignInput(e.target.value)}
              placeholder="Username del estudiante"
              className="flex-1 px-2 py-1.5 text-xs rounded ls-bg-input border ls-border ls-text"
            />
            <button
              onClick={async () => {
                const username = assignInput.trim();
                if (username) {
                  await assignStudentToBox(selectedBox.id, username);
                  setAssignInput("");
                  await refreshBoxes();
                }
              }}
              disabled={!assignInput.trim()}
              className="px-3 py-1.5 text-xs rounded bg-indigo-600 text-white disabled:opacity-40"
            >
              Asignar
            </button>
          </div>
        )}

        {/* Incidentes del box */}
        {selectedBox.incidents.filter((i) => i.status === "active").map((inc) => (
          <div key={inc.id} className={`border-l-2 rounded p-3 mb-2 ${severityColors[inc.severity]}`}>
            <div className="flex items-center gap-2 mb-1">
              <span>{categoryIcons[inc.category]}</span>
              <span className="text-sm font-medium ls-text">{inc.title}</span>
            </div>
            <p className="text-xs ls-text-muted">{inc.description}</p>
            <textarea
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              placeholder="Notas de resolución..."
              rows={2}
              className="w-full px-2 py-1.5 text-xs rounded ls-bg-input border ls-border ls-text mt-2"
            />
            <div className="flex gap-2 mt-2">
              <button onClick={() => { resolveIncident(inc.id, resolveNotes); setResolveNotes(""); }} className="px-2 py-1 text-[10px] rounded bg-green-700 text-white flex items-center gap-0.5">
                <CheckCircle2 className="w-2.5 h-2.5" /> Resolver
              </button>
              <button onClick={() => discussIncident(inc.id)} className="px-2 py-1 text-[10px] rounded bg-indigo-700 text-white flex items-center gap-0.5">
                <MessageSquare className="w-2.5 h-2.5" /> Reunión
              </button>
              {inc.severity === "critical" && (
                <button className="px-2 py-1 text-[10px] rounded bg-red-700 text-white flex items-center gap-0.5">
                  <Phone className="w-2.5 h-2.5" /> Urgencias
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Agenda */}
        <h3 className="text-xs font-semibold uppercase ls-text-muted mb-2 mt-3">Agenda del día</h3>
        <div className="space-y-1.5">
          {selectedBox.agenda.map((item) => (
            <div key={item.id} className="flex items-center gap-3 p-2.5 rounded ls-card border ls-border">
              <div className="min-w-[48px] text-center">
                <span className="text-sm font-bold ls-text">{item.scheduled_time}</span>
                <div className="text-[10px] ls-text-muted">{item.duration_minutes}min</div>
              </div>
              <div className="flex-1">
                <span className="text-sm ls-text">{item.patient_name}</span>
                {item.procedure_name && <p className="text-[10px] ls-text-muted">{item.procedure_name}</p>}
              </div>
              <span className={`text-xs ${statusColors[item.status]}`}>{statusLabels[item.status] ?? item.status}</span>
              {item.status === "scheduled" && (
                <button onClick={() => startPatientAttention(item)} className="px-2 py-1 text-[10px] rounded bg-green-700 text-white flex items-center gap-0.5">
                  <Play className="w-2.5 h-2.5" /> Iniciar
                </button>
              )}
              {item.status === "in_progress" && (
                <button onClick={() => endPatientAttention(item.id)} className="px-2 py-1 text-[10px] rounded bg-amber-700 text-white flex items-center gap-0.5">
                  <Square className="w-2.5 h-2.5" /> Finalizar
                </button>
              )}
            </div>
          ))}
          {selectedBox.agenda.length === 0 && <p className="text-xs ls-text-muted text-center py-4">Sin pacientes agendados</p>}
        </div>
      </div>
    );
  }

  // ─── Vista: Overview (principal) ──────────────────
  return (
    <div className="h-full overflow-auto ls-bg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold ls-text flex items-center gap-2">
          <Building2 className="w-5 h-5" /> Centro
        </h2>
        <div className="flex gap-1.5">
          {isStaff && (
            <>
              <button onClick={() => { loadTemplates(); setView("inject"); }} className="px-2.5 py-1.5 text-xs rounded bg-red-600/80 hover:bg-red-600 text-white flex items-center gap-1">
                <Zap className="w-3 h-3" /> Incidente
              </button>
              <button onClick={() => setView("meeting")} className="px-2.5 py-1.5 text-xs rounded bg-indigo-600/80 hover:bg-indigo-600 text-white flex items-center gap-1">
                <Users className="w-3 h-3" /> Reunión
              </button>
            </>
          )}
          <button onClick={() => setView("chat")} className="px-2.5 py-1.5 text-xs rounded ls-bg-input ls-text-muted hover:ls-text flex items-center gap-1">
            <MessageSquare className="w-3 h-3" /> Chat
          </button>
          <button onClick={refreshBoxes} className="p-1.5 rounded ls-bg-input ls-text-muted hover:ls-text">
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Incidentes activos globales */}
      {activeIncidents.length > 0 && (
        <div className="mb-4">
          <h3 className="text-xs font-semibold uppercase ls-text-muted mb-2 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" /> Incidentes activos ({activeIncidents.length})
          </h3>
          <div className="space-y-1">
            {activeIncidents.slice(0, 5).map((inc) => (
              <div key={inc.id} className={`border-l-2 rounded p-2 text-sm ${severityColors[inc.severity]}`}>
                <div className="flex items-center gap-2">
                  <span>{categoryIcons[inc.category]}</span>
                  <span className="font-medium ls-text flex-1">{inc.title}</span>
                  {inc.affected_box && <span className="text-[10px] ls-text-muted">Box {inc.affected_box}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Grid de boxes */}
      <div className="grid grid-cols-2 gap-3">
        {boxes.map((box) => {
          const activePatient = box.agenda.find((a) => a.status === "in_progress");
          const pending = box.agenda.filter((a) => a.status === "scheduled").length;
          const done = box.agenda.filter((a) => a.status === "completed").length;
          const hasIncident = box.incidents.some((i) => i.status === "active");

          return (
            <div
              key={box.id}
              onClick={() => { setSelectedBoxId(box.id); setView("box"); }}
              className={`p-3 rounded border cursor-pointer transition hover:border-indigo-500 ${
                hasIncident ? "border-amber-500/50 ls-card" : "ls-border ls-card"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold ls-text text-sm">{box.name}</span>
                {hasIncident && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
              </div>
              <p className="text-xs ls-text-muted mb-2">{box.student_name ?? box.student_username ?? "Sin asignar"}</p>
              {activePatient && (
                <div className="text-[10px] bg-amber-900/20 text-amber-300 rounded px-2 py-0.5 mb-1 truncate">
                  🩺 {activePatient.patient_name}
                </div>
              )}
              <div className="flex gap-3 text-[10px] ls-text-muted">
                <span><Clock className="inline w-2.5 h-2.5" /> {pending}</span>
                <span><CheckCircle2 className="inline w-2.5 h-2.5 text-green-400" /> {done}</span>
              </div>
            </div>
          );
        })}
      </div>

      {boxes.length === 0 && (
        <p className="text-xs ls-text-muted text-center py-8">No hay boxes configurados</p>
      )}

      {/* Reuniones activas */}
      {meetings.filter((m) => m.status !== "completed").length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase ls-text-muted mb-2">Reuniones</h3>
          {meetings.filter((m) => m.status !== "completed").map((m) => (
            <div key={m.id} className="p-2 rounded ls-card border ls-border text-sm mb-1 flex items-center gap-2 cursor-pointer hover:border-indigo-500"
              onClick={() => setView("meeting")}>
              <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
              <span className="flex-1 ls-text">{m.title}</span>
              <span className={`text-[10px] ${m.status === "in_progress" ? "text-green-400 animate-pulse" : "text-blue-400"}`}>
                {m.status === "in_progress" ? "En curso" : "Programada"}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Botón detener (staff) */}
      {isStaff && (
        <div className="mt-6 text-center">
          <button onClick={stopCenter} className="px-4 py-1.5 text-xs rounded border border-red-500/30 text-red-400 hover:bg-red-900/20">
            Finalizar sesión de centro
          </button>
        </div>
      )}
    </div>
  );
}
