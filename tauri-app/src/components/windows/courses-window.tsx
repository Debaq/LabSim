import { useState, useEffect, useCallback } from "react";
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
  GraduationCap,
  Plus,
  RefreshCw,
  Loader2,
  Users,
  Upload,
  UserPlus,
  Trash2,
  ArrowLeft,
  FileSpreadsheet,
  Search,
} from "lucide-react";
import { useCoursesStore, type ImportSummary } from "@/stores/courses-store";
import { invoke } from "@tauri-apps/api/core";
import { toast } from "sonner";

type ViewMode = "list" | "detail";

export function CoursesWindow() {
  const {
    courses,
    loading,
    error,
    selectedCourseId,
    selectedCourse,
    members,
    membersLoading,
    setSelectedCourseId,
    fetchCourses,
    createCourse,
    removeStudent,
    importStudents,
    enrollStudent,
  } = useCoursesStore();

  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [newCourseOpen, setNewCourseOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [addStudentOpen, setAddStudentOpen] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleSelectCourse = useCallback((id: string) => {
    setSelectedCourseId(id);
    setViewMode("detail");
  }, [setSelectedCourseId]);

  const handleBack = useCallback(() => {
    setViewMode("list");
    setSelectedCourseId(null);
    fetchCourses();
  }, [setSelectedCourseId, fetchCourses]);

  // ─── VISTA DETALLE DEL CURSO ─────────────────────
  if (viewMode === "detail" && selectedCourseId) {
    return (
      <div className="flex h-full flex-col ls-bg">
        <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
          <Button size="xs" variant="ghost" onClick={handleBack} className="gap-1 ls-text-muted hover:ls-text">
            <ArrowLeft className="h-3 w-3" />
            Cursos
          </Button>
          <div className="mx-1 h-4 w-px ls-bg-input" />
          <GraduationCap className="h-4 w-4 text-sky-400" />
          <span className="text-xs font-medium ls-text2">
            {selectedCourse?.name ?? "Cargando..."}
          </span>
          {selectedCourse?.code && (
            <Badge variant="outline" className="text-[10px] ls-border ls-text-muted">{selectedCourse.code}</Badge>
          )}
          <div className="ml-auto flex items-center gap-1">
            <Button size="xs" variant="ghost" onClick={() => setAddStudentOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
              <UserPlus className="h-3 w-3" />
              Agregar
            </Button>
            <Button size="xs" variant="ghost" onClick={() => setImportOpen(true)} className="gap-1 ls-text-muted hover:ls-text">
              <Upload className="h-3 w-3" />
              Importar CSV
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          {membersLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
            </div>
          ) : members.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs ls-text-muted">
              No hay estudiantes inscritos. Usa "Importar CSV" para agregar.
            </div>
          ) : (
            <div className="p-2">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b ls-border text-left ls-text-muted">
                    <th className="px-2 py-1.5 font-medium">Nombre</th>
                    <th className="px-2 py-1.5 font-medium">Username</th>
                    <th className="px-2 py-1.5 font-medium">ID</th>
                    <th className="px-2 py-1.5 font-medium">Email</th>
                    <th className="px-2 py-1.5 font-medium">Rol</th>
                    <th className="px-2 py-1.5 font-medium w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.id} className="border-b ls-border/50 hover:ls-bg-input">
                      <td className="px-2 py-1.5 ls-text2">{m.full_name ?? "—"}</td>
                      <td className="px-2 py-1.5 ls-text-muted">{m.username}</td>
                      <td className="px-2 py-1.5 ls-text-muted">{m.student_id_number ?? "—"}</td>
                      <td className="px-2 py-1.5 ls-text-muted">{m.email ?? "—"}</td>
                      <td className="px-2 py-1.5">
                        <Badge variant="outline" className="text-[9px] ls-border ls-text-muted">{m.role}</Badge>
                      </td>
                      <td className="px-2 py-1.5">
                        {m.role === "estudiante" && (
                          <Button
                            size="icon-xs"
                            variant="ghost"
                            onClick={async () => {
                              await removeStudent(selectedCourseId, m.id);
                              toast.success("Estudiante eliminado del curso");
                            }}
                            className="text-red-400/60 hover:text-red-400"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </ScrollArea>

        <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
          <span>{members.filter((m) => m.role === "estudiante").length} estudiantes</span>
          {selectedCourse?.period && <span>{selectedCourse.period}</span>}
        </div>

        <ImportDialog
          open={importOpen}
          onOpenChange={setImportOpen}
          courseId={selectedCourseId}
          onImport={importStudents}
        />
        <AddStudentDialog
          open={addStudentOpen}
          onOpenChange={setAddStudentOpen}
          courseId={selectedCourseId}
          onEnroll={enrollStudent}
        />
      </div>
    );
  }

  // ─── VISTA LISTA DE CURSOS ───────────────────────
  return (
    <div className="flex h-full flex-col ls-bg">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <GraduationCap className="h-4 w-4 text-sky-400" />
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

      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : (courses ?? []).length === 0 ? (
          <div className="px-4 py-8 text-center text-xs ls-text-muted">
            No tienes cursos. Crea uno para empezar.
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {(courses ?? []).map((c) => (
              <button
                key={c.id}
                onClick={() => handleSelectCourse(c.id)}
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
              </button>
            ))}
          </div>
        )}
      </ScrollArea>

      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
        <span>{(courses ?? []).length} cursos</span>
        {error && <span className="text-amber-400/60">{error}</span>}
      </div>

      <NewCourseDialog open={newCourseOpen} onOpenChange={setNewCourseOpen} onCreate={createCourse} />
    </div>
  );
}

// ─── Diálogo: Nuevo Curso ────────────────────────────

function NewCourseDialog({
  open,
  onOpenChange,
  onCreate,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  onCreate: (data: { name: string; code?: string; description?: string; period?: string }) => Promise<void>;
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

// ─── Diálogo: Importar CSV ───────────────────────────

function ImportDialog({
  open,
  onOpenChange,
  courseId,
  onImport,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  courseId: string;
  onImport: (courseId: string, students: Array<Record<string, string>>) => Promise<ImportSummary>;
}) {
  const [csvText, setCsvText] = useState("");
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportSummary | null>(null);

  const handleImport = async () => {
    const lines = csvText.trim().split("\n").filter((l) => l.trim());
    if (lines.length === 0) { toast.error("Pega los datos del CSV"); return; }

    // Parsear CSV simple: nombre_completo, identificador, email
    const students: Array<Record<string, string>> = [];
    for (const line of lines) {
      const parts = line.split(/[,;\t]/).map((s) => s.trim());
      if (parts.length === 0 || !parts[0]) continue;
      students.push({
        fullName: parts[0] ?? "",
        studentId: parts[1] ?? "",
        email: parts[2] ?? "",
      });
    }

    if (students.length === 0) { toast.error("No se encontraron estudiantes válidos"); return; }

    setImporting(true);
    try {
      const summary = await onImport(courseId, students);
      setResult(summary);
      toast.success(`${summary.created} creados, ${summary.found} encontrados, ${summary.enrolled} inscritos`);
    } catch (err) { toast.error(`Error: ${err}`); }
    finally { setImporting(false); }
  };

  const handleClose = () => {
    setCsvText("");
    setResult(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="ls-bg ls-text ls-border max-w-lg">
        <DialogHeader>
          <DialogTitle className="ls-text flex items-center gap-2">
            <FileSpreadsheet className="h-4 w-4 text-sky-400" />
            Importar Estudiantes
          </DialogTitle>
        </DialogHeader>

        {result ? (
          <div className="space-y-2 text-xs">
            <div className="rounded-lg border ls-border ls-bg-input p-3 space-y-1">
              <div className="ls-text2"><span className="text-emerald-400 font-medium">{result.created}</span> cuentas creadas</div>
              <div className="ls-text2"><span className="text-sky-400 font-medium">{result.found}</span> ya existían</div>
              <div className="ls-text2"><span className="text-cyan-400 font-medium">{result.enrolled}</span> inscritos en el curso</div>
              {result.errors.length > 0 && (
                <div className="mt-2">
                  <span className="text-red-400 font-medium">{result.errors.length} errores:</span>
                  {result.errors.map((e, i) => <div key={i} className="text-red-400/70">{e}</div>)}
                </div>
              )}
            </div>
            <Button onClick={handleClose} className="w-full" variant="outline">Cerrar</Button>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <p className="text-xs ls-text-muted">
                Pega los datos separados por coma, punto y coma, o tab.
                Formato: <span className="ls-text2">nombre completo, identificador (RUN/matrícula), email (opcional)</span>
              </p>
              <Textarea
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                placeholder={"Juan Pérez, 12345678-9, juan@mail.com\nMaría López, 98765432-1\nCarlos Ruiz, 11223344-5, carlos@uni.cl"}
                rows={8}
                className="ls-border ls-bg-input text-xs ls-text font-mono placeholder:ls-text-muted resize-none"
              />
              <p className="text-[10px] ls-text-muted">
                La contraseña temporal será el identificador de cada estudiante.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose} className="ls-border ls-text2">Cancelar</Button>
              <Button onClick={handleImport} disabled={importing} className="gap-1 bg-sky-600 text-white hover:bg-sky-500">
                {importing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Upload className="h-3 w-3" />}
                Importar
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ─── Diálogo: Agregar Estudiante ─────────────────────

function AddStudentDialog({
  open,
  onOpenChange,
  courseId,
  onEnroll,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  courseId: string;
  onEnroll: (courseId: string, userId: string) => Promise<void>;
}) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Array<{ id: string; username: string; full_name: string | null; student_id_number: string | null }>>([]);
  const [searching, setSearching] = useState(false);
  const [enrolling, setEnrolling] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const result = await invoke<{ data: Array<{ id: string; username: string; full_name: string | null; student_id_number: string | null }> }>(
        "api_list_institution_students", { search: search.trim() }
      );
      setResults(result?.data ?? []);
    } catch { setResults([]); }
    finally { setSearching(false); }
  };

  const handleEnroll = async (userId: string) => {
    setEnrolling(userId);
    try {
      await onEnroll(courseId, userId);
      toast.success("Estudiante inscrito");
      setResults((prev) => prev.filter((r) => r.id !== userId));
    } catch (err) { toast.error(`Error: ${err}`); }
    finally { setEnrolling(null); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ls-bg ls-text ls-border max-w-sm">
        <DialogHeader><DialogTitle className="ls-text">Agregar Estudiante</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div className="flex gap-1">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Buscar por nombre, RUN, email..."
              className="ls-border ls-bg-input text-xs ls-text"
            />
            <Button size="xs" onClick={handleSearch} disabled={searching} className="shrink-0">
              {searching ? <Loader2 className="h-3 w-3 animate-spin" /> : <Search className="h-3 w-3" />}
            </Button>
          </div>
          <ScrollArea className="max-h-[200px]">
            {results.length === 0 ? (
              <p className="text-xs ls-text-muted text-center py-4">
                {search ? "Sin resultados" : "Busca un estudiante"}
              </p>
            ) : (
              <div className="space-y-1">
                {results.map((r) => (
                  <div key={r.id} className="flex items-center justify-between rounded-md px-2 py-1.5 ls-bg-input">
                    <div>
                      <div className="text-xs ls-text2">{r.full_name ?? r.username}</div>
                      <div className="text-[10px] ls-text-muted">{r.student_id_number ?? r.username}</div>
                    </div>
                    <Button
                      size="xs"
                      onClick={() => handleEnroll(r.id)}
                      disabled={enrolling === r.id}
                      className="gap-1 bg-sky-600 text-white hover:bg-sky-500"
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
