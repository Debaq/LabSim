import { useModuleForm } from "@/modules/use-module-form";
import { scheimpflugSchema, CORNEAL_PATHOLOGIES, LENS_STATUS, SEVERITIES, type ScheimpflugData } from "./schema";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Scan } from "lucide-react";

const EYES = [
  { key: "ojoDerecho", label: "Ojo Derecho (OD)", color: "text-red-400" },
  { key: "ojoIzquierdo", label: "Ojo Izquierdo (OI)", color: "text-blue-400" },
] as const;

const PATHO_LABELS: Record<string, string> = {
  normal: "Normal", keratoconus: "Queratocono", pellucid: "Pelúcida",
  "post-lasik": "Post-LASIK", "post-prk": "Post-PRK",
  "fuchs-dystrophy": "Distrofia de Fuchs", "corneal-edema": "Edema Corneal", scarring: "Cicatriz",
};
const LENS_LABELS: Record<string, string> = {
  clear: "Transparente", "cataract-nuclear": "Catarata Nuclear", "cataract-cortical": "Catarata Cortical",
  "cataract-subcapsular": "Catarata Subcapsular", pseudophakic: "Pseudofáquico (IOL)", aphakic: "Afáquico",
};
const SEV_LABELS: Record<string, string> = { leve: "Leve", moderado: "Moderado", severo: "Severo" };

export default function ScheimpflugModule() {
  const { form, onSubmit } = useModuleForm<ScheimpflugData>("scheimpflug", scheimpflugSchema, "Scheimpflug");
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scan className="h-5 w-5 text-teal-400" />
          <h2 className="text-lg font-semibold ls-text">Tomógrafo Scheimpflug — Datos Fisiológicos</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Guardar</Button>
      </div>

      {EYES.map((eye) => (
        <fieldset key={eye.key} className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
          <legend className={`px-2 text-sm font-medium ${eye.color}`}>{eye.label}</legend>

          {/* Córnea */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Córnea</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Patología</Label>
                <Select value={watch(`${eye.key}.cornealPathology`) || "normal"} onValueChange={(v) => setValue(`${eye.key}.cornealPathology`, v as any, { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>{CORNEAL_PATHOLOGIES.map((p) => <SelectItem key={p} value={p}>{PATHO_LABELS[p]}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Severidad</Label>
                <Select value={watch(`${eye.key}.severidad`) || "moderado"} onValueChange={(v) => setValue(`${eye.key}.severidad`, v as any, { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>{SEVERITIES.map((s) => <SelectItem key={s} value={s}>{SEV_LABELS[s]}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Queratometría */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Queratometría (opcional)</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">K1 anterior (D)</Label>
                <Input type="number" step="0.25" {...register(`${eye.key}.k1Anterior`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="43.00" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">K2 anterior (D)</Label>
                <Input type="number" step="0.25" {...register(`${eye.key}.k2Anterior`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="44.00" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Eje (°)</Label>
                <Input type="number" min="0" max="180" {...register(`${eye.key}.kAxis`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="90" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">K1 posterior (D)</Label>
                <Input type="number" step="0.1" {...register(`${eye.key}.k1Posterior`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="-6.4" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">CCT (µm)</Label>
                <Input type="number" {...register(`${eye.key}.cct`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="545" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Punto más delgado (µm)</Label>
                <Input type="number" {...register(`${eye.key}.thinnestPoint`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="530" />
              </div>
            </div>
          </div>

          {/* Cámara anterior */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Cámara anterior</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">ACD (mm)</Label>
                <Input type="number" step="0.1" {...register(`${eye.key}.acd`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="3.2" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Ángulo iridocorneal (°)</Label>
                <Input type="number" {...register(`${eye.key}.iridocornealAngle`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="35" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Volumen CA (mm³)</Label>
                <Input type="number" {...register(`${eye.key}.acVolume`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="160" />
              </div>
            </div>
          </div>

          {/* Cristalino */}
          <div className="space-y-1.5">
            <Label className="text-[10px] ls-text-muted uppercase tracking-wider">Cristalino</Label>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Estado</Label>
                <Select value={watch(`${eye.key}.lensStatus`) || "clear"} onValueChange={(v) => setValue(`${eye.key}.lensStatus`, v as any, { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
                  <SelectContent>{LENS_STATUS.map((l) => <SelectItem key={l} value={l}>{LENS_LABELS[l]}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Densidad (%)</Label>
                <Input type="number" min="0" max="100" {...register(`${eye.key}.lensDensity`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="15" />
              </div>
              <div className="space-y-1">
                <Label className="ls-text2 text-xs">Espesor (mm)</Label>
                <Input type="number" step="0.1" {...register(`${eye.key}.lensThickness`)} className="ls-border ls-bg-input text-xs ls-text" placeholder="4.0" />
              </div>
            </div>
          </div>


          <div className="space-y-1">
            <Label className="ls-text2 text-xs">Notas</Label>
            <Textarea {...register(`${eye.key}.notas`)} className="min-h-12 ls-border ls-bg-input text-xs ls-text resize-none" />
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
