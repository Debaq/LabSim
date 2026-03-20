import { useModuleForm } from "@/modules/use-module-form";
import { supraliminalSchema, type SupraliminalData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, BarChart3 } from "lucide-react";

const EARS = [
  { key: "od", label: "Oido Derecho", color: "text-red-400" },
  { key: "oi", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

const SISI_FREQS = ["500", "1000", "2000", "4000"] as const;
const CARHART_FREQS = ["500", "1000", "2000", "4000"] as const;
const LUSCHER_FREQS = ["500", "1000", "2000", "4000"] as const;
const FOWLER_FREQS = ["500", "1000", "2000", "4000"] as const;

export default function SupraliminalModule() {
  const { form, onSubmit } = useModuleForm<SupraliminalData>(
    "supraliminal", supraliminalSchema, "Supraliminal",
  );
  const { handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Pruebas Supraliminales</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* SISI */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          SISI - Short Increment Sensitivity Index
        </legend>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/40">
                <th className="px-2 py-1 text-left">Oido</th>
                {SISI_FREQS.map((f) => (
                  <th key={f} className="px-2 py-1 text-center">{f} Hz</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EARS.map((ear) => (
                <tr key={ear.key}>
                  <td className={`px-2 py-1 font-medium ${ear.color}`}>{ear.label}</td>
                  {SISI_FREQS.map((freq) => (
                    <td key={freq} className="px-2 py-1">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={watch(`sisi.${ear.key}.${freq}`) ?? ""}
                        onChange={(e) =>
                          setValue(`sisi.${ear.key}.${freq}`, e.target.value ? Number(e.target.value) : null, { shouldDirty: true })
                        }
                        className="h-8 w-20 border-white/10 bg-white/5 text-white text-center"
                        placeholder="%"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </fieldset>

      {/* Carhart (Tone Decay) */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Carhart - Tone Decay Test
        </legend>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/40">
                <th className="px-2 py-1 text-left">Oido</th>
                {CARHART_FREQS.map((f) => (
                  <th key={f} className="px-2 py-1 text-center">{f} Hz</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EARS.map((ear) => (
                <tr key={ear.key}>
                  <td className={`px-2 py-1 font-medium ${ear.color}`}>{ear.label}</td>
                  {CARHART_FREQS.map((freq) => (
                    <td key={freq} className="px-2 py-1">
                      <Input
                        type="number"
                        value={watch(`carhart.${ear.key}.${freq}`) ?? ""}
                        onChange={(e) =>
                          setValue(`carhart.${ear.key}.${freq}`, e.target.value ? Number(e.target.value) : null, { shouldDirty: true })
                        }
                        className="h-8 w-20 border-white/10 bg-white/5 text-white text-center"
                        placeholder="dB"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </fieldset>

      {/* Maspetiol */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Maspetiol
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-1.5">
              <Label className={ear.color}>{ear.label}</Label>
              <Select
                value={watch(`maspetiol.${ear.key}`) ?? ""}
                onValueChange={(v) => setValue(`maspetiol.${ear.key}`, v, { shouldDirty: true })}
              >
                <SelectTrigger className="border-white/10 bg-white/5 text-white">
                  <SelectValue placeholder="Seleccionar resultado" />
                </SelectTrigger>
                <SelectContent>
                  {["Positivo", "Negativo", "Dudoso", "No realizado"].map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Fowler (ABLB) */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Fowler - ABLB (Balance Binaural Alterno)
        </legend>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/40">
                <th className="px-2 py-1 text-left">Frecuencia</th>
                <th className="px-2 py-1 text-center">Resultado</th>
                <th className="px-2 py-1 text-center">Diferencia (dB)</th>
              </tr>
            </thead>
            <tbody>
              {FOWLER_FREQS.map((freq) => (
                <tr key={freq}>
                  <td className="px-2 py-1 text-white/60">{freq} Hz</td>
                  <td className="px-2 py-1">
                    <Select
                      value={watch(`fowler.${freq}.resultado`) ?? ""}
                      onValueChange={(v) => setValue(`fowler.${freq}.resultado`, v, { shouldDirty: true })}
                    >
                      <SelectTrigger className="h-8 border-white/10 bg-white/5 text-white">
                        <SelectValue placeholder="Seleccionar" />
                      </SelectTrigger>
                      <SelectContent>
                        {["Reclutamiento positivo", "Reclutamiento negativo", "Reclutamiento parcial", "No realizado"].map((s) => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="px-2 py-1">
                    <Input
                      type="number"
                      value={watch(`fowler.${freq}.diferencia`) ?? ""}
                      onChange={(e) =>
                        setValue(`fowler.${freq}.diferencia`, e.target.value ? Number(e.target.value) : null, { shouldDirty: true })
                      }
                      className="h-8 w-20 border-white/10 bg-white/5 text-white text-center"
                      placeholder="dB"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </fieldset>

      {/* Luscher */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Luscher - DLI (Umbral Diferencial de Intensidad)
        </legend>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-white/40">
                <th className="px-2 py-1 text-left">Oido</th>
                {LUSCHER_FREQS.map((f) => (
                  <th key={f} className="px-2 py-1 text-center">{f} Hz</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EARS.map((ear) => (
                <tr key={ear.key}>
                  <td className={`px-2 py-1 font-medium ${ear.color}`}>{ear.label}</td>
                  {LUSCHER_FREQS.map((freq) => (
                    <td key={freq} className="px-2 py-1">
                      <Input
                        type="number"
                        step="0.1"
                        value={watch(`luscher.${ear.key}.${freq}`) ?? ""}
                        onChange={(e) =>
                          setValue(`luscher.${ear.key}.${freq}`, e.target.value ? Number(e.target.value) : null, { shouldDirty: true })
                        }
                        className="h-8 w-20 border-white/10 bg-white/5 text-white text-center"
                        placeholder="dB"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">Observaciones</legend>
        <Textarea
          {...form.register("observaciones")}
          className="min-h-20 border-white/10 bg-white/5 text-white"
          placeholder="Observaciones sobre las pruebas supraliminales..."
        />
      </fieldset>
    </form>
  );
}
