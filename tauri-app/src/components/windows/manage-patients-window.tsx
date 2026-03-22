import { useState, useEffect, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Search,
  Plus,
  RefreshCw,
  Loader2,
  Users,
  Pencil,
  Copy,
  Trash2,
  Archive,
  ArchiveRestore,
  Globe,
  GlobeLock,
  MoreVertical,
  FileText,
  Filter,
  ArrowLeft,
  Save,
  CloudUpload,
} from "lucide-react";
import { useCasesStore, type CaseSummary } from "@/stores/cases-store";
import { usePatientStore } from "@/stores/patient-store";
import { ClinicalLayout } from "@/components/clinical/clinical-layout";
import { invoke } from "@tauri-apps/api/core";
import { toast } from "sonner";

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Fácil",
  medium: "Media",
  hard: "Difícil",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "text-emerald-400 bg-emerald-500/10",
  medium: "text-amber-400 bg-amber-500/10",
  hard: "text-red-400 bg-red-500/10",
};

const STATUS_FILTERS = [
  { value: "all" as const, label: "Todos" },
  { value: "published" as const, label: "Publicados" },
  { value: "draft" as const, label: "Borradores" },
  { value: "archived" as const, label: "Archivados" },
];

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function getStatusBadge(c: CaseSummary) {
  if (c.is_archived) return { label: "Archivado", className: "text-zinc-400 bg-zinc-500/10" };
  if (c.is_published) return { label: "Publicado", className: "text-emerald-400 bg-emerald-500/10" };
  return { label: "Borrador", className: "text-amber-400 bg-amber-500/10" };
}

type ViewMode = "list" | "editor";

