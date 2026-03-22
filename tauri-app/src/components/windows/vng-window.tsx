/**
 * VNG LabSim — LabSim VN-200
 * Videonistagmografía: estación modular de pruebas vestibulares.
 * El operador elige la prueba y el equipo registra movimiento ocular.
 */

import { useState, useMemo } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { EyeTraceChart } from "@/components/vestibular/eye-trace-chart";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  generateSpontaneousNystagmus,
  generateCaloricResponse,
  generateSaccades,
  type NystagmusParams,
} from "@/lib/vestibular-synthetic";
import type { VNGData } from "@/modules/vng/schema";
import { Play, Link2, Link2Off } from "lucide-react";

type TestMode =
  | "spontaneous" | "spontaneous-fixation"
  | "caloric-rw" | "caloric-rc" | "caloric-lw" | "caloric-lc"
  | "positional-dhR" | "positional-dhL" | "positional-rollR" | "positional-rollL"
  | "positional-supine" | "positional-hh" | "positional-sit"
  | "saccades" | "smooth-pursuit" | "optokinetic";

interface TestGroup { label: string; tests: { id: TestMode; label: string }[] }

const TEST_GROUPS: TestGroup[] = [
  { label: "Espontáneo", tests: [
    { id: "spontaneous", label: "Sin fijación" },
    { id: "spontaneous-fixation", label: "Con fijación" },
  ]},
  { label: "Calórico", tests: [
    { id: "caloric-rw", label: "OD Cal" },
    { id: "caloric-rc", label: "OD Frío" },
    { id: "caloric-lw", label: "OI Cal" },
    { id: "caloric-lc", label: "OI Frío" },
  ]},
  { label: "Posicional", tests: [
    { id: "positional-dhR", label: "DH Der" },
    { id: "positional-dhL", label: "DH Izq" },
    { id: "positional-rollR", label: "Roll Der" },
    { id: "positional-rollL", label: "Roll Izq" },
    { id: "positional-supine", label: "Supino" },
    { id: "positional-hh", label: "Head Hang" },
    { id: "positional-sit", label: "Sentado" },
  ]},
  { label: "Oculomotor", tests: [
    { id: "saccades", label: "Sacadas" },
    { id: "smooth-pursuit", label: "Seguimiento" },
    { id: "optokinetic", label: "OPK" },
  ]},
];

const POSITIONAL_KEYS: Record<string, string> = {
  "positional-dhR": "dixHallpikeRight",
  "positional-dhL": "dixHallpikeLeft",
  "positional-rollR": "rollTestRight",
  "positional-rollL": "rollTestLeft",
  "positional-supine": "supine",
  "positional-hh": "headHanging",
  "positional-sit": "sitting",
};

