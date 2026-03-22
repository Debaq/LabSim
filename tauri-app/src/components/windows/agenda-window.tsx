import { useEffect, useState, useMemo, useCallback } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { invoke } from "@tauri-apps/api/core";
import { useAgendaTimerStore } from "@/stores/agenda-timer-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CalendarDays,
  Clock,
  RotateCcw,
  Users,
  Loader2,
  Plus,
  AlertTriangle,
  RefreshCw,
  Eye,
  Building2,
} from "lucide-react";
import { toast } from "sonner";

interface AgendaItem {
  id: string;
  patient_name: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  status: string;
  procedure_name: string | null;
  procedure_code: string | null;
  author_name: string | null;
  author_username: string | null;
  author_id: string;
  assigned_to: string | null;
  assigned_name: string | null;
  assigned_username: string | null;
  course_name: string | null;
  course_code: string | null;
  course_id: string | null;
  case_id: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  rescheduled: "Reagendada",
  no_show: "No asistió",
};

const STATUS_COLORS: Record<string, string> = {
  scheduled: "text-sky-400 bg-sky-500/10",
  in_progress: "text-amber-400 bg-amber-500/10",
  completed: "text-emerald-400 bg-emerald-500/10",
  cancelled: "text-zinc-400 bg-zinc-500/10",
  rescheduled: "text-orange-400 bg-orange-500/10",
  no_show: "text-red-400 bg-red-500/10",
};

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (d.getTime() === today.getTime()) return "Hoy";
    if (d.getTime() === tomorrow.getTime()) return "Mañana";
    return d.toLocaleDateString("es-CL", { weekday: "short", day: "2-digit", month: "short" });
  } catch {
    return dateStr;
  }
}

type ViewMode = "agenda" | "centro";

