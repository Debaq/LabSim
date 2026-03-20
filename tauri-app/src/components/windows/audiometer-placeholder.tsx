import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { AudiogramChart, type AudiogramPoint } from "@/charts/audiogram/audiogram-chart";
import { UnifiedDisplay } from "@/components/audiometer/unified-display";
import { VuMeter } from "@/components/audiometer/vu-meter";
import { RotaryKnob } from "@/components/audiometer/rotary-knob";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import type { ChannelState, StimulusType, TransducerType, OutputType } from "@/components/audiometer/channel-strip";
import { cn } from "@/lib/utils";
import { ISO_FREQUENCIES, THRESHOLD_MIN, THRESHOLD_MAX } from "@/lib/constants";
import { RotateCcw, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";

const defaultCh = (out: "right" | "left"): ChannelState => ({
  frequency: 1000, intensity: 40, stimulus: "tone", transducer: "air",
  output: out, toneMode: "continuous", reversed: false, extRange: false,
  highFreq: false, step: 5, isPlaying: false, vuLevel: 0,
});
const I_MARKS = [0, 40, 80, 120].map((v) => ({ value: v, label: `${v}` }));

export function AudiometerPlaceholder() {
  const [ch0, setCh0] = useState<ChannelState>(defaultCh("right"));
  const [ch1, setCh1] = useState<ChannelState>(defaultCh("left"));
  const [testMode, setTestMode] = useState("umbrales");
  const [points, setPoints] = useState<AudiogramPoint[]>([]);
  const [showAG, setShowAG] = useState(false);
  const [freq, setFreq] = useState(1000);
  const [step, setStep] = useState(5);
  const [extRange, setExtRange] = useState(false);
  const [highFreq, setHighFreq] = useState(false);
  const [logoOk, setLogoOk] = useState(0);
  const [logoN, setLogoN] = useState(0);
  const [secs, setSecs] = useState(0);
  const [timerOn, setTimerOn] = useState(false);
  const tmr = useRef<ReturnType<typeof setInterval>>(undefined);
  const v0 = useRef<ReturnType<typeof setInterval>>(undefined);
  const v1 = useRef<ReturnType<typeof setInterval>>(undefined);

  const u0 = useCallback((u: Partial<ChannelState>) => setCh0((p) => ({ ...p, ...u })), []);
  const u1 = useCallback((u: Partial<ChannelState>) => setCh1((p) => ({ ...p, ...u })), []);

  useEffect(() => { u0({ frequency: freq, step, extRange, highFreq }); u1({ frequency: freq, step, extRange, highFreq }); }, [freq, step, extRange, highFreq, u0, u1]);

  useEffect(() => {
    if (timerOn) tmr.current = setInterval(() => setSecs((s) => s + 1), 1000);
    else if (tmr.current) clearInterval(tmr.current);
    return () => { if (tmr.current) clearInterval(tmr.current); };
  }, [timerOn]);
  const tStr = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;

  const fi = ISO_FREQUENCIES.indexOf(freq as (typeof ISO_FREQUENCIES)[number]);
  const mfi = highFreq ? ISO_FREQUENCIES.length - 1 : 10;
  const fP = () => { if (fi > 0) setFreq(ISO_FREQUENCIES[fi - 1]); };
  const fN = () => { if (fi < mfi) setFreq(ISO_FREQUENCIES[fi + 1]); };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      if (k === "w") u0({ intensity: Math.min(extRange ? 130 : 120, ch0.intensity + step) });
      else if (k === "s") u0({ intensity: Math.max(-10, ch0.intensity - step) });
      else if (k === "o") u1({ intensity: Math.min(extRange ? 130 : 120, ch1.intensity + step) });
      else if (k === "l") u1({ intensity: Math.max(-10, ch1.intensity - step) });
      else if (k === "arrowleft") { e.preventDefault(); fP(); }
      else if (k === "arrowright") { e.preventDefault(); fN(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const play = useCallback(async (ch: ChannelState) => {
    const nm: Record<string, string> = { wn: "white", pn: "pink", sn: "speech", nbn: "narrowband" };
    try {
      if (nm[ch.stimulus]) await invoke("play_noise", { params: { noiseType: nm[ch.stimulus], duration: 30, levelDbfs: ch.intensity - 80, ...(nm[ch.stimulus] === "narrowband" ? { centerHz: ch.frequency, bandwidthHz: ch.frequency * 0.15 } : {}) } });
      else await invoke("play_tone", { params: { frequency: ch.frequency, duration: 30, levelDbfs: ch.intensity - 80, ...(ch.toneMode === "pulsed" ? { pulsatileHz: 2.5, dutyCycle: 0.5 } : {}) } });
    } catch { /* */ }
  }, []);
  const stopA = useCallback(async () => { try { await invoke("stop_playback"); } catch { /* */ } }, []);
  const vuOn = (s: typeof u0, r: typeof v0) => { if (r.current) clearInterval(r.current); r.current = setInterval(() => s({ vuLevel: 50 + Math.random() * 30 }), 100); };
  const vuOff = (s: typeof u0, r: typeof v0) => { if (r.current) clearInterval(r.current); r.current = undefined; s({ vuLevel: 0 }); };

  const mkS = (ch: ChannelState, s: typeof u0, r: typeof v0) => {
    let h = false;
    return {
      d: () => { if (h) return; h = true; s({ isPlaying: true }); vuOn(s, r); play(ch); },
      u: () => { if (!h) return; h = false; s({ isPlaying: false }); vuOff(s, r); stopA(); },
    };
  };
  const s0 = mkS(ch0, u0, v0);
  const s1 = mkS(ch1, u1, v1);

  const reg = useCallback((ch: ChannelState, nr = false) => {
    setPoints((p) => {
      const pt: AudiogramPoint = { frequency: ch.frequency, threshold: ch.intensity, type: ch.transducer === "bone" ? "bone" : "air", ear: ch.output, masked: false, noResponse: nr };
      return [...p.filter((x) => !(x.frequency === pt.frequency && x.ear === pt.ear && x.type === pt.type)), pt];
    });
  }, []);

  // === INLINE SUB-COMPONENTS ===

  // Stimulus button - big round button
  const SBtn = ({ on, d, u, c }: { on: boolean; d: () => void; u: () => void; c: "r" | "b" }) => (
    <div className="flex flex-col items-center gap-1">
      <div className={cn("h-2.5 w-2.5 rounded-full transition shadow-sm", on ? (c === "r" ? "bg-red-400 shadow-red-400" : "bg-blue-400 shadow-blue-400") : "bg-white/10")} />
      <button onMouseDown={d} onMouseUp={u} onMouseLeave={u}
        className={cn("h-11 w-11 rounded-full border-2 border-white/10 shadow-lg shadow-black/50 active:translate-y-0.5 active:shadow-sm select-none transition",
          on ? (c === "r" ? "bg-red-500" : "bg-blue-500") : (c === "r" ? "bg-red-900/50 hover:bg-red-800/50" : "bg-blue-900/50 hover:bg-blue-800/50"))} />
    </div>
  );

  // Toggle button
  const Tb = ({ on, click, ch }: { on: boolean; click: () => void; ch: React.ReactNode }) => (
    <button onClick={click} className={cn("rounded border px-2 py-1 text-[8px] font-bold uppercase tracking-wide transition min-w-[36px]",
      on ? "border-amber-500/30 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/25 hover:text-white/50 hover:bg-white/[0.06]")}>{ch}</button>
  );

  // Stim type row
  const StRow = ({ ch, s, n }: { ch: ChannelState; s: typeof u0; n: number }) => (
    <div className="flex gap-0.5">
      {(["tone", "fm", "nbn", "speech", "wn", "sn", "pn"] as StimulusType[]).map((st) => {
        const lb: Record<StimulusType, string> = { tone: "Tono", fm: "FM", speech: "Hab", nbn: "NBN", wn: "WN", sn: "SN", pn: "PN" };
        const dis = n === 1 && st === "fm";
        return <button key={st} disabled={dis} onClick={() => s({ stimulus: st })}
          className={cn("rounded px-1.5 py-0.5 text-[8px] font-bold transition",
            ch.stimulus === st ? "bg-amber-500/25 text-amber-300" : dis ? "text-white/[0.06]" : "text-white/25 hover:bg-white/5 hover:text-white/50")}>{lb[st]}</button>;
      })}
    </div>
  );

  const logoText = testMode === "logoaudiometria" ? `${logoOk}/${logoN} : ${logoN > 0 ? Math.round((logoOk / logoN) * 100) : 0}%` : undefined;

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#3d424d] to-[#2d3139]">
      {showAG && (
        <div className="h-[40%] shrink-0 border-b border-black/30 p-1">
          <AudiogramChart points={points}
            onPointAdd={(p) => setPoints((x) => [...x.filter((q) => !(q.frequency === p.frequency && q.ear === p.ear && q.type === p.type)), p])}
            onPointRemove={(f, e, t) => setPoints((x) => x.filter((q) => !(q.frequency === f && q.ear === e && q.type === t)))}
            activeEar={ch0.output} activeType={ch0.transducer === "bone" ? "bone" : "air"} interactive />
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Brand bar */}
        <div className="flex h-6 shrink-0 items-center justify-between bg-[#1e2127] px-3">
          <span className="text-[9px] font-bold tracking-[0.2em] text-white/30">LABSIM <span className="font-normal text-white/12">DA-80</span></span>
          <div className="flex items-center gap-2">
            <ToggleSwitch value={testMode} onChange={setTestMode} options={[{ value: "umbrales", label: "Umbrales" }, { value: "logoaudiometria", label: "Logo" }]} />
            <button onClick={() => setShowAG(!showAG)} className="text-white/20 hover:text-white/40">
              {showAG ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
            </button>
            <button onClick={() => setPoints([])} className="text-white/15 hover:text-white/30"><RotateCcw className="h-3 w-3" /></button>
          </div>
        </div>

        {/* === AUDIOMETER PANEL === */}
        <div className="flex flex-1 flex-col gap-2 p-3 overflow-hidden">

          {/* ROW 1: DISPLAY */}
          <UnifiedDisplay ch0={ch0} ch1={ch1} frequency={freq} testMode={testMode} time={tStr} logoText={logoText} />

          {/* ROW 2: VU METERS */}
          <div className="flex gap-2">
            <div className="flex-1"><VuMeter level={ch0.vuLevel} active={ch0.isPlaying} height={14} /></div>
            <div className="flex-1"><VuMeter level={ch1.vuLevel} active={ch1.isPlaying} height={14} /></div>
          </div>

          {/* ROW 3: CONFIG — grid layout per channel side by side */}
          <div className="flex gap-3">
            {/* CH0 config */}
            <div className="flex-1 rounded border border-red-500/10 bg-black/20 p-2">
              <div className="mb-1.5 text-[8px] font-bold tracking-wider text-red-400/50">CANAL 1</div>
              {/* Stimulus grid */}
              <div className="mb-1.5">
                <div className="mb-0.5 text-[7px] uppercase text-white/20">Estímulo</div>
                <div className="grid grid-cols-4 gap-1">
                  {(["tone", "fm", "nbn", "speech"] as StimulusType[]).map((st) => {
                    const lb: Record<string, string> = { tone: "Tono", fm: "FM", nbn: "NBN", speech: "Habla" };
                    return <button key={st} onClick={() => u0({ stimulus: st })}
                      className={cn("rounded border py-1 text-[9px] font-bold transition",
                        ch0.stimulus === st ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08] hover:text-white/60")}>{lb[st]}</button>;
                  })}
                  {(["wn", "sn", "pn"] as StimulusType[]).map((st) => {
                    const lb: Record<string, string> = { wn: "WN", sn: "SN", pn: "PN" };
                    return <button key={st} onClick={() => u0({ stimulus: st })}
                      className={cn("rounded border py-1 text-[9px] font-bold transition",
                        ch0.stimulus === st ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08] hover:text-white/60")}>{lb[st]}</button>;
                  })}
                </div>
              </div>
              {/* Transductor + Salida */}
              <div className="flex gap-2">
                <div>
                  <div className="mb-0.5 text-[7px] uppercase text-white/20">Transductor</div>
                  <div className="flex gap-1">
                    {([["air","VA"],["bone","VO"],["free","CL"]] as const).map(([v,l]) => (
                      <button key={v} onClick={() => u0({ transducer: v as TransducerType })}
                        className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                          ch0.transducer === v ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>{l}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-0.5 text-[7px] uppercase text-white/20">Salida</div>
                  <div className="flex gap-1">
                    <button onClick={() => u0({ output: "right" })}
                      className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                        ch0.output === "right" ? "border-red-500/40 bg-red-500/20 text-red-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OD</button>
                    <button onClick={() => u0({ output: "left" })}
                      className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                        ch0.output === "left" ? "border-blue-500/40 bg-blue-500/20 text-blue-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OI</button>
                  </div>
                </div>
                <div className="ml-auto flex items-end gap-1">
                  <button onClick={() => reg(ch0)} className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[9px] font-bold text-emerald-400 hover:bg-emerald-500/20">Reg</button>
                  <button onClick={() => reg(ch0, true)} className="rounded border border-white/10 px-2 py-1 text-[9px] font-bold text-white/30 hover:bg-white/[0.06]">S/R</button>
                </div>
              </div>
            </div>

            {/* CH1 config */}
            <div className="flex-1 rounded border border-blue-500/10 bg-black/20 p-2">
              <div className="mb-1.5 text-[8px] font-bold tracking-wider text-blue-400/50">CANAL 2</div>
              <div className="mb-1.5">
                <div className="mb-0.5 text-[7px] uppercase text-white/20">Estímulo</div>
                <div className="grid grid-cols-4 gap-1">
                  {(["tone", "fm", "nbn", "speech"] as StimulusType[]).map((st) => {
                    const lb: Record<string, string> = { tone: "Tono", fm: "FM", nbn: "NBN", speech: "Habla" };
                    const dis = st === "fm";
                    return <button key={st} disabled={dis} onClick={() => u1({ stimulus: st })}
                      className={cn("rounded border py-1 text-[9px] font-bold transition",
                        ch1.stimulus === st ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : dis ? "border-white/[0.04] text-white/[0.08]" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08] hover:text-white/60")}>{lb[st]}</button>;
                  })}
                  {(["wn", "sn", "pn"] as StimulusType[]).map((st) => {
                    const lb: Record<string, string> = { wn: "WN", sn: "SN", pn: "PN" };
                    return <button key={st} onClick={() => u1({ stimulus: st })}
                      className={cn("rounded border py-1 text-[9px] font-bold transition",
                        ch1.stimulus === st ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08] hover:text-white/60")}>{lb[st]}</button>;
                  })}
                </div>
              </div>
              <div className="flex gap-2">
                <div>
                  <div className="mb-0.5 text-[7px] uppercase text-white/20">Transductor</div>
                  <div className="flex gap-1">
                    {([["air","VA"],["bone","VO"],["free","CL"]] as const).map(([v,l]) => (
                      <button key={v} onClick={() => u1({ transducer: v as TransducerType })}
                        className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                          ch1.transducer === v ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>{l}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-0.5 text-[7px] uppercase text-white/20">Salida</div>
                  <div className="flex gap-1">
                    <button onClick={() => u1({ output: "right" })}
                      className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                        ch1.output === "right" ? "border-red-500/40 bg-red-500/20 text-red-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OD</button>
                    <button onClick={() => u1({ output: "left" })}
                      className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                        ch1.output === "left" ? "border-blue-500/40 bg-blue-500/20 text-blue-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OI</button>
                  </div>
                </div>
                <div className="ml-auto flex items-end gap-1">
                  <button onClick={() => reg(ch1)} className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[9px] font-bold text-emerald-400 hover:bg-emerald-500/20">Reg</button>
                  <button onClick={() => reg(ch1, true)} className="rounded border border-white/10 px-2 py-1 text-[9px] font-bold text-white/30 hover:bg-white/[0.06]">S/R</button>
                </div>
              </div>
            </div>
          </div>

          {/* ROW 4: KNOBS ROW — the main physical controls */}
          <div className="flex flex-1 items-center border-t border-white/[0.06] pt-2">

            {/* CH1 knob */}
            <div className="flex-shrink-0">
              <RotaryKnob value={ch0.intensity} min={THRESHOLD_MIN} max={extRange ? 130 : THRESHOLD_MAX}
                step={step} onChange={(v) => u0({ intensity: v })} label="CH 1" size="lg" marks={I_MARKS} />
            </div>

            {/* CH0: pulso, rev, STIM, alt */}
            <div className="mx-3 flex flex-col items-center gap-1">
              <Tb on={ch0.toneMode === "pulsed"} click={() => u0({ toneMode: ch0.toneMode === "pulsed" ? "continuous" : "pulsed" })} ch="Pulso" />
              <Tb on={ch0.reversed} click={() => u0({ reversed: !ch0.reversed })} ch="Revers" />
              <SBtn on={ch0.isPlaying} d={s0.d} u={s0.u} c="r" />
              <Tb on={ch0.toneMode === "alternated"} click={() => u0({ toneMode: ch0.toneMode === "alternated" ? "continuous" : "alternated" })} ch="Alter" />
            </div>

            {/* CENTER: freq buttons + steps + ext + hf */}
            <div className="flex flex-1 items-center justify-center gap-3">
              <button onClick={fP} disabled={fi <= 0}
                className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white/10 bg-white/[0.04] text-white/40 transition hover:bg-white/10 disabled:opacity-20">
                <ChevronLeft className="h-5 w-5" />
              </button>

              <div className="flex flex-col items-center gap-1">
                <ToggleSwitch label="Pasos dB" value={String(step)} onChange={(v) => setStep(Number(v))}
                  options={[{ value: "1", label: "1" }, { value: "3", label: "3" }, { value: "5", label: "5" }]} />
                <div className="flex gap-1">
                  <Tb on={extRange} click={() => setExtRange(!extRange)} ch="Ext.Rango" />
                  <Tb on={highFreq} click={() => setHighFreq(!highFreq)} ch="Alt.Freq" />
                </div>
              </div>

              <button onClick={fN} disabled={fi >= mfi}
                className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white/10 bg-white/[0.04] text-white/40 transition hover:bg-white/10 disabled:opacity-20">
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            {/* CH1: pulso, rev, STIM */}
            <div className="mx-3 flex flex-col items-center gap-1">
              <Tb on={ch1.toneMode === "pulsed"} click={() => u1({ toneMode: ch1.toneMode === "pulsed" ? "continuous" : "pulsed" })} ch="Pulso" />
              <Tb on={ch1.reversed} click={() => u1({ reversed: !ch1.reversed })} ch="Revers" />
              <SBtn on={ch1.isPlaying} d={s1.d} u={s1.u} c="b" />
            </div>

            {/* CH2 knob */}
            <div className="flex-shrink-0">
              <RotaryKnob value={ch1.intensity} min={THRESHOLD_MIN} max={extRange ? 130 : THRESHOLD_MAX}
                step={step} onChange={(v) => u1({ intensity: v })} label="CH 2" size="lg" marks={I_MARKS} />
            </div>
          </div>

          {/* ROW 5: Timer + logo */}
          <div className="flex shrink-0 items-center justify-center gap-3 text-[9px]">
            <button onClick={() => setTimerOn(true)} className="text-emerald-400/60 hover:text-emerald-400">Iniciar</button>
            <button onClick={() => setTimerOn(false)} className="text-amber-400/60 hover:text-amber-400">Detener</button>
            <button onClick={() => { setTimerOn(false); setSecs(0); }} className="text-white/25 hover:text-white/50">Borrar</button>
            {testMode === "logoaudiometria" && (
              <>
                <span className="h-3 w-px bg-white/10" />
                <button onClick={() => { setLogoOk((c) => c + 1); setLogoN((t) => t + 1); }} className="font-bold text-emerald-400/70 hover:text-emerald-400">+1</button>
                <button onClick={() => setLogoN((t) => t + 1)} className="font-bold text-red-400/70 hover:text-red-400">-1</button>
                <button onClick={() => { setLogoOk(0); setLogoN(0); }} className="text-white/25 hover:text-white/50">Limpiar</button>
              </>
            )}
          </div>
        </div>

        {/* Status bar */}
        <div className="flex h-5 shrink-0 items-center justify-between bg-black/25 px-3 text-[8px] text-white/20">
          <span>W/S: CH1 dB | ←→: Freq</span>
          <span>{points.length} umbrales</span>
          <span>O/L: CH2 dB</span>
        </div>
      </div>
    </div>
  );
}
