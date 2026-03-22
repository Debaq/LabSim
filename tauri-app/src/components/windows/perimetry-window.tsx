/**
 * Campímetro LabSim — Perimetría Automatizada
 *
 * Simula un Humphrey HFA III real.
 * El test presenta estímulos uno por uno y el paciente simulado
 * responde según sus datos fisiológicos + cooperación + fatiga.
 * El estudiante controla el equipo, no observa una animación.
 */

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { VisualFieldMap } from "@/components/perimetry/visual-field-map";
import { EyeCamera } from "@/components/perimetry/eye-camera";
import { GazePlot } from "@/components/perimetry/gaze-plot";
import { PerimetryControls, type PerimetrySettings } from "@/components/perimetry/perimetry-controls";
import { PerimetryResults } from "@/components/perimetry/perimetry-results";
import { StimulusDisplay } from "@/components/perimetry/stimulus-display";
import {
  initTestState,
  executePresentation,
  applyPresentation,
  type TestState,
  type TestConfig,
  type PresentationResult,
} from "@/components/perimetry/perimetry-test-engine";
import { normalSensitivity, type Strategy, type StimulusSize } from "@/lib/perimetry-config";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import type { VFEyeConfig } from "@/modules/visual-field/schema";
import { cn } from "@/lib/utils";
import { Play, Pause, RotateCcw, Link2, Link2Off } from "lucide-react";

type ViewMode = "numeric" | "grayscale" | "deviation";

