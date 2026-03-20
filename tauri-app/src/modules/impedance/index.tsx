import { useModuleForm } from "@/modules/use-module-form";
import { impedanceSchema, type ImpedanceData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, Activity } from "lucide-react";

const EARS = [
  { key: "oidoDerecho", label: "Oido Derecho", color: "text-red-400" },
  { key: "oidoIzquierdo", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

const REFLEX_FREQS = ["500", "1000", "2000", "4000", "WN"] as const;
const REFLEX_FREQ_LABELS: Record<string, string> = {
  "500": "500 Hz",
  "1000": "1000 Hz",
  "2000": "2000 Hz",
  "4000": "4000 Hz",
  "WN": "Ruido Blanco",
};

export default function ImpedanceModule() {
  const { form, onSubmit } = useModuleForm<ImpedanceData>(
    "impedance", impedanceSchema, "Impedanciometria",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Impedanciometria</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* Timpanometria */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Timpanometria
        </legend>
        <div className="grid gap-6 lg:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-3">
              <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label className="text-white/70">Compliance Max. (ml)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min={0}
                    max={10}
                    {...register(`timpanometria.${ear.key}.complianceMaxima`)}
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-white/70">Presion (daPa)</Label>
                  <Input
                    type="number"
                    min={-400}
                    max={200}
                    {...register(`timpanometria.${ear.key}.presion`)}
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-white/70">Volumen EAC (ml)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min={0}
                    max={10}
                    {...register(`timpanometria.${ear.key}.volumenEac`)}
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-white/70">Gradiente</Label>
                  <Input
                    type="number"
                    step="0.1"
                    {...register(`timpanometria.${ear.key}.gradiente`)}
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Reflejos Acusticos */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          Reflejos Acusticos
        </legend>
        {EARS.map((ear) => (
          <div key={ear.key} className="space-y-3">
            <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-white/40">
                    <th className="px-2 py-1 text-left">Via</th>
                    {REFLEX_FREQS.map((f) => (
                      <th key={f} className="px-2 py-1 text-center">{REFLEX_FREQ_LABELS[f]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(["ipsi", "contra"] as const).map((via) => (
                    <tr key={via}>
                      <td className="px-2 py-1 text-white/60 capitalize">{via === "ipsi" ? "Ipsilateral" : "Contralateral"}</td>
                      {REFLEX_FREQS.map((freq) => (
                        <td key={freq} className="px-2 py-1">
                          <Input
                            type="text"
                            value={watch(`reflejosAcusticos.${ear.key}.${via}.${freq}`) ?? ""}
                            onChange={(e) =>
                              setValue(
                                `reflejosAcusticos.${ear.key}.${via}.${freq}`,
                                e.target.value,
                                { shouldDirty: true },
                              )
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
          </div>
        ))}
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 border-white/10 bg-white/5 text-white"
          placeholder="Observaciones sobre la impedanciometria..."
        />
      </fieldset>
    </form>
  );
}
