import { useModuleForm } from "@/modules/use-module-form";
import { cornealTopographySchema, PATHOLOGIES, SEVERITIES, type CornealTopographyData } from "./schema";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, CircleDot } from "lucide-react";

const EYES = [
  { key: "ojoDerecho", label: "Ojo Derecho (OD)", color: "text-red-400" },
  { key: "ojoIzquierdo", label: "Ojo Izquierdo (OI)", color: "text-blue-400" },
] as const;

const PATHO_LABELS: Record<string, string> = {
  normal: "Normal",
  keratoconus: "Queratocono",
  pellucid: "Degeneración Marginal Pelúcida",
  "wtr-astigmatism": "Astigmatismo a la Regla",
  "atr-astigmatism": "Astigmatismo contra la Regla",
  "oblique-astigmatism": "Astigmatismo Oblicuo",
  "post-lasik": "Post-LASIK/PRK",
};

const SEV_LABELS: Record<string, string> = {
  leve: "Leve", moderado: "Moderado", severo: "Severo",
};

const MAP_LABELS: Record<string, string> = {
  axial: "Axial (Sagital)",
  tangential: "Tangencial",
  elevation: "Elevación",
  pachymetry: "Paquimetría",
};

export default function CornealTopographyModule() {
  const { form, onSubmit } = useModuleForm<CornealTopographyData>(
    "cornealTopography",
    cornealTopographySchema,
    "Topografía Corneal",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CircleDot className="h-5 w-5 text-teal-400" />
          <h2 className="text-lg font-semibold ls-text">Topografía Corneal - Configuración del Caso</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      <p className="text-xs ls-text-muted">
        Configura la patología corneal que el topógrafo mostrará cuando el estudiante abra la ventana con este caso cargado.
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
              <Label className="ls-text2">Mapa Preferido</Label>
              <Select
                value={watch(`${eye.key}.mapaPreferido`) || "axial"}
                onValueChange={(v) => setValue(`${eye.key}.mapaPreferido`, v as "axial" | "tangential" | "elevation" | "pachymetry", { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MAP_LABELS).map(([k, label]) => (
                    <SelectItem key={k} value={k}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="ls-text2">Calidad Captura (1-10)</Label>
              <Input
                type="number" min={1} max={10}
                {...register(`${eye.key}.calidadCaptura`)}
                className="ls-border ls-bg-input ls-text"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="ls-text2">Notas para este ojo</Label>
            <Textarea
              {...register(`${eye.key}.notas`)}
              className="min-h-12 ls-border ls-bg-input ls-text"
              placeholder="Ej: Queratocono incipiente con Kmax 48D, adelgazamiento inferior..."
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
          placeholder="Contexto clínico, correlación con otros hallazgos, indicación de crosslinking..."
        />
      </fieldset>
    </form>
  );
}