export function AgendaWindow() {
  const [items, setItems] = useState<AgendaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("agenda");
  const [newCitaOpen, setNewCitaOpen] = useState(false);
  const [rescheduleItem, setRescheduleItem] = useState<AgendaItem | null>(null);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");

  const role = useAuthStore((s) => s.role);
  const userId = useAuthStore((s) => s.userInfo?.id);
  const isStaff = role === "admin" || role === "docente" || role === "instructor";

  const loadAgenda = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split("T")[0];
      const future = new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0];
      const result = await invoke<{ data: AgendaItem[] }>("api_get_agenda", { from: today, to: future });
      setItems(result?.data ?? []);
    } catch (e) {
      setError(String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAgenda(); }, [loadAgenda]);

  // Agrupar por fecha
  const groupedByDate = useMemo(() => {
    const groups: Record<string, AgendaItem[]> = {};
    for (const item of items) {
      const key = item.scheduled_date;
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [items]);

  // Vista Centro: agrupar por estudiante
  const groupedByStudent = useMemo(() => {
    const groups: Record<string, { name: string; items: AgendaItem[] }> = {};
    for (const item of items) {
      if (!item.assigned_to) continue;
      if (!groups[item.assigned_to]) {
        groups[item.assigned_to] = { name: item.assigned_name ?? item.assigned_username ?? "?", items: [] };
      }
      groups[item.assigned_to].items.push(item);
    }
    return Object.entries(groups).sort(([, a], [, b]) => a.name.localeCompare(b.name));
  }, [items]);

  // Detectar conflictos: items del mismo estudiante que se solapan
  const conflictIds = useMemo(() => {
    const ids = new Set<string>();
    const byStudentDate: Record<string, AgendaItem[]> = {};
    for (const item of items) {
      if (!item.assigned_to || item.status === "cancelled" || item.status === "rescheduled") continue;
      const key = `${item.assigned_to}_${item.scheduled_date}`;
      if (!byStudentDate[key]) byStudentDate[key] = [];
      byStudentDate[key].push(item);
    }
    for (const group of Object.values(byStudentDate)) {
      for (let i = 0; i < group.length; i++) {
        for (let j = i + 1; j < group.length; j++) {
          const a = group[i], b = group[j];
          const aStart = timeToMin(a.scheduled_time);
          const aEnd = aStart + (a.duration_minutes ?? 30);
          const bStart = timeToMin(b.scheduled_time);
          const bEnd = bStart + (b.duration_minutes ?? 30);
          if (aStart < bEnd && aEnd > bStart) {
            ids.add(a.id);
            ids.add(b.id);
          }
        }
      }
    }
    return ids;
  }, [items]);

  async function handleReschedule() {
    if (!rescheduleItem || !newDate || !newTime) return;
    try {
      await invoke("api_reschedule_appointment", {
        appointmentId: rescheduleItem.id,
        scheduledDate: newDate,
        scheduledTime: newTime,
      });
      if (rescheduleItem.patient_name) {
        useAgendaTimerStore.getState().triggerRescheduleConsequence(
          rescheduleItem.patient_name,
          rescheduleItem.id,
        );
      }
      setRescheduleItem(null);
      toast.success("Cita reagendada");
      await loadAgenda();
    } catch (e) {
      toast.error(`Error al reagendar: ${e}`);
    }
  }

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <CalendarDays className="h-4 w-4 text-amber-400" />
        <span className="text-xs font-medium ls-text2">Agenda</span>

        {isStaff && (
          <div className="ml-2 flex items-center gap-0.5">
            <button
              onClick={() => setViewMode("agenda")}
              className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
                viewMode === "agenda" ? "bg-amber-500/15 text-amber-400" : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              <Eye className="inline h-3 w-3 mr-0.5" />Mi agenda
            </button>
            <button
              onClick={() => setViewMode("centro")}
              className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
                viewMode === "centro" ? "bg-amber-500/15 text-amber-400" : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              <Building2 className="inline h-3 w-3 mr-0.5" />Centro
            </button>
          </div>
        )}

        <div className="ml-auto flex items-center gap-1">
          {isStaff && (
            <Button size="xs" variant="ghost" onClick={() => setNewCitaOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
              <Plus className="h-3 w-3" />
              Nueva Cita
            </Button>
          )}
          <Button size="icon-xs" variant="ghost" onClick={loadAgenda} className="ls-text-muted hover:ls-text">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : items.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <CalendarDays className="mx-auto h-10 w-10 ls-text-muted opacity-30 mb-3" />
            <p className="text-xs ls-text-muted">No hay citas programadas</p>
          </div>
        ) : viewMode === "centro" && isStaff ? (
          /* ─── VISTA CENTRO: por estudiante ─── */
          <div className="p-3 space-y-3">
            {groupedByStudent.map(([studentId, { name, items: studentItems }]) => (
              <div key={studentId} className="rounded-lg border ls-border ls-bg-input p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-3.5 w-3.5 text-cyan-400" />
                  <span className="text-xs font-medium ls-text2">{name}</span>
                  <span className="text-[10px] ls-text-muted">{studentItems.length} citas</span>
                </div>
                <div className="space-y-1">
                  {studentItems
                    .sort((a, b) => `${a.scheduled_date}${a.scheduled_time}`.localeCompare(`${b.scheduled_date}${b.scheduled_time}`))
                    .map((item) => (
                    <div
                      key={item.id}
                      className={`flex items-center gap-2 rounded px-2 py-1.5 text-xs ${
                        conflictIds.has(item.id) ? "bg-red-500/10 border border-red-500/20" : "hover:bg-white/5"
                      }`}
                    >
                      {conflictIds.has(item.id) && <AlertTriangle className="h-3 w-3 text-red-400 shrink-0" />}
                      <span className="ls-text-muted w-16 shrink-0">{formatDate(item.scheduled_date)}</span>
                      <span className="font-medium ls-text2 w-12 shrink-0">{item.scheduled_time?.slice(0, 5)}</span>
                      <span className="ls-text2 truncate flex-1">{item.patient_name}</span>
                      {item.procedure_name && (
                        <span className="text-[10px] ls-text-muted truncate max-w-[100px]">{item.procedure_name}</span>
                      )}
                      {item.author_id !== userId && item.author_name && (
                        <Badge variant="outline" className="text-[8px] px-1 py-0 text-indigo-400 bg-indigo-500/10 shrink-0">
                          {item.author_name}
                        </Badge>
                      )}
                      {item.course_name && (
                        <Badge variant="outline" className="text-[8px] px-1 py-0 ls-border ls-text-muted shrink-0">
                          {item.course_code ?? item.course_name}
                        </Badge>
                      )}
                      <Badge variant="outline" className={`text-[8px] px-1 py-0 shrink-0 ${STATUS_COLORS[item.status] ?? ""}`}>
                        {STATUS_LABELS[item.status] ?? item.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* ─── VISTA AGENDA: por fecha ─── */
          <div className="p-3 space-y-3">
            {groupedByDate.map(([date, dayItems]) => (
              <div key={date}>
                <div className="px-1 py-1 text-[10px] font-bold uppercase tracking-wider ls-text-muted">
                  {formatDate(date)}
                </div>
                <div className="space-y-1">
                  {dayItems.map((item) => (
                    <div
                      key={item.id}
                      className={`flex items-start gap-2.5 rounded-lg px-2.5 py-2 border ls-border ${
                        conflictIds.has(item.id) ? "border-red-500/30 bg-red-500/5" : ""
                      }`}
                    >
                      <div className="flex flex-col items-center min-w-[44px]">
                        <span className="text-sm font-bold ls-text">{item.scheduled_time?.slice(0, 5)}</span>
                        <span className="text-[10px] ls-text-muted flex items-center gap-0.5">
                          <Clock className="h-2.5 w-2.5" />{item.duration_minutes ?? 30}m
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          {conflictIds.has(item.id) && <AlertTriangle className="h-3 w-3 text-red-400 shrink-0" />}
                          <span className="text-xs font-medium ls-text2 truncate">{item.patient_name}</span>
                          <Badge variant="outline" className={`text-[9px] px-1 py-0 ${STATUS_COLORS[item.status] ?? ""}`}>
                            {STATUS_LABELS[item.status] ?? item.status}
                          </Badge>
                        </div>
                        {item.procedure_name && (
                          <p className="text-[10px] ls-text-muted mt-0.5">{item.procedure_name}</p>
                        )}
                        <div className="flex items-center gap-2 mt-0.5">
                          {isStaff && item.assigned_name && (
                            <span className="text-[10px] text-cyan-400">
                              → {item.assigned_name}
                            </span>
                          )}
                          {item.author_id !== userId && item.author_name && (
                            <span className="text-[10px] text-indigo-400">
                              por {item.author_name}
                            </span>
                          )}
                          {item.course_name && (
                            <Badge variant="outline" className="text-[8px] px-1 py-0 ls-border ls-text-muted">
                              {item.course_code ?? item.course_name}
                            </Badge>
                          )}
                        </div>
                      </div>
                      {!isStaff && item.status === "scheduled" && (
                        <button
                          onClick={() => { setRescheduleItem(item); setNewDate(""); setNewTime(""); }}
                          className="shrink-0 rounded p-1 hover:ls-bg-input"
                          title="Reagendar"
                        >
                          <RotateCcw className="h-3.5 w-3.5 text-amber-400" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
        <span>{items.length} citas</span>
        {conflictIds.size > 0 && (
          <span className="text-red-400 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            {conflictIds.size} conflictos
          </span>
        )}
        {error && <span className="text-amber-400/60">{error}</span>}
      </div>

      {/* Reagendar (estudiante) */}
      <Dialog open={!!rescheduleItem} onOpenChange={(o) => !o && setRescheduleItem(null)}>
        <DialogContent className="ls-bg ls-text ls-border max-w-xs">
          <DialogHeader>
            <DialogTitle className="ls-text">Reagendar: {rescheduleItem?.patient_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Nueva fecha</Label>
              <Input type="date" value={newDate} onChange={(e) => setNewDate(e.target.value)} className="ls-border ls-bg-input text-xs ls-text" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Nueva hora</Label>
              <Input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)} className="ls-border ls-bg-input text-xs ls-text" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRescheduleItem(null)} className="ls-border ls-text2">Cancelar</Button>
            <Button onClick={handleReschedule} disabled={!newDate || !newTime} className="bg-amber-600 text-white hover:bg-amber-500">
              Reagendar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Nueva Cita (docente) */}
      <NewCitaDialog open={newCitaOpen} onOpenChange={setNewCitaOpen} onCreated={loadAgenda} />
    </div>
  );
}

function timeToMin(time: string): number {
  return parseInt(time.slice(0, 2)) * 60 + parseInt(time.slice(3, 2));
}

// ─── Diálogo: Nueva Cita ─────────────────────────────

function NewCitaDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  onCreated: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [patientName, setPatientName] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState("30");
  const [courseId, setCourseId] = useState("");
  const [assignAll, setAssignAll] = useState(false);

  // Cargar cursos del docente
  const [courses, setCourses] = useState<Array<{ id: string; name: string; code: string | null }>>([]);
  useEffect(() => {
    if (!open) return;
    invoke<{ data: Array<{ id: string; name: string; code: string | null }> }>("api_list_courses", {})
      .then((r) => setCourses(r?.data ?? []))
      .catch(() => setCourses([]));
  }, [open]);

  const handleSubmit = async () => {
    if (!patientName.trim() || !date || !time) {
      toast.error("Paciente, fecha y hora son obligatorios");
      return;
    }
    setSaving(true);
    try {
      if (assignAll && courseId) {
        const result = await invoke<{ count: number; conflictStudents?: string[]; conflictCount?: number }>(
          "api_assign_agenda_group",
          { item: { patientName, scheduledDate: date, scheduledTime: time, durationMinutes: parseInt(duration), courseId } }
        );
        if (result.conflictCount && result.conflictCount > 0) {
          toast.warning(`Cita creada para ${result.count} estudiantes. ${result.conflictCount} tienen conflictos de horario.`);
        } else {
          toast.success(`Cita asignada a ${result.count} estudiantes`);
        }
      } else {
        await invoke("api_create_agenda_item", {
          item: { patientName, scheduledDate: date, scheduledTime: time, durationMinutes: parseInt(duration), courseId: courseId || undefined },
        });
        toast.success("Cita creada");
      }
      setPatientName(""); setDate(""); setTime(""); setCourseId(""); setAssignAll(false);
      onOpenChange(false);
      onCreated();
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-w-sm">
        <DialogHeader><DialogTitle className="ls-text">Nueva Cita</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Paciente *</Label>
            <Input value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Nombre del paciente" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Fecha *</Label>
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="ls-border ls-bg-input text-xs ls-text" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Hora *</Label>
              <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="ls-border ls-bg-input text-xs ls-text" />
            </div>
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Duración (minutos)</Label>
            <Input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          {courses.length > 0 && (
            <>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Curso</Label>
                <select
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value)}
                  className="w-full h-7 rounded-md px-2 text-xs ls-border ls-bg-input ls-text"
                >
                  <option value="">Sin curso</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}{c.code ? ` (${c.code})` : ""}</option>
                  ))}
                </select>
              </div>
              {courseId && (
                <label className="flex items-center gap-2 text-xs ls-text2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={assignAll}
                    onChange={(e) => setAssignAll(e.target.checked)}
                    className="rounded"
                  />
                  Asignar a todos los estudiantes del curso
                </label>
              )}
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="ls-border ls-text2">Cancelar</Button>
          <Button onClick={handleSubmit} disabled={saving} className="gap-1 bg-amber-600 text-white hover:bg-amber-500">
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            Crear
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
