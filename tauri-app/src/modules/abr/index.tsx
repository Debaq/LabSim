import { useModuleForm } from "@/modules/use-module-form";
import { abrSchema, type AbrData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, BrainCircuit } from "lucide-react";

const EARS = [
  { key: "oidoDerecho", label: "Oido Derecho", color: "text-red-400" },
  { key: "oidoIzquierdo", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

const WAVES = [
  { key: "ondaI", label: "Onda I" },
  { key: "ondaII", label: "Onda II" },
  { key: "ondaIII", label: "Onda III" },
  { key: "ondaIV", label: "Onda IV" },
  { key: "ondaV", label: "Onda V" },
] as const;

const INTENSITY_LEVELS = [
  { key: "db80", label: "80 dB" },
  { key: "final", label: "Umbral" },
] as const;

const STIMULUS_TYPES = [
  { value: "click", label: "Click" },
  { value: "toneBurst", label: "Tone Burst" },
  { value: "chirp", label: "Chirp" },
];

const TONE_BURST_FREQS = [
  { value: "500", label: "500 Hz" },
  { value: "1k", label: "1000 Hz" },
  { value: "2k", label: "2000 Hz" },
  { value: "4k", label: "4000 Hz" },
];

export default function AbrModule() {
  const { form, onSubmit } = useModuleForm<AbrData>(
    "abr", abrSchema, "Potenciales Evocados (ABR)",
  );
  const { register, handleSubmit, setValue, watch } = form;

  const stimulusActivo = watch("stimulusActivo") ?? "click";
  const toneBurstActivo = watch("toneBurstActivo") ?? "1k";

  // Determinar la clave de datos activa segun el estimulo
  const getDataPath = () => {
    if (stimulusActivo === "click") return "click";
    if (stimulusActivo === "chirp") return "chirp";
    return `toneBurst.${toneBurstActivo}`;
  };

  const dataPath = getDataPath();

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Potenciales Evocados Auditivos (ABR)</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* Selector de Estimulo */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Tipo de Estimulo
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="ls-text2">Estimulo</Label>
            <Select
              value={stimulusActivo}
              onValueChange={(v) => setValue("stimulusActivo", v ?? "", { shouldDirty: true })}
            >
              <SelectTrigger className="ls-border ls-bg-input ls-text">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STIMULUS_TYPES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {stimulusActivo === "toneBurst" && (
            <div className="space-y-1.5">
              <Label className="ls-text2">Frecuencia Tone Burst</Label>
              <Select
                value={toneBurstActivo}
                onValueChange={(v) => setValue("toneBurstActivo", v ?? "", { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TONE_BURST_FREQS.map((f) => (
                    <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </fieldset>

      {/* Tabla de Ondas por oido e intensidad */}
      {EARS.map((ear) => (
        <fieldset key={ear.key} className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
          <legend className={`px-2 text-xs font-medium tracking-wider uppercase ${ear.color}`}>
            {ear.label}
          </legend>
          {INTENSITY_LEVELS.map((level) => (
            <div key={level.key} className="space-y-3">
              <h4 className="text-sm font-medium ls-text2">{level.label}</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="ls-text-muted">
                      <th className="px-2 py-1 text-left">Onda</th>
                      <th className="px-2 py-1 text-center">Presente</th>
                      <th className="px-2 py-1 text-center">Latencia (ms)</th>
                      <th className="px-2 py-1 text-center">Amplitud (uV)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {WAVES.map((wave) => {
                      const basePath = `${dataPath}.${ear.key}.${level.key}.${wave.key}` as const;
                      return (
                        <tr key={wave.key}>
                          <td className="px-2 py-1 ls-text2">{wave.label}</td>
                          <td className="px-2 py-1 text-center">
                            <div className="flex justify-center">
                              <Checkbox
                                checked={watch(`${basePath}.presente` as any) ?? false}
                                onCheckedChange={(v) => setValue(`${basePath}.presente` as any, !!v, { shouldDirty: true })}
                              />
                            </div>
                          </td>
                          <td className="px-2 py-1">
                            <Input
                              type="number"
                              step="0.01"
                              min={0}
                              max={15}
                              {...register(`${basePath}.latencia` as any)}
                              className="h-8 w-20 ls-border ls-bg-input ls-text text-center mx-auto"
                              placeholder="ms"
                            />
                          </td>
                          <td className="px-2 py-1">
                            <Input
                              type="number"
                              step="0.01"
                              min={0}
                              max={5}
                              {...register(`${basePath}.amplitud` as any)}
                              className="h-8 w-20 ls-border ls-bg-input ls-text text-center mx-auto"
                              placeholder="uV"
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </fieldset>
      ))}

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 ls-border ls-bg-input ls-text"
          placeholder="Observaciones sobre los potenciales evocados..."
        />
      </fieldset>
    </form>
  );
}
