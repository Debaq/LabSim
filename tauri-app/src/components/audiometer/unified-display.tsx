import { cn } from "@/lib/utils";
import type { ChannelState, StimulusType, TransducerType, ToneMode } from "./channel-strip";

interface UnifiedDisplayProps {
  ch0: ChannelState;
  ch1: ChannelState;
  frequency: number;
  testMode: string;
  time: string;
  logoText?: string;
}

const stimL: Record<StimulusType, string> = { tone: "Tono", fm: "FM", speech: "Habla", nbn: "NBN", wn: "WN", sn: "SN", pn: "PN" };
const transL: Record<TransducerType, string> = { air: "Aérea", bone: "Ósea", free: "C.Libre" };
const modeL: Record<ToneMode, string> = { continuous: "Continuo", pulsed: "Pulsado", alternated: "Alternado" };
const fmtF = (f: number) => (f >= 1000 ? `${f / 1000}k` : `${f}`);

function ChannelInfo({ ch, label, color, ledColor }: { ch: ChannelState; label: string; color: string; ledColor: string }) {
  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <span className={cn("text-[10px] font-bold tracking-wider", color)}>{label}</span>
        {ch.isPlaying && (
          <div className="flex items-center gap-1">
            <div className={cn("h-2.5 w-2.5 animate-pulse rounded-full shadow-sm", ledColor)} />
          </div>
        )}
      </div>

      {/* Intensity — dominant number */}
      <div className="flex items-baseline gap-1 mb-1">
        <span className={cn("font-mono text-3xl font-black tabular-nums leading-none", color,
          `[text-shadow:0_0_12px_currentColor]`)}>
          {ch.intensity}
        </span>
        <span className="text-[10px] text-white/30">dB</span>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-px text-[10px]">
        <div className="flex justify-between">
          <span className="text-white/25">Trans</span>
          <span className="font-semibold text-white/60">{transL[ch.transducer]}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/25">Salida</span>
          <span className={cn("font-semibold", ch.output === "right" ? "text-red-400/70" : "text-blue-400/70")}>
            {ch.output === "right" ? "Derecha" : "Izquierda"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/25">Estím</span>
          <span className="font-semibold text-white/60">{stimL[ch.stimulus]}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/25">Modo</span>
          <span className="font-semibold text-white/60">{modeL[ch.toneMode]}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/25">Pasos</span>
          <span className="font-semibold text-white/60">{ch.step} dB</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/25">Revers</span>
          <span className={cn("font-semibold", ch.reversed ? "text-amber-400/70" : "text-white/40")}>
            {ch.reversed ? "Invertido" : "Normal"}
          </span>
        </div>
      </div>
    </div>
  );
}

export function UnifiedDisplay({ ch0, ch1, frequency, testMode, time, logoText }: UnifiedDisplayProps) {
  return (
    <div className="flex rounded border border-white/[0.08] bg-gradient-to-b from-[#080a0d] to-[#0d1014]">
      {/* CH0 */}
      <div className="flex-1 border-r border-white/[0.06] px-3 py-2">
        <ChannelInfo ch={ch0} label="CANAL 1" color="text-red-400" ledColor="bg-red-400 shadow-red-400" />
      </div>

      {/* Center */}
      <div className="flex w-[120px] shrink-0 flex-col items-center justify-center gap-1 px-2 py-2">
        {/* Frequency — big */}
        <div className="text-center">
          <div className="font-mono text-2xl font-black tabular-nums leading-none text-amber-400 [text-shadow:0_0_12px_rgb(251_191_36/0.5)]">
            {fmtF(frequency)}
          </div>
          <div className="text-[10px] text-white/25 mt-0.5">Hz</div>
        </div>

        {/* Test mode */}
        <div className="rounded bg-white/[0.04] px-2 py-0.5 text-[10px] font-semibold text-white/40">
          {testMode === "umbrales" ? "Umbrales" : "Logoaudiometría"}
        </div>

        {/* Time */}
        <div className="font-mono text-sm font-bold tabular-nums text-green-400/80 [text-shadow:0_0_6px_rgb(74_222_128/0.3)]">
          {time}
        </div>

        {/* Logo counter */}
        {logoText && (
          <div className="font-mono text-xs font-bold text-cyan-400/80">{logoText}</div>
        )}
      </div>

      {/* CH1 */}
      <div className="flex-1 border-l border-white/[0.06] px-3 py-2">
        <ChannelInfo ch={ch1} label="CANAL 2" color="text-blue-400" ledColor="bg-blue-400 shadow-blue-400" />
      </div>
    </div>
  );
}
