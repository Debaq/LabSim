import { useState, useCallback } from "react";
import { useModuleForm } from "@/modules/use-module-form";
import { audiometrySchema, type AudiometryData } from "./schema";
import { AudiogramChart, type AudiogramPoint } from "@/charts/audiogram/audiogram-chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Save, AudioLines } from "lucide-react";
import { ISO_FREQUENCIES } from "@/lib/constants";

const BONE_FREQUENCIES = [250, 500, 1000, 2000, 3000, 4000];

export default function AudiometryModule() {
  const { form, onSubmit } = useModuleForm<AudiometryData>(
    "audiometry", audiometrySchema, "Audiometría",
  );
  const { register, handleSubmit, watch, setValue } = form;
  const [activeEar, setActiveEar] = useState<"right" | "left">("right");
  const [activeType, setActiveType] = useState<"air" | "bone">("air");

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

  const freqs = activeType === "air" ? ISO_FREQUENCIES : BONE_FREQUENCIES;
  const section = activeType === "air" ? "umbralesAereos" : "umbralesOseos";
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
      </div>

      {/* Audiogram chart */}
      <div className="rounded-lg border ls-border ls-bg-input p-2" style={{ height: 400 }}>
        <AudiogramChart points={points} onPointAdd={handlePointAdd} onPointRemove={handlePointRemove}
          activeEar={activeEar} activeType={activeType} interactive />
      </div>

      {/* Manual input table */}
      <fieldset className="space-y-3 rounded-lg border ls-border ls-bg-input p-4">
        <legend className="px-2 text-xs font-medium tracking-wider ls-text-muted uppercase">
          {activeType === "air" ? "Umbrales Aéreos" : "Umbrales Óseos"} — {activeEar === "right" ? "Oído Derecho" : "Oído Izquierdo"}
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
