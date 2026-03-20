import { cn } from "@/lib/utils";
import type { ChannelState, StimulusType, TransducerType, ToneMode } from "./channel-strip";

interface ChannelDisplayProps {
  state: ChannelState;
  color: "red" | "blue";
  label: string;
}

const stimLabels: Record<StimulusType, string> = {
  tone: "Tono", fm: "FM", speech: "Habla", nbn: "NBN", wn: "WN", sn: "SN", pn: "PN",
};
const transLabels: Record<TransducerType, string> = {
  air: "Aérea", bone: "Ósea", free: "C.Libre",
};
const modeLabels: Record<ToneMode, string> = {
  continuous: "Continuo", pulsed: "Pulsado", alternated: "Alternado",
};
const formatFreq = (f: number) => (f >= 1000 ? `${f / 1000}k` : `${f}`);

export function ChannelDisplay({ state, color, label }: ChannelDisplayProps) {
  const borderColor = color === "red" ? "border-red-500/15" : "border-blue-500/15";
  const accentColor = color === "red" ? "text-red-400" : "text-blue-400";
  const glowColor = color === "red"
    ? "[text-shadow:0_0_6px_rgb(248_113_113/0.4)]"
    : "[text-shadow:0_0_6px_rgb(96_165_250/0.4)]";

  return (
    <div className={cn("rounded-sm border bg-black/70 p-1.5", borderColor)}>
      {/* Header */}
      <div className="mb-1 flex items-center justify-between">
        <span className={cn("text-[7px] font-bold tracking-wider", accentColor)}>{label}</span>
        {state.isPlaying && (
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-400 shadow-sm shadow-red-400/50" />
            <span className="text-[6px] text-red-400/60">ON</span>
          </div>
        )}
      </div>

      {/* Main info grid */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
        {/* Frequency */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">Freq</span>
          <span className={cn("font-mono text-sm font-bold tabular-nums text-amber-400 [text-shadow:0_0_6px_rgb(251_191_36/0.4)]")}>
            {formatFreq(state.frequency)}
          </span>
        </div>

        {/* Intensity */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">dB HL</span>
          <span className={cn(
            "font-mono text-sm font-bold tabular-nums",
            state.intensity > 90 ? "text-red-400 [text-shadow:0_0_6px_rgb(248_113_113/0.4)]" : cn(accentColor, glowColor),
          )}>
            {state.intensity}
          </span>
        </div>

        {/* Transducer */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">Trans</span>
          <span className="text-[9px] font-medium text-white/50">{transLabels[state.transducer]}</span>
        </div>

        {/* Output */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">Salida</span>
          <span className={cn("text-[9px] font-bold", state.output === "right" ? "text-red-400/70" : "text-blue-400/70")}>
            {state.output === "right" ? "OD" : "OI"}
          </span>
        </div>

        {/* Stimulus */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">Estím</span>
          <span className="text-[9px] font-medium text-white/50">{stimLabels[state.stimulus]}</span>
        </div>

        {/* Mode */}
        <div className="flex items-baseline justify-between">
          <span className="text-[6px] uppercase text-white/20">Modo</span>
          <span className="text-[9px] font-medium text-white/50">{modeLabels[state.toneMode]}</span>
        </div>
      </div>

      {/* Flags row */}
      <div className="mt-1 flex gap-1">
        <span className="text-[6px] uppercase text-white/20">Pasos:{state.step}</span>
        {state.reversed && <span className="text-[6px] font-bold text-amber-400/60">REV</span>}
        {state.extRange && <span className="text-[6px] font-bold text-purple-400/60">EXT</span>}
        {state.highFreq && <span className="text-[6px] font-bold text-cyan-400/60">HF</span>}
      </div>
    </div>
  );
}
