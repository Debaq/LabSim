import { useModuleForm } from "@/modules/use-module-form";
import { oaeSchema, type OaeData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Waves } from "lucide-react";

const EARS = [
  { key: "oidoDerecho", label: "Oido Derecho", color: "text-red-400" },
  { key: "oidoIzquierdo", label: "Oido Izquierdo", color: "text-blue-400" },
] as const;

const RESULT_OPTIONS = ["Presente", "Ausente", "Parcial", "No evaluado"];

export default function OaeModule() {
  const { form, onSubmit } = useModuleForm<OaeData>(
    "oae", oaeSchema, "Emisiones Otoacusticas",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Waves className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Emisiones Otoacusticas (OAE)</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* TEOAE */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          TEOAE - Emisiones Evocadas Transitorias
        </legend>
        <div className="grid gap-6 lg:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-3">
              <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label className="text-white/70">Reproducibilidad (%)</Label>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    {...register(`teoae.${ear.key}.reproducibilidad`)}
                    className="border-white/10 bg-white/5 text-white"
                    placeholder="%"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-white/70">Resultado</Label>
                  <Select
                    value={watch(`teoae.${ear.key}.resultado`) || ""}
                    onValueChange={(v) => setValue(`teoae.${ear.key}.resultado`, v ?? "", { shouldDirty: true })}
                  >
                    <SelectTrigger className="border-white/10 bg-white/5 text-white">
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      {RESULT_OPTIONS.map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          ))}
        </div>
      </fieldset>

      {/* DPOAE */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">
          DPOAE - Productos de Distorsion
        </legend>
        <div className="grid gap-6 lg:grid-cols-2">
          {EARS.map((ear) => (
            <div key={ear.key} className="space-y-3">
              <h3 className={`text-sm font-medium ${ear.color}`}>{ear.label}</h3>
              <div className="space-y-1.5">
                <Label className="text-white/70">Resultado</Label>
                <Select
                  value={watch(`dpoae.${ear.key}.resultado`) || ""}
                  onValueChange={(v) => setValue(`dpoae.${ear.key}.resultado`, v ?? "", { shouldDirty: true })}
                >
                  <SelectTrigger className="border-white/10 bg-white/5 text-white">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {RESULT_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Observaciones */}
      <fieldset className="space-y-4 rounded-lg border border-white/5 bg-white/[0.02] p-4">
        <legend className="px-2 text-xs font-medium tracking-wider text-white/40 uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 border-white/10 bg-white/5 text-white"
          placeholder="Observaciones sobre las emisiones otoacusticas..."
        />
      </fieldset>
    </form>
  );
}
