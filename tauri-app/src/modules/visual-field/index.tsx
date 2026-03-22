import { useModuleForm } from "@/modules/use-module-form";
import { visualFieldSchema, DEFECT_TYPES, SEVERITIES, type VisualFieldData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Target } from "lucide-react";

const EYES = [
  { key: "ojoDerecho", label: "Ojo Derecho (OD)", color: "text-red-400" },
  { key: "ojoIzquierdo", label: "Ojo Izquierdo (OI)", color: "text-blue-400" },
] as const;

const DEFECT_LABELS: Record<string, string> = {
  normal: "Normal",
  "escotoma-arcuato-sup": "Escotoma Arcuato Superior",
  "escotoma-arcuato-inf": "Escotoma Arcuato Inferior",
  "escotoma-arcuato-doble": "Escotoma Arcuato Doble",
  "escalon-nasal": "Escalón Nasal",
  "hemianopsia-homonima-der": "Hemianopsia Homónima Derecha",
  "hemianopsia-homonima-izq": "Hemianopsia Homónima Izquierda",
  "hemianopsia-bitemporal": "Hemianopsia Bitemporal",
  "cuadrantanopsia-sup": "Cuadrantanopsia Superior",
  "cuadrantanopsia-inf": "Cuadrantanopsia Inferior",
  "depresion-general": "Depresión Generalizada",
  "isla-central": "Isla Central (visión tubular)",
  "constriccion-periferica": "Constricción Periférica",
};

const SEV_LABELS: Record<string, string> = {
  leve: "Leve", moderado: "Moderado", severo: "Severo",
};

export default function VisualFieldModule() {
  const { form, onSubmit } = useModuleForm<VisualFieldData>(
    "visualField", visualFieldSchema, "Campo Visual",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-violet-400" />
          <h2 className="text-lg font-semibold ls-text">Campo Visual — Datos Fisiológicos</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {EYES.map((eye) => (
        <fieldset key={eye.key} className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
          <legend className={`px-2 text-sm font-medium ${eye.color}`}>{eye.label}</legend>

          {/* Defecto visual */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Defecto visual</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Tipo de defecto</Label>
                <Select
                  value={watch(`${eye.key}.defecto`) || "normal"}
                  onValueChange={(v) => setValue(`${eye.key}.defecto`, v as typeof DEFECT_TYPES[number], { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {DEFECT_TYPES.map((d) => <SelectItem key={d} value={d}>{DEFECT_LABELS[d]}</SelectItem>)}
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
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">MD Objetivo (dB)</Label>
                <Input type="number" step="0.5" {...register(`${eye.key}.mdObjetivo`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="Ej: -8.5" />
              </div>
            </div>
          </div>

          {/* Comportamiento del paciente */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Comportamiento del paciente durante el examen</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Falsos positivos (0-1)</Label>
                <Input type="number" step="0.01" min="0" max="1" {...register(`${eye.key}.falsePositiveRate`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="0.03" />
                <p className="text-[9px] ls-text-muted">Aprieta sin estímulo</p>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Falsos negativos (0-1)</Label>
                <Input type="number" step="0.01" min="0" max="1" {...register(`${eye.key}.falseNegativeRate`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="0.02" />
                <p className="text-[9px] ls-text-muted">No responde aunque ve</p>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Pérdida de fijación (0-1)</Label>
                <Input type="number" step="0.01" min="0" max="1" {...register(`${eye.key}.fixationLossRate`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="0.05" />
                <p className="text-[9px] ls-text-muted">Se mueve del punto</p>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Tiempo reacción (ms)</Label>
                <Input type="number" step="50" min="100" max="2000" {...register(`${eye.key}.reactionTimeMs`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="300" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Fatiga (0-1)</Label>
                <Input type="number" step="0.05" min="0" max="1" {...register(`${eye.key}.fatigueFactor`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="0.1" />
                <p className="text-[9px] ls-text-muted">Empeora al avanzar el test</p>
              </div>
            </div>
          </div>

          {/* Protocolo preferido */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Protocolo preferido (opcional)</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Patrón</Label>
                <Select
                  value={watch(`${eye.key}.patron`) || ""}
                  onValueChange={(v) => setValue(`${eye.key}.patron`, v as "24-2" | "30-2" | "10-2", { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Libre" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24-2">24-2</SelectItem>
                    <SelectItem value="30-2">30-2</SelectItem>
                    <SelectItem value="10-2">10-2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Estrategia</Label>
                <Select
                  value={watch(`${eye.key}.estrategia`) || ""}
                  onValueChange={(v) => setValue(`${eye.key}.estrategia`, v as "sita-standard" | "sita-fast" | "full-threshold", { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Libre" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sita-standard">SITA Standard</SelectItem>
                    <SelectItem value="sita-fast">SITA Fast</SelectItem>
                    <SelectItem value="full-threshold">Full Threshold</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Estímulo</Label>
                <Select
                  value={watch(`${eye.key}.tamanoEstimulo`) || ""}
                  onValueChange={(v) => setValue(`${eye.key}.tamanoEstimulo`, v as "I" | "II" | "III" | "IV" | "V", { shouldDirty: true })}
                >
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Libre" /></SelectTrigger>
                  <SelectContent>
                    {["I", "II", "III", "IV", "V"].map((s) => <SelectItem key={s} value={s}>Goldmann {s}</SelectItem>)}
                  </SelectContent>
                </Select>
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
