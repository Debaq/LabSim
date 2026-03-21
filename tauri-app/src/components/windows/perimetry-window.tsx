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
import { usePatientStore } from "@/stores/patient-store";
import { cn } from "@/lib/utils";
import { Play, RotateCcw, Pause, Link2, Link2Off } from "lucide-react";

type ViewMode = "numeric" | "grayscale" | "deviation";
type TestState = "idle" | "running" | "paused" | "done";

type DefectType =
  | "normal" | "escotoma-arcuato-sup" | "escotoma-arcuato-inf" | "escotoma-arcuato-doble"
  | "escalon-nasal" | "hemianopsia-homonima-der" | "hemianopsia-homonima-izq"
  | "hemianopsia-bitemporal" | "cuadrantanopsia-sup" | "cuadrantanopsia-inf"
  | "depresion-general" | "isla-central" | "constriccion-periferica";

type Severity = "leve" | "moderado" | "severo";

// Generate defect-aware sensitivity for a point
function defectSensitivity(
  x: number, y: number, defect: DefectType, severity: Severity, mdTarget: number | null,
): number {
  const norm = normalSensitivity(x, y);
  const sevFactor = severity === "leve" ? 0.4 : severity === "moderado" ? 0.7 : 1.0;
  const noise = (Math.random() - 0.5) * 4;

  let loss = 0;

  switch (defect) {
    case "normal":
      return Math.max(0, Math.min(40, Math.round(norm + noise)));

    case "escotoma-arcuato-sup":
      // Superior arcuate: affects inferior visual field (y < 0), nasal side
      if (y < -3 && x > -3) loss = 18 * sevFactor * Math.exp(-((y + 12) ** 2) / 120);
      break;

    case "escotoma-arcuato-inf":
      // Inferior arcuate: affects superior visual field (y > 0), nasal side
      if (y > 3 && x > -3) loss = 18 * sevFactor * Math.exp(-((y - 12) ** 2) / 120);
      break;

    case "escotoma-arcuato-doble":
      if (y < -3 && x > -3) loss = 16 * sevFactor * Math.exp(-((y + 12) ** 2) / 120);
      if (y > 3 && x > -3) loss += 16 * sevFactor * Math.exp(-((y - 12) ** 2) / 120);
      break;

    case "escalon-nasal":
      // Nasal step: difference at horizontal midline, nasal side
      if (x > 6) loss = 12 * sevFactor * (y < 0 ? 1 : 0.2);
      break;

    case "hemianopsia-homonima-der":
      if (x > 0) loss = 28 * sevFactor;
      break;

    case "hemianopsia-homonima-izq":
      if (x < 0) loss = 28 * sevFactor;
      break;

    case "hemianopsia-bitemporal":
      // Temporal side affected for both eyes — here we don't know the eye,
      // so we affect x < 0 (temporal for OD). Caller should flip for OI.
      if (x < 0) loss = 28 * sevFactor;
      break;

    case "cuadrantanopsia-sup":
      if (y > 0 && x > 0) loss = 26 * sevFactor;
      break;

    case "cuadrantanopsia-inf":
      if (y < 0 && x > 0) loss = 26 * sevFactor;
      break;

    case "depresion-general":
      loss = 10 * sevFactor;
      break;

    case "isla-central": {
      const ecc = Math.sqrt(x * x + y * y);
      if (ecc > 10) loss = 25 * sevFactor;
      break;
    }

    case "constriccion-periferica": {
      const ecc2 = Math.sqrt(x * x + y * y);
      if (ecc2 > 15) loss = 22 * sevFactor;
      else if (ecc2 > 10) loss = 12 * sevFactor;
      break;
    }
  }

  let sensitivity = norm - loss + noise;

  // Apply MD target adjustment if specified
  if (mdTarget !== null) {
    const currentDev = sensitivity - norm;
    const targetDev = mdTarget; // MD is negative for loss
    const adjustment = (targetDev - currentDev) * 0.3;
    sensitivity += adjustment;
  }

  return Math.max(0, Math.min(40, Math.round(sensitivity)));
}

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

  // Case data from patient store
  const vfConfig = usePatientStore((s) => s.data.visualField);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const hasCaseLoaded = patientId !== null && Object.keys(vfConfig).length > 0;

  // Current eye case config
  const getEyeConfig = useCallback(() => {
    if (!hasCaseLoaded) return null;
    const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
    return (vfConfig as Record<string, Record<string, unknown>>)[eyeKey] ?? null;
  }, [hasCaseLoaded, eye, vfConfig]);

  // Sync protocol from case
  useEffect(() => {
    const cfg = getEyeConfig();
    if (!cfg) return;
    if (cfg.patron && typeof cfg.patron === "string") setPattern(cfg.patron);
    if (cfg.estrategia && typeof cfg.estrategia === "string") setStrategy(cfg.estrategia as Strategy);
    if (cfg.tamanoEstimulo && typeof cfg.tamanoEstimulo === "string") setStimSize(cfg.tamanoEstimulo as StimulusSize);
  }, [getEyeConfig]);

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

    const cfg = getEyeConfig();
    const defect: DefectType = (cfg?.defecto as DefectType) ?? "normal";
    const severity: Severity = (cfg?.severidad as Severity) ?? "moderado";
    const mdTarget = cfg?.mdObjetivo != null ? Number(cfg.mdObjetivo) : null;
    const goodReliability = cfg?.confiabilidadBuena !== false;

    const flRate = goodReliability ? 0.05 : 0.18;
    const fpRate = goodReliability ? 0.03 : 0.12;
    const fnRate = goodReliability ? 0.02 : 0.10;

    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);

    gazeRef.current = setInterval(() => {
      const fixing = Math.random() > (goodReliability ? 0.06 : 0.15);
      setIsFixating(fixing);
      setGazeHistory((h) => {
        const x = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 15;
        const y = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 12;
        return [...h.slice(-100), { x, y, fixating: fixing }];
      });
    }, 200);

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

        // For bitemporal hemianopsia, flip x for OI
        let px = pts[i].x;
        const py = pts[i].y;
        if (defect === "hemianopsia-bitemporal" && eye === "OI") px = -px;

        const sensitivity = defectSensitivity(px, py, defect, severity, mdTarget);
        const norm = normalSensitivity(pts[i].x, pts[i].y);

        setReliability((r) => {
          const newR = { ...r, fixationLossesTotal: r.fixationLossesTotal + 1 };
          if (Math.random() < flRate) newR.fixationLosses++;
          if (Math.random() < 0.08) { newR.falsePositivesTotal++; if (Math.random() < fpRate) newR.falsePositives++; }
          if (Math.random() < 0.08) { newR.falseNegativesTotal++; if (Math.random() < fnRate) newR.falseNegatives++; }
          return newR;
        });

        const newPts = [...pts];
        newPts[i] = { ...pts[i], sensitivity, seen: sensitivity > 0, totalDeviation: sensitivity - norm };
        return newPts;
      });
    }, strategy === "sita-fast" ? 600 + Math.random() * 800 : 900 + Math.random() * 1200);
  }, [testState, initPoints, stopAll, getEyeConfig, eye, strategy]);

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
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">LABSIM <span className="font-normal ls-text-muted">PERIMETRY HFA-III</span></span>
        <div className="flex items-center gap-2 text-xs ls-text-muted">
          {hasCaseLoaded ? (
            <span className="flex items-center gap-1 text-emerald-400/70">
              <Link2 className="h-3 w-3" /> Caso
            </span>
          ) : (
            <span className="flex items-center gap-1 ls-text-muted">
              <Link2Off className="h-3 w-3" /> Libre
            </span>
          )}
          <span>|</span>
          <span>{eye} | {pattern} | {stratLabel} | Goldmann {stimSize}</span>
        </div>
      </div>

      {/* Main layout: 3 columns */}
      <div className="flex flex-1 overflow-hidden gap-2 p-2">

        {/* LEFT COLUMN */}
        <div className="flex w-[170px] shrink-0 flex-col gap-2">
          <EyeCamera isFixating={isFixating} isRunning={testState === "running"} eye={eye} />
          <GazePlot gazeHistory={gazeHistory} />

          <div className={cn("flex items-center justify-center gap-2 rounded border p-1.5",
            isFixating ? "border-emerald-500/20 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5 animate-pulse"
          )}>
            <div className={cn("h-3 w-3 rounded-full", isFixating ? "bg-emerald-400" : "bg-red-400")} />
            <span className={cn("text-xs font-bold", isFixating ? "text-emerald-400" : "text-red-400")}>
              {isFixating ? "FIJANDO" : "PÉRDIDA"}
            </span>
            <span className="text-xs ls-text-muted">{flPct}%</span>
          </div>

          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 flex justify-between text-xs">
              <span className="ls-text-muted">Progreso</span>
              <span className="font-mono font-bold ls-text2">{tested}/{total}</span>
            </div>
            <div className="h-2 rounded-full bg-black/40">
              <div className="h-full rounded-full bg-emerald-500/60 transition-all" style={{ width: `${progress}%` }} />
            </div>
            <div className="mt-1 flex justify-between text-xs">
              <span className="ls-text-muted">Tiempo</span>
              <span className="font-mono font-bold ls-text2">{mins}:{String(secs).padStart(2, "0")}</span>
            </div>
          </div>

          <div className="flex gap-1">
            {testState !== "running" ? (
              <button onClick={startTest}
                className="flex flex-1 items-center justify-center gap-1 rounded border border-emerald-500/30 bg-emerald-500/10 py-2 text-xs font-bold text-emerald-400 hover:bg-emerald-500/20">
                <Play className="h-3.5 w-3.5" />
                {testState === "paused" ? "Continuar" : "Iniciar"}
              </button>
            ) : (
              <button onClick={pauseTest}
                className="flex flex-1 items-center justify-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 py-2 text-xs font-bold text-amber-400 hover:bg-amber-500/20">
                <Pause className="h-3.5 w-3.5" />
                Pausar
              </button>
            )}
            <button onClick={resetTest}
              className="flex items-center justify-center rounded border ls-border px-3 py-2 ls-text-muted hover:ls-bg-input">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* CENTER */}
        <div className="flex flex-1 flex-col gap-1 min-w-0">
          <div className="flex-1 min-h-0">
            <VisualFieldMap points={points} currentPoint={currentPoint} eye={eye} mode={viewMode} />
          </div>
          <div className="flex items-center justify-center">
            <ToggleSwitch value={viewMode} onChange={(v) => setViewMode(v as ViewMode)} options={[
              { value: "numeric", label: "Numérico" },
              { value: "grayscale", label: "Escala Gris" },
              { value: "deviation", label: "Desviación" },
            ]} />
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="flex w-[160px] shrink-0 flex-col gap-2">
          <div className="rounded border ls-border ls-bg-panel2 p-2 space-y-1.5">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">Protocolo</div>

            <div>
              <div className="mb-0.5 text-xs uppercase ls-text-muted">Ojo</div>
              <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); resetTest(); }} options={[
                { value: "OD", label: "OD", color: "bg-red-600 ls-text" },
                { value: "OI", label: "OI", color: "bg-blue-600 ls-text" },
              ]} />
            </div>

            {!hasCaseLoaded && (
              <>
                <div>
                  <div className="mb-0.5 text-xs uppercase ls-text-muted">Patrón</div>
                  <ToggleSwitch value={pattern} onChange={setPattern} options={[
                    { value: "24-2", label: "24-2" },
                    { value: "30-2", label: "30-2" },
                    { value: "10-2", label: "10-2" },
                  ]} />
                </div>

                <div>
                  <div className="mb-0.5 text-xs uppercase ls-text-muted">Estrategia</div>
                  <ToggleSwitch value={strategy} onChange={(v) => setStrategy(v as Strategy)} options={[
                    { value: "sita-standard", label: "Std" },
                    { value: "sita-fast", label: "Fast" },
                    { value: "full-threshold", label: "Full" },
                  ]} />
                </div>

                <div>
                  <div className="mb-0.5 text-xs uppercase ls-text-muted">Estímulo Goldmann</div>
                  <ToggleSwitch value={stimSize} onChange={(v) => setStimSize(v as StimulusSize)} options={
                    STIMULUS_SIZES.map((s) => ({ value: s, label: s }))
                  } />
                </div>
              </>
            )}

            {hasCaseLoaded && (
              <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-1.5">
                <span className="text-xs text-emerald-400/80">
                  Protocolo definido por el caso clínico
                </span>
              </div>
            )}
          </div>

          <ReliabilityPanel indices={reliability} />

          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Resultados</div>
            <div className="space-y-0.5 text-xs">
              <div className="flex justify-between">
                <span className="ls-text-muted">DM:</span>
                <span className={cn("font-mono font-bold", Number(md) < -3 ? "text-red-400/70" : "text-emerald-400/70")}>{md} dB</span>
              </div>
              <div className="flex justify-between">
                <span className="ls-text-muted">Estado:</span>
                <span className={cn("font-bold text-xs",
                  testState === "running" ? "text-emerald-400" : testState === "paused" ? "text-amber-400" : testState === "done" ? "text-blue-400" : "ls-text-muted",
                )}>{testState === "running" ? "Ejecutando" : testState === "paused" ? "Pausado" : testState === "done" ? "Completo" : "Configurar"}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-5 shrink-0 items-center justify-between ls-bg-panel2 px-3 text-xs ls-text-muted">
        <span>{eye} | {pattern} | {stratLabel} | Goldmann {stimSize}</span>
        <span>{testState === "done" ? "Test completado" : `${progress}% completado`}</span>
      </div>
    </div>
  );
}
