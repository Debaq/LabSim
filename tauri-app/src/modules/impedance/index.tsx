import { useModuleForm } from "@/modules/use-module-form";
import { impedanceSchema, type ImpedanceData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Save, Activity, Zap } from "lucide-react";

const REFLEX_FREQS = [500, 1000, 2000, 4000] as const;

function EarConfig({
  prefix,
  label,
  register,
  setValue,
  watch,
}: {
  prefix: "oidoDerecho" | "oidoIzquierdo";
  label: string;
  register: any;
  setValue: any;
  watch: any;
}) {
  return (
    <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
      <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">{label}</legend>

      {/* Timpanometría */}
      <div className="space-y-1.5">
        <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Timpanometría</Label>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Compliance pico (ml)</Label>
            <Input {...register(`${prefix}.compliancePeak`)} type="number" step="0.1" placeholder="0.8" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Presión oído medio (daPa)</Label>
            <Input {...register(`${prefix}.middleEarPressure`)} type="number" placeholder="0" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Volumen CAE (ml)</Label>
            <Input {...register(`${prefix}.earCanalVolume`)} type="number" step="0.1" placeholder="1.1" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Ancho curva (daPa)</Label>
            <Input {...register(`${prefix}.tympWidth`)} type="number" placeholder="100" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <Checkbox
              checked={watch(`${prefix}.perforated`) ?? false}
              onCheckedChange={(v) => setValue(`${prefix}.perforated`, !!v, { shouldDirty: true })}
            />
            <Label className="ls-text2 text-xs">Perforación timpánica</Label>
          </div>
        </div>
      </div>

      {/* Reflejos */}
      <div className="space-y-1.5">
        <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Reflejos acústicos (umbral dB HL, vacío = ausente)</Label>
        <div className="grid grid-cols-5 gap-1 text-[10px]">
          <div className="ls-text-muted font-medium">Hz</div>
          {REFLEX_FREQS.map((f) => <div key={f} className="text-center ls-text-muted font-medium">{f}</div>)}
          <div className="ls-text2">Ipsi</div>
          {REFLEX_FREQS.map((f) => <Input key={`i${f}`} {...register(`${prefix}.reflexIpsi${f}`)} type="number" placeholder="—" className="h-6 text-center ls-border ls-bg-input text-[10px] ls-text" />)}
          <div className="ls-text2">Contra</div>
          {REFLEX_FREQS.map((f) => <Input key={`c${f}`} {...register(`${prefix}.reflexContra${f}`)} type="number" placeholder="—" className="h-6 text-center ls-border ls-bg-input text-[10px] ls-text" />)}
        </div>
      </div>

      {/* Deterioro */}
      <div className="space-y-1.5">
        <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Deterioro del reflejo (% decaimiento en 10s)</Label>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">500 Hz</Label>
            <Input {...register(`${prefix}.reflexDecay500`)} type="number" placeholder="10" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">1000 Hz</Label>
            <Input {...register(`${prefix}.reflexDecay1000`)} type="number" placeholder="15" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
        </div>
      </div>

      {/* Función tubárica */}
      <div className="space-y-1.5">
        <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Función tubárica (desplazamiento daPa)</Label>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Toynbee</Label>
            <Input {...register(`${prefix}.toynbeeShift`)} type="number" placeholder="-15" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Valsalva</Label>
            <Input {...register(`${prefix}.valsalvaShift`)} type="number" placeholder="15" className="ls-border ls-bg-input text-xs ls-text" />
          </div>
        </div>
      </div>
    </fieldset>
  );
}

export default function ImpedanceModule() {
  const { form, onSubmit } = useModuleForm<ImpedanceData>(
    "impedance", impedanceSchema, "Impedanciometría",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-semibold ls-text">Impedanciometría — Datos Fisiológicos</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />
          Guardar
        </Button>
      </div>

      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-400/80">
        <Zap className="inline h-3.5 w-3.5 mr-1" />
        Configure los parámetros fisiológicos reales del oído. El simulador generará las curvas automáticamente.
      </div>

      <EarConfig prefix="oidoDerecho" label="Oído Derecho" register={register} setValue={setValue} watch={watch} />
      <EarConfig prefix="oidoIzquierdo" label="Oído Izquierdo" register={register} setValue={setValue} watch={watch} />

      <div className="space-y-1.5">
        <Label className="ls-text2 text-xs">Varianza natural</Label>
        <Input {...register("naturalVariance")} type="number" step="0.05" min="0" max="1" placeholder="0.05" className="ls-border ls-bg-input text-xs ls-text max-w-[120px]" />
        <p className="text-[10px] ls-text-muted">0 = mediciones perfectas, 1 = mucha variación</p>
      </div>

      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea {...register("observaciones")} rows={3} className="ls-border ls-bg-input text-xs ls-text resize-none" />
      </fieldset>
    </form>
  );
}