export function PerimetryWindow() {
  const [settings, setSettings] = useState<PerimetrySettings>({
    eye: "OD",
    pattern: "24-2",
    strategy: "sita-standard" as Strategy,
    stimulusSize: "III" as StimulusSize,
  });
  const [viewMode, setViewMode] = useState<ViewMode>("numeric");
  const [testState, setTestState] = useState<TestState | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [lastResponse, setLastResponse] = useState<PresentationResult | null>(null);
  const [isFixating, setIsFixating] = useState(true);
  const [gazeHistory, setGazeHistory] = useState<{ x: number; y: number; fixating: boolean }[]>([]);

  const testRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const timerRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const gazeRef = useRef<ReturnType<typeof setInterval>>(undefined);

  // Patient data
  const vfConfig = usePatientStore((s) => s.data.modules.visualField ?? {});
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const hasCaseLoaded = patientId !== null && Object.keys(vfConfig).length > 0;

  const eyeKey = settings.eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
  const eyeConfig: VFEyeConfig = (vfConfig[eyeKey] as VFEyeConfig) ?? {};

  // Sync settings from case
  useEffect(() => {
    if (!hasCaseLoaded || !eyeConfig) return;
    if (eyeConfig.patron) setSettings((s) => ({ ...s, pattern: eyeConfig.patron! }));
    if (eyeConfig.estrategia) setSettings((s) => ({ ...s, strategy: eyeConfig.estrategia as Strategy }));
    if (eyeConfig.tamanoEstimulo) setSettings((s) => ({ ...s, stimulusSize: eyeConfig.tamanoEstimulo as StimulusSize }));
  }, [hasCaseLoaded, eyeConfig]);

  const seed = useMemo(() => {
    if (!patientId) return 42;
    return patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) + (settings.eye === "OI" ? 1000 : 0);
  }, [patientId, settings.eye]);

  // ─── Test loop ─────────────────────────────────────

  const stopAll = useCallback(() => {
    if (testRef.current) { clearTimeout(testRef.current); testRef.current = undefined; }
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = undefined; }
    if (gazeRef.current) { clearInterval(gazeRef.current); gazeRef.current = undefined; }
    setIsRunning(false);
  }, []);

  const presentNext = useCallback(() => {
    setTestState((prev) => {
      if (!prev || prev.phase === "done") {
        stopAll();
        return prev;
      }

      const config: TestConfig = {
        pattern: settings.pattern,
        strategy: settings.strategy,
        eye: settings.eye,
        eyeConfig,
        seed,
      };

      const result = executePresentation(prev, config);
      if (!result) {
        stopAll();
        return { ...prev, phase: "done" };
      }

      setLastResponse(result);
      setIsFixating(result.response.wasFixating);

      // Gaze update
      setGazeHistory((h) => {
        const fixing = result.response.wasFixating;
        const x = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 15;
        const y = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 12;
        return [...h.slice(-100), { x, y, fixating: fixing }];
      });

      const updated = applyPresentation(prev, result, settings.strategy);

      // Schedule next presentation
      const delay = settings.strategy === "sita-fast"
        ? 600 + Math.random() * 600
        : 900 + Math.random() * 900;

      // Add patient reaction time
      const rtDelay = result.response.reactionTimeMs ?? 0;

      testRef.current = setTimeout(() => presentNext(), delay + rtDelay);

      return updated;
    });
  }, [settings, eyeConfig, seed, stopAll]);

  const startTest = useCallback(() => {
    stopAll();

    const config: TestConfig = {
      pattern: settings.pattern,
      strategy: settings.strategy,
      eye: settings.eye,
      eyeConfig,
      seed,
    };

    const initial = initTestState(config);
    initial.phase = "presenting";
    initial.startedAt = Date.now();
    setTestState(initial);
    setIsRunning(true);
    setElapsed(0);
    setLastResponse(null);
    setGazeHistory([]);

    addEvent({ type: "test_start", simulator: "perimetry", details: `${settings.eye} ${settings.pattern} ${settings.strategy}` });

    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    gazeRef.current = setInterval(() => {
      setGazeHistory((h) => {
        const fixing = Math.random() > 0.1;
        setIsFixating(fixing);
        const x = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 15;
        const y = fixing ? (Math.random() - 0.5) * 3 : (Math.random() - 0.5) * 12;
        return [...h.slice(-100), { x, y, fixating: fixing }];
      });
    }, 300);

    // Start first presentation after brief delay
    testRef.current = setTimeout(() => presentNext(), 1000);
  }, [settings, eyeConfig, seed, stopAll, presentNext, addEvent]);

  const pauseTest = useCallback(() => {
    if (testRef.current) { clearTimeout(testRef.current); testRef.current = undefined; }
    setIsRunning(false);
  }, []);

  const resumeTest = useCallback(() => {
    setIsRunning(true);
    testRef.current = setTimeout(() => presentNext(), 500);
  }, [presentNext]);

  const resetTest = useCallback(() => {
    stopAll();
    setTestState(null);
    setElapsed(0);
    setLastResponse(null);
    setGazeHistory([]);
  }, [stopAll]);

  useEffect(() => () => stopAll(), [stopAll]);

  // ─── Map data for VisualFieldMap ───────────────────

  const mapPoints = useMemo(() => {
    if (!testState) return [];
    return testState.points.map((p) => ({
      x: p.x,
      y: p.y,
      sensitivity: p.estimatedThreshold,
      seen: p.estimatedThreshold !== null && p.estimatedThreshold > 0,
      totalDeviation: p.estimatedThreshold !== null
        ? p.estimatedThreshold - normalSensitivity(p.x, p.y)
        : undefined,
    }));
  }, [testState]);

  const isDone = testState?.phase === "done";
  const stratLabel = settings.strategy === "sita-standard" ? "SITA Standard" : settings.strategy === "sita-fast" ? "SITA Fast" : "Full Threshold";

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="Campimetría" />

      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">PERIMETRY HFA-III</span>
        </span>
        <div className="flex items-center gap-2 text-xs ls-text-muted">
          {hasCaseLoaded ? (
            <span className="flex items-center gap-1 text-emerald-400/70"><Link2 className="h-3 w-3" /> Caso</span>
          ) : (
            <span className="flex items-center gap-1 ls-text-muted"><Link2Off className="h-3 w-3" /> Libre</span>
          )}
          <span>|</span>
          <span>{settings.eye} | {settings.pattern} | {stratLabel} | Goldmann {settings.stimulusSize}</span>
        </div>
      </div>

      {/* Stimulus indicator */}
      <StimulusDisplay
        pointX={lastResponse ? testState?.points[lastResponse.pointIndex]?.x ?? null : null}
        pointY={lastResponse ? testState?.points[lastResponse.pointIndex]?.y ?? null : null}
        stimulusDb={lastResponse?.stimulusDb ?? null}
        responded={lastResponse?.response.responded ?? null}
        isPresenting={isRunning}
      />

      {/* Main: 3 columns */}
      <div className="flex flex-1 overflow-hidden gap-2 p-2">
        {/* LEFT: Camera + Gaze + Controls */}
        <div className="flex w-[170px] shrink-0 flex-col gap-2">
          <EyeCamera isFixating={isFixating} isRunning={isRunning} eye={settings.eye} />
          <GazePlot gazeHistory={gazeHistory} />

          <div className={cn(
            "flex items-center justify-center gap-2 rounded border p-1.5",
            isFixating ? "border-emerald-500/30 bg-emerald-900/10" : "border-red-500/30 bg-red-900/10"
          )}>
            <div className={`h-2 w-2 rounded-full ${isFixating ? "bg-emerald-400" : "bg-red-400 animate-pulse"}`} />
            <span className={`text-[10px] font-medium ${isFixating ? "text-emerald-400" : "text-red-400"}`}>
              {isFixating ? "FIJANDO" : "PÉRDIDA"}
            </span>
          </div>

          {/* Test controls */}
          <div className="flex gap-1">
            {!isRunning && !isDone && (
              <button onClick={testState ? resumeTest : startTest} className="flex-1 flex items-center justify-center gap-1 rounded border ls-border py-1 text-[10px] text-emerald-400 hover:bg-emerald-500/10">
                <Play className="h-3 w-3" />
                {testState ? "Continuar" : "Iniciar"}
              </button>
            )}
            {isRunning && (
              <button onClick={pauseTest} className="flex-1 flex items-center justify-center gap-1 rounded border ls-border py-1 text-[10px] text-amber-400 hover:bg-amber-500/10">
                <Pause className="h-3 w-3" />
                Pausa
              </button>
            )}
            <button onClick={resetTest} className="flex items-center justify-center gap-1 rounded border ls-border px-2 py-1 text-[10px] ls-text-muted hover:ls-bg-input">
              <RotateCcw className="h-3 w-3" />
            </button>
          </div>

          {/* Results */}
          {testState && <PerimetryResults state={testState} elapsed={elapsed} />}
        </div>

        {/* CENTER: Visual Field Map */}
        <div className="flex-1 flex items-center justify-center overflow-hidden">
          <VisualFieldMap
            points={mapPoints}
            mode={viewMode}
            currentPoint={testState?.currentPointIndex ?? null}
            eye={settings.eye}
          />
        </div>

        {/* RIGHT: Controls + View mode */}
        <div className="flex w-[150px] shrink-0 flex-col gap-2 overflow-auto">
          <PerimetryControls
            settings={settings}
            onChange={setSettings}
            locked={hasCaseLoaded}
          />

          <div className="h-px ls-bg-input" />

          {/* View mode */}
          <div className="space-y-1 p-2">
            <span className="text-[9px] ls-text-muted uppercase tracking-wider">Vista</span>
            {(["numeric", "grayscale", "deviation"] as ViewMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setViewMode(m)}
                className={`block w-full rounded px-2 py-0.5 text-left text-[10px] transition ${
                  viewMode === m ? "bg-violet-500/20 text-violet-400" : "ls-text-muted hover:ls-bg-input"
                }`}
              >
                {m === "numeric" ? "Numérico (dB)" : m === "grayscale" ? "Escala Gris" : "Desviación Total"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border ls-bg-panel2 px-3 py-1 text-[9px] font-mono ls-text-muted">
        <span>{settings.eye} | {settings.pattern} | {stratLabel}</span>
        <span>
          {testState ? `${testState.points.filter((p) => p.done).length}/${testState.points.length} puntos | ${testState.presentationCount} presentaciones` : "Listo"}
        </span>
      </div>
    </div>
  );
}
