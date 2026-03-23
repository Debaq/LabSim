import { useModuleForm } from "@/modules/use-module-form";
import { tuningForkSchema, type TuningForkData, RINNE_RESULTS, WEBER_RESULTS, SCHWABACH_RESULTS } from "./schema";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Save, Music } from "lucide-react";

function Select({ value, onChange, options, placeholder }: {
  value: string | null | undefined;
  onChange: (v: string | null) => void;
  options: readonly string[];
  placeholder?: string;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="h-8 rounded border ls-border ls-bg-input px-2 text-xs ls-text capitalize"
    >
      <option value="">{placeholder ?? "—"}</option>
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

export default function TuningForkModule() {
  const { form, onSubmit } = useModuleForm<TuningForkData>(
    "tuningFork", tuningForkSchema, "Acumetría",
  );
  const { handleSubmit, watch, setValue } = form;
  const data = watch();

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Music className="h-5 w-5 text-amber-400" />
          <h2 className="text-lg font-semibold ls-text">Acumetría (Diapasones)</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Guardar</Button>
      </div>

      <p className="text-xs ls-text-muted">
        Resultados esperados de las pruebas con diapasón de 512 Hz.
        Estos datos se pueden derivar automáticamente desde el perfil audiológico en el módulo de Audiometría.
      </p>

      {/* Rinne */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Rinne</legend>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label className="text-xs ls-text-muted">Oído Derecho</Label>
            <Select
              value={data.rinne?.oidoDerecho}
              onChange={(v) => setValue("rinne.oidoDerecho", v as TuningForkData["rinne"]["oidoDerecho"], { shouldDirty: true })}
              options={RINNE_RESULTS}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text-muted">Oído Izquierdo</Label>
            <Select
              value={data.rinne?.oidoIzquierdo}
              onChange={(v) => setValue("rinne.oidoIzquierdo", v as TuningForkData["rinne"]["oidoIzquierdo"], { shouldDirty: true })}
              options={RINNE_RESULTS}
            />
          </div>
        </div>
      </fieldset>

      {/* Weber */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Weber</legend>
        <div className="space-y-1">
          <Label className="text-xs ls-text-muted">Lateralización</Label>
          <Select
            value={data.weber?.lateralizacion}
            onChange={(v) => setValue("weber.lateralizacion", v as TuningForkData["weber"]["lateralizacion"], { shouldDirty: true })}
            options={WEBER_RESULTS}
          />
        </div>
      </fieldset>

      {/* Schwabach */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Schwabach</legend>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label className="text-xs ls-text-muted">Oído Derecho</Label>
            <Select
              value={data.schwabach?.oidoDerecho}
              onChange={(v) => setValue("schwabach.oidoDerecho", v as TuningForkData["schwabach"]["oidoDerecho"], { shouldDirty: true })}
              options={SCHWABACH_RESULTS}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs ls-text-muted">Oído Izquierdo</Label>
            <Select
              value={data.schwabach?.oidoIzquierdo}
              onChange={(v) => setValue("schwabach.oidoIzquierdo", v as TuningForkData["schwabach"]["oidoIzquierdo"], { shouldDirty: true })}
              options={SCHWABACH_RESULTS}
            />
          </div>
        </div>
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea {...form.register("observaciones")} className="min-h-16 ls-border ls-bg-input ls-text" placeholder="Observaciones..." />
      </fieldset>
    </form>
  );
}
