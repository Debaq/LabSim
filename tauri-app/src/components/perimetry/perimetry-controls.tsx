/**
 * Controles del campímetro.
 * Patrón, estrategia, estímulo, ojo — como panel lateral de un Humphrey.
 */

import { Label } from "@/components/ui/label";
import type { Strategy, StimulusSize } from "@/lib/perimetry-config";

export interface PerimetrySettings {
  eye: "OD" | "OI";
  pattern: string;
  strategy: Strategy;
  stimulusSize: StimulusSize;
}

interface Props {
  settings: PerimetrySettings;
  onChange: (s: PerimetrySettings) => void;
  locked: boolean; // Si hay caso cargado, bloquear cambios
}

const PATTERNS = [
  { value: "24-2", label: "24-2" },
  { value: "30-2", label: "30-2" },
  { value: "10-2", label: "10-2" },
];

const STRATEGIES = [
  { value: "sita-standard" as const, label: "SITA Std" },
  { value: "sita-fast" as const, label: "SITA Fast" },
  { value: "full-threshold" as const, label: "Full Thr" },
];

const STIMULI = ["I", "II", "III", "IV", "V"] as const;

export function PerimetryControls({ settings, onChange, locked }: Props) {
  const set = <K extends keyof PerimetrySettings>(key: K, value: PerimetrySettings[K]) =>
    onChange({ ...settings, [key]: value });

  return (
    <div className="space-y-3 p-2">
      {/* Ojo */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Ojo</Label>
        <div className="flex gap-0.5">
          <button
            onClick={() => set("eye", "OD")}
            className={`rounded px-3 py-1 text-xs font-bold transition ${
              settings.eye === "OD" ? "bg-red-500/20 text-red-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            OD
          </button>
          <button
            onClick={() => set("eye", "OI")}
            className={`rounded px-3 py-1 text-xs font-bold transition ${
              settings.eye === "OI" ? "bg-blue-500/20 text-blue-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            OI
          </button>
        </div>
      </div>

      <div className="h-px ls-bg-input" />

      {/* Patrón */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Patrón</Label>
        <div className="flex flex-col gap-0.5">
          {PATTERNS.map((p) => (
            <button
              key={p.value}
              onClick={() => !locked && set("pattern", p.value)}
              disabled={locked}
              className={`rounded px-2 py-0.5 text-left text-[10px] transition ${
                settings.pattern === p.value
                  ? "bg-violet-500/20 text-violet-400"
                  : "ls-text-muted hover:ls-bg-input"
              } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Estrategia */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Estrategia</Label>
        <div className="flex flex-col gap-0.5">
          {STRATEGIES.map((s) => (
            <button
              key={s.value}
              onClick={() => !locked && set("strategy", s.value)}
              disabled={locked}
              className={`rounded px-2 py-0.5 text-left text-[10px] transition ${
                settings.strategy === s.value
                  ? "bg-violet-500/20 text-violet-400"
                  : "ls-text-muted hover:ls-bg-input"
              } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Goldmann */}
      <div className="space-y-1">
        <Label className="text-[9px] ls-text-muted uppercase tracking-wider">Goldmann</Label>
        <div className="flex gap-0.5">
          {STIMULI.map((s) => (
            <button
              key={s}
              onClick={() => !locked && set("stimulusSize", s)}
              disabled={locked}
              className={`rounded px-1.5 py-0.5 text-[10px] font-mono transition ${
                settings.stimulusSize === s
                  ? "bg-violet-500/20 text-violet-400"
                  : "ls-text-muted hover:ls-bg-input"
              } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {locked && (
        <p className="text-[8px] text-amber-400/60 mt-2">
          Protocolo definido por el caso
        </p>
      )}
    </div>
  );
}
