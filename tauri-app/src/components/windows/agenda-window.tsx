import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useSyncStore } from "@/stores/sync-store";
import { invoke } from "@tauri-apps/api/core";
import { useAgendaTimerStore } from "@/stores/agenda-timer-store";
import { CalendarDays, Clock, RotateCcw, Users } from "lucide-react";

interface AgendaItem {
  id: string;
  title: string;
  description?: string;
  patient_name?: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes?: number;
  item_type: string;
  author_username?: string;
  author_name?: string;
  assigned_username?: string;
  assigned_name?: string;
}

const typeLabels: Record<string, string> = {
  appointment: "Cita",
  class: "Clase",
  exam: "Examen",
  practice: "Práctica",
  reschedule: "Reagendado",
  other: "Otro",
};

const typeColors: Record<string, string> = {
  appointment: "bg-blue-900/30 text-blue-400",
  class: "bg-purple-900/30 text-purple-400",
  exam: "bg-red-900/30 text-red-400",
  practice: "bg-green-900/30 text-green-400",
  reschedule: "bg-amber-900/30 text-amber-400",
  other: "bg-gray-900/30 text-gray-400",
};

export function AgendaWindow() {
  const [items, setItems] = useState<AgendaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rescheduleItem, setRescheduleItem] = useState<AgendaItem | null>(null);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const getAgenda = useSyncStore((s) => s.getAgenda);
  const role = useAuthStore((s) => s.role);

  useEffect(() => {
    loadAgenda();
  }, []);

  async function loadAgenda() {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split("T")[0];
      const nextMonth = new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0];
      const result = (await getAgenda(today, nextMonth)) as { items?: AgendaItem[] };
      setItems(result?.items ?? []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleReschedule() {
    if (!rescheduleItem || !newDate || !newTime) return;
    setError(null);
    try {
      await invoke("api_reschedule_appointment", {
        appointmentId: rescheduleItem.id,
        scheduledDate: newDate,
        scheduledTime: newTime,
      });

      // Consecuencia: posible queja del paciente (según pressureLevel)
      if (rescheduleItem.patient_name) {
        useAgendaTimerStore.getState().triggerRescheduleConsequence(
          rescheduleItem.patient_name,
          rescheduleItem.id,
        );
      }

      setRescheduleItem(null);
      setNewDate("");
      setNewTime("");
      await loadAgenda();
    } catch (e) {
      setError(`Error al reagendar: ${e}`);
    }
  }

  // Agrupar por fecha
  const grouped: Record<string, AgendaItem[]> = {};
  for (const item of items) {
    const date = item.scheduled_date;
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(item);
  }

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = d.getTime() - today.getTime();
    const days = Math.round(diff / 86400000);

    if (days === 0) return "Hoy";
    if (days === 1) return "Mañana";
    return d.toLocaleDateString("es", { weekday: "long", day: "numeric", month: "short" });
  }

  const isDocente = role === "admin" || role === "docente" || role === "instructor";

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center ls-bg ls-text-muted">
        Cargando agenda...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center ls-bg p-4">
        <CalendarDays className="w-10 h-10 ls-text-muted mb-3" />
        <p className="text-sm ls-text-muted mb-1">No se pudo cargar la agenda</p>
        <p className="text-xs text-red-400 mb-3">{error}</p>
        <button onClick={loadAgenda} className="ls-btn-primary px-4 py-1.5 rounded text-sm">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto ls-bg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold ls-text flex items-center gap-2">
          <CalendarDays className="w-5 h-5" /> Agenda
        </h2>
        {isDocente && (
          <span className="text-[10px] ls-text-muted flex items-center gap-1">
            <Users className="w-3 h-3" /> Vista docente
          </span>
        )}
      </div>

      {/* Modal reagendar (estudiante) */}
      {rescheduleItem && (
        <div className="mb-4 p-3 rounded border ls-border ls-card">
          <h4 className="text-sm font-medium ls-text mb-2 flex items-center gap-1">
            <RotateCcw className="w-3.5 h-3.5" /> Reagendar: {rescheduleItem.patient_name ?? rescheduleItem.title}
          </h4>
          <div className="flex gap-2 items-end">
            <div>
              <label className="text-[10px] ls-text-muted block mb-0.5">Nueva fecha</label>
              <input
                type="date"
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                className="px-2 py-1 text-xs rounded ls-bg-input border ls-border ls-text"
              />
            </div>
            <div>
              <label className="text-[10px] ls-text-muted block mb-0.5">Nueva hora</label>
              <input
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="px-2 py-1 text-xs rounded ls-bg-input border ls-border ls-text"
              />
            </div>
            <button
              onClick={handleReschedule}
              disabled={!newDate || !newTime}
              className="px-3 py-1 text-xs rounded bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-40"
            >
              Reagendar
            </button>
            <button
              onClick={() => setRescheduleItem(null)}
              className="px-3 py-1 text-xs rounded ls-bg-input ls-text-muted hover:ls-text"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {Object.keys(grouped).length === 0 ? (
        <div className="text-center py-12">
          <CalendarDays className="w-12 h-12 mx-auto ls-text-muted mb-3 opacity-30" />
          <p className="text-sm ls-text-muted">No hay eventos programados</p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(grouped).map(([date, dayItems]) => (
            <div key={date}>
              <h3 className="text-xs font-semibold uppercase ls-text-muted mb-2 capitalize">
                {formatDate(date)}
              </h3>
              <div className="space-y-1.5">
                {dayItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 p-2.5 rounded ls-card border ls-border"
                  >
                    <div className="flex flex-col items-center min-w-[44px]">
                      <span className="text-sm font-bold ls-text">{item.scheduled_time}</span>
                      {item.duration_minutes && (
                        <span className="text-[10px] ls-text-muted flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5" />{item.duration_minutes}m
                        </span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium ls-text truncate">{item.title}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${typeColors[item.item_type] ?? typeColors.other}`}>
                          {typeLabels[item.item_type] ?? item.item_type}
                        </span>
                      </div>
                      {item.patient_name && (
                        <p className="text-xs ls-text-muted mt-0.5">Paciente: {item.patient_name}</p>
                      )}
                      {item.description && (
                        <p className="text-xs ls-text-muted mt-0.5 truncate">{item.description}</p>
                      )}
                      {/* Mostrar quién lo asignó / a quién está asignado */}
                      {isDocente && item.assigned_name && (
                        <p className="text-[10px] text-indigo-400 mt-0.5">
                          Asignado a: {item.assigned_name}
                        </p>
                      )}
                      {!isDocente && item.author_name && (
                        <p className="text-[10px] text-indigo-400 mt-0.5">
                          Asignado por: {item.author_name}
                        </p>
                      )}
                    </div>
                    {/* Estudiantes pueden reagendar */}
                    {!isDocente && item.patient_name && (
                      <button
                        onClick={() => { setRescheduleItem(item); setNewDate(""); setNewTime(""); }}
                        className="shrink-0 p-1 rounded hover:ls-bg-input"
                        title="Reagendar paciente"
                      >
                        <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
