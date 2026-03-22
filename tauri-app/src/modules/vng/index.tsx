import { useModuleForm } from "@/modules/use-module-form";
import { vngSchema, type VNGData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Eye } from "lucide-react";

const DIRECTIONS = [
  { value: "ninguno", label: "Ninguno (normal)" },
  { value: "derecha", label: "Derecha" },
  { value: "izquierda", label: "Izquierda" },
  { value: "up-beating", label: "Up-beating" },
  { value: "down-beating", label: "Down-beating" },
];

const POSITIONS = [
  { key: "dixHallpikeRight", label: "Dix-Hallpike Derecho" },
  { key: "dixHallpikeLeft", label: "Dix-Hallpike Izquierdo" },
  { key: "rollTestRight", label: "Roll Test Derecho" },
  { key: "rollTestLeft", label: "Roll Test Izquierdo" },
  { key: "supine", label: "Decúbito Supino" },
  { key: "headHanging", label: "Head Hanging" },
  { key: "sitting", label: "Sentado" },
];

export default function VNGModule() {
  const { form, onSubmit } = useModuleForm<VNGData>("vng", vngSchema, "VNG");
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="h-5 w-5 text-violet-400" />
          <h2 className="text-lg font-semibold ls-text">VNG — Datos Fisiológicos por Prueba</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Guardar</Button>
      </div>

      <p className="text-xs ls-text-muted">
        Configure cada prueba alterada. Las pruebas sin datos darán resultado normal.
      </p>

      {/* Espontáneo */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Nistagmo Espontáneo</legend>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Dirección</Label>
            <Select value={watch("spontaneous.direction") || "ninguno"} onValueChange={(v) => setValue("spontaneous.direction", v as any, { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
              <SelectContent>{DIRECTIONS.slice(0, 3).map((d) => <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">SPV (°/s)</Label>
            <Input type="number" step="0.5" {...register("spontaneous.spv")} className="ls-border ls-bg-input text-xs ls-text" placeholder="0" />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <Checkbox checked={watch("spontaneous.fixationSuppression") ?? true} onCheckedChange={(v) => setValue("spontaneous.fixationSuppression", !!v, { shouldDirty: true })} />
            <Label className="ls-text2 text-xs">Se suprime con fijación</Label>
          </div>
        </div>
      </fieldset>

      {/* Calórico */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Prueba Calórica — SPV pico (°/s)</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1"><Label className="ls-text2 text-xs">OD caliente (44°C)</Label><Input type="number" {...register("caloric.rightWarmSpv")} className="ls-border ls-bg-input text-xs ls-text" placeholder="30" /></div>
          <div className="space-y-1"><Label className="ls-text2 text-xs">OD frío (30°C)</Label><Input type="number" {...register("caloric.rightCoolSpv")} className="ls-border ls-bg-input text-xs ls-text" placeholder="25" /></div>
          <div className="space-y-1"><Label className="ls-text2 text-xs">OI caliente (44°C)</Label><Input type="number" {...register("caloric.leftWarmSpv")} className="ls-border ls-bg-input text-xs ls-text" placeholder="28" /></div>
          <div className="space-y-1"><Label className="ls-text2 text-xs">OI frío (30°C)</Label><Input type="number" {...register("caloric.leftCoolSpv")} className="ls-border ls-bg-input text-xs ls-text" placeholder="26" /></div>
        </div>
        <p className="text-[9px] ls-text-muted">Normal: 15-50. Arreflexia: &lt;5. Asimetría &gt;25% = paresia canalicular.</p>
      </fieldset>

      {/* Posicionales */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Posicionales</legend>
        <p className="text-[9px] ls-text-muted mb-2">Configure solo las posiciones alteradas.</p>
        {POSITIONS.map((pos) => (
          <details key={pos.key} className="rounded border ls-border p-2">
            <summary className="text-xs ls-text2 cursor-pointer">{pos.label}</summary>
            <div className="grid gap-2 sm:grid-cols-3 mt-2">
              <div className="space-y-1">
                <Label className="ls-text2 text-[10px]">Dirección</Label>
                <Select value={watch(`positionals.${pos.key}.direction`) || "ninguno"} onValueChange={(v) => setValue(`positionals.${pos.key}.direction`, v as any, { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text h-7 text-[10px]"><SelectValue /></SelectTrigger>
                  <SelectContent>{DIRECTIONS.map((d) => <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="ls-text2 text-[10px]">SPV (°/s)</Label><Input type="number" {...register(`positionals.${pos.key}.spv`)} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="0" /></div>
              <div className="space-y-1"><Label className="ls-text2 text-[10px]">Duración (s)</Label><Input type="number" {...register(`positionals.${pos.key}.durationSec`)} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="30" /></div>
              <div className="space-y-1"><Label className="ls-text2 text-[10px]">Latencia (s)</Label><Input type="number" {...register(`positionals.${pos.key}.latencySec`)} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="2" /></div>
              <div className="flex items-center gap-2 pt-4">
                <Checkbox checked={watch(`positionals.${pos.key}.fatigable`) ?? false} onCheckedChange={(v) => setValue(`positionals.${pos.key}.fatigable`, !!v, { shouldDirty: true })} />
                <Label className="ls-text2 text-[10px]">Fatigable</Label>
              </div>
            </div>
          </details>
        ))}
      </fieldset>

      {/* Oculomotor */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Oculomotor</legend>

        <details className="rounded border ls-border p-2">
          <summary className="text-xs ls-text2 cursor-pointer">Sacadas</summary>
          <div className="grid gap-2 sm:grid-cols-3 mt-2">
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Latencia (ms)</Label><Input type="number" {...register("oculomotor.saccades.latency")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="220" /></div>
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Precisión (0-1)</Label><Input type="number" step="0.05" {...register("oculomotor.saccades.accuracy")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.95" /></div>
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Vel. pico (°/s)</Label><Input type="number" {...register("oculomotor.saccades.peakVelocity")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="400" /></div>
          </div>
        </details>

        <details className="rounded border ls-border p-2">
          <summary className="text-xs ls-text2 cursor-pointer">Seguimiento (Smooth Pursuit)</summary>
          <div className="grid gap-2 sm:grid-cols-2 mt-2">
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Ganancia</Label><Input type="number" step="0.05" {...register("oculomotor.smoothPursuit.gain")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.95" /></div>
            <div className="space-y-1">
              <Label className="ls-text2 text-[10px]">Tipo</Label>
              <Select value={watch("oculomotor.smoothPursuit.type") || "sinusoidal"} onValueChange={(v) => setValue("oculomotor.smoothPursuit.type", v as any, { shouldDirty: true })}>
                <SelectTrigger className="ls-border ls-bg-input ls-text h-7 text-[10px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sinusoidal">Sinusoidal (normal)</SelectItem>
                  <SelectItem value="sacadico">Sacádico</SelectItem>
                  <SelectItem value="ataxico">Atáxico</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </details>

        <details className="rounded border ls-border p-2">
          <summary className="text-xs ls-text2 cursor-pointer">Optocinético</summary>
          <div className="grid gap-2 sm:grid-cols-2 mt-2">
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Ganancia derecha</Label><Input type="number" step="0.05" {...register("oculomotor.optokinetic.gainRight")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.9" /></div>
            <div className="space-y-1"><Label className="ls-text2 text-[10px]">Ganancia izquierda</Label><Input type="number" step="0.05" {...register("oculomotor.optokinetic.gainLeft")} className="h-7 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.9" /></div>
          </div>
        </details>
      </fieldset>


      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea {...register("observaciones")} className="min-h-12 ls-border ls-bg-input text-xs ls-text resize-none" />
      </fieldset>
    </form>
  );
}
