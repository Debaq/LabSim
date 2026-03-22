import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BotMessageSquare,
  Lock,
  Unlock,
  Loader2,
  RefreshCw,
  Save,
} from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth-store";
import {
  useKarimeConfigStore,
  type KarimeTone,
  type DirectiveFormData,
  type KarimeDirective,
} from "@/stores/karime-config-store";

const TONE_OPTIONS: { value: KarimeTone; label: string; desc: string }[] = [
  { value: "profesional", label: "Profesional", desc: "Formal, objetiva, corporativa" },
  { value: "amigable", label: "Amigable", desc: "Casual, empática, con emojis" },
  { value: "estricto", label: "Estricto", desc: "Directa, sin margen, consecuencias" },
  { value: "relajado", label: "Relajado", desc: "Tranquila, sin urgencia" },
];

const PRESSURE_LABELS = ["Muy relajado", "Relajado", "Normal", "Alto", "Intenso"];

const TREATMENT_OPTIONS = [
  { value: "formal", label: "Formal (Estimado/a)" },
  { value: "por_nombre", label: "Por nombre" },
  { value: "custom", label: "Personalizado" },
];

const PREVIEW_MESSAGES: Record<string, string[]> = {
  profesional: [
    "{treatment}, {patient} ya se encuentra en el box. Procedimiento: Audiometría. Tiempo asignado: 30 minutos.",
    "{treatment}, le quedan aproximadamente 5 minutos con {patient}.",
  ],
  amigable: [
    "¡Hola {treatment}! {patient} ya está en el box, viene por Audiometría. Tienes 30 minutitos 😊",
    "{treatment}, ojo que te quedan como 5 min con {patient} ⏰",
  ],
  estricto: [
    "{treatment}, el paciente {patient} está en el box. Tiene exactamente 30 minutos. Comience.",
    "{treatment}, 5 minutos restantes con {patient}. Vaya cerrando.",
  ],
  relajado: [
    "Hola {treatment}, {patient} ya está ahí. Tranqui, tienes 30 min 😌",
    "{treatment}, como para ir cerrando con {patient}, quedan unos 5 min.",
  ],
};

function getLockedFields(directive: KarimeDirective | null): string[] {
  if (!directive || !directive.is_locked || !directive.custom_messages_json) return [];
  try {
    const parsed = JSON.parse(directive.custom_messages_json);
    return Object.keys(parsed).filter((k) => parsed[k] === true);
  } catch {
    return [];
  }
}

function formFromDirective(directive: KarimeDirective | null): DirectiveFormData {
  if (!directive) {
    return {
      title: "Configuración Karime",
      tone: "profesional",
      pressure_level: 2,
      student_treatment: "formal",
      rules_text: "",
      locked_fields: [],
    };
  }
  return {
    title: directive.title,
    tone: directive.tone,
    pressure_level: directive.pressure_level,
    student_treatment: directive.student_treatment,
    rules_text: directive.rules_text ?? "",
    locked_fields: getLockedFields(directive),
  };
}

function getTreatmentType(value: string): string {
  if (value === "formal" || value === "por_nombre") return value;
  return "custom";
}

function getTreatmentDisplay(value: string): string {
  if (value === "formal") return "Estimado/a";
  if (value === "por_nombre") return "Estudiante";
  return value;
}

// ─── Componente principal ───────────────────────────