export function ManagePatientsWindow() {
  const {
    cases,
    totalCases,
    loading,
    error,
    searchQuery,
    filterStatus,
    selectedCaseId,
    setSearchQuery,
    setFilterStatus,
    setSelectedCaseId,
    fetchCases,
    deleteCase,
    duplicateCase,
    togglePublish,
    toggleArchive,
    getCase,
  } = useCasesStore();

  const resetData = usePatientStore((s) => s.resetData);
  const loadCaseForEditing = usePatientStore((s) => s.loadCaseForEditing);
  const currentPatientId = usePatientStore((s) => s.currentPatientId);
  const data = usePatientStore((s) => s.data);

  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [editingTitle, setEditingTitle] = useState("");
  const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [caseToDelete, setCaseToDelete] = useState<CaseSummary | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // Debounce search
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(debouncedSearch);
    }, 300);
    return () => clearTimeout(timer);
  }, [debouncedSearch, setSearchQuery]);

  // Re-fetch when filters change
  useEffect(() => {
    fetchCases();
  }, [searchQuery, filterStatus, fetchCases]);

  const selectedCase = useMemo(
    () => (cases ?? []).find((c) => c.id === selectedCaseId) ?? null,
    [cases, selectedCaseId],
  );

  const handleNewPatient = useCallback(() => {
    resetData();
    setEditingCaseId(null);
    setEditingTitle("");
    setViewMode("editor");
  }, [resetData]);

  const handleEdit = useCallback(async (c: CaseSummary) => {
    setActionLoading("edit");
    try {
      const detail = await getCase(c.id);
      loadCaseForEditing(c.id, c.title, detail.profile);
      setEditingCaseId(c.id);
      setEditingTitle(c.title);
      setViewMode("editor");
    } catch (err) {
      toast.error(`Error al cargar caso: ${err}`);
    } finally {
      setActionLoading(null);
    }
  }, [getCase, loadCaseForEditing]);

  const handleBackToList = useCallback(() => {
    setViewMode("list");
    fetchCases();
  }, [fetchCases]);

  const handleSave = useCallback(async () => {
    const effectiveTitle = editingTitle.trim() || "Paciente sin nombre";
    setSaving(true);
    try {
      if (editingCaseId) {
        await invoke("api_update_case", {
          caseId: editingCaseId,
          caseData: { title: effectiveTitle, profile: data },
        });
        toast.success("Caso actualizado");
      } else {
        const result = await invoke<{ case: { id: string } }>("api_push_case", {
          caseData: { title: effectiveTitle, profile: data },
        });
        setEditingCaseId(result.case.id);
        usePatientStore.getState().setPatientId(result.case.id);
        toast.success("Caso creado");
      }
    } catch (err) {
      toast.error(`Error al guardar: ${err}`);
    } finally {
      setSaving(false);
    }
  }, [editingTitle, editingCaseId, data]);

  const handleDuplicate = useCallback(async (c: CaseSummary) => {
    setActionLoading("duplicate");
    try {
      await duplicateCase(c.id);
      toast.success(`"Copia de ${c.title}" creada`);
    } catch (err) {
      toast.error(`Error al duplicar: ${err}`);
    } finally {
      setActionLoading(null);
    }
  }, [duplicateCase]);

  const handleTogglePublish = useCallback(async (c: CaseSummary) => {
    setActionLoading("publish");
    try {
      await togglePublish(c.id);
      toast.success(c.is_published ? "Caso despublicado" : "Caso publicado");
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setActionLoading(null);
    }
  }, [togglePublish]);

  const handleToggleArchive = useCallback(async (c: CaseSummary) => {
    setActionLoading("archive");
    try {
      await toggleArchive(c.id);
      toast.success(c.is_archived ? "Caso desarchivado" : "Caso archivado");
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setActionLoading(null);
    }
  }, [toggleArchive]);

  const handleConfirmDelete = useCallback(async () => {
    if (!caseToDelete) return;
    setActionLoading("delete");
    try {
      await deleteCase(caseToDelete.id);
      toast.success("Caso eliminado");
    } catch (err) {
      const msg = String(err);
      if (msg.includes("409") || msg.toLowerCase().includes("asignado")) {
        toast.error("No se puede eliminar: el caso está asignado a sesiones activas");
      } else {
        toast.error(`Error al eliminar: ${msg}`);
      }
    } finally {
      setActionLoading(null);
      setDeleteDialogOpen(false);
      setCaseToDelete(null);
    }
  }, [caseToDelete, deleteCase]);

  // ─── VISTA EDITOR ────────────────────────────────
  if (viewMode === "editor") {
    return (
      <div className="flex h-full flex-col ls-bg">
        {/* Editor header */}
        <div className="flex items-center gap-2 border-b ls-border px-3 py-1.5">
          <Button
            size="xs"
            variant="ghost"
            onClick={handleBackToList}
            className="gap-1 ls-text-muted hover:ls-text"
          >
            <ArrowLeft className="h-3 w-3" />
            Volver
          </Button>
          <div className="mx-1 h-4 w-px ls-bg-input" />
          <CloudUpload className="h-3.5 w-3.5 text-purple-400" />
          <Input
            placeholder="Nombre del caso..."
            value={editingTitle}
            onChange={(e) => setEditingTitle(e.target.value)}
            className="h-6 max-w-[240px] ls-border ls-bg-input text-xs ls-text placeholder:ls-text-muted"
          />
          <Button
            size="xs"
            onClick={handleSave}
            disabled={saving}
            className="ml-auto gap-1 bg-purple-600 text-white hover:bg-purple-500"
          >
            {saving ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Save className="h-3 w-3" />
            )}
            {editingCaseId ? "Guardar" : "Crear"}
          </Button>
        </div>

        {/* Clinical editor */}
        <div className="flex-1 overflow-hidden">
          <ClinicalLayout />
        </div>
      </div>
    );
  }

  // ─── VISTA LISTA ─────────────────────────────────
  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <Users className="h-4 w-4 text-purple-400" />
        <span className="text-xs font-medium ls-text2">Gestionar Pacientes</span>

        <div className="ml-auto flex items-center gap-1">
          <Button
            size="xs"
            variant="ghost"
            onClick={handleNewPatient}
            className="gap-1 ls-text-muted hover:ls-text"
          >
            <Plus className="h-3 w-3" />
            Nuevo
          </Button>
          <Button
            size="icon-xs"
            variant="ghost"
            onClick={() => fetchCases()}
            className="ls-text-muted hover:ls-text"
            title="Recargar"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 ls-text-muted" />
          <Input
            placeholder="Buscar pacientes..."
            value={debouncedSearch}
            onChange={(e) => setDebouncedSearch(e.target.value)}
            className="h-7 ls-border ls-bg-input pl-7 text-xs ls-text placeholder:ls-text-muted"
          />
        </div>
        <div className="flex items-center gap-0.5">
          <Filter className="h-3 w-3 ls-text-muted" />
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilterStatus(f.value)}
              className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
                filterStatus === f.value
                  ? "bg-purple-500/15 text-purple-400"
                  : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Case list */}
        <div className="w-[300px] shrink-0 border-r ls-border">
          <ScrollArea className="h-full">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
              </div>
            ) : (cases ?? []).length === 0 ? (
              <div className="px-3 py-8 text-center text-xs ls-text-muted">
                {searchQuery ? "Sin resultados" : "No hay pacientes creados"}
              </div>
            ) : (
              <div className="p-1">
                {(cases ?? []).map((c) => {
                  const status = getStatusBadge(c);
                  return (
                    <button
                      key={c.id}
                      onClick={() => setSelectedCaseId(c.id)}
                      className={`flex w-full flex-col gap-1 rounded-md px-2.5 py-2 text-left transition ${
                        selectedCaseId === c.id ? "bg-purple-500/10" : "hover:ls-bg-input"
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`truncate text-xs font-medium ${
                            selectedCaseId === c.id ? "text-purple-300" : "ls-text2"
                          }`}
                        >
                          {c.title}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Badge variant="outline" className={`px-1 py-0 text-[9px] ${status.className}`}>
                          {status.label}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`px-1 py-0 text-[9px] ${DIFFICULTY_COLORS[c.difficulty] ?? ""}`}
                        >
                          {DIFFICULTY_LABELS[c.difficulty] ?? c.difficulty}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-[10px] ls-text-muted">
                        <span>{c.author_name || c.author_username}</span>
                        <span>{formatDate(c.updated_at)}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Detail panel */}
        <div className="flex-1">
          {selectedCase ? (
            <ScrollArea className="h-full">
              <div className="p-4">
                {/* Case header */}
                <div className="mb-4">
                  <h3 className="text-sm font-semibold ls-text">{selectedCase.title}</h3>
                  {selectedCase.description && (
                    <p className="mt-1 text-xs ls-text2">{selectedCase.description}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {(() => {
                      const s = getStatusBadge(selectedCase);
                      return (
                        <Badge variant="outline" className={`text-xs ${s.className}`}>
                          {s.label}
                        </Badge>
                      );
                    })()}
                    <Badge
                      variant="outline"
                      className={`text-xs ${DIFFICULTY_COLORS[selectedCase.difficulty] ?? ""}`}
                    >
                      {DIFFICULTY_LABELS[selectedCase.difficulty] ?? selectedCase.difficulty}
                    </Badge>
                  </div>
                </div>

                {/* Info */}
                <div className="space-y-3">
                  <div className="rounded-lg border ls-border ls-bg-input p-3">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide ls-text2">
                      Información
                    </h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="ls-text-muted">Autor:</span>{" "}
                        <span className="ls-text2">
                          {selectedCase.author_name || selectedCase.author_username}
                        </span>
                      </div>
                      <div>
                        <span className="ls-text-muted">Creado:</span>{" "}
                        <span className="ls-text2">{formatDate(selectedCase.created_at)}</span>
                      </div>
                      <div>
                        <span className="ls-text-muted">Modificado:</span>{" "}
                        <span className="ls-text2">{formatDate(selectedCase.updated_at)}</span>
                      </div>
                      {selectedCase.tags && (
                        <div>
                          <span className="ls-text-muted">Tags:</span>{" "}
                          <span className="ls-text2">{selectedCase.tags}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleEdit(selectedCase)}
                    disabled={actionLoading === "edit"}
                    className="gap-1.5 bg-purple-600 ls-text hover:bg-purple-500"
                  >
                    {actionLoading === "edit" ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Pencil className="h-3.5 w-3.5" />
                    )}
                    Editar
                  </Button>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size="sm" variant="outline" className="gap-1.5 ls-border ls-text2">
                        <MoreVertical className="h-3.5 w-3.5" />
                        Acciones
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="ls-bg ls-border">
                      <DropdownMenuItem
                        onClick={() => handleDuplicate(selectedCase)}
                        disabled={actionLoading === "duplicate"}
                        className="ls-text2 focus:ls-bg-input focus:ls-text"
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        Duplicar
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleTogglePublish(selectedCase)}
                        disabled={actionLoading === "publish"}
                        className="ls-text2 focus:ls-bg-input focus:ls-text"
                      >
                        {selectedCase.is_published ? (
                          <>
                            <GlobeLock className="mr-2 h-4 w-4" />
                            Despublicar
                          </>
                        ) : (
                          <>
                            <Globe className="mr-2 h-4 w-4" />
                            Publicar
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleToggleArchive(selectedCase)}
                        disabled={actionLoading === "archive"}
                        className="ls-text2 focus:ls-bg-input focus:ls-text"
                      >
                        {selectedCase.is_archived ? (
                          <>
                            <ArchiveRestore className="mr-2 h-4 w-4" />
                            Desarchivar
                          </>
                        ) : (
                          <>
                            <Archive className="mr-2 h-4 w-4" />
                            Archivar
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="ls-bg-input" />
                      <DropdownMenuItem
                        onClick={() => {
                          setCaseToDelete(selectedCase);
                          setDeleteDialogOpen(true);
                        }}
                        className="text-red-400 focus:bg-red-500/10 focus:text-red-300"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </ScrollArea>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl ls-bg-input">
                <FileText className="h-7 w-7 ls-text-muted" />
              </div>
              <div>
                <p className="text-xs ls-text-muted">Selecciona un paciente para ver sus datos</p>
                <p className="mt-0.5 text-xs ls-text-muted">{totalCases} pacientes creados</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
        <span>{totalCases} pacientes</span>
        {error && <span className="text-amber-400/60">{error}</span>}
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="ls-bg ls-text ls-border">
          <DialogHeader>
            <DialogTitle className="ls-text">Eliminar Caso</DialogTitle>
            <DialogDescription className="ls-text2">
              ¿Estás seguro de eliminar &quot;{caseToDelete?.title}&quot;? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} className="ls-border ls-text2">
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={actionLoading === "delete"}
            >
              {actionLoading === "delete" ? (
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              )}
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
