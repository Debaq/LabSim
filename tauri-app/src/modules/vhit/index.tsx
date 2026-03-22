import { useModuleForm } from "@/modules/use-module-form";
import { vhitSchema, type VHITData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Save, RotateCcw } from "lucide-react";

const CANALS = [
  { key: "lateralRight", label: "Lateral Derecho", pair: "Laterales" },
  { key: "lateralLeft", label: "Lateral Izquierdo", pair: "Laterales" },
  { key: "anteriorRight", label: "Anterior Derecho", pair: "LARP" },
  { key: "posteriorLeft", label: "Posterior Izquierdo", pair: "LARP" },
  { key: "anteriorLeft", label: "Anterior Izquierdo", pair: "RALP" },
  { key: "posteriorRight", label: "Posterior Derecho", pair: "RALP" },
] as const;

export default function VHITModule() {
  const { form, onSubmit } = useModuleForm<VHITData>("vhit", vhitSchema, "vHIT");
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <RotateCcw className="h-5 w-5 text-orange-400" />
          <h2 className="text-lg font-semibold ls-text">vHIT — Datos por Canal Semicircular</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Guardar</Button>
      </div>

      {CANALS.map((c) => (
        <fieldset key={c.key} className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
          <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
            {c.label} <span className="ls-text-muted">({c.pair})</span>
          </legend>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="space-y-1">
              <Label className="ls-text2 text-xs">Ganancia VOR</Label>
              <Input type="number" step="0.05" min="0" max="1.5" {...register(`datos.${c.key}.gain`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="1.0" />
              <p className="text-[9px] ls-text-muted">Normal: 0.8-1.2</p>
            </div>
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-2">
                <Checkbox checked={watch(`datos.${c.key}.hasOvertSaccades`) ?? false} onCheckedChange={(v) => setValue(`datos.${c.key}.hasOvertSaccades`, !!v, { shouldDirty: true })} />
                <Label className="ls-text2 text-xs">Sacadas overt</Label>
              </div>
              {watch(`datos.${c.key}.hasOvertSaccades`) && (
                <div className="space-y-1 pl-6">
                  <Label className="ls-text2 text-[10px]">Tasa (0-1)</Label>
                  <Input type="number" step="0.1" min="0" max="1" {...register(`datos.${c.key}.overtRate`)} className="h-6 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.7" />
                </div>
              )}
            </div>
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-2">
                <Checkbox checked={watch(`datos.${c.key}.hasCovertSaccades`) ?? false} onCheckedChange={(v) => setValue(`datos.${c.key}.hasCovertSaccades`, !!v, { shouldDirty: true })} />
                <Label className="ls-text2 text-xs">Sacadas covert</Label>
              </div>
              {watch(`datos.${c.key}.hasCovertSaccades`) && (
                <div className="space-y-1 pl-6">
                  <Label className="ls-text2 text-[10px]">Tasa (0-1)</Label>
                  <Input type="number" step="0.1" min="0" max="1" {...register(`datos.${c.key}.covertRate`)} className="h-6 ls-border ls-bg-input text-[10px] ls-text" placeholder="0.5" />
                </div>
              )}
            </div>
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
