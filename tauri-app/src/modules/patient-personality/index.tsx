import { useModuleForm } from "@/modules/use-module-form";
import { personalitySchema, type PersonalityData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, Drama } from "lucide-react";

const PERSONALITY_TYPES = [
  { value: "colaborador", label: "Colaborador", desc: "Paciente amable y dispuesto" },
  { value: "ansioso", label: "Ansioso", desc: "Preocupado, hace muchas preguntas" },
  { value: "impaciente", label: "Impaciente", desc: "Quiere terminar rápido, se queja del tiempo" },
  { value: "timido", label: "Tímido", desc: "Habla poco, hay que sacarle las respuestas" },
  { value: "agresivo", label: "Difícil", desc: "Se irrita fácilmente, cuestiona al profesional" },
  { value: "confuso", label: "Confuso", desc: "No entiende bien las instrucciones, responde inconsistente" },
];

const COMMUNICATION_STYLES = [
  { value: "detallista", label: "Detallista" },
  { value: "breve", label: "Breve" },
  { value: "evasivo", label: "Evasivo" },
];

const TONE_OPTIONS = [
  { value: "formal", label: "Formal" },
  { value: "informal", label: "Informal" },
  { value: "coloquial", label: "Coloquial" },
];

const COOPERATION_LEVELS = [
  { value: "total", label: "Total", desc: "Respuestas consistentes, sigue instrucciones" },
  { value: "parcial", label: "Parcial", desc: "Pequeñas inconsistencias, coopera en general" },
  { value: "dificil", label: "Difícil", desc: "Respuestas inconsistentes, artefactos frecuentes" },
];

export default function PatientPersonalityModule() {
  const { form, onSubmit } = useModuleForm<PersonalityData>(
    "personality", personalitySchema, "Personalidad del paciente",
  );
  const { register, handleSubmit, setValue, watch, formState: { errors } } = form;

  const currentPersonality = watch("personalityType");
  const currentCooperation = watch("examCooperation");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Drama className="h-5 w-5 text-pink-400" />
          <h2 className="text-lg font-semibold ls-text">Personalidad del Paciente</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5">
          <Save className="h-3.5 w-3.5" />
          Guardar
        </Button>
      </div>

      {/* Identidad */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Identidad
        </legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="displayName" className="ls-text2">Nombre para mostrar</Label>
            <Input
              id="displayName"
              {...register("displayName")}
              className="ls-border ls-bg-input ls-text"
              placeholder="Sra. Rosa Martínez"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="age" className="ls-text2">Edad del personaje</Label>
            <Input
              id="age"
              type="number"
              {...register("age")}
              className="ls-border ls-bg-input ls-text"
              placeholder="62"
            />
          </div>
        </div>
      </fieldset>

      {/* Personalidad */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Comportamiento
        </legend>

        <div className="space-y-1.5">
          <Label className="ls-text2">Tipo de personalidad</Label>
          <div className="grid gap-2 sm:grid-cols-3">
            {PERSONALITY_TYPES.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setValue("personalityType", p.value, { shouldDirty: true })}
                className={`rounded-lg border p-2.5 text-left transition ${
                  currentPersonality === p.value
                    ? "border-pink-500/40 bg-pink-500/10"
                    : "ls-border hover:ls-bg-input"
                }`}
              >
                <span className={`text-xs font-medium ${currentPersonality === p.value ? "text-pink-400" : "ls-text2"}`}>
                  {p.label}
                </span>
                <p className="text-[10px] ls-text-muted mt-0.5">{p.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="ls-text2">Estilo de comunicación</Label>
            <div className="flex gap-1.5">
              {COMMUNICATION_STYLES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setValue("communicationStyle", s.value, { shouldDirty: true })}
                  className={`rounded-md px-3 py-1.5 text-xs transition ${
                    watch("communicationStyle") === s.value
                      ? "bg-pink-500/15 text-pink-400"
                      : "ls-bg-input ls-text-muted hover:ls-text2"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="ls-text2">Tono de voz</Label>
            <div className="flex gap-1.5">
              {TONE_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setValue("toneOfVoice", t.value, { shouldDirty: true })}
                  className={`rounded-md px-3 py-1.5 text-xs transition ${
                    watch("toneOfVoice") === t.value
                      ? "bg-pink-500/15 text-pink-400"
                      : "ls-bg-input ls-text-muted hover:ls-text2"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </fieldset>

      {/* Cooperación en exámenes */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Cooperación en Exámenes
        </legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {COOPERATION_LEVELS.map((c) => (
            <button
              key={c.value}
              type="button"
              onClick={() => setValue("examCooperation", c.value, { shouldDirty: true })}
              className={`rounded-lg border p-2.5 text-left transition ${
                currentCooperation === c.value
                  ? "border-amber-500/40 bg-amber-500/10"
                  : "ls-border hover:ls-bg-input"
              }`}
            >
              <span className={`text-xs font-medium ${currentCooperation === c.value ? "text-amber-400" : "ls-text2"}`}>
                {c.label}
              </span>
              <p className="text-[10px] ls-text-muted mt-0.5">{c.desc}</p>
            </button>
          ))}
        </div>
      </fieldset>

      {/* Historia / Backstory */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Historia del Paciente
        </legend>
        <div className="space-y-1.5">
          <Label htmlFor="backstory" className="ls-text2">
            Lo que el paciente contará cuando le pregunten
          </Label>
          <Textarea
            id="backstory"
            {...register("backstory")}
            className="ls-border ls-bg-input ls-text min-h-[120px] resize-none"
            placeholder="Ej: Hace 3 años que no escucho bien del oído derecho. Trabajo en construcción hace 20 años. Mi señora me dice que pongo la tele muy fuerte. Vengo porque mi doctora me mandó..."
          />
          <p className="text-[10px] ls-text-muted">
            Escribe en primera persona, como si fuera el paciente hablando. El LLM usará esto como base para las conversaciones.
          </p>
        </div>
      </fieldset>
    </form>
  );
}
