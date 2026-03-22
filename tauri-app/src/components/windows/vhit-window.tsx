/**
 * vHIT LabSim — LabSim HI-600
 * Video Head Impulse Test: evalúa los 6 canales semicirculares.
 */

import { useState, useMemo } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { EyeTraceChart } from "@/components/vestibular/eye-trace-chart";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { generateVHITImpulses, type SemicircularCanal, type VHITResult, type VHITCanalParams } from "@/lib/vestibular-synthetic";
import type { VHITConfig, CanalConfig } from "@/modules/vhit/schema";
import { Play, Link2, Link2Off, AlertTriangle } from "lucide-react";

const CANALS: { id: SemicircularCanal; key: string; label: string; pair: string }[] = [
  { id: "lateral-der", key: "lateralRight", label: "Lat. Der.", pair: "Laterales" },
  { id: "lateral-izq", key: "lateralLeft", label: "Lat. Izq.", pair: "Laterales" },
  { id: "anterior-der", key: "anteriorRight", label: "Ant. Der.", pair: "LARP" },
  { id: "posterior-izq", key: "posteriorLeft", label: "Post. Izq.", pair: "LARP" },
  { id: "anterior-izq", key: "anteriorLeft", label: "Ant. Izq.", pair: "RALP" },
  { id: "posterior-der", key: "posteriorRight", label: "Post. Der.", pair: "RALP" },
];

