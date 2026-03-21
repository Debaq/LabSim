import { useEffect, useState } from "react";
import { useSyncStore } from "@/stores/sync-store";
import { usePatientStore } from "@/stores/patient-store";
import { Calendar, Download, FileText, Clock, ChevronRight, Send, CheckCircle, Loader2 } from "lucide-react";

interface Session {
  id: string;
  title: string;
  description?: string;
  status: string;
  scheduled_date?: string;
  scheduled_time?: string;
  duration_minutes?: number;
  group_name?: string;
  instructions?: string;
  cases?: Array<{
    id: string;
    title: string;
    description?: string;
    difficulty?: string;
    is_required?: number;
  }>;
  guides?: Array<{
    id: string;
    title: string;
    guide_type: string;
    file_size?: number;
    external_url?: string;
  }>;
}

/**
 * Ventana de Sesiones Prácticas (vista estudiante)
 * Muestra las sesiones asignadas, material guía, y permite cargar casos
 */
export function PracticeSessionsWindow() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submissions, setSubmissions] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<string | null>(null);
  const getSessions = useSyncStore((s) => s.getSessions);
  const getSessionDetail = useSyncStore((s) => s.getSessionDetail);
  const getSubmissions = useSyncStore((s) => s.getSubmissions);
  const submitWork = useSyncStore((s) => s.submitWork);
  const loadCase = usePatientStore((s) => s.loadCase);
  const caseInfo = usePatientStore((s) => s.caseInfo);
  const mode = usePatientStore((s) => s.mode);
  const getSnapshot = usePatientStore((s) => s.getSubmissionSnapshot);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    setLoading(true);
    setError(null);
    try {
      const result = (await getSessions("active")) as { items?: Session[] };
      setSessions(result?.items ?? []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function selectSession(session: Session) {
    try {
      const detail = (await getSessionDetail(session.id)) as { session: Session };
      setSelectedSession(detail.session);

      // Cargar estado de entregas
      const subs = (await getSubmissions(session.id)) as {
        items?: Array<{ case_id: string; status: string }>;
      };
      const statusMap: Record<string, string> = {};
      for (const sub of subs?.items ?? []) {
        statusMap[sub.case_id] = sub.status;
      }
      setSubmissions(statusMap);
    } catch {
      setSelectedSession(session);
    }
  }

  function handleLoadCase(caseData: NonNullable<Session["cases"]>[0]) {
    // Cargar caso en modo sesión: el estudiante recibe patientInfo + anamnesis,
    // pero los módulos de resultados llegan vacíos
    loadCase({
      caseId: caseData.id,
      sessionId: selectedSession?.id,
      title: caseData.title,
      baseProfile: (caseData as Record<string, unknown>).profile as never ?? {
        patientInfo: {},
        anamnesis: {},
        audiometry: {},
        logoaudiometry: {},
        supraliminal: {},
        impedance: {},
        oae: {},
        abr: {},
        electrocochleo: {},
        hearingAids: {},
        oct: {},
        visualField: {},
      },
    });
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center ls-bg ls-text-muted">
        Cargando sesiones...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center ls-bg p-4">
        <p className="text-red-400 mb-3">{error}</p>
        <button onClick={loadSessions} className="ls-btn-primary px-4 py-2 rounded">
          Reintentar
        </button>
      </div>
    );
  }

  // Vista detalle de sesión
  if (selectedSession) {
    return (
      <div className="h-full overflow-auto ls-bg p-4">
        <button
          onClick={() => setSelectedSession(null)}
          className="text-sm ls-text-muted hover:ls-text mb-3 flex items-center gap-1"
        >
          ← Volver a sesiones
        </button>

        <h2 className="text-lg font-semibold ls-text mb-1">{selectedSession.title}</h2>
        {selectedSession.description && (
          <p className="text-sm ls-text-muted mb-3">{selectedSession.description}</p>
        )}

        <div className="flex gap-4 text-xs ls-text-muted mb-4">
          {selectedSession.scheduled_date && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {selectedSession.scheduled_date} {selectedSession.scheduled_time}
            </span>
          )}
          {selectedSession.duration_minutes && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {selectedSession.duration_minutes} min
            </span>
          )}
        </div>

        {selectedSession.instructions && (
          <div className="ls-card p-3 mb-4 rounded border ls-border">
            <h3 className="text-sm font-medium ls-text mb-1">Instrucciones</h3>
            <p className="text-sm ls-text-muted whitespace-pre-wrap">{selectedSession.instructions}</p>
          </div>
        )}

        {/* Guías */}
        {selectedSession.guides && selectedSession.guides.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium ls-text mb-2 flex items-center gap-1">
              <Download className="w-4 h-4" /> Material guía
            </h3>
            <div className="space-y-1">
              {selectedSession.guides.map((g) => (
                <div key={g.id} className="flex items-center gap-2 p-2 rounded ls-card border ls-border text-sm">
                  <FileText className="w-4 h-4 ls-text-muted" />
                  <span className="ls-text flex-1">{g.title}</span>
                  <span className="text-xs ls-text-muted">{g.guide_type}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Casos */}
        {selectedSession.cases && selectedSession.cases.length > 0 && (
          <div>
            <h3 className="text-sm font-medium ls-text mb-2">Casos a completar</h3>
            <div className="space-y-2">
              {selectedSession.cases.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center gap-3 p-3 rounded ls-card border ls-border cursor-pointer hover:border-indigo-500 transition-colors"
                  onClick={() => handleLoadCase(c)}
                >
                  <div className="flex-1">
                    <span className="text-sm font-medium ls-text">{c.title}</span>
                    {c.description && (
                      <p className="text-xs ls-text-muted mt-0.5">{c.description}</p>
                    )}
                  </div>
                  {submissions[c.id] && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex items-center gap-0.5 ${
                      submissions[c.id] === "reviewed" ? "bg-green-900/30 text-green-400" :
                      submissions[c.id] === "submitted" ? "bg-blue-900/30 text-blue-400" :
                      submissions[c.id] === "returned" ? "bg-amber-900/30 text-amber-400" :
                      "bg-gray-900/30 text-gray-400"
                    }`}>
                      {submissions[c.id] === "reviewed" && <CheckCircle className="w-2.5 h-2.5" />}
                      {submissions[c.id] === "reviewed" ? "Calificado" :
                       submissions[c.id] === "submitted" ? "Enviado" :
                       submissions[c.id] === "returned" ? "Devuelto" : "Borrador"}
                    </span>
                  )}
                  {c.difficulty && (
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      c.difficulty === "hard" ? "bg-red-900/30 text-red-400" :
                      c.difficulty === "easy" ? "bg-green-900/30 text-green-400" :
                      "bg-yellow-900/30 text-yellow-400"
                    }`}>
                      {c.difficulty}
                    </span>
                  )}
                  {caseInfo?.caseId === c.id && mode === "session" && !submissions[c.id]?.match(/submitted|reviewed/) && (
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        setSubmitting(c.id);
                        try {
                          const snapshot = getSnapshot();
                          await submitWork(
                            selectedSession?.id ?? "",
                            c.id,
                            snapshot.data as unknown as Record<string, unknown>,
                          );
                          setSubmissions((prev) => ({ ...prev, [c.id]: "submitted" }));
                        } catch { /* error silencioso */ } finally {
                          setSubmitting(null);
                        }
                      }}
                      disabled={submitting === c.id}
                      className="shrink-0 px-2 py-1 text-[10px] rounded bg-indigo-600 text-white flex items-center gap-1 disabled:opacity-50"
                    >
                      {submitting === c.id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Send className="w-3 h-3" />
                      )}
                      Enviar
                    </button>
                  )}
                  <ChevronRight className="w-4 h-4 ls-text-muted" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Lista de sesiones
  return (
    <div className="h-full overflow-auto ls-bg p-4">
      <h2 className="text-lg font-semibold ls-text mb-3">Mis Sesiones Prácticas</h2>

      {sessions.length === 0 ? (
        <p className="text-sm ls-text-muted text-center py-8">No tienes sesiones asignadas</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="p-3 rounded ls-card border ls-border cursor-pointer hover:border-indigo-500 transition-colors"
              onClick={() => selectSession(s)}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium ls-text">{s.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  s.status === "active" ? "bg-green-900/30 text-green-400" :
                  s.status === "approved" ? "bg-blue-900/30 text-blue-400" :
                  "bg-gray-900/30 text-gray-400"
                }`}>
                  {s.status}
                </span>
              </div>
              {s.scheduled_date && (
                <div className="flex items-center gap-1 text-xs ls-text-muted mt-1">
                  <Calendar className="w-3 h-3" /> {s.scheduled_date}
                  {s.group_name && <span>· {s.group_name}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
