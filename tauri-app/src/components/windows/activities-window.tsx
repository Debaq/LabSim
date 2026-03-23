import { useState, useEffect, useMemo } from "react";
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
  CalendarCheck2,
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
  ArrowLeft,
  Building2,
  Shuffle,
  Trash2,
  UserPlus,
  X,
  RotateCcw,
  ExternalLink,
} from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useActivitiesStore, type CourseMember, type GroupDraft } from "@/stores/activities-store";
import { useCoursesStore } from "@/stores/courses-store";
import { useUIStore } from "@/stores/ui-store";
import { WINDOW_SIZES } from "@/components/layout/desktop-area";
import { toast } from "sonner";

// ─── Steps ──────────────────────────────────────────

const STEPS = [
  { num: 1 as const, label: "Curso", icon: GraduationCap },
  { num: 2 as const, label: "Participantes", icon: Users },
  { num: 3 as const, label: "Sesión", icon: ClipboardList },
  { num: 4 as const, label: "Grupos", icon: UsersRound },
  { num: 5 as const, label: "Planificación", icon: CalendarDays },
];

// ─── Main ───────────────────────────────────────────

export function ActivitiesWindow() {
  const currentStep = useActivitiesStore((s) => s.currentStep);
  const setStep = useActivitiesStore((s) => s.setStep);
  const selectedCourseId = useActivitiesStore((s) => s.selectedCourseId);
  const sessionId = useActivitiesStore((s) => s.sessionId);
  const sessionType = useActivitiesStore((s) => s.sessionDraft.sessionType);
  const groupsSaved = useActivitiesStore((s) => s.groupsSaved);
  const courses = useActivitiesStore((s) => s.courses);
  const reset = useActivitiesStore((s) => s.reset);

  const canGoTo = (step: number) => {
    if (step === 1) return true;
    if (step === 2) return !!selectedCourseId;
    if (step === 3) return !!selectedCourseId;
    if (step === 4) return !!sessionId && sessionType === "grupal";
    if (step === 5) return !!sessionId && (sessionType === "conjunto" || groupsSaved);
    return false;
  };

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <CalendarCheck2 className="h-4 w-4 text-orange-400" />
        <span className="text-xs font-medium ls-text2">Actividades</span>
        <div className="ml-auto">
          <Button size="xs" variant="ghost" onClick={reset} className="gap-1 ls-text-muted hover:ls-text">
            <RotateCcw className="h-3 w-3" />Nueva
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-[150px] shrink-0 border-r ls-border p-2 space-y-1">
          {STEPS.map((step) => {
            if (step.num === 4 && sessionType !== "grupal") return null;
            const isActive = currentStep === step.num;
            const isCompleted =
              (step.num === 1 && !!selectedCourseId) ||
              (step.num === 2 && currentStep > 2) ||
              (step.num === 3 && !!sessionId) ||
              (step.num === 4 && groupsSaved) ||
              false;
            const canClick = canGoTo(step.num);
            const Icon = step.icon;

            return (
              <button
                key={step.num}
                onClick={() => canClick && setStep(step.num as 1 | 2 | 3 | 4 | 5)}
                disabled={!canClick}
                className={`flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-xs transition ${
                  isActive
                    ? "bg-orange-500/10 text-orange-400"
                    : canClick
                      ? "ls-text2 hover:ls-bg-input"
                      : "ls-text-muted/50 cursor-not-allowed"
                }`}
              >
                {isCompleted && !isActive ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Icon className="h-3.5 w-3.5" />
                )}
                <span className="font-medium">{step.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {currentStep === 1 && <StepCurso />}
          {currentStep === 2 && <StepParticipantes />}
          {currentStep === 3 && <StepSesion />}
          {currentStep === 4 && <StepGrupos />}
          {currentStep === 5 && <StepPlanificacion />}
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-3 border-t ls-border px-3 py-1.5 text-[10px] ls-text-muted">
        {selectedCourse && (
          <span>
            <GraduationCap className="inline h-3 w-3 mr-0.5" />
            {selectedCourse.name}
          </span>
        )}
        {sessionId && (
          <span>
            <ClipboardList className="inline h-3 w-3 mr-0.5" />
            {sessionType === "grupal" ? "Grupal" : "Conjunto"}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Step 1: Curso ──────────────────────────────────

function StepCurso() {
  const { courses, coursesLoading, selectedCourseId, fetchCourses, selectCourse, error } =
    useActivitiesStore();
  const createCourse = useCoursesStore((s) => s.createCourse);
  const [newCourseOpen, setNewCourseOpen] = useState(false);

  useEffect(() => { fetchCourses(); }, [fetchCourses]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <span className="text-xs font-medium ls-text2">Selecciona un curso</span>
        <div className="ml-auto flex items-center gap-1">
          <Button size="xs" variant="ghost" onClick={() => setNewCourseOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
            <Plus className="h-3 w-3" />Nuevo
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
        ) : courses.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs ls-text-muted">
            No tienes cursos. Crea uno para empezar.
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {courses.map((c) => (
              <button
                key={c.id}
                onClick={() => selectCourse(c.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition ${
                  selectedCourseId === c.id ? "bg-orange-500/10 ring-1 ring-orange-500/30" : "hover:ls-bg-input"
                }`}
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/10">
                  <GraduationCap className="h-4.5 w-4.5 text-sky-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium ls-text2 truncate">{c.name}</span>
                    {c.code && <Badge variant="outline" className="text-[9px] ls-border ls-text-muted shrink-0">{c.code}</Badge>}
                  </div>
                  <div className="text-[10px] ls-text-muted">
                    <Users className="inline h-3 w-3 mr-0.5" />{c.student_count ?? 0} estudiantes
                    {c.period && <span> · {c.period}</span>}
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 ls-text-muted shrink-0" />
              </button>
            ))}
          </div>
        )}
      </ScrollArea>

      {error && <div className="border-t ls-border px-3 py-1.5 text-[10px] text-amber-400">{error}</div>}

      <NewCourseDialog open={newCourseOpen} onOpenChange={setNewCourseOpen} onCreate={async (data) => {
        await createCourse(data);
        await fetchCourses();
      }} />
    </div>
  );
}

// ─── Step 2: Participantes ──────────────────────────

function StepParticipantes() {
  const {
    courseMembers, selectedCourseId, selectedDocentes, selectedInstructores, selectedEstudiantes,
    toggleParticipant, selectAllParticipants, selectCourse, setStep,
    removeFromCourse, changeParticipantRole,
  } = useActivitiesStore();

  const [addOpen, setAddOpen] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [moving, setMoving] = useState(false);

  const docentes = courseMembers.filter((m) => m.role === "docente");
  const instructores = courseMembers.filter((m) => m.role === "instructor");
  const estudiantes = courseMembers.filter((m) => m.role === "estudiante");

  const handleRemove = async (userId: string) => {
    setRemoving(userId);
    try {
      await removeFromCourse(userId);
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
    setMoving(true);
    try {
      await changeParticipantRole(userId, targetRole);
      toast.success(`Movido a ${targetRole}`);
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setMoving(false);
    }
  };

  const renderSection = (
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
          // Solo limpiar si sale del contenedor, no de un hijo
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
            Arrastra personas aquí
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
                  <button
                    onClick={() => toggleParticipant(m.id, role)}
                    className="shrink-0"
                  >
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

  const totalSelected = selectedDocentes.length + selectedInstructores.length + selectedEstudiantes.length;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <Button size="xs" variant="ghost" onClick={() => setStep(1)} className="gap-1 ls-text-muted hover:ls-text">
          <ArrowLeft className="h-3 w-3" />Curso
        </Button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <span className="text-xs font-medium ls-text2">Participantes</span>
        <div className="ml-auto flex items-center gap-1">
          <Button size="xs" variant="ghost" onClick={() => setAddOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
            <UserPlus className="h-3 w-3" />Agregar
          </Button>
          <Button size="xs" variant="ghost" onClick={selectAllParticipants} className="gap-1 ls-text-muted hover:ls-text">
            Todos
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-3">
          {courseMembers.length === 0 ? (
            <div className="py-6 text-center">
              <Users className="h-8 w-8 mx-auto ls-text-muted mb-2" />
              <p className="text-xs ls-text-muted">No hay participantes en el curso</p>
              <p className="text-[10px] ls-text-muted mt-1">Usa "Agregar" para buscar e inscribir personas</p>
            </div>
          ) : (
            <>
              {renderSection("Docentes", docentes, selectedDocentes, "docente")}
              {renderSection("Instructores", instructores, selectedInstructores, "instructor")}
              {renderSection("Estudiantes", estudiantes, selectedEstudiantes, "estudiante")}
            </>
          )}
        </div>
      </ScrollArea>

      <div className="border-t ls-border px-3 py-2 shrink-0 flex items-center justify-between">
        <span className="text-[10px] ls-text-muted">{totalSelected} participantes</span>
        <Button
          size="sm"
          onClick={() => setStep(3)}
          className="gap-1.5 bg-orange-600 text-white hover:bg-orange-500"
        >
          Continuar
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>

      {selectedCourseId && (
        <AddParticipantDialog
          open={addOpen}
          onOpenChange={setAddOpen}
          courseId={selectedCourseId}
          existingIds={new Set(courseMembers.map((m) => m.id))}
          onAdded={() => {
            if (selectedCourseId) selectCourse(selectedCourseId);
          }}
        />
      )}
    </div>
  );
}

// ─── Diálogo: Agregar Participante ──────────────────

function AddParticipantDialog({
  open, onOpenChange, courseId, existingIds, onAdded,
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
        "api_search_users", { search: search.trim() },
      );
      // Filtrar los que ya están en el curso
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
          {/* Rol */}
          <div className="flex items-center gap-1">
            <Label className="text-xs ls-text2 shrink-0">Inscribir como:</Label>
            <select
              value={enrollRole}
              onChange={(e) => setEnrollRole(e.target.value)}
              className="h-7 rounded border px-2 text-xs ls-border ls-bg-input ls-text"
            >
              <option value="estudiante">Estudiante</option>
              <option value="instructor">Instructor</option>
              <option value="docente">Docente</option>
            </select>
          </div>

          {/* Búsqueda */}
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

          {/* Resultados */}
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

// ─── Step 3: Sesión ─────────────────────────────────

function StepSesion() {
  const { sessionDraft, updateDraft, createSession, saving, setStep } = useActivitiesStore();

  const handleCreate = async () => {
    try {
      await createSession();
      toast.success("Sesión creada");
    } catch (e) {
      toast.error(`Error: ${e}`);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2 shrink-0">
        <Button size="xs" variant="ghost" onClick={() => setStep(2)} className="gap-1 ls-text-muted hover:ls-text">
          <ArrowLeft className="h-3 w-3" />Participantes
        </Button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <span className="text-xs font-medium ls-text2">Definir Sesión</span>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-4">
          {/* Info básica */}
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Título *</Label>
              <Input
                value={sessionDraft.title}
                onChange={(e) => updateDraft({ title: e.target.value })}
                placeholder="Audiometría tonal — Semana 3"
                className="ls-border ls-bg-input text-xs ls-text"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs ls-text2">Descripción</Label>
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
                <Input type="date" value={sessionDraft.startDate} onChange={(e) => { updateDraft({ startDate: e.target.value }); e.target.blur(); }} className="ls-border ls-bg-input text-xs ls-text" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Fecha fin</Label>
                <Input type="date" value={sessionDraft.endDate} onChange={(e) => { updateDraft({ endDate: e.target.value }); e.target.blur(); }} className="ls-border ls-bg-input text-xs ls-text" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Hora</Label>
                <Input type="time" value={sessionDraft.scheduledTime} onChange={(e) => updateDraft({ scheduledTime: e.target.value })} className="ls-border ls-bg-input text-xs ls-text" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Duración (min)</Label>
                <Input type="number" value={sessionDraft.durationMinutes} onChange={(e) => updateDraft({ durationMinutes: parseInt(e.target.value) || 90 })} className="ls-border ls-bg-input text-xs ls-text" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs ls-text2">Ubicación</Label>
                <Input value={sessionDraft.location} onChange={(e) => updateDraft({ location: e.target.value })} placeholder="Lab. 301" className="ls-border ls-bg-input text-xs ls-text" />
              </div>
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

          {/* Tipo de sesión */}
          <div>
            <Label className="text-xs ls-text2 mb-2 block">Tipo de sesión</Label>
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
            </div>

            {/* Toggle Centro */}
            {sessionDraft.sessionType === "grupal" && (
              <button
                onClick={() => updateDraft({ centroEnabled: !sessionDraft.centroEnabled })}
                className={`mt-2 flex w-full items-center gap-2 rounded-lg border p-2.5 text-left transition ${
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
                    <span className="text-xs font-medium ls-text2">Habilitar Centro Clínico</span>
                  </div>
                  <p className="text-[10px] ls-text-muted mt-0.5">
                    Incidentes, reuniones clínicas, chat y feedback de pacientes
                  </p>
                </div>
              </button>
            )}
          </div>
        </div>
      </ScrollArea>

      <div className="border-t ls-border px-3 py-2 shrink-0 flex justify-end">
        <Button
          size="sm"
          onClick={handleCreate}
          disabled={saving || !sessionDraft.title.trim()}
          className="gap-1.5 bg-orange-600 text-white hover:bg-orange-500"
        >
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ClipboardList className="h-3.5 w-3.5" />}
          Crear Sesión
        </Button>
      </div>
    </div>
  );
}

// ─── Step 4: Grupos ─────────────────────────────────

function StepGrupos() {
  const {
    groups, selectedEstudiantes, selectedInstructores, selectedDocentes,
    courseMembers, addGroup, removeGroup, renameGroup,
    assignStudentToGroup, removeStudentFromGroup, assignInstructorToGroup,
    distributeGroups, saveGroups, saving, setStep,
  } = useActivitiesStore();

  const [groupCount, setGroupCount] = useState(3);

  // Estudiantes asignados y sin asignar
  const assignedIds = useMemo(
    () => new Set(groups.flatMap((g) => g.studentIds)),
    [groups],
  );
  const unassigned = selectedEstudiantes.filter((id) => !assignedIds.has(id));
  const getMember = (id: string) => courseMembers.find((m) => m.id === id);

  // Staff disponible para asignar a grupos
  const staff = courseMembers.filter(
    (m) => selectedInstructores.includes(m.id) || selectedDocentes.includes(m.id),
  );

  const handleSave = async () => {
    try {
      await saveGroups();
      toast.success("Grupos guardados");
    } catch (e) {
      toast.error(`Error: ${e}`);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <Button size="xs" variant="ghost" onClick={() => setStep(3)} className="gap-1 ls-text-muted hover:ls-text">
          <ArrowLeft className="h-3 w-3" />Sesión
        </Button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <span className="text-xs font-medium ls-text2">Crear Grupos</span>
        <div className="ml-auto flex items-center gap-1">
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
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-3">
          {/* Sin asignar — drop zone para devolver estudiantes */}
          {unassigned.length > 0 && (
            <div
              className="rounded-lg border border-dashed ls-border p-2 transition-colors"
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-amber-500/60", "bg-amber-500/5"); }}
              onDragLeave={(e) => { e.currentTarget.classList.remove("border-amber-500/60", "bg-amber-500/5"); }}
              onDrop={(e) => {
                e.preventDefault();
                e.currentTarget.classList.remove("border-amber-500/60", "bg-amber-500/5");
                const sid = e.dataTransfer.getData("text/student-id");
                const fromGroup = e.dataTransfer.getData("text/from-group");
                if (sid && fromGroup !== "") {
                  removeStudentFromGroup(sid, parseInt(fromGroup));
                }
              }}
            >
              <p className="text-[10px] font-medium text-amber-400 mb-1">
                {unassigned.length} sin asignar — arrastra aquí para quitar de un grupo
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

          {/* Grupos */}
          {groups.length === 0 ? (
            <div className="py-6 text-center text-xs ls-text-muted">
              Usa "Distribuir" para crear grupos automáticamente o "Grupo" para agregar uno manual.
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
        </div>
      </ScrollArea>

      <div className="border-t ls-border px-3 py-2 shrink-0 flex items-center justify-between">
        <span className="text-[10px] ls-text-muted">
          {groups.length} grupos · {assignedIds.size}/{selectedEstudiantes.length} asignados
        </span>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={saving || groups.length === 0 || unassigned.length > 0}
          className="gap-1.5 bg-orange-600 text-white hover:bg-orange-500"
        >
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UsersRound className="h-3.5 w-3.5" />}
          Guardar Grupos
        </Button>
      </div>
    </div>
  );
}

function GroupCard({
  group, index, staff, unassigned, getMember,
  onRename, onRemove, onAssignStudent, onRemoveStudent, onAssignInstructor,
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

  return (
    <div
      className="rounded-lg border ls-border p-2.5 space-y-2 transition-colors"
      onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-sky-500/50", "bg-sky-500/5"); }}
      onDragLeave={(e) => { e.currentTarget.classList.remove("border-sky-500/50", "bg-sky-500/5"); }}
      onDrop={(e) => {
        e.preventDefault();
        e.currentTarget.classList.remove("border-sky-500/50", "bg-sky-500/5");
        const sid = e.dataTransfer.getData("text/student-id");
        if (sid) onAssignStudent(sid);
      }}
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
          className="h-6 rounded border px-1 text-[10px] ls-border ls-bg-input ls-text"
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

      {/* Estudiantes en el grupo — draggable */}
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
          <span className="text-[10px] ls-text-muted italic">Arrastra estudiantes aquí</span>
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

      {/* Picker de estudiantes sin asignar */}
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

// ─── Step 5: Planificación ──────────────────────────

function StepPlanificacion() {
  const {
    courses, selectedCourseId, selectedDocentes, selectedInstructores, selectedEstudiantes,
    courseMembers, sessionDraft, sessionId, groups, groupsSaved, reset,
  } = useActivitiesStore();
  const openWindow = useUIStore((s) => s.openWindow);

  const course = courses.find((c) => c.id === selectedCourseId);
  const getMember = (id: string) => courseMembers.find((m) => m.id === id);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <span className="text-xs font-medium ls-text2">Resumen</span>
        <Badge variant="outline" className="text-[9px] text-emerald-400 bg-emerald-500/10">
          Sesión creada
        </Badge>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-3">
          {/* Curso */}
          <SummarySection title="Curso">
            <p className="text-xs ls-text2">{course?.name} {course?.code ? `(${course.code})` : ""}</p>
          </SummarySection>

          {/* Participantes */}
          <SummarySection title="Participantes">
            <div className="flex gap-3 text-[10px] ls-text-muted">
              <span>{selectedDocentes.length} docentes</span>
              <span>{selectedInstructores.length} instructores</span>
              <span>{selectedEstudiantes.length} estudiantes</span>
            </div>
          </SummarySection>

          {/* Sesión */}
          <SummarySection title="Sesión">
            <p className="text-xs ls-text2 font-medium">{sessionDraft.title}</p>
            {sessionDraft.description && <p className="text-[10px] ls-text-muted">{sessionDraft.description}</p>}
            <div className="flex flex-wrap gap-2 mt-1 text-[10px] ls-text-muted">
              {sessionDraft.startDate && <span>Inicio: {sessionDraft.startDate}</span>}
              {sessionDraft.endDate && <span>Fin: {sessionDraft.endDate}</span>}
              {sessionDraft.location && <span>Lugar: {sessionDraft.location}</span>}
            </div>
            <div className="flex gap-2 mt-1">
              <Badge variant="outline" className={`text-[9px] ${
                sessionDraft.sessionType === "grupal" ? "text-amber-400 bg-amber-500/10" : "text-sky-400 bg-sky-500/10"
              }`}>
                {sessionDraft.sessionType === "grupal" ? "Grupal" : "Conjunto"}
              </Badge>
              {sessionDraft.centroEnabled && (
                <Badge variant="outline" className="text-[9px] text-amber-400 bg-amber-500/10">
                  Centro Clínico
                </Badge>
              )}
            </div>
          </SummarySection>

          {/* Grupos */}
          {sessionDraft.sessionType === "grupal" && groups.length > 0 && (
            <SummarySection title={`${groups.length} Grupos`}>
              <div className="space-y-1">
                {groups.map((g, i) => {
                  const instructor = g.instructorId ? getMember(g.instructorId) : null;
                  return (
                    <div key={i} className="flex items-center gap-2 text-[10px]">
                      <span className="ls-text2 font-medium">{g.name}</span>
                      <span className="ls-text-muted">{g.studentIds.length} est.</span>
                      {instructor && <span className="ls-text-muted">· {instructor.full_name ?? instructor.username}</span>}
                    </div>
                  );
                })}
              </div>
            </SummarySection>
          )}
        </div>
      </ScrollArea>

      <div className="border-t ls-border px-3 py-2 shrink-0 flex items-center justify-between">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            openWindow("agenda", "Agenda", "agenda", WINDOW_SIZES.agenda);
          }}
          className="gap-1.5 ls-border ls-text2"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Abrir Agenda
        </Button>
        <Button
          size="sm"
          onClick={reset}
          className="gap-1.5 bg-emerald-600 text-white hover:bg-emerald-500"
        >
          <Check className="h-3.5 w-3.5" />
          Finalizar
        </Button>
      </div>
    </div>
  );
}

function SummarySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border ls-border ls-bg-input p-2.5">
      <h4 className="text-[10px] font-semibold uppercase tracking-wide ls-text-muted mb-1">{title}</h4>
      {children}
    </div>
  );
}

// ─── Diálogo: Nuevo Curso ───────────────────────────

function NewCourseDialog({
  open, onOpenChange, onCreate,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  onCreate: (data: { name: string; code?: string; period?: string }) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [period, setPeriod] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) { toast.error("El nombre es obligatorio"); return; }
    setSaving(true);
    try {
      await onCreate({ name: name.trim(), code: code.trim() || undefined, period: period.trim() || undefined });
      toast.success("Curso creado");
      setName(""); setCode(""); setPeriod("");
      onOpenChange(false);
    } catch (err) { toast.error(`Error: ${err}`); }
    finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-w-sm">
        <DialogHeader><DialogTitle className="ls-text">Nuevo Curso</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Nombre *</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Audiología Clínica I" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Código</Label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="AUD-301" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text2">Período</Label>
            <Input value={period} onChange={(e) => setPeriod(e.target.value)} placeholder="2026-S1" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="ls-border ls-text2">Cancelar</Button>
          <Button onClick={handleSubmit} disabled={saving} className="gap-1 bg-sky-600 text-white hover:bg-sky-500">
            {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            Crear
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
