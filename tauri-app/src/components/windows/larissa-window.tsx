import { useState, useCallback, useEffect } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useSyncStore } from "@/stores/sync-store";
import { TabNavigation } from "@/components/clinical/tab-navigation";
import { ModuleLoader } from "@/components/clinical/module-loader";
import { MODULE_IDS, MODULE_LABELS, type ModuleId } from "@/lib/constants";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import {
  ChevronLeft,
  ChevronRight,
  Send,
  User,
  FileCheck,
  AlertCircle,
} from "lucide-react";

/**
 * Larissa — Sistema de fichas clínicas del estudiante
 *
 * Aquí el estudiante registra los resultados de sus evaluaciones:
 * datos del paciente, anamnesis, audiometría, impedanciometría, etc.
 * Cuando trabaja en una sesión práctica, los datos del paciente y anamnesis
 * vienen pre-cargados del caso base, y los módulos de resultados están vacíos.
 */
export function LarissaWindow() {
  const [activeTab, setActiveTab] = useState<ModuleId>("patient-info");
  const [submitting, setSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  const data = usePatientStore((s) => s.data);
  const mode = usePatientStore((s) => s.mode);
  const caseInfo = usePatientStore((s) => s.caseInfo);
  const getSnapshot = usePatientStore((s) => s.getSubmissionSnapshot);
  const submitWork = useSyncStore((s) => s.submitWork);

  const currentIndex = MODULE_IDS.indexOf(activeTab);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < MODULE_IDS.length - 1;

  const goPrev = useCallback(() => {
    if (hasPrev) setActiveTab(MODULE_IDS[currentIndex - 1]);
  }, [currentIndex, hasPrev]);

  const goNext = useCallback(() => {
    if (hasNext) setActiveTab(MODULE_IDS[currentIndex + 1]);
  }, [currentIndex, hasNext]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "ArrowLeft") { e.preventDefault(); goPrev(); }
      else if (e.ctrlKey && e.key === "ArrowRight") { e.preventDefault(); goNext(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goPrev, goNext]);

  // Contar módulos con datos
  const filledModules = MODULE_IDS.filter((id) => {
    const mod = data[id as keyof typeof data];
    return mod && Object.keys(mod).length > 0;
  }).length;

  async function handleSubmit() {
    if (!caseInfo) return;
    setSubmitting(true);
    setSubmitMessage(null);

    try {
      const snapshot = getSnapshot();
      await submitWork(
        snapshot.sessionId ?? "",
        snapshot.caseId ?? "",
        snapshot.data as unknown as Record<string, unknown>,
      );
      setSubmitMessage("Entrega enviada correctamente");
    } catch (e) {
      setSubmitMessage("Error al enviar: " + String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header con info del caso */}
      <div className="flex items-center justify-between border-b ls-border px-4 py-2 ls-bg-panel/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <User className="h-4 w-4 text-cyan-400" />
            <span className="text-sm font-semibold ls-text">Larissa</span>
          </div>
          {mode === "session" && caseInfo && (
            <span className="text-xs ls-text-muted">
              — {caseInfo.title}
            </span>
          )}
          {mode === "free" && (
            <span className="text-xs ls-text-muted">
              — Práctica libre
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs ls-text-muted">
            <FileCheck className="inline h-3 w-3 mr-1" />
            {filledModules}/{MODULE_IDS.length} módulos
          </span>
          {mode === "session" && caseInfo && (
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={submitting}
              className="gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
            >
              <Send className="h-3 w-3" />
              {submitting ? "Enviando..." : "Entregar"}
            </Button>
          )}
        </div>
      </div>

      {submitMessage && (
        <div className={`px-4 py-2 text-xs flex items-center gap-1 ${
          submitMessage.includes("Error") ? "bg-red-900/20 text-red-400" : "bg-emerald-900/20 text-emerald-400"
        }`}>
          <AlertCircle className="h-3 w-3" />
          {submitMessage}
        </div>
      )}

      {/* Tabs */}
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Contenido del módulo */}
      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-4xl p-6">
          <ModuleLoader moduleId={activeTab} />
        </div>
      </ScrollArea>

      {/* Navegación inferior */}
      <div className="flex items-center justify-between border-t ls-border ls-bg-panel/50 px-4 py-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={goPrev}
          disabled={!hasPrev}
          className="gap-1 ls-text2 hover:ls-text"
        >
          <ChevronLeft className="h-4 w-4" />
          Anterior
        </Button>

        <span className="text-xs ls-text-muted">
          {currentIndex + 1} / {MODULE_IDS.length} · {MODULE_LABELS[activeTab]}
        </span>

        <Button
          variant="ghost"
          size="sm"
          onClick={goNext}
          disabled={!hasNext}
          className="gap-1 ls-text2 hover:ls-text"
        >
          Siguiente
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
