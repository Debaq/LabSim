import { useModuleForm } from "@/modules/use-module-form";
import { logoaudiometrySchema, type LogoaudiometryData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, AudioLines } from "lucide-react";

const EARS = [
  { key: "oidoDerecho", label: "Oido Derecho", color: "text-red-400" },
  { key: "oidoIzquierdo", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

const UMD_ROWS = ["umd1", "umd2", "umd3"] as const;

export default function LogoaudiometryModule() {
  const { form, onSubmit } = useModuleForm<LogoaudiometryData>(
    "logoaudiometry", logoaudiometrySchema, "Logoaudiometria",
  );
  const { register, handleSubmit } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AudioLines className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Logoaudiometria</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* SDT */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          SDT - Umbral de Deteccion del Habla
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-1.5">
              <Label className={ear.color}>{ear.label} (dB)</Label>
              <Input
                type="number"
                min={0}
                max={100}
                {...register(`sdt.${ear.key}`)}
                className="ls-border ls-bg-input ls-text"
                placeholder="dB"
              />
            </div>
          ))}
        </div>
      </fieldset>

      {/* SRT */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          SRT - Umbral de Recepcion del Habla
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-1.5">
              <Label className={ear.color}>{ear.label} (dB)</Label>
              <Input
                type="number"
                min={0}
                max={100}
                {...register(`srt.${ear.key}`)}
                className="ls-border ls-bg-input ls-text"
                placeholder="dB"
              />
            </div>
          ))}
        </div>
      </fieldset>

      {/* UMD */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          UMD - Umbral Maximo de Discriminacion
        </legend>
        {EARS.map((ear) => (
          <div key={ear.key} className="space-y-3">
            <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="ls-text-muted">
                    <th className="px-2 py-1 text-left">Nivel</th>
                    <th className="px-2 py-1 text-left">Intensidad (dB)</th>
                    <th className="px-2 py-1 text-left">Porcentaje (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {UMD_ROWS.map((row, i) => (
                    <tr key={row}>
                      <td className="px-2 py-1 ls-text2">UMD {i + 1}</td>
                      <td className="px-2 py-1">
                        <Input
                          type="number"
                          min={0}
                          max={100}
                          {...register(`umd.${ear.key}.${row}.intensidad`)}
                          className="h-8 w-24 ls-border ls-bg-input ls-text"
                        />
                      </td>
                      <td className="px-2 py-1">
                        <Input
                          type="number"
                          min={0}
                          max={100}
                          {...register(`umd.${ear.key}.${row}.porcentaje`)}
                          className="h-8 w-24 ls-border ls-bg-input ls-text"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 ls-border ls-bg-input ls-text"
          placeholder="Observaciones sobre la logoaudiometria..."
        />
      </fieldset>
    </form>
  );
}
