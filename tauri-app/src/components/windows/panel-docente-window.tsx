import { useState, useEffect, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  LayoutDashboard,
  GraduationCap,
  ClipboardList,
  CalendarDays,
  Users,
  UsersRound,
  Plus,
  Loader2,
  Check,
  ChevronRight,
  RefreshCw,
  Building2,
  Shuffle,
  Trash2,
  UserPlus,
  X,
  ExternalLink,
  Settings2,
  FileText,
  BarChart3,
  Clock,
  Repeat,
} from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import {
  usePanelDocenteStore,
  type Course,
  type CourseMember,
  type Session,
  type GroupDraft,
  type Procedure,
  type ScheduleBlock,
} from "@/stores/panel-docente-store";
import { useCoursesStore } from "@/stores/courses-store";
import { useUIStore } from "@/stores/ui-store";
import { WINDOW_SIZES } from "@/components/layout/desktop-area";
import { toast } from "sonner";

// ─── Status helpers ────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  pending_approval: "Pendiente",
  approved: "Aprobada",
  active: "Activa",
  completed: "Completada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "text-zinc-400 bg-zinc-500/10",
  pending_approval: "text-amber-400 bg-amber-500/10",
  approved: "text-sky-400 bg-sky-500/10",
  active: "text-emerald-400 bg-emerald-500/10",
  completed: "text-zinc-400 bg-zinc-500/10",
  cancelled: "text-zinc-400 bg-zinc-500/10",
};

const ACTIVE_STATUSES = new Set(["draft", "pending_approval", "approved", "active"]);
const PAST_STATUSES = new Set(["completed", "cancelled"]);

// ─── Main Component ────────────────────────────────────

