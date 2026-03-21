import { useModuleForm } from "@/modules/use-module-form";
import { octSchema, PATHOLOGIES, SEVERITIES, type OctData } from "./schema";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, ScanEye } from "lucide-react";

const EYES = [
  { key: "ojoDerecho", label: "Ojo Derecho (OD)", color: "text-red-400" },
  { key: "ojoIzquierdo", label: "Ojo Izquierdo (OI)", color: "text-blue-400" },
] as const;

const PATHO_LABELS: Record<string, string> = {
  normal: "Normal", glaucoma: "Glaucoma", edema: "Edema Macular",
  drusen: "Drusen", epiretinal: "Membrana Epiretiniana",
  "amd-dry": "DMAE Seca", "amd-wet": "DMAE Húmeda",
};

const SEV_LABELS: Record<string, string> = {
  leve: "Leve", moderado: "Moderado", severo: "Severo",
};

export default function OctModule() {
  const { form, onSubmit } = useModuleForm<OctData>("oct", octSchema, "OCT");
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ScanEye className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-semibold ls-text">OCT - Configuración del Caso</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      <p className="text-xs ls-text-muted">
        Configura la patología que el simulador OCT mostrará cuando el estudiante abra la ventana OCT con este caso cargado.
      </p>

      {EYES.map((eye) => (
        <fieldset key={eye.key} className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
          <legend className={`px-2 text-sm font-medium ${eye.color}`}>
            {eye.label}
          </legend>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label className="ls-text2">Patología</Label>
              <Select
                value={watch(`${eye.key}.patologia`) || "normal"}
                onValueChange={(v) => setValue(`${eye.key}.patologia`, v as typeof PATHOLOGIES[number], { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PATHOLOGIES.map((p) => (
                    <SelectItem key={p} value={p}>{PATHO_LABELS[p]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="ls-text2">Severidad</Label>
              <Select
                value={watch(`${eye.key}.severidad`) || "moderado"}
                onValueChange={(v) => setValue(`${eye.key}.severidad`, v as typeof SEVERITIES[number], { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map((s) => (
                    <SelectItem key={s} value={s}>{SEV_LABELS[s]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="ls-text2">Scan Preferido</Label>
              <Select
                value={watch(`${eye.key}.scanPreferido`) || "disco"}
                onValueChange={(v) => setValue(`${eye.key}.scanPreferido`, v as "disco" | "macula", { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="disco">Disco Óptico</SelectItem>
                  <SelectItem value="macula">Mácula</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="ls-text2">Calidad Señal (1-10)</Label>
              <Input
                type="number" min={1} max={10}
                {...register(`${eye.key}.calidadSenal`)}
                className="ls-border ls-bg-input ls-text"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="ls-text2">Notas para este ojo</Label>
            <Textarea
              {...register(`${eye.key}.notas`)}
              className="min-h-12 ls-border ls-bg-input ls-text"
              placeholder="Ej: Adelgazamiento RNFL inferior, sospecha glaucoma incipiente..."
            />
          </div>
        </fieldset>
      ))}

      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Observaciones Generales
        </legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-16 ls-border ls-bg-input ls-text"
          placeholder="Contexto clínico, correlación con otros hallazgos..."
        />
      </fieldset>
    </form>
  );
}
