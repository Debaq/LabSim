/**
 * Impedanciómetro LabSim
 *
 * Simula un equipo real (tipo Interacoustics AT235 / GSI TympStar).
 * El equipo muestra datos crudos — no interpreta. El estudiante analiza.
 *
 * Pruebas disponibles:
 * - Timpanometría (sweep de presión con curva en tiempo real)
 * - Reflejos acústicos (ipsi/contra, búsqueda de umbral)
 * - Deterioro del reflejo (10s de estimulación sostenida)
 * - Función tubárica (3 timpanogramas: basal, Toynbee, Valsalva)
 */

import { useState, useMemo } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { ProbeIndicator, type ProbeStatus } from "@/components/impedance/probe-indicator";
import { ImpedanceControls, DEFAULT_SETTINGS, type ImpedanceSettings } from "@/components/impedance/impedance-controls";
import { TympanometryPanel } from "@/components/impedance/tympanometry-panel";
import { ReflexPanel } from "@/components/impedance/reflex-panel";
import { ReflexDecayPanel } from "@/components/impedance/reflex-decay-panel";
import { EustachianPanel } from "@/components/impedance/eustachian-panel";
import { generateTympanogram } from "@/lib/impedance-synthetic";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { EarPhysiology } from "@/modules/impedance/schema";

type TestMode = "tympanometry" | "reflex" | "decay" | "eustachian";
const EMPTY_CONFIG = {};

export function ImpedancePlaceholder() {
  const [ear, setEar] = useState<"OD" | "OI">("OD");
  const [testMode, setTestMode] = useState<TestMode>("tympanometry");
  const [settings, setSettings] = useState<ImpedanceSettings>({ ...DEFAULT_SETTINGS });
  const [probeStatus, setProbeStatus] = useState<ProbeStatus>("disconnected");
  const [tympRunning, setTympRunning] = useState(false);

  // Datos del paciente
  const impedanceConfig = usePatientStore((s) => s.data.modules.impedance ?? EMPTY_CONFIG);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);

  const earKey = ear === "OD" ? "oidoDerecho" : "oidoIzquierdo";
  const earData: EarPhysiology = (impedanceConfig[earKey] as EarPhysiology) ?? {};
  const variance = (impedanceConfig.naturalVariance as number) ?? 0.05;
  const hasCaseLoaded = patientId !== null && Object.keys(earData).length > 0;

  // Seed determinístico
  const seed = useMemo(() => {
    if (!patientId) return 42;
    return patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) + (ear === "OI" ? 1000 : 0);
  }, [patientId, ear]);

  // Generar timpanograma
  const tympData = useMemo(() => {
    if (!hasCaseLoaded) {
      return null;
    }
    return generateTympanogram(
      earData,
      settings.probeFrequency,
      [settings.pressureMin, settings.pressureMax],
      seed,
      variance,
    );
  }, [hasCaseLoaded, earData, settings.probeFrequency, settings.pressureMin, settings.pressureMax, seed, variance]);

  const handleStartTymp = () => {
    // Simular inserción de sonda
    setProbeStatus("inserting");
    setTimeout(() => {
      setProbeStatus("sealed");
      setTympRunning(true);
      addEvent({ type: "test_start", simulator: "impedance", details: `Timpanometría ${ear}` });
    }, 800);
  };

  const TEST_MODES: { value: TestMode; label: string }[] = [
    { value: "tympanometry", label: "Timpanometría" },
    { value: "reflex", label: "Reflejos" },
    { value: "decay", label: "Deterioro" },
    { value: "eustachian", label: "Función Tubárica" },
  ];

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="Impedanciómetro" />

      {/* Header del equipo */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">IMPEDANCE Z-400</span>
        </span>
        <div className="flex items-center gap-3">
          <ProbeIndicator status={probeStatus} />
          {hasCaseLoaded && (
            <span className="text-xs text-emerald-400/60 font-mono">CASE</span>
          )}
        </div>
      </div>

      {/* Ear selector + test mode */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-1.5">
        {/* Oído */}
        <div className="flex gap-0.5">
          <button
            onClick={() => setEar("OD")}
            className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${
              ear === "OD" ? "bg-red-500/20 text-red-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            OD
          </button>
          <button
            onClick={() => setEar("OI")}
            className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${
              ear === "OI" ? "bg-blue-500/20 text-blue-400" : "ls-text-muted hover:ls-bg-input"
            }`}
          >
            OI
          </button>
        </div>

        <div className="mx-1 h-4 w-px ls-bg-input" />

        {/* Test mode */}
        <div className="flex gap-0.5">
          {TEST_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setTestMode(m.value)}
              className={`rounded px-2 py-0.5 text-xs transition ${
                testMode === m.value
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "ls-text-muted hover:ls-bg-input"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content: panel izquierdo (controles) + derecho (visualización) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Controles */}
        <div className="w-[180px] shrink-0 border-r ls-border overflow-auto">
          <ImpedanceControls settings={settings} onChange={setSettings} />
        </div>

        {/* Visualización */}
        <ScrollArea className="flex-1">
          <div className="p-3">
            {!hasCaseLoaded ? (
              <div className="flex h-[200px] w-full items-center justify-center rounded bg-black/40">
                <span className="text-xs font-mono ls-text-muted">SIN SEÑAL</span>
              </div>
            ) : (
              <>
                {testMode === "tympanometry" && tympData && (
                  <TympanometryPanel
                    data={tympData}
                    settings={settings}
                    onStart={handleStartTymp}
                    isRunning={tympRunning}
                  />
                )}
                {testMode === "reflex" && (
                  <ReflexPanel
                    ear={earData}
                    settings={settings}
                    seed={seed}
                    variance={variance}
                  />
                )}
                {testMode === "decay" && (
                  <div className="space-y-4">
                    <ReflexDecayPanel ear={earData} frequency={500} seed={seed} />
                    <ReflexDecayPanel ear={earData} frequency={1000} seed={seed} />
                  </div>
                )}
                {testMode === "eustachian" && (
                  <EustachianPanel
                    ear={earData}
                    seed={seed}
                    variance={variance}
                    pressureRange={[settings.pressureMin, settings.pressureMax]}
                  />
                )}
              </>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border ls-bg-panel2 px-3 py-1 text-xs font-mono ls-text-muted">
        <span>{ear} · {settings.probeFrequency} Hz · {settings.pressureMin}/{settings.pressureMax} daPa</span>
        <span>{testMode.toUpperCase()}</span>
      </div>
    </div>
  );
}