export function PanelDocenteWindow() {
  const view = usePanelDocenteStore((s) => s.view);
  const navigate = usePanelDocenteStore((s) => s.navigate);
  const currentCourse = usePanelDocenteStore((s) => s.currentCourse);
  const sessionDetail = usePanelDocenteStore((s) => s.sessionDetail);

  return (
    <div className="flex h-full flex-col overflow-hidden ls-bg">
      {/* Breadcrumb header */}
      <Breadcrumb
        view={view}
        currentCourse={currentCourse}
        sessionTitle={sessionDetail?.title ?? null}
        navigate={navigate}
      />

      {/* Page content */}
      <div className="flex-1 overflow-hidden">
        {view.page === "courses" && <CoursesPage />}
        {view.page === "activities" && <ActivitiesPage courseId={view.courseId} />}
        {view.page === "activity-detail" && <ActivityDetailPage courseId={view.courseId} sessionId={view.sessionId} />}
        {view.page === "activity-config" && <ActivityConfigPage courseId={view.courseId} sessionId={view.sessionId} />}
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-3 border-t ls-border px-3 py-1.5 text-[10px] ls-text-muted shrink-0">
        {currentCourse && (
          <span>
            <GraduationCap className="inline h-3 w-3 mr-0.5" />
            {currentCourse.name}
          </span>
        )}
        {view.page === "activity-detail" && sessionDetail && (
          <span>
            <ClipboardList className="inline h-3 w-3 mr-0.5" />
            {sessionDetail.session_type === "grupal" ? "Grupal" : "Conjunto"}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Breadcrumb ────────────────────────────────────────

function Breadcrumb({
  view,
  currentCourse,
  sessionTitle,
  navigate,
}: {
  view: ReturnType<typeof usePanelDocenteStore.getState>["view"];
  currentCourse: Course | null;
  sessionTitle: string | null;
  navigate: ReturnType<typeof usePanelDocenteStore.getState>["navigate"];
}) {
  const parts: Array<{ label: string; icon?: React.ReactNode; onClick?: () => void }> = [
    {
      label: "Panel Docente",
      icon: <LayoutDashboard className="h-3.5 w-3.5 text-orange-400" />,
      onClick: view.page !== "courses" ? () => navigate({ page: "courses" }) : undefined,
    },
  ];

  if (view.page !== "courses" && currentCourse) {
    parts.push({
      label: currentCourse.name,
      onClick: view.page !== "activities" ? () => navigate({ page: "activities", courseId: view.courseId }) : undefined,
    });
  }

  if (view.page === "activity-detail" && sessionTitle) {
    parts.push({ label: sessionTitle });
  }

  if (view.page === "activity-config") {
    parts.push({ label: view.sessionId ? "Configurar" : "Nueva Actividad" });
  }

  return (
    <div className="flex items-center gap-1.5 border-b ls-border px-3 py-2 shrink-0">
      {parts.map((part, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="h-3 w-3 ls-text-muted" />}
          {part.icon}
          {part.onClick ? (
            <button onClick={part.onClick} className="text-xs font-medium ls-text-muted hover:ls-text transition truncate max-w-[140px]">
              {part.label}
            </button>
          ) : (
            <span className="text-xs font-medium ls-text2 truncate max-w-[180px]">{part.label}</span>
          )}
        </span>
      ))}
    </div>
  );
}

// ─── Page: Courses ─────────────────────────────────────

function CoursesPage() {
  const courses = usePanelDocenteStore((s) => s.courses);
  const coursesLoading = usePanelDocenteStore((s) => s.coursesLoading);
  const fetchCourses = usePanelDocenteStore((s) => s.fetchCourses);
  const navigate = usePanelDocenteStore((s) => s.navigate);
  const error = usePanelDocenteStore((s) => s.error);

  const [newCourseOpen, setNewCourseOpen] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
        <span className="text-xs font-medium ls-text2">Mis Cursos</span>
        <div className="ml-auto flex items-center gap-1">
          <Button size="xs" variant="ghost" onClick={() => setNewCourseOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
            <Plus className="h-3 w-3" />
            Nuevo Curso
          </Button>
          <Button size="icon-xs" variant="ghost" onClick={() => fetchCourses()} className="ls-text-muted hover:ls-text">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        {coursesLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : (courses ?? []).length === 0 ? (
          <div className="px-4 py-8 text-center">
            <GraduationCap className="mx-auto h-10 w-10 ls-text-muted opacity-30 mb-3" />
            <p className="text-xs ls-text-muted">No tienes cursos. Crea uno para empezar.</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {(courses ?? []).map((c) => (
              <button
                key={c.id}
                onClick={() => navigate({ page: "activities", courseId: c.id })}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition hover:ls-bg-input"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/10">
                  <GraduationCap className="h-4.5 w-4.5 text-sky-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium ls-text2 truncate">{c.name}</span>
                    {c.code && (
                      <Badge variant="outline" className="text-[9px] ls-border ls-text-muted shrink-0">{c.code}</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[10px] ls-text-muted">
                    <span><Users className="inline h-3 w-3 mr-0.5" />{c.student_count ?? 0} estudiantes</span>
                    {c.period && <span>· {c.period}</span>}
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 ls-text-muted shrink-0" />
              </button>
            ))}
          </div>
        )}
      </ScrollArea>

      {error && <div className="border-t ls-border px-3 py-1.5 text-[10px] text-amber-400 shrink-0">{error}</div>}

      <NewCourseDialog open={newCourseOpen} onOpenChange={setNewCourseOpen} onCreated={fetchCourses} />
    </div>
  );
}

// ─── Page: Activities ──────────────────────────────────

function ActivitiesPage({ courseId }: { courseId: string }) {
  const sessions = usePanelDocenteStore((s) => s.sessions);
  const sessionsLoading = usePanelDocenteStore((s) => s.sessionsLoading);
  const sessionsTab = usePanelDocenteStore((s) => s.sessionsTab);
  const setSessionsTab = usePanelDocenteStore((s) => s.setSessionsTab);
  const navigate = usePanelDocenteStore((s) => s.navigate);
  const fetchSessions = usePanelDocenteStore((s) => s.fetchSessions);

  const filteredSessions = useMemo(() => {
    const statusSet = sessionsTab === "active" ? ACTIVE_STATUSES : PAST_STATUSES;
    return sessions.filter((s) => statusSet.has(s.status));
  }, [sessions, sessionsTab]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
        {/* Tabs */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setSessionsTab("active")}
            className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
              sessionsTab === "active" ? "bg-orange-500/15 text-orange-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Activas
          </button>
          <button
            onClick={() => setSessionsTab("past")}
            className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
              sessionsTab === "past" ? "bg-orange-500/15 text-orange-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Pasadas
          </button>
        </div>

        <div className="ml-auto flex items-center gap-1">
          <Button
            size="xs"
            variant="ghost"
            onClick={() => navigate({ page: "activity-config", courseId, sessionId: null })}
            className="gap-1 ls-text-muted hover:ls-text"
          >
            <Plus className="h-3 w-3" />
            Nueva Actividad
          </Button>
          <Button size="icon-xs" variant="ghost" onClick={() => fetchSessions(courseId)} className="ls-text-muted hover:ls-text">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        {sessionsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <ClipboardList className="mx-auto h-10 w-10 ls-text-muted opacity-30 mb-3" />
            <p className="text-xs ls-text-muted">
              {sessionsTab === "active" ? "No hay actividades activas" : "No hay actividades pasadas"}
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredSessions.map((s) => (
              <SessionCard
                key={s.id}
                session={s}
                onClick={() => navigate({ page: "activity-detail", courseId, sessionId: s.id })}
              />
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

function SessionCard({ session, onClick }: { session: Session; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition hover:ls-bg-input"
    >
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500/10">
        <ClipboardList className="h-4.5 w-4.5 text-orange-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium ls-text2 truncate">{session.title}</span>
          <Badge variant="outline" className={`text-[9px] px-1 py-0 shrink-0 ${STATUS_COLORS[session.status] ?? "text-zinc-400 bg-zinc-500/10"}`}>
            {STATUS_LABELS[session.status] ?? session.status}
          </Badge>
        </div>
        <div className="flex items-center gap-2 text-[10px] ls-text-muted">
          {session.scheduled_date && (
            <span><CalendarDays className="inline h-3 w-3 mr-0.5" />{session.scheduled_date}</span>
          )}
          {session.session_type && (
            <span>· {session.session_type === "grupal" ? "Grupal" : "Conjunto"}</span>
          )}
          {session.case_count > 0 && (
            <span>· {session.case_count} casos</span>
          )}
        </div>
      </div>
      <ChevronRight className="h-4 w-4 ls-text-muted shrink-0" />
    </button>
  );
}

// ─── Page: Activity Detail ─────────────────────────────

function ActivityDetailPage({ courseId, sessionId }: { courseId: string; sessionId: string }) {
  const sessionDetail = usePanelDocenteStore((s) => s.sessionDetail);
  const detailLoading = usePanelDocenteStore((s) => s.detailLoading);
  const navigate = usePanelDocenteStore((s) => s.navigate);
  const openWindow = useUIStore((s) => s.openWindow);

  // Submission stats (must be before early return for hooks rules)
  const submissionsByStatus = useMemo(() => {
    if (!sessionDetail) return {};
    const map: Record<string, number> = {};
    for (const sub of sessionDetail.submissions ?? []) {
      map[sub.status] = (map[sub.status] ?? 0) + 1;
    }
    return map;
  }, [sessionDetail]);

  if (detailLoading || !sessionDetail) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-3">
          {/* Summary */}
          <div className="rounded-lg border ls-border ls-bg-input p-3 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium ls-text2">{sessionDetail.title}</span>
              <Badge variant="outline" className={`text-[9px] px-1 py-0 ${STATUS_COLORS[sessionDetail.status] ?? "text-zinc-400 bg-zinc-500/10"}`}>
                {STATUS_LABELS[sessionDetail.status] ?? sessionDetail.status}
              </Badge>
              {sessionDetail.session_type && (
                <Badge variant="outline" className={`text-[9px] px-1 py-0 ${
                  sessionDetail.session_type === "grupal" ? "text-amber-400 bg-amber-500/10" : "text-sky-400 bg-sky-500/10"
                }`}>
                  {sessionDetail.session_type === "grupal" ? "Grupal" : "Conjunto"}
                </Badge>
              )}
            </div>
            {sessionDetail.description && (
              <p className="text-[10px] ls-text-muted">{sessionDetail.description}</p>
            )}
            <div className="flex flex-wrap gap-3 text-[10px] ls-text-muted">
              {sessionDetail.scheduled_date && (
                <span><CalendarDays className="inline h-3 w-3 mr-0.5" />Fecha: {sessionDetail.scheduled_date}</span>
              )}
              {sessionDetail.location && (
                <span>Lugar: {sessionDetail.location}</span>
              )}
            </div>
            {sessionDetail.instructions && (
              <div className="mt-1 rounded bg-black/20 p-2 text-[10px] ls-text-muted">
                <FileText className="inline h-3 w-3 mr-1" />
                {sessionDetail.instructions}
              </div>
            )}
          </div>

          {/* Stats */}
          {(sessionDetail.submissions ?? []).length > 0 && (
            <div className="rounded-lg border ls-border ls-bg-input p-3">
              <h4 className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted mb-2">
                <BarChart3 className="inline h-3 w-3 mr-1" />
                Entregas
              </h4>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(submissionsByStatus).map(([status, count]) => (
                  <div key={status} className="rounded border ls-border p-2 text-center">
                    <div className="text-sm font-bold ls-text2">{count}</div>
                    <div className="text-[9px] ls-text-muted capitalize">{STATUS_LABELS[status] ?? status}</div>
                  </div>
                ))}
                <div className="rounded border ls-border p-2 text-center">
                  <div className="text-sm font-bold ls-text2">{(sessionDetail.submissions ?? []).length}</div>
                  <div className="text-[9px] ls-text-muted">Total</div>
                </div>
              </div>
            </div>
          )}

          {/* Cases */}
          {(sessionDetail.cases ?? []).length > 0 && (
            <div className="rounded-lg border ls-border ls-bg-input p-3">
              <h4 className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted mb-2">
                Casos ({sessionDetail.cases.length})
              </h4>
              <div className="space-y-1">
                {sessionDetail.cases.map((c) => (
                  <div key={c.id} className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-black/10">
                    <FileText className="h-3.5 w-3.5 text-sky-400 shrink-0" />
                    <span className="text-xs ls-text2 truncate">{c.title}</span>
                    <Badge variant="outline" className="text-[9px] ls-border ls-text-muted shrink-0">
                      {c.difficulty}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t ls-border px-3 py-2 shrink-0 flex items-center justify-between">
        <Button
          size="sm"
          variant="outline"
          onClick={() => openWindow("larissa", "Larissa", "larissa")}
          className="gap-1.5 ls-border ls-text2"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Abrir Larissa
        </Button>
        <Button
          size="sm"
          onClick={() => navigate({ page: "activity-config", courseId, sessionId })}
          className="gap-1.5 bg-orange-600 text-white hover:bg-orange-500"
        >
          <Settings2 className="h-3.5 w-3.5" />
          Configurar
        </Button>
      </div>
    </div>
  );
}

// ─── Page: Activity Config ─────────────────────────────

function ActivityConfigPage({ courseId, sessionId }: { courseId: string; sessionId: string | null }) {
  const sessionDraft = usePanelDocenteStore((s) => s.sessionDraft);
  const updateDraft = usePanelDocenteStore((s) => s.updateDraft);
  const courseMembers = usePanelDocenteStore((s) => s.courseMembers);
  const selectedDocentes = usePanelDocenteStore((s) => s.selectedDocentes);
  const selectedInstructores = usePanelDocenteStore((s) => s.selectedInstructores);
  const selectedEstudiantes = usePanelDocenteStore((s) => s.selectedEstudiantes);
  const toggleParticipant = usePanelDocenteStore((s) => s.toggleParticipant);
  const selectAllParticipants = usePanelDocenteStore((s) => s.selectAllParticipants);
  const removeFromCourse = usePanelDocenteStore((s) => s.removeFromCourse);
  const changeParticipantRole = usePanelDocenteStore((s) => s.changeParticipantRole);
  const groups = usePanelDocenteStore((s) => s.groups);
  const addGroup = usePanelDocenteStore((s) => s.addGroup);
  const removeGroup = usePanelDocenteStore((s) => s.removeGroup);
  const renameGroup = usePanelDocenteStore((s) => s.renameGroup);
  const assignStudentToGroup = usePanelDocenteStore((s) => s.assignStudentToGroup);
  const removeStudentFromGroup = usePanelDocenteStore((s) => s.removeStudentFromGroup);
  const assignInstructorToGroup = usePanelDocenteStore((s) => s.assignInstructorToGroup);
  const distributeGroups = usePanelDocenteStore((s) => s.distributeGroups);
  const createSession = usePanelDocenteStore((s) => s.createSession);
  const updateSession = usePanelDocenteStore((s) => s.updateSession);
  const saveGroups = usePanelDocenteStore((s) => s.saveGroups);
  const saving = usePanelDocenteStore((s) => s.saving);
  const navigate = usePanelDocenteStore((s) => s.navigate);
  const loadCourseMembers = usePanelDocenteStore((s) => s.loadCourseMembers);
  const procedures = usePanelDocenteStore((s) => s.procedures);
  const scheduleBlocks = usePanelDocenteStore((s) => s.scheduleBlocks);
  const fetchProcedures = usePanelDocenteStore((s) => s.fetchProcedures);
  const addBlock = usePanelDocenteStore((s) => s.addBlock);
  const removeBlock = usePanelDocenteStore((s) => s.removeBlock);
  const repeatWeek = usePanelDocenteStore((s) => s.repeatWeek);
  const saveSchedule = usePanelDocenteStore((s) => s.saveSchedule);

  const [addParticipantOpen, setAddParticipantOpen] = useState(false);
  const [groupCount, setGroupCount] = useState(3);
  const [calendarOpen, setCalendarOpen] = useState(false);

  const isEditing = sessionId !== null;

  useEffect(() => { fetchProcedures(); }, [fetchProcedures]);

  const handleSave = async () => {
    try {
      if (isEditing) {
        await updateSession(sessionId);
        if (sessionDraft.sessionType === "grupal" && groups.length > 0) {
          await saveGroups(sessionId);
        }
        if (scheduleBlocks.length > 0) {
          await saveSchedule(sessionId);
        }
        toast.success("Actividad actualizada");
      } else {
        const newId = await createSession(courseId);
        if (sessionDraft.sessionType === "grupal" && groups.length > 0 && newId) {
          await saveGroups(newId);
        }
        if (scheduleBlocks.length > 0 && newId) {
          await saveSchedule(newId);
        }
        toast.success("Actividad creada");
      }
      navigate({ page: "activities", courseId });
    } catch (e) {
      toast.error(`Error: ${e}`);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-4">
          {/* General section */}
          <ConfigSection title="General">
            <div className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Titulo *</Label>
                <Input
                  value={sessionDraft.title}
                  onChange={(e) => updateDraft({ title: e.target.value })}
                  placeholder="Audiometria tonal - Semana 3"
                  className="ls-border ls-bg-input text-xs ls-text"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Descripcion</Label>
                <Textarea
                  value={sessionDraft.description}
                  onChange={(e) => updateDraft({ description: e.target.value })}
                  placeholder="Objetivos y contexto de la actividad..."
                  rows={2}
                  className="ls-border ls-bg-input text-xs ls-text resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs ls-text2">Fecha inicio</Label>
                  <Input
                    type="date"
                    value={sessionDraft.startDate}
                    onChange={(e) => { updateDraft({ startDate: e.target.value }); e.target.blur(); }}
                    className="ls-border ls-bg-input text-xs ls-text"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs ls-text2">Fecha fin</Label>
                  <Input
                    type="date"
                    value={sessionDraft.endDate}
                    onChange={(e) => { updateDraft({ endDate: e.target.value }); e.target.blur(); }}
                    className="ls-border ls-bg-input text-xs ls-text"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Ubicacion</Label>
                <Input
                  value={sessionDraft.location}
                  onChange={(e) => updateDraft({ location: e.target.value })}
                  placeholder="Lab. 301"
                  className="ls-border ls-bg-input text-xs ls-text"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Instrucciones</Label>
                <Textarea
                  value={sessionDraft.instructions}
                  onChange={(e) => updateDraft({ instructions: e.target.value })}
                  placeholder="Instrucciones para los estudiantes..."
                  rows={2}
                  className="ls-border ls-bg-input text-xs ls-text resize-none"
                />
              </div>
            </div>
          </ConfigSection>

          {/* Participantes section */}
          <ConfigSection
            title="Participantes"
            actions={
              <div className="flex items-center gap-1">
                <Button size="xs" variant="ghost" onClick={() => setAddParticipantOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
                  <UserPlus className="h-3 w-3" />Agregar
                </Button>
                <Button size="xs" variant="ghost" onClick={selectAllParticipants} className="gap-1 ls-text-muted hover:ls-text">
                  Todos
                </Button>
              </div>
            }
          >
            <ParticipantsSection
              courseMembers={courseMembers}
              selectedDocentes={selectedDocentes}
              selectedInstructores={selectedInstructores}
              selectedEstudiantes={selectedEstudiantes}
              toggleParticipant={toggleParticipant}
              removeFromCourse={removeFromCourse}
              changeParticipantRole={changeParticipantRole}
              courseId={courseId}
            />
          </ConfigSection>

          {/* Modo section */}
          <ConfigSection title="Modo de sesion">
            <div className="space-y-2">
              <button
                onClick={() => updateDraft({ sessionType: "conjunto", centroEnabled: false })}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  sessionDraft.sessionType === "conjunto"
                    ? "border-orange-500/50 bg-orange-500/10"
                    : "ls-border hover:ls-bg-input"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-sky-400" />
                  <span className="text-xs font-medium ls-text2">Conjunto</span>
                </div>
                <p className="text-[10px] ls-text-muted mt-1">
                  Todos los estudiantes comparten la misma agenda
                </p>
              </button>
              <button
                onClick={() => updateDraft({ sessionType: "grupal" })}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  sessionDraft.sessionType === "grupal"
                    ? "border-orange-500/50 bg-orange-500/10"
                    : "ls-border hover:ls-bg-input"
                }`}
              >
                <div className="flex items-center gap-2">
                  <UsersRound className="h-4 w-4 text-amber-400" />
                  <span className="text-xs font-medium ls-text2">Grupal</span>
                </div>
                <p className="text-[10px] ls-text-muted mt-1">
                  Trabajo por grupos con boxes separados
                </p>
              </button>

              {/* Toggle Centro */}
              {sessionDraft.sessionType === "grupal" && (
                <button
                  onClick={() => updateDraft({ centroEnabled: !sessionDraft.centroEnabled })}
                  className={`flex w-full items-center gap-2 rounded-lg border p-2.5 text-left transition ${
                    sessionDraft.centroEnabled
                      ? "border-amber-500/50 bg-amber-500/10"
                      : "ls-border hover:ls-bg-input"
                  }`}
                >
                  <div className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                    sessionDraft.centroEnabled ? "border-amber-500 bg-amber-500" : "ls-border"
                  }`}>
                    {sessionDraft.centroEnabled && <Check className="h-3 w-3 text-white" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <Building2 className="h-3.5 w-3.5 text-amber-400" />
                      <span className="text-xs font-medium ls-text2">Habilitar Centro Clinico</span>
                    </div>
                    <p className="text-[10px] ls-text-muted mt-0.5">
                      Incidentes, reuniones clinicas, chat y feedback de pacientes
                    </p>
                  </div>
                </button>
              )}
            </div>
          </ConfigSection>

          {/* Grupos section (only when grupal) */}
          {sessionDraft.sessionType === "grupal" && (
            <ConfigSection
              title="Grupos"
              actions={
                <div className="flex items-center gap-1">
                  <Input
                    type="number"
                    value={groupCount}
                    onChange={(e) => setGroupCount(Math.max(1, parseInt(e.target.value) || 1))}
                    className="h-6 w-12 ls-border ls-bg-input text-[10px] ls-text text-center"
                    min={1}
                    max={20}
                  />
                  <Button size="xs" variant="ghost" onClick={() => distributeGroups(groupCount)} className="gap-1 ls-text-muted hover:ls-text">
                    <Shuffle className="h-3 w-3" />Distribuir
                  </Button>
                  <Button size="xs" variant="ghost" onClick={addGroup} className="gap-1 ls-text-muted hover:ls-text">
                    <Plus className="h-3 w-3" />Grupo
                  </Button>
                </div>
              }
            >
              <GroupsSection
                groups={groups}
                courseMembers={courseMembers}
                selectedEstudiantes={selectedEstudiantes}
                selectedInstructores={selectedInstructores}
                selectedDocentes={selectedDocentes}
                renameGroup={renameGroup}
                removeGroup={removeGroup}
                assignStudentToGroup={assignStudentToGroup}
                removeStudentFromGroup={removeStudentFromGroup}
                assignInstructorToGroup={assignInstructorToGroup}
              />
            </ConfigSection>
          )}

          {/* Planificación */}
          <ConfigSection title="Planificación">
            <div className="flex items-center justify-between">
              <p className="text-xs ls-text-muted">
                {scheduleBlocks.length > 0
                  ? `${scheduleBlocks.length} bloques configurados`
                  : "Sin bloques configurados"}
              </p>
              <Button
                size="xs"
                onClick={() => setCalendarOpen(true)}
                className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500"
              >
                <CalendarDays className="h-3 w-3" />
                Configurar calendario
              </Button>
            </div>
          </ConfigSection>

          <CalendarModal
            open={calendarOpen}
            onOpenChange={setCalendarOpen}
            blocks={scheduleBlocks}
            procedures={procedures}
            startDate={sessionDraft.startDate}
            endDate={sessionDraft.endDate}
            onAddBlock={addBlock}
            onRemoveBlock={removeBlock}
            onRepeatWeek={repeatWeek}
          />
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="border-t ls-border px-3 py-2 shrink-0 flex items-center justify-between">
        <Button
          size="sm"
          variant="outline"
          onClick={() => navigate({ page: "activities", courseId })}
          className="ls-border ls-text2"
        >
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={saving || !sessionDraft.title.trim()}
          className="gap-1.5 bg-orange-600 text-white hover:bg-orange-500"
        >
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
          {isEditing ? "Guardar Cambios" : "Crear Actividad"}
        </Button>
      </div>

      {/* Add participant dialog */}
      <AddParticipantDialog
        open={addParticipantOpen}
        onOpenChange={setAddParticipantOpen}
        courseId={courseId}
        existingIds={new Set(courseMembers.map((m) => m.id))}
        onAdded={() => loadCourseMembers(courseId)}
      />
    </div>
  );
}

// ─── Config Section ────────────────────────────────────

function ConfigSection({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border ls-border p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted">{title}</h3>
        {actions}
      </div>
      {children}
    </div>
  );
}

// ─── Participants Section ──────────────────────────────

function ParticipantsSection({
  courseMembers,
  selectedDocentes,
  selectedInstructores,
  selectedEstudiantes,
  toggleParticipant,
  removeFromCourse,
  changeParticipantRole,
  courseId,
}: {
  courseMembers: CourseMember[];
  selectedDocentes: string[];
  selectedInstructores: string[];
  selectedEstudiantes: string[];
  toggleParticipant: (id: string, role: "docente" | "instructor" | "estudiante") => void;
  removeFromCourse: (userId: string, courseId: string) => Promise<void>;
  changeParticipantRole: (userId: string, newRole: "docente" | "instructor" | "estudiante", courseId: string) => Promise<void>;
  courseId: string;
}) {
  const [removing, setRemoving] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);

  const docentes = courseMembers.filter((m) => m.role === "docente");
  const instructores = courseMembers.filter((m) => m.role === "instructor");
  const estudiantes = courseMembers.filter((m) => m.role === "estudiante");

  const handleRemove = async (userId: string) => {
    setRemoving(userId);
    try {
      await removeFromCourse(userId, courseId);
      toast.success("Eliminado del curso");
    } catch (e) {
      toast.error(`Error: ${e}`);
    } finally {
      setRemoving(null);
    }
  };

  const handleDrop = async (e: React.DragEvent, targetRole: "docente" | "instructor" | "estudiante") => {
    e.preventDefault();
    e.stopPropagation();
    setDropTarget(null);
    const userId = e.dataTransfer.getData("text/participant-id");
    const fromRole = e.dataTransfer.getData("text/participant-role");
    if (!userId || !fromRole || fromRole === targetRole) return;
    try {
      await changeParticipantRole(userId, targetRole, courseId);
      toast.success(`Movido a ${targetRole}`);
    } catch (err) {
      toast.error(`Error: ${err}`);
    }
  };

  const renderRoleSection = (
    title: string,
    members: CourseMember[],
    selectedIds: string[],
    role: "docente" | "instructor" | "estudiante",
  ) => {
    const isOver = dropTarget === role;
    return (
      <div
        onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setDropTarget(role); }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node)) setDropTarget(null);
        }}
        onDrop={(e) => handleDrop(e, role)}
        className={`rounded-lg border p-2 transition-all ${
          isOver ? "border-orange-400 bg-orange-500/10" : "ls-border"
        }`}
      >
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium ls-text2">{title}</span>
          <Badge variant="outline" className="text-[9px] ls-border ls-text-muted">
            {selectedIds.length}/{members.length}
          </Badge>
        </div>
        {members.length === 0 ? (
          <p className="text-[10px] ls-text-muted py-2 italic text-center">
            Arrastra personas aqui
          </p>
        ) : (
          <div className="space-y-0.5">
            {members.map((m) => {
              const selected = selectedIds.includes(m.id);
              return (
                <div
                  key={m.id}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/participant-id", m.id);
                    e.dataTransfer.setData("text/participant-role", role);
                    e.dataTransfer.effectAllowed = "move";
                  }}
                  className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs transition cursor-grab active:cursor-grabbing active:opacity-50 ${
                    selected ? "bg-orange-500/10 text-orange-300" : "ls-text2 hover:ls-bg-input"
                  }`}
                >
                  <button onClick={() => toggleParticipant(m.id, role)} className="shrink-0">
                    <div className={`flex h-4 w-4 items-center justify-center rounded border ${
                      selected ? "border-orange-500 bg-orange-500" : "ls-border"
                    }`}>
                      {selected && <Check className="h-3 w-3 text-white" />}
                    </div>
                  </button>
                  <span className="truncate flex-1">{m.full_name ?? m.username}</span>
                  <span className="text-[9px] ls-text-muted">{m.username}</span>
                  <button
                    onClick={() => handleRemove(m.id)}
                    disabled={removing === m.id}
                    className="shrink-0 text-red-400/40 hover:text-red-400 transition"
                    title="Eliminar del curso"
                  >
                    {removing === m.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  if (courseMembers.length === 0) {
    return (
      <div className="py-4 text-center">
        <Users className="h-8 w-8 mx-auto ls-text-muted mb-2" />
        <p className="text-xs ls-text-muted">No hay participantes en el curso</p>
        <p className="text-[10px] ls-text-muted mt-1">Usa "Agregar" para buscar e inscribir personas</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {renderRoleSection("Docentes", docentes, selectedDocentes, "docente")}
      {renderRoleSection("Instructores", instructores, selectedInstructores, "instructor")}
      {renderRoleSection("Estudiantes", estudiantes, selectedEstudiantes, "estudiante")}
    </div>
  );
}

// ─── Groups Section ────────────────────────────────────

function GroupsSection({
  groups,
  courseMembers,
  selectedEstudiantes,
  selectedInstructores,
  selectedDocentes,
  renameGroup,
  removeGroup,
  assignStudentToGroup,
  removeStudentFromGroup,
  assignInstructorToGroup,
}: {
  groups: GroupDraft[];
  courseMembers: CourseMember[];
  selectedEstudiantes: string[];
  selectedInstructores: string[];
  selectedDocentes: string[];
  renameGroup: (index: number, name: string) => void;
  removeGroup: (index: number) => void;
  assignStudentToGroup: (studentId: string, groupIndex: number) => void;
  removeStudentFromGroup: (studentId: string, groupIndex: number) => void;
  assignInstructorToGroup: (instructorId: string | null, groupIndex: number) => void;
}) {
  const assignedIds = useMemo(
    () => new Set(groups.flatMap((g) => g.studentIds)),
    [groups],
  );
  const unassigned = selectedEstudiantes.filter((id) => !assignedIds.has(id));
  const getMember = useCallback(
    (id: string) => courseMembers.find((m) => m.id === id),
    [courseMembers],
  );

  const staff = courseMembers.filter(
    (m) => selectedInstructores.includes(m.id) || selectedDocentes.includes(m.id),
  );

  const [unassignedDropHighlight, setUnassignedDropHighlight] = useState(false);

  return (
    <div className="space-y-2">
      {/* Unassigned area */}
      {unassigned.length > 0 && (
        <div
          onDragOver={(e) => { e.preventDefault(); setUnassignedDropHighlight(true); }}
          onDragLeave={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node)) setUnassignedDropHighlight(false);
          }}
          onDrop={(e) => {
            e.preventDefault();
            setUnassignedDropHighlight(false);
            const sid = e.dataTransfer.getData("text/student-id");
            const fromGroup = e.dataTransfer.getData("text/from-group");
            if (sid && fromGroup !== "") {
              removeStudentFromGroup(sid, parseInt(fromGroup));
            }
          }}
          className={`rounded-lg border border-dashed p-2 transition-colors ${
            unassignedDropHighlight ? "border-amber-500/60 bg-amber-500/5" : "ls-border"
          }`}
        >
          <p className="text-[10px] font-medium text-amber-400 mb-1">
            {unassigned.length} sin asignar
          </p>
          <div className="flex flex-wrap gap-1">
            {unassigned.map((id) => {
              const m = getMember(id);
              return (
                <span
                  key={id}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/student-id", id);
                    e.dataTransfer.setData("text/from-group", "");
                  }}
                  className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-300 cursor-grab active:cursor-grabbing"
                >
                  {m?.full_name ?? m?.username ?? id}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Group cards */}
      {groups.length === 0 ? (
        <div className="py-4 text-center text-xs ls-text-muted">
          Usa "Distribuir" para crear grupos o "Grupo" para agregar uno manual.
        </div>
      ) : (
        groups.map((group, gi) => (
          <GroupCard
            key={gi}
            group={group}
            index={gi}
            staff={staff}
            unassigned={unassigned}
            getMember={getMember}
            onRename={(name) => renameGroup(gi, name)}
            onRemove={() => removeGroup(gi)}
            onAssignStudent={(sid) => assignStudentToGroup(sid, gi)}
            onRemoveStudent={(sid) => removeStudentFromGroup(sid, gi)}
            onAssignInstructor={(iid) => assignInstructorToGroup(iid, gi)}
          />
        ))
      )}

      {groups.length > 0 && (
        <div className="text-[10px] ls-text-muted text-center">
          {groups.length} grupos · {assignedIds.size}/{selectedEstudiantes.length} asignados
        </div>
      )}
    </div>
  );
}

// ─── Group Card ────────────────────────────────────────

function GroupCard({
  group,
  index,
  staff,
  unassigned,
  getMember,
  onRename,
  onRemove,
  onAssignStudent,
  onRemoveStudent,
  onAssignInstructor,
}: {
  group: GroupDraft;
  index: number;
  staff: CourseMember[];
  unassigned: string[];
  getMember: (id: string) => CourseMember | undefined;
  onRename: (name: string) => void;
  onRemove: () => void;
  onAssignStudent: (id: string) => void;
  onRemoveStudent: (id: string) => void;
  onAssignInstructor: (id: string | null) => void;
}) {
  const [addOpen, setAddOpen] = useState(false);
  const [dropHighlight, setDropHighlight] = useState(false);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDropHighlight(true); }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setDropHighlight(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDropHighlight(false);
        const sid = e.dataTransfer.getData("text/student-id");
        if (sid) onAssignStudent(sid);
      }}
      className={`rounded-lg border p-2.5 space-y-2 transition-colors ${
        dropHighlight ? "border-sky-500/50 bg-sky-500/5" : "ls-border"
      }`}
    >
      <div className="flex items-center gap-2">
        <Input
          value={group.name}
          onChange={(e) => onRename(e.target.value)}
          className="h-6 flex-1 ls-border ls-bg-input text-xs ls-text font-medium"
        />
        <select
          value={group.instructorId ?? ""}
          onChange={(e) => onAssignInstructor(e.target.value || null)}
          className="h-6 rounded border px-1 text-[10px] ls-border ls-bg-input ls-text" style={{ colorScheme: "dark" }}
        >
          <option value="">Sin supervisor</option>
          {staff.map((s) => (
            <option key={s.id} value={s.id}>
              {s.full_name ?? s.username} ({s.role})
            </option>
          ))}
        </select>
        <Button size="icon-xs" variant="ghost" onClick={onRemove} className="text-red-400/60 hover:text-red-400 shrink-0">
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      {/* Students in group */}
      <div className="flex flex-wrap gap-1 min-h-[24px]">
        {group.studentIds.map((sid) => {
          const m = getMember(sid);
          return (
            <span
              key={sid}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData("text/student-id", sid);
                e.dataTransfer.setData("text/from-group", String(index));
              }}
              className="flex items-center gap-1 rounded bg-sky-500/10 px-1.5 py-0.5 text-[10px] text-sky-300 cursor-grab active:cursor-grabbing"
            >
              {m?.full_name ?? m?.username ?? sid}
              <button onClick={() => onRemoveStudent(sid)} className="hover:text-red-400">
                <X className="h-2.5 w-2.5" />
              </button>
            </span>
          );
        })}
        {group.studentIds.length === 0 && (
          <span className="text-[10px] ls-text-muted italic">Arrastra estudiantes aqui</span>
        )}
        {unassigned.length > 0 && (
          <button
            onClick={() => {
              if (unassigned.length === 1) {
                onAssignStudent(unassigned[0]);
              } else {
                setAddOpen(!addOpen);
              }
            }}
            className="flex items-center gap-0.5 rounded border border-dashed ls-border px-1.5 py-0.5 text-[10px] ls-text-muted hover:ls-text"
          >
            <UserPlus className="h-2.5 w-2.5" />
          </button>
        )}
      </div>

      {/* Student picker */}
      {addOpen && unassigned.length > 0 && (
        <div className="rounded border ls-border p-1 max-h-24 overflow-y-auto space-y-0.5">
          {unassigned.map((sid) => {
            const m = getMember(sid);
            return (
              <button
                key={sid}
                onClick={() => { onAssignStudent(sid); setAddOpen(false); }}
                className="flex w-full items-center gap-1 rounded px-1.5 py-1 text-[10px] ls-text2 hover:ls-bg-input"
              >
                <UserPlus className="h-2.5 w-2.5 ls-text-muted" />
                {m?.full_name ?? m?.username ?? sid}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Dialog: Add Participant ───────────────────────────

function AddParticipantDialog({
  open,
  onOpenChange,
  courseId,
  existingIds,
  onAdded,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  courseId: string;
  existingIds: Set<string>;
  onAdded: () => void;
}) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Array<{ id: string; username: string; full_name: string | null; role: string }>>([]);
  const [searching, setSearching] = useState(false);
  const [enrolling, setEnrolling] = useState<string | null>(null);
  const [enrollRole, setEnrollRole] = useState<string>("estudiante");

  const handleSearch = async () => {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const result = await invoke<{ items: Array<{ id: string; username: string; full_name: string | null; role: string }> }>(
        "api_search_users",
        { search: search.trim() },
      );
      setResults((result?.items ?? []).filter((u) => !existingIds.has(u.id)));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleEnroll = async (userId: string) => {
    setEnrolling(userId);
    try {
      await invoke("api_enroll_student", { courseId, userId, role: enrollRole });
      toast.success("Participante agregado al curso");
      setResults((prev) => prev.filter((r) => r.id !== userId));
      onAdded();
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setEnrolling(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-w-sm">
        <DialogHeader>
          <DialogTitle className="ls-text flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-orange-400" />
            Agregar Participante
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          {/* Role */}
          <div className="flex items-center gap-1">
            <Label className="text-xs ls-text2 shrink-0">Inscribir como:</Label>
            <select
              value={enrollRole}
              onChange={(e) => setEnrollRole(e.target.value)}
              className="h-7 rounded border px-2 text-xs ls-border ls-bg-input ls-text" style={{ colorScheme: "dark" }}
            >
              <option value="estudiante">Estudiante</option>
              <option value="instructor">Instructor</option>
              <option value="docente">Docente</option>
            </select>
          </div>

          {/* Search */}
          <div className="flex gap-1">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Buscar por nombre, RUN, email..."
              className="ls-border ls-bg-input text-xs ls-text"
            />
            <Button size="xs" onClick={handleSearch} disabled={searching} className="shrink-0 px-2">
              {searching ? <Loader2 className="h-3 w-3 animate-spin" /> : <Users className="h-3 w-3" />}
            </Button>
          </div>

          {/* Results */}
          <ScrollArea className="max-h-[200px]">
            {results.length === 0 ? (
              <p className="text-xs ls-text-muted text-center py-4">
                {search ? "Sin resultados" : "Busca una persona para agregarla"}
              </p>
            ) : (
              <div className="space-y-1">
                {results.map((r) => (
                  <div key={r.id} className="flex items-center justify-between rounded-md px-2 py-1.5 ls-bg-input">
                    <div>
                      <div className="text-xs ls-text2">{r.full_name ?? r.username}</div>
                      <div className="text-[10px] ls-text-muted">{r.username} · {r.role}</div>
                    </div>
                    <Button
                      size="xs"
                      onClick={() => handleEnroll(r.id)}
                      disabled={enrolling === r.id}
                      className="gap-1 bg-orange-600 text-white hover:bg-orange-500"
                    >
                      {enrolling === r.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <UserPlus className="h-3 w-3" />}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Dialog: New Course ────────────────────────────────

function NewCourseDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  onCreated: () => void;
}) {
  const createCourse = useCoursesStore((s) => s.createCourse);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [period, setPeriod] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast.error("El nombre es obligatorio");
      return;
    }
    setSaving(true);
    try {
      await createCourse({
        name: name.trim(),
        code: code.trim() || undefined,
        period: period.trim() || undefined,
      });
      toast.success("Curso creado");
      setName("");
      setCode("");
      setPeriod("");
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
        <DialogHeader>
          <DialogTitle className="ls-text">Nuevo Curso</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Nombre *</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Audiologia Clinica I"
              className="ls-border ls-bg-input text-xs ls-text"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Codigo</Label>
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="AUD-301"
              className="ls-border ls-bg-input text-xs ls-text"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Periodo</Label>
            <Input
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              placeholder="2026-S1"
              className="ls-border ls-bg-input text-xs ls-text"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="ls-border ls-text2">
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={saving} className="gap-1 bg-orange-600 text-white hover:bg-orange-500">
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            Crear
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─── Modal Calendario ────────────────────────────────

function CalendarModal({
  open,
  onOpenChange,
  blocks,
  procedures,
  startDate,
  endDate,
  onAddBlock,
  onRemoveBlock,
  onRepeatWeek,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  blocks: ScheduleBlock[];
  procedures: Procedure[];
  startDate: string;
  endDate: string;
  onAddBlock: (block: ScheduleBlock) => void;
  onRemoveBlock: (index: number) => void;
  onRepeatWeek: () => void;
}) {
  const [selectedDate, setSelectedDate] = useState<string | null>(startDate || null);
  const [newTime, setNewTime] = useState("08:30");
  const [newDuration, setNewDuration] = useState(30);
  const [newBlockName, setNewBlockName] = useState("");

  // Si no hay fechas, usar hoy como único día
  const calendarDays = useMemo(() => {
    const s = startDate || new Date().toISOString().split("T")[0];
    const e = endDate || s;
    const days: string[] = [];
    const current = new Date(s + "T00:00:00");
    const end = new Date(e + "T00:00:00");
    while (current <= end) {
      days.push(current.toISOString().split("T")[0]);
      current.setDate(current.getDate() + 1);
    }
    return days;
  }, [startDate, endDate]);

  // Auto-seleccionar primer día
  useEffect(() => {
    if (!selectedDate && calendarDays.length > 0) setSelectedDate(calendarDays[0]);
  }, [calendarDays]);

  const dayBlocks = useMemo(() => {
    if (!selectedDate) return [];
    return blocks
      .map((b, i) => ({ ...b, originalIndex: i }))
      .filter((b) => b.date === selectedDate)
      .sort((a, b) => a.time.localeCompare(b.time));
  }, [blocks, selectedDate]);

  const blockCountByDate = useMemo(() => {
    const c: Record<string, number> = {};
    for (const b of blocks) c[b.date] = (c[b.date] ?? 0) + 1;
    return c;
  }, [blocks]);

  const usedNames = useMemo(() => {
    const s = new Set<string>();
    for (const b of blocks) if (b.procedureName) s.add(b.procedureName);
    return [...s];
  }, [blocks]);

  const handleAdd = () => {
    if (!selectedDate || !newTime || !newBlockName.trim()) return;
    onAddBlock({
      date: selectedDate,
      time: newTime,
      durationMinutes: newDuration,
      procedureId: null,
      procedureName: newBlockName.trim(),
    });
    const [h, m] = newTime.split(":").map(Number);
    const next = (h * 60 + m + newDuration) % 1440;
    setNewTime(`${String(Math.floor(next / 60)).padStart(2, "0")}:${String(next % 60).padStart(2, "0")}`);
  };

  const HOUR_HEIGHT = 80; // px por hora — más grande para que los bloques de 30min sean legibles
  const HOURS = Array.from({ length: 13 }, (_, i) => i + 7); // 07:00 a 19:00
  const DAY_NAMES = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

  const isSingleDay = calendarDays.length === 1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border sm:max-w-3xl max-h-[80vh] p-0 flex flex-col" showCloseButton={false}>
        {/* Header */}
        <div className="flex items-center gap-2 border-b ls-border px-4 py-3 shrink-0">
          <CalendarDays className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-medium ls-text">Configurar Calendario</span>
          <div className="ml-auto flex items-center gap-2">
            {blocks.length > 0 && (
              <Button size="xs" variant="ghost" onClick={onRepeatWeek} className="gap-1 ls-text-muted hover:ls-text">
                <Repeat className="h-3 w-3" />Repetir semana
              </Button>
            )}
            <Badge variant="outline" className="text-[10px] ls-border ls-text-muted">
              {blocks.length} bloques
            </Badge>
          </div>
        </div>

        {/* Grilla semana/día */}
        <div className="flex-1 overflow-auto">
          <div className="flex min-w-0">
            {/* Columna de horas */}
            <div className="w-11 shrink-0 sticky left-0 ls-bg" style={{ zIndex: 2 }}>
              <div className="h-8" /> {/* espacio para header de días */}
              {HOURS.map((hour) => (
                <div key={hour} className="flex items-start justify-end pr-1.5 -mt-1.5" style={{ height: HOUR_HEIGHT }}>
                  <span className="text-[10px] ls-text-muted">{String(hour).padStart(2, "0")}:00</span>
                </div>
              ))}
            </div>

            {/* Columnas de días */}
            {calendarDays.map((date) => {
              const d = new Date(date + "T00:00:00");
              const isSelected = selectedDate === date;
              const dayBlocksForCol = blocks
                .map((b, i) => ({ ...b, originalIndex: i }))
                .filter((b) => b.date === date)
                .sort((a, b) => a.time.localeCompare(b.time));

              return (
                <div
                  key={date}
                  className={`flex-1 min-w-[80px] border-l ls-border/50 ${isSelected ? "bg-cyan-500/5" : ""}`}
                  onClick={() => setSelectedDate(date)}
                >
                  {/* Header del día */}
                  <div className={`sticky top-0 h-8 flex flex-col items-center justify-center border-b ls-border ls-bg cursor-pointer ${
                    isSelected ? "bg-cyan-500/10" : ""
                  }`} style={{ zIndex: 1 }}>
                    <span className="text-[9px] font-bold uppercase ls-text-muted">{DAY_NAMES[d.getDay()]}</span>
                    <span className={`text-[11px] font-medium leading-none ${isSelected ? "text-cyan-400" : "ls-text2"}`}>{d.getDate()}</span>
                  </div>

                  {/* Celdas de hora */}
                  <div className="relative" style={{ height: HOURS.length * HOUR_HEIGHT }}>
                    {HOURS.map((hour) => (
                      <div key={hour} className="absolute left-0 right-0 border-t ls-border/30" style={{ top: (hour - 7) * HOUR_HEIGHT, height: HOUR_HEIGHT }} />
                    ))}

                    {/* Bloques */}
                    {dayBlocksForCol.map((block) => {
                      const [h, m] = block.time.split(":").map(Number);
                      const top = ((h - 7) * 60 + m) / 60 * HOUR_HEIGHT;
                      const height = Math.max((block.durationMinutes / 60) * HOUR_HEIGHT, 24);

                      return (
                        <div
                          key={block.originalIndex}
                          className="absolute left-0.5 right-0.5 rounded-md bg-cyan-500/20 border border-cyan-500/30 px-1.5 py-1 group cursor-default overflow-hidden"
                          style={{ top, height }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="flex items-start gap-0.5">
                            <span className="text-[10px] font-semibold text-cyan-300 truncate flex-1 leading-tight">
                              {block.procedureName}
                            </span>
                            <button
                              onClick={() => onRemoveBlock(block.originalIndex)}
                              className="text-red-400/0 group-hover:text-red-400 shrink-0"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                          {height > 30 && (
                            <span className="text-[9px] text-cyan-400/50 leading-none">{block.time} — {block.durationMinutes} min</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer: agregar bloque + guardar */}
        <div className="border-t ls-border px-4 py-2.5 shrink-0 space-y-2">
          <div className="flex items-end gap-2">
            {!isSingleDay && (
              <div className="space-y-0.5">
                <Label className="text-[9px] ls-text-muted">Día</Label>
                <select
                  value={selectedDate ?? ""}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="h-7 rounded-md border px-2 text-xs ls-border ls-bg-input ls-text"
                  style={{ colorScheme: "dark" }}
                >
                  {calendarDays.map((date) => {
                    const d = new Date(date + "T00:00:00");
                    return <option key={date} value={date}>{DAY_NAMES[d.getDay()]} {d.getDate()}</option>;
                  })}
                </select>
              </div>
            )}
            <div className="space-y-0.5">
              <Label className="text-[9px] ls-text-muted">Hora</Label>
              <Input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)}
                className="h-7 w-[90px] ls-border ls-bg-input text-xs ls-text" />
            </div>
            <div className="space-y-0.5 flex-1">
              <Label className="text-[9px] ls-text-muted">Procedimiento</Label>
              <Input
                value={newBlockName}
                onChange={(e) => setNewBlockName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                placeholder="Audiometría tonal, Impedanciometría..."
                className="h-7 ls-border ls-bg-input text-xs ls-text"
                list="cal-proc-names"
              />
              <datalist id="cal-proc-names">
                {usedNames.map((n) => <option key={n} value={n} />)}
              </datalist>
            </div>
            <div className="space-y-0.5">
              <Label className="text-[9px] ls-text-muted">Min</Label>
              <Input type="number" value={newDuration} onChange={(e) => setNewDuration(parseInt(e.target.value) || 30)}
                className="h-7 w-[55px] ls-border ls-bg-input text-xs ls-text" min={5} step={5} />
            </div>
            <Button size="sm" onClick={handleAdd} disabled={!newBlockName.trim()} className="gap-1 bg-cyan-600 text-white hover:bg-cyan-500 shrink-0">
              <Plus className="h-3.5 w-3.5" />Agregar
            </Button>
          </div>
          <div className="flex items-center justify-end">
            <Button size="sm" onClick={() => onOpenChange(false)} className="gap-1 bg-orange-600 text-white hover:bg-orange-500">
              <Check className="h-3.5 w-3.5" />Listo
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