export function VNGWindow() {
  const [testMode, setTestMode] = useState<TestMode>("spontaneous");
  const [seed, setSeed] = useState(42);
  const [running, setRunning] = useState(false);

  const config = usePatientStore((s) => s.data.modules.vng ?? {}) as VNGData;
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const hasCaseLoaded = patientId !== null && Object.keys(config).length > 0;

  useMemo(() => {
    if (patientId) setSeed(patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0));
  }, [patientId]);

  const handleRun = () => {
    setSeed(Math.floor(Math.random() * 10000));
    setRunning(true);
    addEvent({ type: "test_start", simulator: "vng", details: testMode });
    setTimeout(() => setRunning(false), 1500);
  };

  const traceData = useMemo(() => {
    const sp = config.spontaneous ?? {};
    const cal = config.caloric ?? {};
    const pos = config.positionals ?? {};
    const ocu = config.oculomotor ?? {};

    switch (testMode) {
      case "spontaneous":
      case "spontaneous-fixation": {
        const hasFix = testMode === "spontaneous-fixation";
        const suppresses = sp.fixationSuppression !== false;
        const effectiveSpv = (hasFix && suppresses) ? 0 : (sp.spv ?? 0);
        const params: NystagmusParams = {
          direction: effectiveSpv > 0 ? (sp.direction ?? "ninguno") : "ninguno",
          frequency: effectiveSpv > 0 ? Math.min(4, effectiveSpv / 5) : 0,
          amplitude: Math.min(15, effectiveSpv),
          slowPhaseVelocity: effectiveSpv,
        };
        return { type: "nystagmus" as const, trace: generateSpontaneousNystagmus(params, 10000, seed), label: hasFix ? "Espontáneo con fijación" : "Espontáneo sin fijación" };
      }
      case "caloric-rw": return { type: "caloric" as const, result: generateCaloricResponse("derecho", "caliente", cal.rightWarmSpv ?? 30, "moderado", seed) };
      case "caloric-rc": return { type: "caloric" as const, result: generateCaloricResponse("derecho", "fria", cal.rightCoolSpv ?? 25, "moderado", seed + 1) };
      case "caloric-lw": return { type: "caloric" as const, result: generateCaloricResponse("izquierdo", "caliente", cal.leftWarmSpv ?? 28, "moderado", seed + 2) };
      case "caloric-lc": return { type: "caloric" as const, result: generateCaloricResponse("izquierdo", "fria", cal.leftCoolSpv ?? 26, "moderado", seed + 3) };

      default: {
        // Posicionales
        const posKey = POSITIONAL_KEYS[testMode];
        if (posKey) {
          const p = (pos as Record<string, any>)[posKey] ?? {};
          const effectiveSpv = p.spv ?? 0;
          const params: NystagmusParams = {
            direction: effectiveSpv > 0 ? (p.direction ?? "ninguno") : "ninguno",
            frequency: effectiveSpv > 0 ? Math.min(4, effectiveSpv / 5) : 0,
            amplitude: Math.min(15, effectiveSpv),
            slowPhaseVelocity: effectiveSpv,
          };
          const duration = (p.durationSec ?? 30) * 1000;
          return { type: "nystagmus" as const, trace: generateSpontaneousNystagmus(params, duration, seed + 10), label: testMode };
        }

        // Oculomotor
        if (testMode === "saccades") {
          const s = ocu.saccades ?? {};
          return { type: "saccade" as const, result: generateSaccades(s.latency ?? 220, s.accuracy ?? 0.95, s.peakVelocity ?? 400, seed + 20) };
        }

        return { type: "empty" as const };
      }
    }
  }, [testMode, config, seed]);

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="VNG" />
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">LABSIM <span className="font-normal">VN-200 VNG</span></span>
        <span className="text-xs ls-text-muted">{hasCaseLoaded ? <><Link2 className="inline h-3 w-3" /> Caso</> : <><Link2Off className="inline h-3 w-3" /> Libre</>}</span>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: test selector by group */}
        <div className="w-[160px] shrink-0 border-r ls-border overflow-auto">
          {TEST_GROUPS.map((group) => (
            <div key={group.label} className="py-1">
              <div className="px-2 py-1 text-[8px] font-bold uppercase tracking-wider ls-text-muted">{group.label}</div>
              {group.tests.map((t) => (
                <button key={t.id} onClick={() => setTestMode(t.id)}
                  className={`block w-full px-3 py-1 text-left text-[10px] transition ${
                    testMode === t.id ? "bg-violet-500/15 text-violet-400" : "ls-text-muted hover:ls-bg-input"
                  }`}
                >{t.label}</button>
              ))}
            </div>
          ))}
        </div>

        {/* Center: trace display */}
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium ls-text2">{testMode}</span>
              <button onClick={handleRun} disabled={running} className="flex items-center gap-1 rounded px-2 py-0.5 text-[10px] text-emerald-400 hover:bg-emerald-500/10">
                <Play className="h-3 w-3" />{running ? "Registrando..." : "Registrar"}
              </button>
            </div>

            {traceData.type === "nystagmus" && (
              <EyeTraceChart eyeTrace={traceData.trace} label={traceData.label} yRange={15} width={480} />
            )}
            {traceData.type === "caloric" && (
              <>
                <EyeTraceChart eyeTrace={traceData.result.trace} label="Calórico" yRange={25} width={480} height={160} />
                <div className="flex gap-3 text-[10px] font-mono">
                  <span className="ls-text-muted">SPV pico: <span className="text-cyan-400">{traceData.result.peakSPV}°/s</span></span>
                  <span className="ls-text-muted">T pico: <span className="text-cyan-400">{traceData.result.timeToPeak}s</span></span>
                </div>
              </>
            )}
            {traceData.type === "saccade" && (
              <>
                <EyeTraceChart eyeTrace={traceData.result.trace} label="Sacadas" yRange={25} width={480} height={160} />
                <div className="flex gap-3 text-[10px] font-mono">
                  <span className="ls-text-muted">Latencia: <span className="text-cyan-400">{traceData.result.avgLatency}ms</span></span>
                  <span className="ls-text-muted">Precisión: <span className="text-cyan-400">{traceData.result.avgAccuracy}%</span></span>
                  <span className="ls-text-muted">Vel: <span className="text-cyan-400">{traceData.result.avgPeakVelocity}°/s</span></span>
                </div>
              </>
            )}
            {traceData.type === "empty" && (
              <div className="py-8 text-center text-xs ls-text-muted">
                Seleccione una prueba e inicie el registro
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      <div className="border-t ls-border ls-bg-panel2 px-3 py-1 text-[9px] font-mono ls-text-muted">
        {testMode}
      </div>
    </div>
  );
}