export function VHITWindow() {
  const [selectedCanal, setSelectedCanal] = useState<SemicircularCanal>("lateral-der");
  const [selectedImpulse, setSelectedImpulse] = useState(0);
  const [seed, setSeed] = useState(42);
  const [running, setRunning] = useState(false);

  const config = usePatientStore((s) => s.data.modules.vhit ?? {});
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const hasCaseLoaded = patientId !== null && Object.keys(config).length > 0;

  const datos: VHITConfig = (config.datos as VHITConfig) ?? {};

  useMemo(() => {
    if (patientId) setSeed(patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0));
  }, [patientId]);

  const handleRun = () => {
    setSeed(Math.floor(Math.random() * 10000));
    setRunning(true);
    setSelectedImpulse(0);
    addEvent({ type: "test_start", simulator: "vhit", details: selectedCanal });
    setTimeout(() => setRunning(false), 2000);
  };

  // Leer configuración del canal seleccionado
  const canalInfo = CANALS.find((c) => c.id === selectedCanal)!;
  const canalConfig: CanalConfig = (datos[canalInfo.key as keyof VHITConfig] as CanalConfig) ?? {};

  const params: VHITCanalParams = {
    gain: canalConfig.gain ?? 1.0,
    hasOvertSaccades: canalConfig.hasOvertSaccades ?? false,
    hasCovertSaccades: canalConfig.hasCovertSaccades ?? false,
    overtRate: canalConfig.overtRate ?? 0.7,
    covertRate: canalConfig.covertRate ?? 0.5,
    goggleArtifactRate: 0,
  };

  const result: VHITResult = useMemo(
    () => generateVHITImpulses(selectedCanal, params, 15, seed + CANALS.indexOf(canalInfo) * 100),
    [selectedCanal, params.gain, params.hasOvertSaccades, params.hasCovertSaccades, seed],
  );

  const currentImpulse = result.impulses[selectedImpulse];

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="vHIT" />
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">LABSIM <span className="font-normal">HI-600 vHIT</span></span>
        <span className="text-xs ls-text-muted">{hasCaseLoaded ? <><Link2 className="inline h-3 w-3" /> Caso</> : <><Link2Off className="inline h-3 w-3" /> Libre</>}</span>
      </div>

      {/* Canal selector */}
      <div className="flex items-center gap-1 border-b ls-border px-3 py-1.5 flex-wrap">
        {CANALS.map((c) => {
          const cfg: CanalConfig = (datos[c.key as keyof VHITConfig] as CanalConfig) ?? {};
          const g = cfg.gain ?? 1.0;
          return (
            <button key={c.id} onClick={() => { setSelectedCanal(c.id); setSelectedImpulse(0); }}
              className={`rounded px-2 py-0.5 text-[10px] transition ${selectedCanal === c.id ? "bg-orange-500/20 text-orange-400" : "ls-text-muted hover:ls-bg-input"}`}
            >
              {c.label}
              <span className={`ml-1 font-mono ${g < 0.7 ? "text-red-400" : g < 0.8 ? "text-amber-400" : "text-emerald-400"}`}>
                {g.toFixed(2)}
              </span>
            </button>
          );
        })}
        <button onClick={handleRun} disabled={running} className="ml-auto flex items-center gap-1 rounded px-2 py-0.5 text-[10px] text-emerald-400 hover:bg-emerald-500/10">
          <Play className="h-3 w-3" />{running ? "Capturando..." : "Capturar"}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: impulse list */}
        <div className="w-[140px] shrink-0 border-r ls-border overflow-auto">
          <div className="p-1 space-y-0.5">
            {result.impulses.map((imp, i) => (
              <button key={i} onClick={() => setSelectedImpulse(i)}
                className={`flex w-full items-center justify-between rounded px-2 py-1 text-[10px] transition ${
                  selectedImpulse === i ? "bg-orange-500/15 text-orange-400" : "ls-text-muted hover:ls-bg-input"
                }`}
              >
                <span>#{i + 1}</span>
                <span className={`font-mono ${imp.gain < 0.7 ? "text-red-400" : imp.gain < 0.8 ? "text-amber-400" : "text-emerald-400"}`}>
                  {imp.gain.toFixed(2)}
                </span>
                <div className="flex gap-0.5">
                  {imp.isGoggleArtifact && (
                    <Badge variant="outline" className="text-[7px] px-0.5 py-0 text-zinc-400 bg-zinc-500/10">
                      <AlertTriangle className="inline h-2 w-2" />
                    </Badge>
                  )}
                  {imp.hasCorrectiveSaccade && (
                    <Badge variant="outline" className={`text-[7px] px-0.5 py-0 ${imp.saccadeType === "overt" ? "text-red-400 bg-red-500/10" : "text-amber-400 bg-amber-500/10"}`}>
                      {imp.saccadeType === "overt" ? "OV" : "CV"}
                    </Badge>
                  )}
                </div>
              </button>
            ))}
          </div>
          <div className="border-t ls-border p-2 text-[10px] space-y-0.5">
            <div className="flex justify-between ls-text-muted">
              <span>Promedio:</span>
              <span className={`font-mono font-medium ${result.avgGain < 0.7 ? "text-red-400" : result.avgGain < 0.8 ? "text-amber-400" : "text-emerald-400"}`}>
                {result.avgGain.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between ls-text-muted">
              <span>Overts:</span>
              <span className="font-mono">{result.impulses.filter((i) => i.saccadeType === "overt").length}</span>
            </div>
            <div className="flex justify-between ls-text-muted">
              <span>Coverts:</span>
              <span className="font-mono">{result.impulses.filter((i) => i.saccadeType === "covert").length}</span>
            </div>
            <div className="flex justify-between ls-text-muted">
              <span>Artefactos:</span>
              <span className="font-mono">{result.impulses.filter((i) => i.isGoggleArtifact).length}</span>
            </div>
          </div>
        </div>

        {/* Center: traces */}
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-2">
            {currentImpulse && (
              <>
                <EyeTraceChart
                  eyeTrace={currentImpulse.eyeTrace}
                  headTrace={currentImpulse.headTrace}
                  label={`Impulso #${selectedImpulse + 1} — G: ${currentImpulse.gain.toFixed(2)}${currentImpulse.isGoggleArtifact ? " ⚠ ARTEFACTO" : ""}`}
                  width={450}
                  height={180}
                  yRange={25}
                />
                <div className="flex gap-3 text-[10px] font-mono">
                  <span className="ls-text-muted">Ganancia: <span className="text-cyan-400">{currentImpulse.gain.toFixed(2)}</span></span>
                  <span className="ls-text-muted">Sacada: <span className={currentImpulse.hasCorrectiveSaccade ? "text-red-400" : "text-emerald-400"}>
                    {currentImpulse.hasCorrectiveSaccade ? currentImpulse.saccadeType : "ninguna"}
                  </span></span>
                  {currentImpulse.isGoggleArtifact && (
                    <span className="text-zinc-400 flex items-center gap-0.5">
                      <AlertTriangle className="h-3 w-3" /> Posible artefacto de gafas
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </div>

      <div className="border-t ls-border ls-bg-panel2 px-3 py-1 text-[9px] font-mono ls-text-muted">
        {canalInfo.label} ({canalInfo.pair}) | {result.impulses.length} impulsos | G̅: {result.avgGain.toFixed(2)}
      </div>
    </div>
  );
}
