import { useModuleForm } from "@/modules/use-module-form";
import { hearingAidsSchema, type HearingAidsData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Ear } from "lucide-react";

const FIELD_FREQS = ["250", "500", "1000", "2000", "3000", "4000", "6000", "8000"] as const;

export default function HearingAidsModule() {
  const { form, onSubmit } = useModuleForm<HearingAidsData>(
    "hearingAids", hearingAidsSchema, "Audifonos",
  );
  const { register, handleSubmit, setValue, watch } = form;

  const usoAnterior = watch("history.usoAnterior") ?? false;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Ear className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Audifonos</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* Historia de uso */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Historia de Uso de Audifonos
        </legend>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={usoAnterior}
            onCheckedChange={(v) => setValue("history.usoAnterior", !!v, { shouldDirty: true })}
          />
          <Label className="ls-text2">Uso anterior de audifonos</Label>
        </div>
        {usoAnterior && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label className="ls-text2">Marca</Label>
              <Input
                {...register("history.marca")}
                className="ls-border ls-bg-input ls-text"
                placeholder="Marca del audifono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="ls-text2">Modelo</Label>
              <Input
                {...register("history.modelo")}
                className="ls-border ls-bg-input ls-text"
                placeholder="Modelo"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="ls-text2">Anos de uso</Label>
              <Input
                type="number"
                min={0}
                {...register("history.anosUso")}
                className="ls-border ls-bg-input ls-text"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="ls-text2">Tipo</Label>
              <Select
                value={watch("history.tipoAnterior") ?? ""}
                onValueChange={(v) => setValue("history.tipoAnterior", v ?? "", { shouldDirty: true })}
              >
                <SelectTrigger className="ls-border ls-bg-input ls-text">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent>
                  {["Retroauricular (BTE)", "Intracanal (ITC)", "Intraauricular (ITE)", "RIC/RITE", "CIC", "Implante coclear"].map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="ls-text2">Satisfaccion (0-10)</Label>
              <Input
                type="number"
                min={0}
                max={10}
                {...register("history.satisfaccion")}
                className="ls-border ls-bg-input ls-text"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="ls-text2">Motivo de cambio</Label>
              <Input
                {...register("history.motivoCambio")}
                className="ls-border ls-bg-input ls-text"
                placeholder="Razon del cambio"
              />
            </div>
          </div>
        )}
      </fieldset>

      {/* Prescripcion */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Prescripcion
        </legend>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1.5">
            <Label className="ls-text2">Formula prescriptiva</Label>
            <Select
              value={watch("prescripcion.formula") ?? "NAL-NL2"}
              onValueChange={(v) => setValue("prescripcion.formula", v ?? "", { shouldDirty: true })}
            >
              <SelectTrigger className="ls-border ls-bg-input ls-text">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["NAL-NL2", "DSL v5", "NAL-NL1", "DSL v4", "Otra"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Tipo de audifono</Label>
            <Select
              value={watch("prescripcion.tipoAudifono") ?? ""}
              onValueChange={(v) => setValue("prescripcion.tipoAudifono", v ?? "", { shouldDirty: true })}
            >
              <SelectTrigger className="ls-border ls-bg-input ls-text">
                <SelectValue placeholder="Seleccionar" />
              </SelectTrigger>
              <SelectContent>
                {["Retroauricular (BTE)", "RIC/RITE", "Intracanal (ITC)", "CIC", "Intraauricular (ITE)"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Tipo de molde</Label>
            <Select
              value={watch("prescripcion.moldeTipo") ?? ""}
              onValueChange={(v) => setValue("prescripcion.moldeTipo", v ?? "", { shouldDirty: true })}
            >
              <SelectTrigger className="ls-border ls-bg-input ls-text">
                <SelectValue placeholder="Seleccionar" />
              </SelectTrigger>
              <SelectContent>
                {["Cerrado", "Abierto", "Domo abierto", "Domo cerrado", "Domo doble", "A medida"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Ventilacion</Label>
            <Select
              value={watch("prescripcion.ventilacion") ?? ""}
              onValueChange={(v) => setValue("prescripcion.ventilacion", v ?? "", { shouldDirty: true })}
            >
              <SelectTrigger className="ls-border ls-bg-input ls-text">
                <SelectValue placeholder="Seleccionar" />
              </SelectTrigger>
              <SelectContent>
                {["Sin ventilacion", "1 mm", "2 mm", "3 mm", "IROS", "Abierto"].map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={watch("prescripcion.oidoDerecho") ?? false}
              onCheckedChange={(v) => setValue("prescripcion.oidoDerecho", !!v, { shouldDirty: true })}
            />
            <Label className="text-red-400">Oido Derecho</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              checked={watch("prescripcion.oidoIzquierdo") ?? false}
              onCheckedChange={(v) => setValue("prescripcion.oidoIzquierdo", !!v, { shouldDirty: true })}
            />
            <Label className="text-blue-400">Oido Izquierdo</Label>
          </div>
        </div>
      </fieldset>

      {/* Audiometria en Campo Libre */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Audiometria en Campo Libre
        </legend>
        {(["sinAudifonos", "conAudifonos", "gananciaFuncional"] as const).map((section) => {
          const labels: Record<string, string> = {
            sinAudifonos: "Sin Audifonos",
            conAudifonos: "Con Audifonos",
            gananciaFuncional: "Ganancia Funcional",
          };
          return (
            <div key={section} className="space-y-2">
              <h4 className="text-sm font-medium ls-text2">{labels[section]}</h4>
              <div className="overflow-x-auto">
                <div className="flex gap-2">
                  {FIELD_FREQS.map((freq) => (
                    <div key={freq} className="flex flex-col items-center gap-1">
                      <span className="text-xs ls-text-muted">{freq}</span>
                      <Input
                        type="number"
                        value={watch(`fieldAudio.${section}.${freq}`) ?? ""}
                        onChange={(e) =>
                          setValue(
                            `fieldAudio.${section}.${freq}`,
                            e.target.value ? Number(e.target.value) : null,
                            { shouldDirty: true },
                          )
                        }
                        className="h-8 w-16 ls-border ls-bg-input ls-text text-center"
                        placeholder="dB"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </fieldset>

      {/* Prueba / Trial */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Prueba de Audifonos
        </legend>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1.5">
            <Label className="ls-text2">Marca</Label>
            <Input
              {...register("trial.marca")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Marca"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Modelo</Label>
            <Input
              {...register("trial.modelo")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Modelo"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Programa</Label>
            <Input
              {...register("trial.programa")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Programa activo"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Logo con audifonos (%)</Label>
            <Input
              type="number"
              min={0}
              max={100}
              {...register("trial.logoConAudifonos")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Logo sin audifonos (%)</Label>
            <Input
              type="number"
              min={0}
              max={100}
              {...register("trial.logoSinAudifonos")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Satisfaccion (0-10)</Label>
            <Input
              type="number"
              min={0}
              max={10}
              {...register("trial.satisfaccion")}
              className="ls-border ls-bg-input ls-text"
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label className="ls-text2">Observaciones de la prueba</Label>
          <Textarea
            {...register("trial.observaciones")}
            className="min-h-16 ls-border ls-bg-input ls-text"
            placeholder="Comentarios sobre la prueba de audifonos..."
          />
        </div>
      </fieldset>

      {/* Observaciones generales */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones Generales</legend>
        <Textarea
          {...register("observaciones")}
          className="min-h-20 ls-border ls-bg-input ls-text"
          placeholder="Observaciones generales sobre audifonos..."
        />
      </fieldset>
    </form>
  );
}
