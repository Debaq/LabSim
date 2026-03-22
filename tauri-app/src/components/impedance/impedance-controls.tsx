/**
 * Controles ajustables del impedanciómetro.
 * Como en un equipo real, el operador puede configurar:
 * - Frecuencia de sonda
 * - Rango de presión
 * - Velocidad del sweep
 * - Intensidad de reflejos
 */

import { Label } from "@/components/ui/label";

export interface ImpedanceSettings {
  probeFrequency: 226 | 678 | 1000;
  pressureMin: number;
  pressureMax: number;
  sweepSpeed: "slow" | "normal" | "fast";
  reflexIntensity: number; // dB HL para búsqueda de reflejos
  reflexFrequency: 500 | 1000 | 2000 | 4000;
  reflexMode: "ipsi" | "contra";
}

export const DEFAULT_SETTINGS: ImpedanceSettings = {
  probeFrequency: 226,
  pressureMin: -400,
  pressureMax: 200,
  sweepSpeed: "normal",
  reflexIntensity: 85,
  reflexFrequency: 1000,
  reflexMode: "ipsi",
};

const PROBE_FREQS = [226, 678, 1000] as const;
const SWEEP_SPEEDS: { value: ImpedanceSettings["sweepSpeed"]; label: string }[] = [
  { value: "slow", label: "Lento" },
  { value: "normal", label: "Normal" },
  { value: "fast", label: "Rápido" },
];
const REFLEX_FREQS = [500, 1000, 2000, 4000] as const;

interface Props {
  settings: ImpedanceSettings;
  onChange: (settings: ImpedanceSettings) => void;
}

export function ImpedanceControls({ settings, onChange }: Props) {
  const set = <K extends keyof ImpedanceSettings>(key: K, value: ImpedanceSettings[K]) =>
    onChange({ ...settings, [key]: value });

  return (
    <div className="space-y-3 p-2">
      {/* Frecuencia de sonda */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Sonda</Label>
        <div className="flex gap-0.5">
          {PROBE_FREQS.map((f) => (
            <button
              key={f}
              onClick={() => set("probeFrequency", f)}
              className={`rounded px-2 py-0.5 text-[10px] font-mono transition ${
                settings.probeFrequency === f
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              {f} Hz
            </button>
          ))}
        </div>
      </div>

      {/* Rango de presión */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Rango presión (daPa)</Label>
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={settings.pressureMin}
            onChange={(e) => set("pressureMin", parseInt(e.target.value) || -400)}
            className="w-14 rounded px-1 py-0.5 text-center text-[10px] font-mono ls-border ls-bg-input ls-text"
          />
          <span className="text-[10px] ls-text-muted">a</span>
          <input
            type="number"
            value={settings.pressureMax}
            onChange={(e) => set("pressureMax", parseInt(e.target.value) || 200)}
            className="w-14 rounded px-1 py-0.5 text-center text-[10px] font-mono ls-border ls-bg-input ls-text"
          />
        </div>
      </div>

      {/* Velocidad sweep */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Velocidad</Label>
        <div className="flex gap-0.5">
          {SWEEP_SPEEDS.map((s) => (
            <button
              key={s.value}
              onClick={() => set("sweepSpeed", s.value)}
              className={`rounded px-2 py-0.5 text-[10px] transition ${
                settings.sweepSpeed === s.value
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-px ls-bg-input" />

      {/* Reflejos: frecuencia + modo */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Reflejo estímulo</Label>
        <div className="flex gap-0.5">
          {REFLEX_FREQS.map((f) => (
            <button
              key={f}
              onClick={() => set("reflexFrequency", f)}
              className={`rounded px-1.5 py-0.5 text-[10px] font-mono transition ${
                settings.reflexFrequency === f
                  ? "bg-sky-500/20 text-sky-400"
                  : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Modo</Label>
        <div className="flex gap-0.5">
          <button
            onClick={() => set("reflexMode", "ipsi")}
            className={`rounded px-2 py-0.5 text-[10px] transition ${
              settings.reflexMode === "ipsi" ? "bg-sky-500/20 text-sky-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Ipsi
          </button>
          <button
            onClick={() => set("reflexMode", "contra")}
            className={`rounded px-2 py-0.5 text-[10px] transition ${
              settings.reflexMode === "contra" ? "bg-sky-500/20 text-sky-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            Contra
          </button>
        </div>
      </div>

      {/* Intensidad reflejo */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Intensidad: {settings.reflexIntensity} dB</Label>
        <input
          type="range"
          min={50}
          max={120}
          step={5}
          value={settings.reflexIntensity}
          onChange={(e) => set("reflexIntensity", parseInt(e.target.value))}
          className="w-full h-1 accent-sky-400"
        />
        <div className="flex justify-between text-[8px] ls-text-muted">
          <span>50</span>
          <span>120 dB</span>
        </div>
      </div>
    </div>
  );
}
