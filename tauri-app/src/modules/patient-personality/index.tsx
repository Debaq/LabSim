import { useModuleForm } from "@/modules/use-module-form";
import { personalitySchema, type PersonalityData } from "./schema";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, Drama, Volume2, Play, Loader2 } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useState } from "react";

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

const VOICE_OPTIONS = [
  { value: "male", label: "Masculina", color: "blue" },
  { value: "female", label: "Femenina", color: "pink" },
];

const TEST_PHRASES = [
  "Hola, buenas tardes doctora.",
  "Me duele mucho el oído desde hace tiempo.",
  "No escucho bien cuando hay ruido.",
  "¿Cuánto va a demorar el examen?",
];

export default function PatientPersonalityModule() {
  const { form, onSubmit } = useModuleForm<PersonalityData>(
    "personality", personalitySchema, "Personalidad del paciente",
  );
  const { register, handleSubmit, setValue, watch } = form;

  const currentPersonality = watch("personalityType");
  const currentCooperation = watch("examCooperation");
  const currentVoice = watch("voiceId") ?? "female";
  const currentPitch = watch("pitchShift") ?? 0;
  const currentRate = watch("speechRate") ?? 1.0;
  const [testPlaying, setTestPlaying] = useState(false);

  const handleTestVoice = async () => {
    setTestPlaying(true);
    try {
      const phrase = TEST_PHRASES[Math.floor(Math.random() * TEST_PHRASES.length)];
      await invoke("tts_speak", {
        text: phrase,
        voiceId: currentVoice,
        pitchShift: currentPitch,
        speechRate: currentRate,
      });
    } catch { /* TTS no cargado */ }
    setTestPlaying(false);
  };

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

      {/* Voz del paciente */}
      <fieldset className="space-y-4 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          Voz del Paciente
        </legend>

        {/* Selección de voz base */}
        <div className="space-y-1.5">
          <Label className="ls-text2">Voz base</Label>
          <div className="flex gap-2">
            {VOICE_OPTIONS.map((v) => (
              <button
                key={v.value}
                type="button"
                onClick={() => setValue("voiceId", v.value, { shouldDirty: true })}
                className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-left transition ${
                  currentVoice === v.value
                    ? v.color === "blue"
                      ? "border-blue-500/40 bg-blue-500/10"
                      : "border-pink-500/40 bg-pink-500/10"
                    : "ls-border hover:ls-bg-input"
                }`}
              >
                <Volume2 className={`h-4 w-4 ${
                  currentVoice === v.value
                    ? v.color === "blue" ? "text-blue-400" : "text-pink-400"
                    : "ls-text-muted"
                }`} />
                <span className={`text-xs font-medium ${
                  currentVoice === v.value
                    ? v.color === "blue" ? "text-blue-400" : "text-pink-400"
                    : "ls-text2"
                }`}>
                  {v.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Parámetros de modificación */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="ls-text2 text-xs">Tono</Label>
              <span className="text-[10px] ls-text-muted">
                {currentPitch > 0 ? `+${currentPitch}` : currentPitch} st
              </span>
            </div>
            <input
              type="range"
              min={-4}
              max={4}
              step={0.5}
              value={currentPitch}
              onChange={(e) => setValue("pitchShift", parseFloat(e.target.value), { shouldDirty: true })}
              className="w-full accent-pink-500"
            />
            <div className="flex justify-between text-[9px] ls-text-muted">
              <span>Grave</span>
              <span>Normal</span>
              <span>Agudo</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="ls-text2 text-xs">Velocidad</Label>
              <span className="text-[10px] ls-text-muted">
                {currentRate.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min={0.75}
              max={1.3}
              step={0.05}
              value={currentRate}
              onChange={(e) => setValue("speechRate", parseFloat(e.target.value), { shouldDirty: true })}
              className="w-full accent-pink-500"
            />
            <div className="flex justify-between text-[9px] ls-text-muted">
              <span>Lento</span>
              <span>Normal</span>
              <span>Rápido</span>
            </div>
          </div>
        </div>

        {/* Probar voz */}
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={handleTestVoice}
          disabled={testPlaying}
          className="gap-1.5 ls-border ls-text2"
        >
          {testPlaying
            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
            : <Play className="h-3.5 w-3.5" />
          }
          Probar voz
        </Button>
        <p className="text-[10px] ls-text-muted">
          Requiere que las voces TTS estén descargadas en Configuración.
        </p>
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
