import { useModuleForm } from "@/modules/use-module-form";
import { anamnesisSchema, type AnamnesisData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Save, ClipboardList } from "lucide-react";

const CONDITIONS = [
  "Diabetes", "Hipertensión", "Cardiopatía", "Enfermedad renal",
  "Ototóxicos", "Cirugía otológica", "TEC", "Meningitis",
  "Otitis crónica", "Hipotiroidismo", "Artritis reumatoide", "Otro",
];

export default function AnamnesisModule() {
  const { form, onSubmit } = useModuleForm<AnamnesisData>(
    "clinicalHistory", anamnesisSchema, "Anamnesis",
  );
  const { register, handleSubmit, watch, setValue, formState: { errors } } = form;
  const tinnitus = watch("tinnitus.presencia");
  const condiciones = watch("antecedentesMorbidos.condiciones") ?? [];

  const toggleCondition = (c: string) => {
    const current = condiciones;
    const next = current.includes(c) ? current.filter((x: string) => x !== c) : [...current, c];
    setValue("antecedentesMorbidos.condiciones", next, { shouldDirty: true });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Anamnesis</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />Guardar
        </Button>
      </div>

      {/* Motivo de consulta */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Motivo de Consulta</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="ls-text2">Síntoma Principal *</Label>
            <Select value={watch("motivoConsulta.sintomaPrincipal") ?? ""} onValueChange={(v) => setValue("motivoConsulta.sintomaPrincipal", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
              <SelectContent>
                {["Hipoacusia", "Tinnitus", "Vértigo", "Otalgia", "Otorrea", "Plenitud aural", "Control", "Otro"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
            {errors.motivoConsulta?.sintomaPrincipal && <p className="text-xs text-red-400">{errors.motivoConsulta.sintomaPrincipal.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Severidad</Label>
            <Select value={watch("motivoConsulta.severidad") ?? ""} onValueChange={(v) => setValue("motivoConsulta.severidad", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
              <SelectContent>
                {["Leve", "Moderado", "Severo"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="ls-text2">Tiempo de Evolución</Label>
            <Input {...register("motivoConsulta.tiempoEvolucion")} className="ls-border ls-bg-input ls-text" placeholder="ej: 6 meses" />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label className="ls-text2">Descripción</Label>
          <Textarea {...register("motivoConsulta.descripcion")} className="min-h-16 ls-border ls-bg-input ls-text" placeholder="Descripción del motivo de consulta..." />
        </div>
      </fieldset>

      {/* Historia */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Valoración del Paciente</legend>
        <div className="flex flex-wrap gap-6">
          {(["cooperativo", "orientado", "confiable", "acompanado"] as const).map((field) => (
            <div key={field} className="flex items-center gap-2">
              <Checkbox id={field} checked={watch(`historiaLibre.${field}`) ?? false} onCheckedChange={(v) => setValue(`historiaLibre.${field}`, !!v, { shouldDirty: true })} />
              <Label htmlFor={field} className="ls-text2 capitalize">{field === "acompanado" ? "Acompañado" : field}</Label>
            </div>
          ))}
        </div>
        <div className="space-y-1.5">
          <Label className="ls-text2">Observaciones</Label>
          <Textarea {...register("historiaLibre.observaciones")} className="min-h-16 ls-border ls-bg-input ls-text" />
        </div>
      </fieldset>

      {/* Antecedentes */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Antecedentes Mórbidos</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {CONDITIONS.map((c) => (
            <div key={c} className="flex items-center gap-2">
              <Checkbox id={`cond-${c}`} checked={condiciones.includes(c)} onCheckedChange={() => toggleCondition(c)} />
              <Label htmlFor={`cond-${c}`} className="text-xs ls-text2">{c}</Label>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Exposición a ruido */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Exposición a Ruido</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="ls-text2">Ocupacional</Label>
            <Select value={watch("exposicionRuido.ocupacional") ?? ""} onValueChange={(v) => setValue("exposicionRuido.ocupacional", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
              <SelectContent>
                {["No", "Sí - Leve", "Sí - Moderado", "Sí - Severo"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Años de exposición</Label>
            <Input type="number" min={0} max={80} {...register("exposicionRuido.anosExposicion")} className="ls-border ls-bg-input ls-text" />
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Protección auditiva</Label>
            <Select value={watch("exposicionRuido.proteccionAuditiva") ?? ""} onValueChange={(v) => setValue("exposicionRuido.proteccionAuditiva", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
              <SelectContent>
                {["No usa", "Ocasional", "Regular", "Siempre"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Recreacional</Label>
            <Select value={watch("exposicionRuido.recreacional") ?? ""} onValueChange={(v) => setValue("exposicionRuido.recreacional", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
              <SelectContent>
                {["No", "Música fuerte", "Conciertos", "Caza/Tiro", "Herramientas", "Otro"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
      </fieldset>

      {/* Tinnitus */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Tinnitus</legend>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label className="ls-text2">Presencia</Label>
            <Select value={tinnitus ?? "ausente"} onValueChange={(v) => setValue("tinnitus.presencia", v ?? "", { shouldDirty: true })}>
              <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ausente">Ausente</SelectItem>
                <SelectItem value="presente">Presente</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {tinnitus === "presente" && (
            <>
              <div className="space-y-1.5">
                <Label className="ls-text2">Lateralidad</Label>
                <Select value={watch("tinnitus.lateralidad") ?? ""} onValueChange={(v) => setValue("tinnitus.lateralidad", v ?? "", { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                  <SelectContent>
                    {["Bilateral", "Oído derecho", "Oído izquierdo", "Central"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="ls-text2">Tipo</Label>
                <Select value={watch("tinnitus.tipo") ?? ""} onValueChange={(v) => setValue("tinnitus.tipo", v ?? "", { shouldDirty: true })}>
                  <SelectTrigger className="ls-border ls-bg-input ls-text"><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                  <SelectContent>
                    {["Tonal agudo", "Tonal grave", "Ruido blanco", "Pulsátil", "Intermitente", "Otro"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </>
          )}
        </div>
        {tinnitus === "presente" && (
          <>
            <div className="space-y-1.5">
              <Label className="ls-text2">Severidad (0-10): {watch("tinnitus.severidad") ?? 0}</Label>
              <input type="range" min={0} max={10} step={1} {...register("tinnitus.severidad")} className="w-full accent-blue-500" />
            </div>
            <div className="flex flex-wrap gap-4">
              {([
                ["constante", "Constante"],
                ["intermitente", "Intermitente"],
                ["empeoraNoche", "Empeora de noche"],
                ["afectaSueno", "Afecta sueño"],
                ["afectaConcentracion", "Afecta concentración"],
              ] as const).map(([field, label]) => (
                <div key={field} className="flex items-center gap-2">
                  <Checkbox checked={watch(`tinnitus.${field}`) ?? false} onCheckedChange={(v) => setValue(`tinnitus.${field}`, !!v, { shouldDirty: true })} />
                  <Label className="text-xs ls-text2">{label}</Label>
                </div>
              ))}
            </div>
          </>
        )}
      </fieldset>
    </form>
  );
}
