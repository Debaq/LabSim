import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ShieldCheck,
  Users,
  Clock,
  CheckCircle,
  RotateCcw,
  Loader2,
  RefreshCw,
  Eye,
} from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { toast } from "sonner";

interface ValidationRequest {
  id: string;
  agenda_item_id: string;
  student_id: string;
  student_name: string | null;
  student_username: string | null;
  procedure_name: string | null;
  patient_name: string | null;
  scheduled_time: string | null;
  status: "pending" | "approved" | "returned";
  docente_notes: string | null;
  requested_at: string;
  resolved_at: string | null;
}

export function SupervisionWindow() {
  const [validations, setValidations] = useState<ValidationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolveDialog, setResolveDialog] = useState<ValidationRequest | null>(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [resolving, setResolving] = useState(false);
  const [tab, setTab] = useState<"pending" | "resolved">("pending");

  const fetchValidations = useCallback(async () => {
    setLoading(true);
    try {
      const result = await invoke<{ data: ValidationRequest[] }>("api_get_validations", {
        status: tab,
      });
      setValidations(result?.data ?? []);
    } catch {
      setValidations([]);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    fetchValidations();
    const interval = setInterval(fetchValidations, 15000); // refresh cada 15s
    return () => clearInterval(interval);
  }, [fetchValidations]);

  const handleResolve = async (status: "approved" | "returned") => {
    if (!resolveDialog) return;
    setResolving(true);
    try {
      await invoke("api_resolve_validation", {
        validationId: resolveDialog.id,
        data: { status, notes: resolveNotes || null },
      });
      toast.success(status === "approved" ? "Validación aprobada" : "Devuelto para corrección");
      setResolveDialog(null);
      setResolveNotes("");
      fetchValidations();
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setResolving(false);
    }
  };

  const pending = validations.filter((v) => v.status === "pending");

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <ShieldCheck className="h-4 w-4 text-indigo-400" />
        <span className="text-xs font-medium ls-text2">Supervisión</span>

        <div className="ml-2 flex items-center gap-0.5">
          <button
            onClick={() => setTab("pending")}
            className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
              tab === "pending" ? "bg-indigo-500/15 text-indigo-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Pendientes
            {pending.length > 0 && (
              <Badge variant="secondary" className="ml-1 h-4 px-1 text-[9px]">{pending.length}</Badge>
            )}
          </button>
          <button
            onClick={() => setTab("resolved")}
            className={`rounded-md px-2 py-1 text-[10px] font-medium transition ${
              tab === "resolved" ? "bg-indigo-500/15 text-indigo-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Resueltas
          </button>
        </div>

        <Button
          size="icon-xs"
          variant="ghost"
          onClick={fetchValidations}
          className="ml-auto ls-text-muted hover:ls-text"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : validations.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <ShieldCheck className="mx-auto h-10 w-10 ls-text-muted opacity-30 mb-3" />
            <p className="text-xs ls-text-muted">
              {tab === "pending" ? "No hay validaciones pendientes" : "No hay validaciones resueltas"}
            </p>
          </div>
        ) : (
          <div className="p-3 space-y-2">
            {validations.map((v) => (
              <div
                key={v.id}
                className={`rounded-lg border ls-border p-3 ${
                  v.status === "pending" ? "bg-amber-500/5 border-amber-500/20" : ""
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-cyan-400" />
                    <span className="text-xs font-medium ls-text2">
                      {v.student_name ?? v.student_username}
                    </span>
                    {v.status === "pending" && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0 text-amber-400 bg-amber-500/10">
                        <Clock className="inline h-2.5 w-2.5 mr-0.5" />
                        Pendiente
                      </Badge>
                    )}
                    {v.status === "approved" && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0 text-emerald-400 bg-emerald-500/10">
                        <CheckCircle className="inline h-2.5 w-2.5 mr-0.5" />
                        Aprobada
                      </Badge>
                    )}
                    {v.status === "returned" && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0 text-orange-400 bg-orange-500/10">
                        <RotateCcw className="inline h-2.5 w-2.5 mr-0.5" />
                        Devuelta
                      </Badge>
                    )}
                  </div>
                  <span className="text-[10px] ls-text-muted">
                    {new Date(v.requested_at).toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>

                <div className="text-xs ls-text-muted space-y-0.5">
                  {v.patient_name && <div>Paciente: <span className="ls-text2">{v.patient_name}</span></div>}
                  {v.procedure_name && <div>Procedimiento: <span className="ls-text2">{v.procedure_name}</span></div>}
                  {v.docente_notes && <div className="mt-1 text-emerald-400/80">Nota: {v.docente_notes}</div>}
                </div>

                {v.status === "pending" && (
                  <div className="mt-2 flex gap-1.5">
                    <Button
                      size="xs"
                      onClick={() => { setResolveDialog(v); setResolveNotes(""); }}
                      className="gap-1 bg-indigo-600 text-white hover:bg-indigo-500"
                    >
                      <Eye className="h-3 w-3" />
                      Revisar
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Status */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-xs ls-text-muted">
        <span>{validations.length} validaciones</span>
        {pending.length > 0 && (
          <span className="text-amber-400">{pending.length} pendientes</span>
        )}
      </div>

      {/* Resolve dialog */}
      <Dialog open={!!resolveDialog} onOpenChange={(o) => !o && setResolveDialog(null)}>
        <DialogContent className="ls-bg ls-text ls-border max-w-sm">
          <DialogHeader>
            <DialogTitle className="ls-text">
              Revisar: {resolveDialog?.student_name} — {resolveDialog?.procedure_name ?? "Procedimiento"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="rounded-lg border ls-border ls-bg-input p-2.5 text-xs ls-text2">
              <div>Paciente: {resolveDialog?.patient_name}</div>
              <div>Hora: {resolveDialog?.scheduled_time}</div>
            </div>
            <Textarea
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              placeholder="Observaciones (opcional)..."
              rows={3}
              className="ls-border ls-bg-input text-xs ls-text resize-none"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleResolve("returned")}
              disabled={resolving}
              className="gap-1 border-orange-500/30 text-orange-400"
            >
              <RotateCcw className="h-3 w-3" />
              Devolver
            </Button>
            <Button
              onClick={() => handleResolve("approved")}
              disabled={resolving}
              className="gap-1 bg-emerald-600 text-white hover:bg-emerald-500"
            >
              {resolving ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3" />}
              Aprobar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