export function KarimeConfigWindow() {
  const role = useAuthStore((s) => s.role);
  const {
    globalDirective,
    myDirective,
    loading,
    fetchDirectives,
    saveDirective,
    updateDirective,
    fetchResolvedPreview,
  } = useKarimeConfigStore();

  const isAdmin = role === "admin";
  const directive = isAdmin ? globalDirective : myDirective;
  const lockedByAdmin = getLockedFields(globalDirective);

  const [form, setForm] = useState<DirectiveFormData>(formFromDirective(directive));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchDirectives();
    fetchResolvedPreview();
  }, [fetchDirectives, fetchResolvedPreview]);

  useEffect(() => {
    setForm(formFromDirective(directive));
  }, [directive]);

  const isFieldLocked = (field: string) => !isAdmin && lockedByAdmin.includes(field);

  const toggleLock = (field: string) => {
    setForm((f) => ({
      ...f,
      locked_fields: f.locked_fields.includes(field)
        ? f.locked_fields.filter((x) => x !== field)
        : [...f.locked_fields, field],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const scope = isAdmin ? "global" as const : "docente" as const;
      if (directive) {
        await updateDirective(directive.id, form);
      } else {
        await saveDirective(form, scope);
      }
      toast.success("Configuración guardada");
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  const treatmentType = getTreatmentType(form.student_treatment);
  const treatmentDisplay = getTreatmentDisplay(form.student_treatment);

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <BotMessageSquare className="h-4 w-4 text-rose-400" />
        <span className="text-xs font-medium ls-text2">Configurar Karime</span>
        <span className="rounded-md bg-rose-500/10 px-1.5 py-0.5 text-[9px] font-medium text-rose-400">
          {isAdmin ? "Admin" : "Docente"}
        </span>
        <Button
          size="icon-xs"
          variant="ghost"
          onClick={() => { fetchDirectives(); fetchResolvedPreview(); }}
          className="ml-auto ls-text-muted hover:ls-text"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin ls-text-muted" />
          </div>
        ) : (
          <div className="space-y-4 p-3">
            {/* Info base para docente */}
            {!isAdmin && globalDirective && (
              <div className="rounded-lg border ls-border bg-indigo-500/5 p-3">
                <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-indigo-400">
                  Configuración base (admin)
                </p>
                <div className="space-y-1 text-xs ls-text-muted">
                  <div>Tono: <span className="ls-text2">{TONE_OPTIONS.find((t) => t.value === globalDirective.tone)?.label}</span></div>
                  <div>Presión: <span className="ls-text2">{PRESSURE_LABELS[(globalDirective.pressure_level || 2) - 1]}</span></div>
                  <div>Tratamiento: <span className="ls-text2">{getTreatmentDisplay(globalDirective.student_treatment)}</span></div>
                  {lockedByAdmin.length > 0 && (
                    <div className="mt-1 flex items-center gap-1 text-amber-400">
                      <Lock className="h-3 w-3" />
                      <span>Campos bloqueados: {lockedByAdmin.join(", ")}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Tono */}
            <FieldWrapper
              label="Tono de comunicación"
              locked={isFieldLocked("tone")}
              isAdmin={isAdmin}
              fieldName="tone"
              isLocked={form.locked_fields.includes("tone")}
              onToggleLock={toggleLock}
            >
              <div className="grid grid-cols-2 gap-1.5">
                {TONE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    disabled={isFieldLocked("tone")}
                    onClick={() => setForm((f) => ({ ...f, tone: opt.value }))}
                    className={`rounded-lg border p-2 text-left transition ${
                      form.tone === opt.value
                        ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
                        : "ls-border hover:ls-bg-input ls-text-muted"
                    } ${isFieldLocked("tone") ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    <div className="text-xs font-medium">{opt.label}</div>
                    <div className="text-[10px] ls-text-muted">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </FieldWrapper>

            {/* Presión */}
            <FieldWrapper
              label="Nivel de presión"
              locked={isFieldLocked("pressure_level")}
              isAdmin={isAdmin}
              fieldName="pressure_level"
              isLocked={form.locked_fields.includes("pressure_level")}
              onToggleLock={toggleLock}
            >
              <div className="flex gap-1">
                {PRESSURE_LABELS.map((lbl, idx) => {
                  const level = idx + 1;
                  return (
                    <button
                      key={level}
                      disabled={isFieldLocked("pressure_level")}
                      onClick={() => setForm((f) => ({ ...f, pressure_level: level }))}
                      className={`flex-1 rounded-lg border py-2 text-center transition ${
                        form.pressure_level === level
                          ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
                          : "ls-border hover:ls-bg-input ls-text-muted"
                      } ${isFieldLocked("pressure_level") ? "cursor-not-allowed opacity-50" : ""}`}
                    >
                      <div className="text-sm font-bold">{level}</div>
                      <div className="text-[9px]">{lbl}</div>
                    </button>
                  );
                })}
              </div>
            </FieldWrapper>

            {/* Tratamiento */}
            <FieldWrapper
              label="Tratamiento al estudiante"
              locked={isFieldLocked("student_treatment")}
              isAdmin={isAdmin}
              fieldName="student_treatment"
              isLocked={form.locked_fields.includes("student_treatment")}
              onToggleLock={toggleLock}
            >
              <div className="flex gap-1.5">
                {TREATMENT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    disabled={isFieldLocked("student_treatment")}
                    onClick={() =>
                      setForm((f) => ({
                        ...f,
                        student_treatment: opt.value === "custom" ? f.student_treatment === "formal" || f.student_treatment === "por_nombre" ? "" : f.student_treatment : opt.value,
                      }))
                    }
                    className={`flex-1 rounded-lg border py-1.5 text-center text-xs transition ${
                      treatmentType === opt.value
                        ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
                        : "ls-border hover:ls-bg-input ls-text-muted"
                    } ${isFieldLocked("student_treatment") ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              {treatmentType === "custom" && (
                <Input
                  value={form.student_treatment}
                  onChange={(e) => setForm((f) => ({ ...f, student_treatment: e.target.value }))}
                  placeholder="Ej: Colega, Futuro profesional..."
                  disabled={isFieldLocked("student_treatment")}
                  className="mt-1.5 ls-border ls-bg-input text-xs ls-text"
                />
              )}
            </FieldWrapper>

            {/* Reglas */}
            <div className="space-y-1.5">
              <Label className="text-xs ls-text2">Reglas adicionales</Label>
              <Textarea
                value={form.rules_text}
                onChange={(e) => setForm((f) => ({ ...f, rules_text: e.target.value }))}
                placeholder="Instrucciones adicionales para Karime..."
                rows={3}
                className="ls-border ls-bg-input text-xs ls-text resize-none"
              />
              <p className="text-[10px] ls-text-muted">
                Estas reglas se concatenan con las de niveles superiores.
              </p>
            </div>

            {/* Preview */}
            <div className="rounded-lg border ls-border p-3">
              <p className="mb-2 text-[10px] font-medium uppercase tracking-wider ls-text-muted">
                Vista previa
              </p>
              <div className="space-y-1.5">
                {(PREVIEW_MESSAGES[form.tone] ?? PREVIEW_MESSAGES.profesional).map((msg, i) => (
                  <div
                    key={i}
                    className="rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-2.5 py-1.5 text-xs ls-text2"
                  >
                    <span className="mr-1 text-emerald-400 font-medium">Karime:</span>
                    {msg.replace(/\{treatment\}/g, treatmentDisplay).replace(/\{patient\}/g, "Sra. Martínez")}
                  </div>
                ))}
              </div>
            </div>

            {/* Guardar */}
            <Button
              onClick={handleSave}
              disabled={saving}
              className="w-full gap-1.5 bg-rose-600 text-white hover:bg-rose-500"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
              Guardar configuración
            </Button>
          </div>
        )}
      </ScrollArea>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border px-3 py-1.5 text-[10px] ls-text-muted">
        <span>{directive ? "Editando directriz existente" : "Nueva configuración"}</span>
        {isAdmin && form.locked_fields.length > 0 && (
          <span className="text-amber-400">{form.locked_fields.length} campos bloqueados</span>
        )}
      </div>
    </div>
  );
}

// ─── Wrapper de campo con candado ───────────────────

function FieldWrapper({
  label,
  locked,
  isAdmin,
  fieldName,
  isLocked,
  onToggleLock,
  children,
}: {
  label: string;
  locked: boolean;
  isAdmin: boolean;
  fieldName: string;
  isLocked: boolean;
  onToggleLock: (field: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5">
        <Label className="text-xs ls-text2">{label}</Label>
        {locked && (
          <Lock className="h-3 w-3 text-amber-400" />
        )}
        {isAdmin && (
          <button
            onClick={() => onToggleLock(fieldName)}
            className="ml-auto flex items-center gap-0.5 rounded px-1 py-0.5 text-[9px] transition hover:ls-bg-input"
            title={isLocked ? "Desbloquear para docentes" : "Bloquear para docentes"}
          >
            {isLocked ? (
              <>
                <Lock className="h-3 w-3 text-amber-400" />
                <span className="text-amber-400">Bloqueado</span>
              </>
            ) : (
              <>
                <Unlock className="h-3 w-3 ls-text-muted" />
                <span className="ls-text-muted">Libre</span>
              </>
            )}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}
