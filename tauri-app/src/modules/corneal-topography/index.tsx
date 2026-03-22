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
  "wtr-astigmatism": "Astigmatismo Con la Regla",
  "atr-astigmatism": "Astigmatismo Contra la Regla",
  "oblique-astigmatism": "Astigmatismo Oblicuo",
  "post-lasik": "Post-LASIK",
};

const SEV_LABELS: Record<string, string> = { leve: "Leve", moderado: "Moderado", severo: "Severo" };

export default function CornealTopographyModule() {
  const { form, onSubmit } = useModuleForm<CornealTopographyData>(
    "cornealTopography", cornealTopographySchema, "Topografía Corneal",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CircleDot className="h-5 w-5 text-teal-400" />
          <h2 className="text-lg font-semibold ls-text">Topografía Corneal — Datos Fisiológicos</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {EYES.map((eye) => (
        <fieldset key={eye.key} className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
          <legend className={`px-2 text-sm font-medium ${eye.color}`}>{eye.label}</legend>

          {/* Tipo de córnea */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Tipo de córnea</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Patología</Label>
                <Select
                  value={watch(`${eye.key}.patologia`) || "normal"}
                  onValueChange={(v) => setValue(`${eye.key}.patologia`, v as typeof PATHOLOGIES[number], { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {PATHOLOGIES.map((p) => <SelectItem key={p} value={p}>{PATHO_LABELS[p]}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Severidad</Label>
                <Select
                  value={watch(`${eye.key}.severidad`) || "moderado"}
                  onValueChange={(v) => setValue(`${eye.key}.severidad`, v as typeof SEVERITIES[number], { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SEVERITIES.map((s) => <SelectItem key={s} value={s}>{SEV_LABELS[s]}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Parámetros queratométricos */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Queratometría (opcional — overridea valores generados)</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">K1 plano (D)</Label>
                <Input type="number" step="0.25" {...register(`${eye.key}.k1`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="43.00" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">K2 empinado (D)</Label>
                <Input type="number" step="0.25" {...register(`${eye.key}.k2`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="44.00" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Eje K1 (°)</Label>
                <Input type="number" min="0" max="180" {...register(`${eye.key}.k1Axis`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="90" />
              </div>
            </div>
          </div>

          {/* Paquimetría */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Paquimetría (opcional)</Label>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">CCT central (µm)</Label>
                <Input type="number" {...register(`${eye.key}.cct`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="545" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Punto más delgado (µm)</Label>
                <Input type="number" {...register(`${eye.key}.thinnestPoint`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="530" />
              </div>
            </div>
          </div>


          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Notas</Label>
            <Textarea {...register(`${eye.key}.notas`)} className="min-h-12 ls-border ls-bg-input text-xs ls-text resize-none" />
          </div>
        </fieldset>
      ))}

      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea {...register("observaciones")} className="min-h-12 ls-border ls-bg-input text-xs ls-text resize-none" />
      </fieldset>
    </form>
  );
}
