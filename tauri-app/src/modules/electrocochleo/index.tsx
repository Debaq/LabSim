import { useModuleForm } from "@/modules/use-module-form";
import { electrocochleoSchema, type ElectrocochleoData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Save, Zap } from "lucide-react";

const EARS = [
  { key: "oidoDerecho", label: "Oido Derecho", color: "text-red-400" },
  { key: "oidoIzquierdo", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

export default function ElectrocochleoModule() {
  const { form, onSubmit } = useModuleForm<ElectrocochleoData>(
    "electrocochleo", electrocochleoSchema, "Electrococleografia",
  );
  const { register, handleSubmit, setValue, watch } = form;

  const spOD = watch("sp.oidoDerecho") ?? 0;
  const apOD = watch("ap.oidoDerecho") ?? 0;
  const spOI = watch("sp.oidoIzquierdo") ?? 0;
  const apOI = watch("ap.oidoIzquierdo") ?? 0;

  const ratioOD = apOD !== 0 ? (spOD / apOD).toFixed(2) : "—";
  const ratioOI = apOI !== 0 ? (spOI / apOI).toFixed(2) : "—";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Electrococleografia</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* SP y AP por oido */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Potenciales SP / AP
        </legend>
        <div className="grid gap-6 lg:grid-cols-2">
          {EARS.map((ear) => {
            const ratio = ear.key === "oidoDerecho" ? ratioOD : ratioOI;
            return (
              <div key={ear.key} className="space-y-3">
                <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label className="ls-text2">SP (uV)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      {...register(`sp.${ear.key}`)}
                      className="ls-border ls-bg-input ls-text"
                      placeholder="uV"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="ls-text2">AP (uV)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      {...register(`ap.${ear.key}`)}
                      className="ls-border ls-bg-input ls-text"
                      placeholder="uV"
                    />
                  </div>
                </div>
                <div className="rounded-md ls-bg-input px-3 py-2">
                  <span className="text-sm ls-text2">Relacion SP/AP: </span>
                  <span className="text-sm font-medium ls-text">{ratio}</span>
                  {typeof ratio === "string" && ratio !== "—" && Number(ratio) > 0.4 && (
                    <span className="ml-2 text-xs text-yellow-400">(elevado &gt; 0.4)</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </fieldset>

      {/* Parametros */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Parametros de Registro
        </legend>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1.5">
            <Label className="ls-text2">Frecuencia Muestreo (Hz)</Label>
            <Input
              type="number"
              {...register("params.fs")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Ventana (ms)</Label>
            <Input
              type="number"
              step="0.1"
              {...register("params.windowMs")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Suavizado</Label>
            <Input
              type="number"
              min={0}
              {...register("params.smooth")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
          <div className="flex items-end gap-2 pb-1">
            <Checkbox
              checked={watch("params.invert") ?? false}
              onCheckedChange={(v) => setValue("params.invert", !!v, { shouldDirty: true })}
            />
            <Label className="ls-text2">Invertir polaridad</Label>
          </div>
        </div>
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 ls-border ls-bg-input ls-text"
          placeholder="Observaciones sobre la electrococleografia..."
        />
      </fieldset>
    </form>
  );
}
