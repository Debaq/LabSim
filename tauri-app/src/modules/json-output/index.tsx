import { usePatientStore } from "@/stores/patient-store";
import { Button } from "@/components/ui/button";
import { FileJson, Download, Copy, Check } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function JsonOutputModule() {
  const data = usePatientStore((s) => s.data);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const [copied, setCopied] = useState(false);

  const jsonString = JSON.stringify(data, null, 2);

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `labsim-paciente-${patientId ?? "sin-id"}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Archivo JSON descargado");
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      toast.success("JSON copiado al portapapeles");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Error al copiar");
    }
  };

  // Contar modulos con datos
  const modulesWithData = Object.entries(data).filter(
    ([, v]) => Object.keys(v).length > 0,
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileJson className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Exportar Datos (JSON)</h2>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" className="gap-1.5" onClick={handleCopy}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copiado" : "Copiar"}
          </Button>
          <Button type="button" size="sm" className="gap-1.5" onClick={handleDownload}>
            <Download className="h-3.5 w-3.5" />Descargar
          </Button>
        </div>
      </div>

      {/* Resumen */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Resumen
        </legend>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-md ls-bg-input px-3 py-2">
            <span className="text-xs ls-text-muted">ID Paciente</span>
            <p className="text-sm font-medium ls-text">{patientId ?? "Sin asignar"}</p>
          </div>
          <div className="rounded-md ls-bg-input px-3 py-2">
            <span className="text-xs ls-text-muted">Modulos con datos</span>
            <p className="text-sm font-medium ls-text">{modulesWithData.length} / {Object.keys(data).length}</p>
          </div>
          <div className="rounded-md ls-bg-input px-3 py-2">
            <span className="text-xs ls-text-muted">Tamano</span>
            <p className="text-sm font-medium ls-text">{(new Blob([jsonString]).size / 1024).toFixed(1)} KB</p>
          </div>
        </div>
        {modulesWithData.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {modulesWithData.map(([key]) => (
              <span
                key={key}
                className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs text-blue-400"
              >
                {key}
              </span>
            ))}
          </div>
        )}
      </fieldset>

      {/* JSON Preview */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Vista previa JSON
        </legend>
        <pre className="max-h-[60vh] overflow-auto rounded-md ls-bg-panel2 p-4 text-xs text-green-400/80 font-mono leading-relaxed">
          {jsonString}
        </pre>
      </fieldset>
    </div>
  );
}
