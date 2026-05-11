import { useState, useCallback } from "react";
import { useModuleForm } from "@/modules/use-module-form";
import { audiometrySchema, type AudiometryData, HEARING_LOSS_TYPES, type HearingLossType } from "./schema";
import { AudiogramChart, type AudiogramPoint } from "@/charts/audiogram/audiogram-chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, AudioLines, Wand2, ChevronDown, ChevronUp } from "lucide-react";
import { ISO_FREQUENCIES } from "@/lib/constants";
import { usePatientStore } from "@/stores/patient-store";
import { deriveAll } from "@/lib/audiometry-coherence";

const BONE_FREQUENCIES = [250, 500, 1000, 2000, 3000, 4000];

const LOSS_LABELS: Record<HearingLossType, string> = {
  normal: "Normal",
  conductiva: "Conductiva",
  "sensorioneural-coclear": "Sensorioneural Coclear",
  "sensorioneural-retrococlear": "Sensorioneural Retrococlear",
  mixta: "Mixta",
};

export default function AudiometryModule() {
  const { form, onSubmit } = useModuleForm<AudiometryData>(
    "audiometry", audiometrySchema, "Audiometría",
  );
  const { register, handleSubmit, watch, setValue } = form;
  const [activeEar, setActiveEar] = useState<"right" | "left">("right");
  const [activeType, setActiveType] = useState<"air" | "bone" | "ldl">("air");
  const [showProfile, setShowProfile] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const [derivePreview, setDerivePreview] = useState<string | null>(null);
  const updateModule = usePatientStore((s) => s.updateModule);

  const data = watch();

  // Convert form data to audiogram points
  const points: AudiogramPoint[] = [];
  (["oidoDerecho", "oidoIzquierdo"] as const).forEach((oido) => {
    const ear = oido === "oidoDerecho" ? "right" : "left";
    const airData = data.umbralesAereos?.[oido] ?? {};
    const boneData = data.umbralesOseos?.[oido] ?? {};
    Object.entries(airData).forEach(([freq, val]) => {
      if (val != null) points.push({ frequency: Number(freq), threshold: val, type: "air", ear, masked: false });
    });
    Object.entries(boneData).forEach(([freq, val]) => {
      if (val != null) points.push({ frequency: Number(freq), threshold: val, type: "bone", ear, masked: false });
    });
  });

  const sectionKey = (type: "air" | "bone" | "ldl") =>
    type === "air" ? "umbralesAereos" : type === "bone" ? "umbralesOseos" : "ldl";

  const handlePointAdd = useCallback((point: AudiogramPoint) => {
    const oido = point.ear === "right" ? "oidoDerecho" : "oidoIzquierdo";
    const section = point.type === "air" ? "umbralesAereos" : "umbralesOseos";
    const current = data[section]?.[oido] ?? {};
    setValue(`${section}.${oido}`, { ...current, [String(point.frequency)]: point.threshold }, { shouldDirty: true });
  }, [data, setValue]);

  const handlePointRemove = useCallback((freq: number, ear: "right" | "left", type: "air" | "bone") => {
    const oido = ear === "right" ? "oidoDerecho" : "oidoIzquierdo";
    const section = type === "air" ? "umbralesAereos" : "umbralesOseos";
    const current = { ...(data[section]?.[oido] ?? {}) };
    delete current[String(freq)];
    setValue(`${section}.${oido}`, current, { shouldDirty: true });
  }, [data, setValue]);

  // Derivar todas las pruebas
  const handleDerive = useCallback(() => {
    const derived = deriveAll(data);

    // Escribir a cada módulo via el store
    updateModule("logoaudiometry", derived.logoaudiometry as unknown as Record<string, unknown>);
    updateModule("supraliminal", derived.supraliminal as unknown as Record<string, unknown>);
    updateModule("tuningFork", derived.tuningFork as unknown as Record<string, unknown>);

    // Preview compacto
    const logo = derived.logoaudiometry;
    const supra = derived.supraliminal;
    const tf = derived.tuningFork;
    const preview = [
      `Logo: SRT OD=${logo.srt.oidoDerecho ?? "—"} OI=${logo.srt.oidoIzquierdo ?? "—"} dB`,
      `SISI OD=${Object.values(supra.sisi.od)[0] ?? "—"}% | Carhart OD=${Object.values(supra.carhart.od)[0] ?? "—"} dB`,
      `Rinne OD=${tf.rinne.oidoDerecho ?? "—"} OI=${tf.rinne.oidoIzquierdo ?? "—"} | Weber=${tf.weber.lateralizacion ?? "—"}`,
    ].join(" | ");
    setDerivePreview(preview);
  }, [data, updateModule]);

  // Tipos de pérdida actuales
  const rightType = data.tipoPerdida?.oidoDerecho ?? "normal";
  const leftType = data.tipoPerdida?.oidoIzquierdo ?? "normal";
  const showRecruitment = (t: HearingLossType) => t === "sensorioneural-coclear" || t === "mixta";
  const showDecay = (t: HearingLossType) => t === "sensorioneural-retrococlear" || t === "mixta";

  const freqs = activeType === "air" ? ISO_FREQUENCIES : activeType === "bone" ? BONE_FREQUENCIES : ISO_FREQUENCIES;
  const section = sectionKey(activeType);
  const oido = activeEar === "right" ? "oidoDerecho" : "oidoIzquierdo";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AudioLines className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold ls-text">Audiometría Tonal</h2>
        </div>
        <Button type="submit" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Guardar</Button>
      </div>

      {/* ─── Perfil audiológico ───────────────────────── */}
      <fieldset className="rounded-lg border ls-border ls-bg-input">
        <button type="button" onClick={() => setShowProfile(!showProfile)}
          className="flex w-full items-center justify-between px-4 py-2 text-xs font-medium tracking-wider ls-text-muted uppercase cursor-pointer hover:ls-text2">
          Perfil Audiológico
          {showProfile ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>

        {showProfile && (
          <div className="space-y-3 px-4 pb-4">
            {/* Tipo de pérdida por oído */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-red-400">Oído Derecho</Label>
                <select
                  value={rightType}
                  onChange={(e) => setValue("tipoPerdida.oidoDerecho", e.target.value as HearingLossType, { shouldDirty: true })}
                  className="h-8 w-full rounded border ls-border ls-bg-input px-2 text-xs ls-text"
                >
                  {HEARING_LOSS_TYPES.map((t) => (
                    <option key={t} value={t}>{LOSS_LABELS[t]}</option>
                  ))}
                </select>
                {showRecruitment(rightType) && (
                  <label className="flex items-center gap-1.5 text-xs ls-text-muted">
                    <input type="checkbox" {...register("reclutamiento.oidoDerecho")} className="rounded" />
                    Reclutamiento
                  </label>
                )}
                {showDecay(rightType) && (
                  <label className="flex items-center gap-1.5 text-xs ls-text-muted">
                    <input type="checkbox" {...register("deterioroTonal.oidoDerecho")} className="rounded" />
                    Deterioro tonal
                  </label>
                )}
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-blue-400">Oído Izquierdo</Label>
                <select
                  value={leftType}
                  onChange={(e) => setValue("tipoPerdida.oidoIzquierdo", e.target.value as HearingLossType, { shouldDirty: true })}
                  className="h-8 w-full rounded border ls-border ls-bg-input px-2 text-xs ls-text"
                >
                  {HEARING_LOSS_TYPES.map((t) => (
                    <option key={t} value={t}>{LOSS_LABELS[t]}</option>
                  ))}
                </select>
                {showRecruitment(leftType) && (
                  <label className="flex items-center gap-1.5 text-xs ls-text-muted">
                    <input type="checkbox" {...register("reclutamiento.oidoIzquierdo")} className="rounded" />
                    Reclutamiento
                  </label>
                )}
                {showDecay(leftType) && (
                  <label className="flex items-center gap-1.5 text-xs ls-text-muted">
                    <input type="checkbox" {...register("deterioroTonal.oidoIzquierdo")} className="rounded" />
                    Deterioro tonal
                  </label>
                )}
              </div>
            </div>

            {/* Config paciente (colapsable) */}
            <button type="button" onClick={() => setShowConfig(!showConfig)}
              className="flex items-center gap-1 text-[10px] ls-text-muted hover:ls-text2 cursor-pointer">
              {showConfig ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              Config. paciente virtual
            </button>
            {showConfig && (
              <div className="grid grid-cols-2 gap-3 rounded border ls-border p-3 sm:grid-cols-4">
                <div className="space-y-1">
                  <Label className="text-[10px] ls-text-muted">Falsos + (%)</Label>
                  <Input type="number" min={0} max={30} step={1}
                    {...register("patientConfig.falsePositiveRate", { valueAsNumber: true })}
                    className="h-7 text-center text-xs ls-border ls-bg-input ls-text" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] ls-text-muted">Falsos - (%)</Label>
                  <Input type="number" min={0} max={30} step={1}
                    {...register("patientConfig.falseNegativeRate", { valueAsNumber: true })}
                    className="h-7 text-center text-xs ls-border ls-bg-input ls-text" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] ls-text-muted">T. reacción (ms)</Label>
                  <Input type="number" min={100} max={2000} step={50}
                    {...register("patientConfig.reactionTimeMs", { valueAsNumber: true })}
                    className="h-7 text-center text-xs ls-border ls-bg-input ls-text" />
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] ls-text-muted">Fatiga (0-1)</Label>
                  <Input type="number" min={0} max={1} step={0.05}
                    {...register("patientConfig.fatigueFactor", { valueAsNumber: true })}
                    className="h-7 text-center text-xs ls-border ls-bg-input ls-text" />
                </div>
              </div>
            )}

            {/* Botón derivar */}
            <div className="flex items-center gap-2">
              <Button type="button" size="sm" variant="outline" onClick={handleDerive} className="gap-1.5">
                <Wand2 className="h-3.5 w-3.5" /> Derivar pruebas
              </Button>
              <span className="text-[10px] ls-text-muted">Logo + Supra + Diapasones</span>
            </div>

            {/* Preview */}
            {derivePreview && (
              <div className="rounded border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5 text-[10px] text-emerald-400">
                {derivePreview}
              </div>
            )}
          </div>
        )}
      </fieldset>

      {/* Controls */}
      <div className="flex items-center gap-2">
        <Button type="button" size="xs" variant={activeEar === "right" ? "default" : "ghost"}
          onClick={() => setActiveEar("right")} className={activeEar === "right" ? "bg-red-500/20 text-red-400" : "ls-text-muted"}>OD</Button>
        <Button type="button" size="xs" variant={activeEar === "left" ? "default" : "ghost"}
          onClick={() => setActiveEar("left")} className={activeEar === "left" ? "bg-blue-500/20 text-blue-400" : "ls-text-muted"}>OI</Button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <Button type="button" size="xs" variant={activeType === "air" ? "default" : "ghost"}
          onClick={() => setActiveType("air")} className={activeType === "air" ? "ls-bg-input ls-text" : "ls-text-muted"}>Vía Aérea</Button>
        <Button type="button" size="xs" variant={activeType === "bone" ? "default" : "ghost"}
          onClick={() => setActiveType("bone")} className={activeType === "bone" ? "ls-bg-input ls-text" : "ls-text-muted"}>Vía Ósea</Button>
        <Button type="button" size="xs" variant={activeType === "ldl" ? "default" : "ghost"}
          onClick={() => setActiveType("ldl")} className={activeType === "ldl" ? "ls-bg-input ls-text" : "ls-text-muted"}>LDL</Button>
      </div>

      {/* Audiogram chart */}
      <div className="rounded-lg border ls-border ls-bg-input p-2" style={{ height: 400 }}>
        <AudiogramChart points={points} onPointAdd={handlePointAdd} onPointRemove={handlePointRemove}
          activeEar={activeEar} activeType={activeType} interactive />
      </div>

      {/* Manual input table */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          {activeType === "air" ? "Umbrales Aéreos" : activeType === "bone" ? "Umbrales Óseos" : "LDL (dB HL)"} — {activeEar === "right" ? "Oído Derecho" : "Oído Izquierdo"}
        </legend>
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-11">
          {freqs.map((freq) => (
            <div key={freq} className="space-y-1">
              <Label className="text-xs ls-text-muted">{freq >= 1000 ? `${freq / 1000}k` : freq}</Label>
              <Input type="number" min={-10} max={130} step={5}
                {...register(`${section}.${oido}.${freq}` as `umbralesAereos.oidoDerecho`)}
                className="h-8 ls-border ls-bg-input px-1.5 text-center text-xs ls-text" />
            </div>
          ))}
        </div>
      </fieldset>

      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">Observaciones</legend>
        <Textarea {...register("observaciones")} className="min-h-16 ls-border ls-bg-input ls-text" placeholder="Observaciones..." />
      </fieldset>
    </form>
  );
}
