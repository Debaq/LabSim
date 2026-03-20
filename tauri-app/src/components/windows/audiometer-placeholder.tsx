import { useState, useCallback, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { AudiogramChart, type AudiogramPoint } from "@/charts/audiogram/audiogram-chart";
import { UnifiedDisplay } from "@/components/audiometer/unified-display";
import { VuMeter } from "@/components/audiometer/vu-meter";
import { RotaryKnob } from "@/components/audiometer/rotary-knob";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import type { ChannelState, StimulusType, TransducerType, OutputType } from "@/components/audiometer/channel-strip";
import {
  getIntensityRange, calibrateToStep, getFrequencyList, getEnabledStimuli,
  PULSATILE_ON, PULSATILE_OFF, ALTERNATE_IPSI, ALTERNATE_SILENCE,
} from "@/lib/audiometer-config";
import { cn } from "@/lib/utils";
import { RotateCcw, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";

// === Components defined OUTSIDE the main component to avoid re-mounting ===
function Tb({ on, click, children }: { on: boolean; click: () => void; children: React.ReactNode }) {
  return (
    <button onClick={(e) => { e.stopPropagation(); click(); }} className={cn("rounded border px-2 py-1 text-[8px] font-bold uppercase tracking-wide transition min-w-[36px] cursor-pointer",
      on ? "border-amber-500/30 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/25 hover:text-white/50 hover:bg-white/[0.06]")}>{children}</button>
  );
}

function SBtn({ on, d, u, c }: { on: boolean; d: () => void; u: () => void; c: "r" | "b" }) {
  return (
    <div className="flex flex-col items-center gap-px">
      <div className={cn("h-2.5 w-2.5 rounded-full transition shadow-sm", on ? (c === "r" ? "bg-red-400 shadow-red-400" : "bg-blue-400 shadow-blue-400") : "bg-white/10")} />
      <button onMouseDown={(e) => { e.stopPropagation(); d(); }} onMouseUp={(e) => { e.stopPropagation(); u(); }} onMouseLeave={u}
        className={cn("h-11 w-11 rounded-full border-2 border-white/10 shadow-lg shadow-black/50 active:translate-y-0.5 active:shadow-sm select-none transition cursor-pointer",
          on ? (c === "r" ? "bg-red-500" : "bg-blue-500") : (c === "r" ? "bg-red-900/50 hover:bg-red-800/50" : "bg-blue-900/50 hover:bg-blue-800/50"))} />
    </div>
  );
}

const defaultCh = (out: "right" | "left"): ChannelState => ({
  frequency: 1000, intensity: 40, stimulus: "tone", transducer: "air",
  output: out, toneMode: "continuous", reversed: false, extRange: false,
  highFreq: false, step: 5, isPlaying: false, vuLevel: 0,
});
const I_MARKS = [0, 40, 80, 120].map((v) => ({ value: v, label: `${v}` }));
const transIdx = (t: string) => t === "bone" ? 1 : t === "free" ? 2 : 0;

export function AudiometerPlaceholder() {
  const [ch0, setCh0] = useState<ChannelState>(defaultCh("right"));
  const [ch1, setCh1] = useState<ChannelState>(defaultCh("left"));
  const [testMode, setTestMode] = useState<"umbrales" | "logo">("umbrales");
  const [points, setPoints] = useState<AudiogramPoint[]>([]);
  const [showAG, setShowAG] = useState(false);
  const [freq, setFreq] = useState(1000);
  const [step, setStep] = useState(5);
  const [extRange, setExtRange] = useState(false);
  const [highFreq, setHighFreq] = useState(false);
  const [logoOk, setLogoOk] = useState(0);
  const [logoN, setLogoN] = useState(25);
  const [secs, setSecs] = useState(0);
  const [timerOn, setTimerOn] = useState(false);
  const tmr = useRef<ReturnType<typeof setInterval>>(undefined);
  const v0 = useRef<ReturnType<typeof setInterval>>(undefined);
  const v1 = useRef<ReturnType<typeof setInterval>>(undefined);
  // Pulsatile timers
  const pulsTimer0 = useRef<ReturnType<typeof setInterval>>(undefined);
  const pulsTimer1 = useRef<ReturnType<typeof setInterval>>(undefined);
  const pulsPhase0 = useRef<"on" | "off">("on");
  const pulsPhase1 = useRef<"on" | "off">("on");
  // Alternate timer
  const altTimer = useRef<ReturnType<typeof setInterval>>(undefined);
  const altCount = useRef(0);
  const altPhase = useRef<"ipsi" | "silence">("ipsi");
  const altActiveCh = useRef(0);

  const u0 = useCallback((u: Partial<ChannelState>) => setCh0((p) => ({ ...p, ...u })), []);
  const u1 = useCallback((u: Partial<ChannelState>) => setCh1((p) => ({ ...p, ...u })), []);

  // Refs to always access current state in callbacks/timers
  const ch0Ref = useRef(ch0);
  const ch1Ref = useRef(ch1);
  useEffect(() => { ch0Ref.current = ch0; }, [ch0]);
  useEffect(() => { ch1Ref.current = ch1; }, [ch1]);

  // Sync shared state
  useEffect(() => { u0({ frequency: freq, step, extRange, highFreq }); u1({ frequency: freq, step, extRange, highFreq }); }, [freq, step, extRange, highFreq, u0, u1]);

  // Timer
  useEffect(() => {
    if (timerOn) tmr.current = setInterval(() => setSecs((s) => s + 1), 1000);
    else if (tmr.current) clearInterval(tmr.current);
    return () => { if (tmr.current) clearInterval(tmr.current); };
  }, [timerOn]);
  const tStr = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;

  // Frequency list based on transductor
  const freqList = getFrequencyList(transIdx(ch0.transducer), highFreq);
  const fi = freqList.indexOf(freq);
  const fP = () => { if (fi > 0) { setFreq(freqList[fi - 1]); setExtRange(false); resetChannels(); } };
  const fN = () => { if (fi < freqList.length - 1) { setFreq(freqList[fi + 1]); setExtRange(false); resetChannels(); } };

  // Intensity change with proper range per freq/transductor
  const changeIntensity = useCallback((ch: 0 | 1, dir: 1 | -1) => {
    const state = ch === 0 ? ch0 : ch1;
    const setter = ch === 0 ? u0 : u1;
    const ti = transIdx(state.transducer);
    const range = getIntensityRange(freq, ti, extRange);
    let newInt = calibrateToStep(state.intensity + dir * step, step);
    newInt = Math.max(range.min, Math.min(range.max, newInt));
    setter({ intensity: newInt });
  }, [ch0, ch1, freq, step, extRange, u0, u1]);

  // Audio play/stop — use refs for current state
  const playAudioFromRef = useCallback(async (chIdx: 0 | 1) => {
    const ch = chIdx === 0 ? ch0Ref.current : ch1Ref.current;
    const nm: Record<string, string> = { wn: "white", pn: "pink", sn: "speech", nbn: "narrowband" };
    try {
      if (nm[ch.stimulus]) {
        await invoke("play_noise", { params: { noiseType: nm[ch.stimulus], duration: 30, levelDbfs: ch.intensity - 80, ...(nm[ch.stimulus] === "narrowband" ? { centerHz: ch.frequency, bandwidthHz: ch.frequency * 0.15 } : {}) } });
      } else {
        await invoke("play_tone", { params: { frequency: ch.frequency, duration: 30, levelDbfs: ch.intensity - 80 } });
      }
    } catch { /* */ }
  }, []);
  const stopAudio = useCallback(async () => { try { await invoke("stop_playback"); } catch { /* */ } }, []);

  const vuOn = (s: typeof u0, r: typeof v0) => { if (r.current) clearInterval(r.current); r.current = setInterval(() => s({ vuLevel: 50 + Math.random() * 30 }), 100); };
  const vuOff = (s: typeof u0, r: typeof v0) => { if (r.current) clearInterval(r.current); r.current = undefined; s({ vuLevel: 0 }); };

  const startCh = useCallback((chIdx: 0 | 1) => {
    const setter = chIdx === 0 ? u0 : u1;
    const vuRef = chIdx === 0 ? v0 : v1;
    playAudioFromRef(chIdx);
    setter({ isPlaying: true });
    vuOn(setter, vuRef);
  }, [playAudioFromRef, u0, u1]);

  const stopCh = useCallback((chIdx: 0 | 1) => {
    const setter = chIdx === 0 ? u0 : u1;
    const vuRef = chIdx === 0 ? v0 : v1;
    stopAudio();
    setter({ isPlaying: false });
    vuOff(setter, vuRef);
  }, [stopAudio, u0, u1]);

  // Reset channels — stops both and replays if reversed
  const resetChannels = useCallback(() => {
    stopCh(0);
    stopCh(1);
    setTimeout(() => {
      if (ch0Ref.current.reversed && ch0Ref.current.stimulus !== "speech") startCh(0);
      if (ch1Ref.current.reversed && ch1Ref.current.stimulus !== "speech") startCh(1);
    }, 50);
  }, [stopCh, startCh]);

  // Pulsatile logic
  const stopPulsatile = useCallback((chIdx: 0 | 1) => {
    const ref = chIdx === 0 ? pulsTimer0 : pulsTimer1;
    if (ref.current) { clearInterval(ref.current); ref.current = undefined; }
  }, []);

  const startPulsatile = useCallback((chIdx: 0 | 1) => {
    const ref = chIdx === 0 ? pulsTimer0 : pulsTimer1;
    const phase = chIdx === 0 ? pulsPhase0 : pulsPhase1;
    stopPulsatile(chIdx);
    phase.current = "on";
    let elapsed = 0;
    ref.current = setInterval(() => {
      elapsed += 50;
      if (phase.current === "on" && elapsed >= PULSATILE_ON) {
        stopCh(chIdx);
        phase.current = "off";
        elapsed = 0;
      } else if (phase.current === "off" && elapsed >= PULSATILE_OFF) {
        startCh(chIdx);
        phase.current = "on";
        elapsed = 0;
      }
    }, 50);
  }, [stopPulsatile, startCh, stopCh]);

  // Alternate logic
  const stopAlternate = useCallback(() => {
    if (altTimer.current) { clearInterval(altTimer.current); altTimer.current = undefined; }
    stopCh(0);
    stopCh(1);
  }, [stopCh]);

  const startAlternate = useCallback((ipsiCh: 0 | 1) => {
    stopAlternate();
    altActiveCh.current = ipsiCh;
    altPhase.current = "ipsi";
    altCount.current = 0;
    altTimer.current = setInterval(() => {
      altCount.current += 1;
      const ch = altActiveCh.current;
      const contra = ch === 0 ? 1 : 0;
      if (altPhase.current === "ipsi") {
        if (altCount.current === 1) startCh(ch as 0 | 1);
        if (altCount.current >= ALTERNATE_IPSI) {
          stopCh(ch as 0 | 1);
          altPhase.current = "silence";
          altCount.current = 0;
          altActiveCh.current = contra;
        }
      } else {
        if (altCount.current >= ALTERNATE_SILENCE) {
          altPhase.current = "ipsi";
          altCount.current = 0;
        }
      }
    }, 100);
  }, [stopAlternate, startCh, stopCh]);

  // Stimulus press/release — reads from refs, no stale closures
  const handleStimPress = useCallback((chIdx: 0 | 1) => {
    const ch = chIdx === 0 ? ch0Ref.current : ch1Ref.current;

    if (ch.toneMode === "alternated") { startAlternate(chIdx); return; }

    if (ch.reversed) {
      stopCh(chIdx);
      if (ch.toneMode === "pulsed") stopPulsatile(chIdx);
    } else {
      startCh(chIdx);
      if (ch.toneMode === "pulsed") startPulsatile(chIdx);
    }
  }, [startCh, stopCh, startPulsatile, stopPulsatile, startAlternate]);

  const handleStimRelease = useCallback((chIdx: 0 | 1) => {
    const ch = chIdx === 0 ? ch0Ref.current : ch1Ref.current;

    if (ch.toneMode === "alternated") { stopAlternate(); return; }

    if (ch.reversed) {
      startCh(chIdx);
      if (ch.toneMode === "pulsed") startPulsatile(chIdx);
    } else {
      stopCh(chIdx);
      if (ch.toneMode === "pulsed") stopPulsatile(chIdx);
    }
  }, [startCh, stopCh, startPulsatile, stopPulsatile, stopAlternate]);

  // Reverse toggle
  const toggleReverse = useCallback((chIdx: 0 | 1) => {
    const ch = chIdx === 0 ? ch0Ref.current : ch1Ref.current;
    const setter = chIdx === 0 ? u0 : u1;
    const newRev = !ch.reversed;
    setter({ reversed: newRev });

    if (newRev && ch.stimulus !== "speech") {
      startCh(chIdx);
    } else if (!newRev) {
      stopCh(chIdx);
    }
  }, [u0, u1, startCh, stopCh]);

  // Stimulus change with auto Habla↔Umbrales logic
  const changeStim = useCallback((chIdx: 0 | 1, stim: StimulusType) => {
    const setter = chIdx === 0 ? u0 : u1;
    const otherSetter = chIdx === 0 ? u1 : u0;
    const otherCh = chIdx === 0 ? ch1Ref.current : ch0Ref.current;

    if (stim === "speech") {
      setTestMode("logo");
      otherSetter({ stimulus: "sn" });
    } else if (stim === "tone" || stim === "fm") {
      if (otherCh.stimulus === "sn" || otherCh.stimulus === "speech") {
        setTestMode("umbrales");
        otherSetter({ stimulus: "nbn" });
      }
    }

    setter({ stimulus: stim });
    resetChannels();
  }, [u0, u1, resetChannels]);

  // Keyboard shortcuts
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      if (k === "w") changeIntensity(0, 1);
      else if (k === "s") changeIntensity(0, -1);
      else if (k === "o") changeIntensity(1, 1);
      else if (k === "l") changeIntensity(1, -1);
      else if (k === "arrowleft") { e.preventDefault(); fP(); }
      else if (k === "arrowright") { e.preventDefault(); fN(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const reg = useCallback((chIdx: 0 | 1, nr = false) => {
    const ch = chIdx === 0 ? ch0Ref.current : ch1Ref.current;
    setPoints((p) => {
      const pt: AudiogramPoint = { frequency: ch.frequency, threshold: ch.intensity, type: ch.transducer === "bone" ? "bone" : "air", ear: ch.output, masked: false, noResponse: nr };
      return [...p.filter((x) => !(x.frequency === pt.frequency && x.ear === pt.ear && x.type === pt.type)), pt];
    });
  }, []);

  // Get enabled stimuli per channel
  const enabled0 = getEnabledStimuli(0);
  const enabled1 = getEnabledStimuli(1);

  // Intensity range for display
  const range0 = getIntensityRange(freq, transIdx(ch0.transducer), extRange);
  const range1 = getIntensityRange(freq, transIdx(ch1.transducer), extRange);

  // Tb and SBtn are defined outside the component to prevent re-mounting

  // Helper to render a channel config panel inline
  const stimLabels: Record<StimulusType, string> = { tone: "Tono", fm: "FM", nbn: "NBN", speech: "Habla", wn: "WN", sn: "SN", pn: "PN" };

  const renderChConfig = (chState: ChannelState, setCh: typeof setCh0, chIdx: 0 | 1, enabled: StimulusType[]) => (
    <div className="flex-1 rounded border border-white/[0.06] bg-black/20 p-2">
      <div className="mb-1 text-[8px] font-bold tracking-wider text-white/20">
        {chIdx === 0 ? "CANAL 1" : "CANAL 2"}
      </div>
      <div className="mb-1.5">
        <div className="mb-0.5 text-[7px] uppercase text-white/15">Estímulo</div>
        <div className="grid grid-cols-4 gap-1">
          {(["tone", "fm", "nbn", "speech", "wn", "sn", "pn"] as StimulusType[]).map((st) => {
            const dis = !enabled.includes(st);
            return <button key={st} disabled={dis} onClick={() => changeStim(chIdx, st)}
              className={cn("rounded border py-1 text-[9px] font-bold transition",
                chState.stimulus === st ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : dis ? "border-white/[0.03] text-white/[0.08]" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>{stimLabels[st]}</button>;
          })}
        </div>
      </div>
      <div className="flex gap-2">
        <div>
          <div className="mb-0.5 text-[7px] uppercase text-white/15">Transductor</div>
          <div className="flex gap-1">
            {([["air", "VA"], ["bone", "VO"], ["free", "CL"]] as const).map(([v, l]) => (
              <button key={v} onClick={() => { setCh((p) => ({ ...p, transducer: v as TransducerType })); resetChannels(); }}
                className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                  chState.transducer === v ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>{l}</button>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-0.5 text-[7px] uppercase text-white/15">Salida</div>
          <div className="flex gap-1">
            <button onClick={() => { setCh((p) => ({ ...p, output: "right" })); resetChannels(); }}
              className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                chState.output === "right" ? "border-red-500/40 bg-red-500/20 text-red-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OD</button>
            <button onClick={() => { setCh((p) => ({ ...p, output: "left" })); resetChannels(); }}
              className={cn("rounded border px-2.5 py-1 text-[9px] font-bold transition",
                chState.output === "left" ? "border-blue-500/40 bg-blue-500/20 text-blue-400" : "border-white/10 bg-white/[0.03] text-white/30 hover:bg-white/[0.08]")}>OI</button>
          </div>
        </div>
        <div className="ml-auto flex items-end gap-1">
          <button onClick={() => reg(chIdx)} className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[9px] font-bold text-emerald-400 hover:bg-emerald-500/20">Reg</button>
          <button onClick={() => reg(chIdx, true)} className="rounded border border-white/10 px-2 py-1 text-[9px] font-bold text-white/30 hover:bg-white/[0.06]">S/R</button>
        </div>
      </div>
    </div>
  );

  const logoText = testMode === "logo" ? `${logoOk}/${logoN} : ${logoN > 0 ? Math.round((logoOk / logoN) * 100) : 0}%` : undefined;

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
        <div className="flex h-6 shrink-0 items-center justify-between bg-[#1e2127] px-3">
          <span className="text-[9px] font-bold tracking-[0.2em] text-white/30">LABSIM <span className="font-normal text-white/12">DA-80</span></span>
          <div className="flex items-center gap-2">
            <ToggleSwitch value={testMode} onChange={(v) => setTestMode(v as "umbrales" | "logo")} options={[{ value: "umbrales", label: "Umbrales" }, { value: "logo", label: "Logo" }]} />
            <button onClick={() => setShowAG(!showAG)} className="text-white/20 hover:text-white/40">
              {showAG ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
            </button>
            <button onClick={() => setPoints([])} className="text-white/15 hover:text-white/30"><RotateCcw className="h-3 w-3" /></button>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-2 p-3 overflow-hidden">
          <UnifiedDisplay ch0={ch0} ch1={ch1} frequency={freq} testMode={testMode === "logo" ? "logoaudiometria" : "umbrales"} time={tStr} logoText={logoText} />

          <div className="flex gap-2">
            <div className="flex-1"><VuMeter level={ch0.vuLevel} active={ch0.isPlaying} height={14} /></div>
            <div className="flex-1"><VuMeter level={ch1.vuLevel} active={ch1.isPlaying} height={14} /></div>
          </div>

          <div className="flex gap-3">
            {renderChConfig(ch0, setCh0, 0, enabled0)}
            {renderChConfig(ch1, setCh1, 1, enabled1)}
          </div>

          {/* KNOBS ROW */}
          <div className="flex flex-1 items-center border-t border-white/[0.06] pt-2">
            <div className="flex-shrink-0">
              <RotaryKnob value={ch0.intensity} min={range0.min} max={range0.max}
                step={step} onChange={(v) => u0({ intensity: v })} label="CH 1" size="lg" marks={I_MARKS} />
            </div>

            <div className="mx-3 flex flex-col items-center gap-1">
              <Tb on={ch0.toneMode === "pulsed"} click={() => setCh0((p) => ({ ...p, toneMode: p.toneMode === "pulsed" ? "continuous" : "pulsed" }))}> Pulso</Tb>
              <Tb on={ch0.reversed} click={() => toggleReverse(0)}> Revers</Tb>
              <SBtn on={ch0.isPlaying} d={() => handleStimPress(0)} u={() => handleStimRelease(0)} c="r" />
              <Tb on={ch0.toneMode === "alternated"} click={() => { setCh0((p) => ({ ...p, toneMode: p.toneMode === "alternated" ? "continuous" : "alternated" })); setCh1((p) => ({ ...p, toneMode: p.toneMode === "alternated" ? "continuous" : "alternated" })); }}> Alter</Tb>
            </div>

            <div className="flex flex-1 items-center justify-center gap-3">
              <button onClick={fP} disabled={fi <= 0}
                className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white/10 bg-white/[0.04] text-white/40 transition hover:bg-white/10 disabled:opacity-20">
                <ChevronLeft className="h-5 w-5" />
              </button>
              <div className="flex flex-col items-center gap-1">
                <ToggleSwitch label="Pasos dB" value={String(step)} onChange={(v) => setStep(Number(v))}
                  options={[{ value: "1", label: "1" }, { value: "3", label: "3" }, { value: "5", label: "5" }]} />
                <div className="flex gap-1">
                  <Tb on={extRange} click={() => setExtRange(!extRange)}> Ext.Rango</Tb>
                  <Tb on={highFreq} click={() => setHighFreq(!highFreq)}> Alt.Freq</Tb>
                </div>
              </div>
              <button onClick={fN} disabled={fi >= freqList.length - 1}
                className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-white/10 bg-white/[0.04] text-white/40 transition hover:bg-white/10 disabled:opacity-20">
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            <div className="mx-3 flex flex-col items-center gap-1">
              <Tb on={ch1.toneMode === "pulsed"} click={() => setCh1((p) => ({ ...p, toneMode: p.toneMode === "pulsed" ? "continuous" : "pulsed" }))}> Pulso</Tb>
              <Tb on={ch1.reversed} click={() => toggleReverse(1)}> Revers</Tb>
              <SBtn on={ch1.isPlaying} d={() => handleStimPress(1)} u={() => handleStimRelease(1)} c="b" />
            </div>

            <div className="flex-shrink-0">
              <RotaryKnob value={ch1.intensity} min={range1.min} max={range1.max}
                step={step} onChange={(v) => u1({ intensity: v })} label="CH 2" size="lg" marks={I_MARKS} />
            </div>
          </div>

          {/* Timer + Logo */}
          <div className="flex shrink-0 items-center justify-center gap-3 text-[9px]">
            <button onClick={() => setTimerOn(true)} className="text-emerald-400/60 hover:text-emerald-400">Iniciar</button>
            <button onClick={() => setTimerOn(false)} className="text-amber-400/60 hover:text-amber-400">Detener</button>
            <button onClick={() => { setTimerOn(false); setSecs(0); }} className="text-white/25 hover:text-white/50">Borrar</button>
            {testMode === "logo" && (
              <>
                <span className="h-3 w-px bg-white/10" />
                <button onClick={() => { setLogoOk((c) => c + 1); }} className="font-bold text-emerald-400/70">+1</button>
                <button onClick={() => { setLogoOk((c) => Math.max(0, c - 1)); }} className="font-bold text-red-400/70">-1</button>
                <button onClick={() => { setLogoOk(0); setLogoN(25); }} className="text-white/25">Limpiar</button>
              </>
            )}
          </div>
        </div>

        <div className="flex h-5 shrink-0 items-center justify-between bg-black/25 px-3 text-[8px] text-white/20">
          <span>W/S: CH1 dB | ←→: Freq</span>
          <span>{freq} Hz | Rango: {range0.min}~{range0.max} dB</span>
          <span>O/L: CH2 dB</span>
        </div>
      </div>
    </div>
  );
}
