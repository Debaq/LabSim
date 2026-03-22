/**
 * Autorefractómetro LabSim — LabSim AR-500
 * Mide refracción objetiva automática: esfera, cilindro, eje.
 * Incluye queratometría y distancia pupilar.
 */

import { useState, useEffect } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { AlignmentPanel, DEFAULT_ALIGNMENT, isAligned, getAlignmentQuality, type AlignmentState } from "@/components/ui/alignment-panel";
import { cn } from "@/lib/utils";
import { Link2, Link2Off } from "lucide-react";
import {
  generateAutorefResult,
  formatDiopter,
  type AutorefResult,
  type AutorefEyeConfig,
} from "@/lib/autoref-synthetic";

const EMPTY_CONFIG = {};

export function AutorefWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [alignment, setAlignment] = useState<AlignmentState>(DEFAULT_ALIGNMENT);
  const [measuring, setMeasuring] = useState(false);
  const [results, setResults] = useState<{ OD: AutorefResult | null; OI: AutorefResult | null }>({ OD: null, OI: null });
  const [seed, setSeed] = useState(42);

  const config = usePatientStore((s) => s.data.modules.autoref ?? EMPTY_CONFIG);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const hasCaseLoaded = patientId !== null && Object.keys(config).length > 0;

  useEffect(() => {
    if (!patientId) return;
    setSeed(patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0));
    setResults({ OD: null, OI: null });
  }, [patientId]);

  const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
  const eyeCfg: AutorefEyeConfig = (config as Record<string, AutorefEyeConfig>)[eyeKey] ?? {};
  const pd = (config as Record<string, number>).distanciaPupilar ?? 63;

  const quality = getAlignmentQuality(alignment);
  const canMeasure = hasCaseLoaded && isAligned(alignment);
  const currentResult = results[eye];

  const handleMeasure = () => {
    if (!canMeasure) return;
    setMeasuring(true);
    addEvent({ type: "test_start", simulator: "autoref", details: `Medición ${eye}` });

    // Simular tiempo de medición
    setTimeout(() => {
      const result = generateAutorefResult(
        eyeCfg,
        pd,
        seed + (eye === "OI" ? 5000 : 0) + Date.now() % 1000,
        quality,
      );
      setResults((prev) => ({ ...prev, [eye]: result }));
      setMeasuring(false);
    }, 1200);
  };

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="Autorefractómetro" />

      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">AR-500 AUTOREF</span>
        </span>
        <div className="flex items-center gap-2 text-xs ls-text-muted">
          {hasCaseLoaded ? (
            <span className="flex items-center gap-1 text-emerald-400/70"><Link2 className="h-3 w-3" /> Caso</span>
          ) : (
            <span className="flex items-center gap-1"><Link2Off className="h-3 w-3" /> Libre</span>
          )}
          <span>|</span>
          <span className={cn("font-bold", eye === "OD" ? "text-red-400/60" : "text-blue-400/60")}>{eye}</span>
        </div>
      </div>

      {/* Eye selector */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-1.5">
        <div className="flex gap-0.5">
          <button onClick={() => setEye("OD")}
            className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${eye === "OD" ? "bg-red-500/20 text-red-400" : "ls-text-muted hover:ls-bg-input"}`}
          >OD</button>
          <button onClick={() => setEye("OI")}
            className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${eye === "OI" ? "bg-blue-500/20 text-blue-400" : "ls-text-muted hover:ls-bg-input"}`}
          >OI</button>
        </div>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <div className="flex items-center gap-1.5">
          {results.OD && <span className="text-xs text-emerald-400/60 font-mono">OD OK</span>}
          {results.OI && <span className="text-xs text-emerald-400/60 font-mono">OI OK</span>}
        </div>
        <button onClick={handleMeasure} disabled={!canMeasure || measuring}
          className={cn("ml-auto flex items-center gap-1 rounded px-3 py-1 text-xs font-bold transition",
            canMeasure && !measuring ? "bg-emerald-600 text-white hover:bg-emerald-500" : "ls-text-muted opacity-50 cursor-not-allowed")}
        >
          {measuring ? "Midiendo..." : !isAligned(alignment) ? "Alinear" : "Medir"}
        </button>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Pantalla del equipo */}
        <div className="flex-1 flex items-center justify-center p-4 overflow-auto">
          <div className="w-full max-w-[460px]">
            {/* Display tipo pantalla LCD del equipo */}
            <div className="rounded-lg border ls-border bg-zinc-950 p-5 font-mono text-sm">
              <div className="text-center text-emerald-400/60 text-sm mb-4">
                ── LABSIM AR-500 ──
              </div>

              {currentResult ? (
                <>
                  <div className={cn("text-center text-base font-bold mb-3", eye === "OD" ? "text-red-400" : "text-blue-400")}>
                    ── {eye} ──
                  </div>

                  {/* Mediciones individuales */}
                  <div className="space-y-1 mb-3">
                    <div className="flex justify-between text-sm text-zinc-500 px-2">
                      <span className="w-10">#</span>
                      <span className="w-20 text-right">SPH</span>
                      <span className="w-20 text-right">CYL</span>
                      <span className="w-14 text-right">AXIS</span>
                    </div>
                    {currentResult.readings.map((r, i) => (
                      <div key={i} className="flex justify-between text-emerald-300/80 text-sm px-2">
                        <span className="w-10 text-zinc-500">{i + 1}</span>
                        <span className="w-20 text-right">{formatDiopter(r.sph)}</span>
                        <span className="w-20 text-right">{formatDiopter(r.cyl)}</span>
                        <span className="w-14 text-right">{r.axis}°</span>
                      </div>
                    ))}
                  </div>

                  <div className="text-zinc-600 text-center">───────────────────────────</div>

                  {/* Promedio */}
                  <div className="flex justify-between text-emerald-400 font-bold text-base mt-1 px-2">
                    <span className="w-10 text-sm">AVG</span>
                    <span className="w-20 text-right">{formatDiopter(currentResult.average.sph)}</span>
                    <span className="w-20 text-right">{formatDiopter(currentResult.average.cyl)}</span>
                    <span className="w-14 text-right">{currentResult.average.axis}°</span>
                  </div>

                  {/* PD + Queratometría */}
                  <div className="mt-4 pt-3 border-t border-zinc-800 space-y-1.5 text-sm">
                    <div className="flex justify-between text-zinc-400 px-2">
                      <span>PD</span>
                      <span className="text-emerald-300">{currentResult.pd} mm</span>
                    </div>
                    <div className="text-zinc-600 text-center text-sm">── KERATOMETRY ──</div>
                    <div className="flex justify-between text-zinc-400 px-2">
                      <span>K1</span>
                      <span className="text-emerald-300">{currentResult.k1} D @{currentResult.k1Axis}°</span>
                    </div>
                    <div className="flex justify-between text-zinc-400 px-2">
                      <span>K2</span>
                      <span className="text-emerald-300">{currentResult.k2} D @{currentResult.k2Axis}°</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-2 border-t border-zinc-800 flex justify-between text-sm px-2">
                    <span className="text-zinc-500">Confiabilidad</span>
                    <span className={cn(
                      currentResult.confidence >= 80 ? "text-emerald-400" :
                      currentResult.confidence >= 60 ? "text-amber-400" : "text-red-400"
                    )}>
                      {currentResult.confidence}%
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-center py-10 space-y-3">
                  <div className={cn("text-2xl font-bold", eye === "OD" ? "text-red-400/40" : "text-blue-400/40")}>
                    {eye}
                  </div>
                  <div className="text-zinc-600 text-sm">
                    {!hasCaseLoaded ? "SIN PACIENTE" : !isAligned(alignment) ? "ALINEAR EQUIPO" : "LISTO PARA MEDIR"}
                  </div>
                  {measuring && (
                    <div className="text-emerald-400 text-sm animate-pulse">
                      MIDIENDO...
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Resumen ambos ojos */}
            {results.OD && results.OI && (
              <div className="mt-3 rounded-lg border ls-border bg-zinc-950 p-4 font-mono">
                <div className="text-center text-sm text-zinc-500 mb-2">── RESUMEN ──</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-center text-red-400/60 font-bold mb-1">OD</div>
                    <div className="text-emerald-300 text-center">
                      {formatDiopter(results.OD.average.sph)} / {formatDiopter(results.OD.average.cyl)} x {results.OD.average.axis}°
                    </div>
                  </div>
                  <div>
                    <div className="text-center text-blue-400/60 font-bold mb-1">OI</div>
                    <div className="text-emerald-300 text-center">
                      {formatDiopter(results.OI.average.sph)} / {formatDiopter(results.OI.average.cyl)} x {results.OI.average.axis}°
                    </div>
                  </div>
                </div>
                <div className="text-center text-zinc-500 text-sm mt-2">
                  PD: {results.OD.pd} mm
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Joystick abajo */}
        <div className="shrink-0 border-t ls-border px-3 py-1.5">
          <AlignmentPanel state={alignment} onChange={setAlignment} onCapture={canMeasure ? handleMeasure : undefined} compact />
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border ls-bg-panel2 px-3 py-1 text-xs font-mono ls-text-muted">
        <span>{eye} | {hasCaseLoaded ? (currentResult ? `SPH ${formatDiopter(currentResult.average.sph)} CYL ${formatDiopter(currentResult.average.cyl)} x${currentResult.average.axis}°` : "Sin medición") : "---"}</span>
        <span>{results.OD ? "OD" : ""}{results.OD && results.OI ? " · " : ""}{results.OI ? "OI" : ""}{!results.OD && !results.OI ? "Sin datos" : ""}</span>
      </div>
    </div>
  );
}
