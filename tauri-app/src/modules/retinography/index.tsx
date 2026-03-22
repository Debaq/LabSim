import { useModuleForm } from "@/modules/use-module-form";
import { retinographySchema, type RetinographyData } from "./schema";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, Eye } from "lucide-react";

const PATHOLOGIES = [
  { value: "normal", label: "Normal" },
  { value: "retinopatia-diabetica-npdr", label: "Retinopatía diabética NPDR" },
  { value: "retinopatia-diabetica-pdr", label: "Retinopatía diabética PDR" },
  { value: "degeneracion-macular-seca", label: "DMAE seca" },
  { value: "degeneracion-macular-humeda", label: "DMAE húmeda" },
  { value: "desprendimiento-retina", label: "Desprendimiento de retina" },
  { value: "oclusion-vena-central", label: "Oclusión vena central" },
  { value: "oclusion-arteria-central", label: "Oclusión arteria central" },
  { value: "papilledema", label: "Papiledema" },
  { value: "glaucoma-excavacion", label: "Excavación glaucomatosa" },
  { value: "nevus-coroideo", label: "Nevus coroideo" },
  { value: "membrana-epirretinal", label: "Membrana epirretinal" },
  { value: "agujero-macular", label: "Agujero macular" },
];

const SEVERITIES = [
  { value: "leve", label: "Leve" },
  { value: "moderado", label: "Moderado" },
  { value: "severo", label: "Severo" },
];

function EyeConfig({
  label,
  prefix,
  register,
  setValue,
  watch,
}: {
  label: string;
  prefix: "ojoDerecho" | "ojoIzquierdo";
  register: any;
  setValue: any;
  watch: any;
}) {
  const currentPathology = watch(`${prefix}.patologia`);
  const currentSeverity = watch(`${prefix}.severidad`);

  return (
    <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
      <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">{label}</legend>

      <div className="space-y-1.5">
        <Label className="ls-text2 text-xs">Patología</Label>
        <div className="flex flex-wrap gap-1">
          {PATHOLOGIES.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => setValue(`${prefix}.patologia`, p.value, { shouldDirty: true })}
              className={`rounded-md px-2 py-1 text-[10px] transition ${
                currentPathology === p.value
                  ? "bg-red-500/15 text-red-400"
                  : "ls-bg-input ls-text-muted hover:ls-text2"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {currentPathology && currentPathology !== "normal" && (
        <div className="space-y-1.5">
          <Label className="ls-text2 text-xs">Severidad</Label>
          <div className="flex gap-1.5">
            {SEVERITIES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setValue(`${prefix}.severidad`, s.value, { shouldDirty: true })}
                className={`rounded-md px-3 py-1 text-xs transition ${
                  currentSeverity === s.value
                    ? "bg-red-500/15 text-red-400"
                    : "ls-bg-input ls-text-muted"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-1.5">
        <Label className="ls-text2 text-xs">Notas</Label>
        <Textarea
          {...register(`${prefix}.notas`)}
          rows={2}
          className="ls-border ls-bg-input text-xs ls-text resize-none"
          placeholder="Hallazgos específicos..."
        />
      </div>
    </fieldset>
  );
}

export default function RetinographyModule() {
  const { form, onSubmit } = useModuleForm<RetinographyData>(
    "retinography", retinographySchema, "Retinografía",
  );
  const { register, handleSubmit, setValue, watch } = form;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="h-5 w-5 text-red-400" />
          <h2 className="text-lg font-semibold ls-text">Retinografía</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />
          Guardar
        </Button>
      </div>

      <EyeConfig label="Ojo Derecho (OD)" prefix="ojoDerecho" register={register} setValue={setValue} watch={watch} />
      <EyeConfig label="Ojo Izquierdo (OI)" prefix="ojoIzquierdo" register={register} setValue={setValue} watch={watch} />

      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea
          {...register("observaciones")}
          rows={3}
          className="ls-border ls-bg-input text-xs ls-text resize-none"
          placeholder="Observaciones generales..."
        />
      </fieldset>
    </form>
  );
}
