import { RotaryKnob } from "./rotary-knob";
import { ToggleSwitch } from "./toggle-switch";
import { StimulusButton } from "./stimulus-button";
import { VuMeter } from "./vu-meter";
import { ChannelDisplay } from "./channel-display";
import { cn } from "@/lib/utils";
import { ISO_FREQUENCIES, THRESHOLD_MIN, THRESHOLD_MAX } from "@/lib/constants";

const FREQ_MARKS = [125, 1000, 4000, 8000].map((f) => ({
  value: ISO_FREQUENCIES.indexOf(f as (typeof ISO_FREQUENCIES)[number]),
  label: f >= 1000 ? `${f / 1000}k` : `${f}`,
}));

const INTENSITY_MARKS = [0, 40, 80, 120].map((v) => ({ value: v, label: `${v}` }));

export type StimulusType = "tone" | "fm" | "speech" | "nbn" | "wn" | "sn" | "pn";
export type TransducerType = "air" | "bone" | "free";
export type OutputType = "right" | "left";
export type ToneMode = "continuous" | "pulsed" | "alternated";

export interface ChannelState {
  frequency: number;
  intensity: number;
  stimulus: StimulusType;
  transducer: TransducerType;
  output: OutputType;
  toneMode: ToneMode;
  reversed: boolean;
  extRange: boolean;
  highFreq: boolean;
  step: number;
  isPlaying: boolean;
  vuLevel: number;
}

interface ChannelStripProps {
  channel: 0 | 1;
  state: ChannelState;
  onChange: (updates: Partial<ChannelState>) => void;
  onStimulusPress: () => void;
  onStimulusRelease: () => void;
  label: string;
  color: "red" | "blue";
}

export function ChannelStrip({
  channel,
  state,
  onChange,
  onStimulusPress,
  onStimulusRelease,
  label,
  color,
}: ChannelStripProps) {
  const freqIndex = ISO_FREQUENCIES.indexOf(state.frequency as (typeof ISO_FREQUENCIES)[number]);

  const handleFreqKnob = (idx: number) => {
    const maxIdx = state.highFreq ? ISO_FREQUENCIES.length - 1 : 10;
    const clamped = Math.max(0, Math.min(maxIdx, Math.round(idx)));
    onChange({ frequency: ISO_FREQUENCIES[clamped] });
  };

  const borderColor = color === "red" ? "border-red-500/15" : "border-blue-500/15";

  return (
    <div className={cn("flex flex-col rounded border ls-bg-panel", borderColor)}>
      {/* === SCREEN: Display + VU === */}
      <div className="p-1.5 space-y-1">
        <ChannelDisplay state={state} color={color} label={label} />
        <VuMeter level={state.vuLevel} active={state.isPlaying} height={14} />
      </div>

      {/* === CONTROLS === */}
      <div className="flex flex-col gap-1 border-t ls-border px-1.5 py-1.5">
        {/* Knobs row */}
        <div className="flex items-start justify-around">
          <RotaryKnob
            value={freqIndex}
            min={0}
            max={state.highFreq ? ISO_FREQUENCIES.length - 1 : 10}
            step={1}
            onChange={handleFreqKnob}
            label="Freq"
            size="sm"
            marks={FREQ_MARKS}
          />
          <RotaryKnob
            value={state.intensity}
            min={THRESHOLD_MIN}
            max={state.extRange ? 130 : THRESHOLD_MAX}
            step={state.step}
            onChange={(v) => onChange({ intensity: v })}
            label="dB HL"
            size="sm"
            marks={INTENSITY_MARKS}
          />
        </div>

        {/* Stimulus type grid */}
        <div className="flex flex-wrap justify-center gap-px">
          {(["tone", "fm", "nbn", "speech", "wn", "sn", "pn"] as StimulusType[]).map((stim) => {
            const labels: Record<StimulusType, string> = {
              tone: "Tono", fm: "FM", speech: "Hab", nbn: "NBN", wn: "WN", sn: "SN", pn: "PN",
            };
            const disabled = channel === 1 && stim === "fm";
            return (
              <button
                key={stim}
                disabled={disabled}
                onClick={() => onChange({ stimulus: stim })}
                className={cn(
                  "rounded px-1 py-px text-xs font-bold uppercase transition",
                  state.stimulus === stim
                    ? "bg-amber-500/25 text-amber-300"
                    : disabled
                      ? "text-white/[0.06] cursor-not-allowed"
                      : "ls-text-muted hover:ls-text-muted",
                )}
              >
                {labels[stim]}
              </button>
            );
          })}
        </div>

        {/* Compact switches: 2 per row */}
        <div className="grid grid-cols-2 gap-x-1 gap-y-0.5">
          <ToggleSwitch
            label="Trans"
            value={state.transducer}
            onChange={(v) => onChange({ transducer: v as TransducerType })}
            options={[
              { value: "air", label: "VA" },
              { value: "bone", label: "VO" },
              { value: "free", label: "CL" },
            ]}
          />
          <ToggleSwitch
            label="Salida"
            value={state.output}
            onChange={(v) => onChange({ output: v as OutputType })}
            options={[
              { value: "right", label: "OD", color: "bg-red-600 ls-text" },
              { value: "left", label: "OI", color: "bg-blue-600 ls-text" },
            ]}
          />
          <ToggleSwitch
            label="Modo"
            value={state.toneMode}
            onChange={(v) => onChange({ toneMode: v as ToneMode })}
            options={[
              { value: "continuous", label: "C" },
              { value: "pulsed", label: "P" },
              { value: "alternated", label: "A" },
            ]}
          />
          <ToggleSwitch
            label="Pasos"
            value={String(state.step)}
            onChange={(v) => onChange({ step: Number(v) })}
            options={[
              { value: "1", label: "1" },
              { value: "3", label: "3" },
              { value: "5", label: "5" },
            ]}
          />
        </div>

        {/* Toggles + Stimulus in one row */}
        <div className="flex items-center justify-between">
          <div className="flex gap-px">
            {([
              { key: "reversed", label: "Rev", activeClass: "border-amber-500/30 bg-amber-500/10 text-amber-400" },
              { key: "extRange", label: "Ext", activeClass: "border-purple-500/30 bg-purple-500/10 text-purple-400" },
              { key: "highFreq", label: "HF", activeClass: "border-cyan-500/30 bg-cyan-500/10 text-cyan-400" },
            ] as const).map(({ key, label: lbl, activeClass }) => (
              <button
                key={key}
                onClick={() => onChange({ [key]: !state[key] })}
                className={cn(
                  "rounded border px-1 py-px text-xs font-bold uppercase transition",
                  state[key] ? activeClass : "ls-border ls-text-muted hover:ls-text-muted",
                )}
              >
                {lbl}
              </button>
            ))}
          </div>

          <StimulusButton
            active={state.isPlaying}
            onPress={onStimulusPress}
            onRelease={onStimulusRelease}
            label="ESTÍM"
            color={color}
          />
        </div>
      </div>
    </div>
  );
}
