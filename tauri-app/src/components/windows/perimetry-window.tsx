import { useState, useCallback, useRef, useEffect } from "react";
import { VisualFieldMap } from "@/components/perimetry/visual-field-map";
import { EyeCamera } from "@/components/perimetry/eye-camera";
import { GazePlot } from "@/components/perimetry/gaze-plot";
import { ReliabilityPanel } from "@/components/perimetry/reliability-panel";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import {
  PATTERNS, normalSensitivity,
  type PointResult, type ReliabilityIndices, type Strategy,
  STIMULUS_SIZES, type StimulusSize,
} from "@/lib/perimetry-config";
import { cn } from "@/lib/utils";
import { Play, Square, RotateCcw, Pause } from "lucide-react";

type ViewMode = "numeric" | "grayscale" | "deviation";
type TestState = "idle" | "running" | "paused" | "done";

export function PerimetryWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [pattern, setPattern] = useState("24-2");
  const [strategy, setStrategy] = useState<Strategy>("sita-standard");
  const [stimSize, setStimSize] = useState<StimulusSize>("III");
  const [viewMode, setViewMode] = useState<ViewMode>("numeric");
  const [testState, setTestState] = useState<TestState>("idle");
  const [currentPoint, setCurrentPoint] = useState<number | null>(null);
  const [points, setPoints] = useState<PointResult[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [isFixating, setIsFixating] = useState(true);
  const [gazeHistory, setGazeHistory] = useState<{ x: number; y: number; fixating: boolean }[]>([]);
  const [reliability, setReliability] = useState<ReliabilityIndices>({
    fixationLosses: 0, fixationLossesTotal: 0,
    falsePositives: 0, falsePositivesTotal: 0,
    falseNegatives: 0, falseNegativesTotal: 0,
  });

  const timerRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const testRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const gazeRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const initPoints = useCallback(() => {
    const coords = PATTERNS[pattern] ?? PATTERNS["24-2"];
    setPoints(coords.map(([x, y]) => ({ x, y, sensitivity: null, seen: false })));
    setCurrentPoint(null);
    setReliability({ fixationLosses: 0, fixationLossesTotal: 0, falsePositives: 0, falsePositivesTotal: 0, falseNegatives: 0, falseNegativesTotal: 0 });
    setElapsed(0);
    setGazeHistory([]);
  }, [pattern]);

  useEffect(() => { initPoints(); }, [initPoints]);

  const stopAll = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = undefined; }
    if (testRef.current) { clearInterval(testRef.current); testRef.current = undefined; }
    if (gazeRef.current) { clearInterval(gazeRef.current); gazeRef.current = undefined; }
  }, []);

  const startTest = useCallback(() => {
    if (testState === "idle" || testState === "done") initPoints();
    setTestState("running");

    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);

    // Simulate gaze data
    gazeRef.current = setInterval(() => {
      const fixing = Math.random() > 0.08;
      setIsFixating(fixing);
      setGazeHistory((h) => {
        const x = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 15;
        const y = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 12;
        return [...h.slice(-100), { x, y, fixating: fixing }];
      });
    }, 200);

    // Test point progression
    testRef.current = setInterval(() => {
      setPoints((pts) => {
        const untested = pts.map((p, i) => ({ p, i })).filter(({ p }) => p.sensitivity === null);
        if (untested.length === 0) {
          stopAll();
          setTestState("done");
          return pts;
        }
        const { i } = untested[Math.floor(Math.random() * untested.length)];
        setCurrentPoint(i);

        const norm = normalSensitivity(pts[i].x, pts[i].y);
        const sensitivity = Math.max(0, Math.min(40, Math.round(norm + (Math.random() - 0.5) * 8)));

        // Reliability checks
        setReliability((r) => {
          const newR = { ...r, fixationLossesTotal: r.fixationLossesTotal + 1 };
          if (Math.random() < 0.08) newR.fixationLosses++;
          if (Math.random() < 0.04) { newR.falsePositivesTotal++; if (Math.random() < 0.1) newR.falsePositives++; }
          if (Math.random() < 0.04) { newR.falseNegativesTotal++; if (Math.random() < 0.08) newR.falseNegatives++; }
          return newR;
        });

        const newPts = [...pts];
        newPts[i] = { ...pts[i], sensitivity, seen: sensitivity > 0, totalDeviation: sensitivity - norm };
        return newPts;
      });
    }, 900 + Math.random() * 1200);
  }, [testState, initPoints, stopAll]);

  const pauseTest = useCallback(() => { stopAll(); setTestState("paused"); }, [stopAll]);
  const resetTest = useCallback(() => { stopAll(); setTestState("idle"); initPoints(); }, [stopAll, initPoints]);
  useEffect(() => () => stopAll(), [stopAll]);

  const tested = points.filter((p) => p.sensitivity !== null).length;
  const total = points.length;
  const progress = total > 0 ? Math.round((tested / total) * 100) : 0;
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  const testedPts = points.filter((p) => p.sensitivity !== null);
  const md = testedPts.length > 0 ? (testedPts.reduce((s, p) => s + (p.totalDeviation ?? 0), 0) / testedPts.length).toFixed(1) : "—";
  const flPct = reliability.fixationLossesTotal > 0 ? Math.round((reliability.fixationLosses / reliability.fixationLossesTotal) * 100) : 0;

  const stratLabel = strategy === "sita-standard" ? "SITA Standard" : strategy === "sita-fast" ? "SITA Fast" : "Full Threshold";

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#12151a] to-[#0d0f13]">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between bg-[#0a0c10] px-3">
        <span className="text-[9px] font-bold tracking-[0.2em] text-white/30">LABSIM <span className="font-normal text-white/12">PERIMETRY HFA-III</span></span>
        <span className="text-[8px] text-white/15">{eye} | {pattern} | {stratLabel} | Goldmann {stimSize}</span>
      </div>

      {/* Main layout: 3 columns */}
      <div className="flex flex-1 overflow-hidden gap-2 p-2">

        {/* LEFT COLUMN: Eye camera + Gaze plot + Controls */}
        <div className="flex w-[170px] shrink-0 flex-col gap-2">
          {/* Eye camera */}
          <EyeCamera isFixating={isFixating} isRunning={testState === "running"} eye={eye} />

          {/* Gaze tracking */}
          <GazePlot gazeHistory={gazeHistory} />

          {/* Fixation status */}
          <div className={cn("flex items-center justify-center gap-2 rounded border p-1.5",
            isFixating ? "border-emerald-500/20 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5 animate-pulse"
          )}>
            <div className={cn("h-3 w-3 rounded-full", isFixating ? "bg-emerald-400" : "bg-red-400")} />
            <span className={cn("text-[9px] font-bold", isFixating ? "text-emerald-400" : "text-red-400")}>
              {isFixating ? "FIJANDO" : "PÉRDIDA"}
            </span>
            <span className="text-[8px] text-white/25">{flPct}%</span>
          </div>

          {/* Progress */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 flex justify-between text-[8px]">
              <span className="text-white/25">Progreso</span>
              <span className="font-mono font-bold text-white/50">{tested}/{total}</span>
            </div>
            <div className="h-2 rounded-full bg-black/40">
              <div className="h-full rounded-full bg-emerald-500/60 transition-all" style={{ width: `${progress}%` }} />
            </div>
            <div className="mt-1 flex justify-between text-[8px]">
              <span className="text-white/25">Tiempo</span>
              <span className="font-mono font-bold text-white/50">{mins}:{String(secs).padStart(2, "0")}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex gap-1">
            {testState !== "running" ? (
              <button onClick={startTest}
                className="flex flex-1 items-center justify-center gap-1 rounded border border-emerald-500/30 bg-emerald-500/10 py-2 text-[10px] font-bold text-emerald-400 hover:bg-emerald-500/20">
                <Play className="h-3.5 w-3.5" />
                {testState === "paused" ? "Continuar" : "Iniciar"}
              </button>
            ) : (
              <button onClick={pauseTest}
                className="flex flex-1 items-center justify-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 py-2 text-[10px] font-bold text-amber-400 hover:bg-amber-500/20">
                <Pause className="h-3.5 w-3.5" />
                Pausar
              </button>
            )}
            <button onClick={resetTest}
              className="flex items-center justify-center rounded border border-white/10 px-3 py-2 text-white/25 hover:bg-white/[0.06]">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* CENTER: Visual field map */}
        <div className="flex flex-1 flex-col gap-1 min-w-0">
          <div className="flex-1 min-h-0">
            <VisualFieldMap points={points} currentPoint={currentPoint} eye={eye} mode={viewMode} />
          </div>
          {/* View mode selector */}
          <div className="flex items-center justify-center">
            <ToggleSwitch value={viewMode} onChange={(v) => setViewMode(v as ViewMode)} options={[
              { value: "numeric", label: "Numérico" },
              { value: "grayscale", label: "Escala Gris" },
              { value: "deviation", label: "Desviación" },
            ]} />
          </div>
        </div>

        {/* RIGHT COLUMN: Configuration + Reliability + Results */}
        <div className="flex w-[160px] shrink-0 flex-col gap-2">
          {/* Protocol config */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2 space-y-1.5">
            <div className="text-[8px] font-bold uppercase tracking-wider text-white/25">Protocolo</div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Ojo</div>
              <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); resetTest(); }} options={[
                { value: "OD", label: "OD", color: "bg-red-600 text-white" },
                { value: "OI", label: "OI", color: "bg-blue-600 text-white" },
              ]} />
            </div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Patrón</div>
              <ToggleSwitch value={pattern} onChange={setPattern} options={[
                { value: "24-2", label: "24-2" },
                { value: "30-2", label: "30-2" },
                { value: "10-2", label: "10-2" },
              ]} />
            </div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Estrategia</div>
              <ToggleSwitch value={strategy} onChange={(v) => setStrategy(v as Strategy)} options={[
                { value: "sita-standard", label: "Std" },
                { value: "sita-fast", label: "Fast" },
                { value: "full-threshold", label: "Full" },
              ]} />
            </div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Estímulo Goldmann</div>
              <ToggleSwitch value={stimSize} onChange={(v) => setStimSize(v as StimulusSize)} options={
                STIMULUS_SIZES.map((s) => ({ value: s, label: s }))
              } />
            </div>
          </div>

          {/* Reliability */}
          <ReliabilityPanel indices={reliability} />

          {/* Results */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[8px] font-bold uppercase tracking-wider text-white/25">Resultados</div>
            <div className="space-y-0.5 text-[9px]">
              <div className="flex justify-between">
                <span className="text-white/30">DM:</span>
                <span className={cn("font-mono font-bold", Number(md) < -3 ? "text-red-400/70" : "text-emerald-400/70")}>{md} dB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/30">Estado:</span>
                <span className={cn("font-bold text-[8px]",
                  testState === "running" ? "text-emerald-400" : testState === "paused" ? "text-amber-400" : testState === "done" ? "text-blue-400" : "text-white/30",
                )}>{testState === "running" ? "Ejecutando" : testState === "paused" ? "Pausado" : testState === "done" ? "Completo" : "Configurar"}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-5 shrink-0 items-center justify-between bg-black/30 px-3 text-[7px] text-white/15">
        <span>{eye} | {pattern} | {stratLabel} | Goldmann {stimSize}</span>
        <span>{testState === "done" ? "Test completado" : `${progress}% completado`}</span>
      </div>
    </div>
  );
}
