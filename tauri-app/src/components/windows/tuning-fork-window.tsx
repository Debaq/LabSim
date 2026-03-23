/**
 * Simulador interactivo de diapasón (512 Hz).
 *
 * El estudiante:
 * 1. Selecciona prueba (Rinne / Weber / Schwabach) y oído
 * 2. "Golpea" el diapasón (botón Activar)
 * 3. Coloca el diapasón en la zona correspondiente (click en zona)
 * 4. Observa la respuesta del paciente (escucha / no escucha)
 * 5. Registra el resultado
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { Button } from "@/components/ui/button";
import { Music, RotateCcw } from "lucide-react";
import {
  simulateRinne, simulateWeber, simulateSchwabach,
  type RinneResponse, type WeberResponse, type SchwabachResponse,
} from "@/lib/tuning-fork-patient";
import type { AudiometryData } from "@/modules/audiometry/schema";
import type { EarSide } from "@/lib/audiometry-patient";

type TestType = "rinne" | "weber" | "schwabach";
type Placement = "mastoides" | "conducto" | "vertex" | null;

const EMPTY_AUDIO: AudiometryData = {
  umbralesAereos: { oidoDerecho: {}, oidoIzquierdo: {} },
  umbralesOseos: { oidoDerecho: {}, oidoIzquierdo: {} },
  ldl: { oidoDerecho: {}, oidoIzquierdo: {} },
  tipoPerdida: { oidoDerecho: "normal", oidoIzquierdo: "normal" },
  reclutamiento: { oidoDerecho: false, oidoIzquierdo: false },
  deterioroTonal: { oidoDerecho: false, oidoIzquierdo: false },
  patientConfig: { falsePositiveRate: 0.03, falseNegativeRate: 0.02, reactionTimeMs: 350, fatigueFactor: 0.1, seed: 42 },
};

// ─── Componentes auxiliares ─────────────────────────────

function ForkIcon({ vibrating, className }: { vibrating: boolean; className?: string }) {
  return (
    <svg viewBox="0 0 40 120" className={`${className} ${vibrating ? "animate-pulse" : ""}`} fill="none" stroke="currentColor" strokeWidth="2">
      {/* Mango */}
      <rect x="16" y="60" width="8" height="55" rx="3" fill="currentColor" opacity={0.3} />
      {/* Brazos */}
      <path d={vibrating ? "M12,5 Q10,30 14,58" : "M14,5 L14,58"} strokeWidth="3" strokeLinecap="round" />
      <path d={vibrating ? "M28,5 Q30,30 26,58" : "M26,5 L26,58"} strokeWidth="3" strokeLinecap="round" />
      {/* Base de los brazos */}
      <path d="M14,58 Q20,62 26,58" strokeWidth="2" />
    </svg>
  );
}

function HeadDiagram({ ear, placement, onPlace, testType }: {
  ear: EarSide;
  placement: Placement;
  onPlace: (p: Placement) => void;
  testType: TestType;
}) {
  const isRight = ear === "right";

  // Zonas activas según la prueba
  const showMastoides = testType === "rinne" || testType === "schwabach";
  const showConducto = testType === "rinne";
  const showVertex = testType === "weber";

  return (
    <div className="relative w-full max-w-[280px] mx-auto select-none">
      {/* Cabeza esquemática (vista lateral) */}
      <svg viewBox="0 0 200 220" className="w-full h-auto">
        {/* Cabeza */}
        <ellipse cx="100" cy="100" rx="65" ry="80" fill="none" stroke="currentColor" strokeWidth="1.5" opacity={0.3} />
        {/* Oreja */}
        <ellipse cx={isRight ? 165 : 35} cy="100" rx="12" ry="22" fill="none" stroke="currentColor" strokeWidth="1.5" opacity={0.4} />
        {/* Nariz */}
        <path d={isRight ? "M35,95 Q25,105 35,115" : "M165,95 Q175,105 165,115"} fill="none" stroke="currentColor" strokeWidth="1" opacity={0.2} />

        {/* Indicador de oído */}
        <text x="100" y="195" textAnchor="middle" fill="currentColor" fontSize="11" opacity={0.5}>
          {isRight ? "Oído Derecho" : "Oído Izquierdo"}
        </text>

        {/* Zona: Vértex */}
        {showVertex && (
          <g className="cursor-pointer" onClick={() => onPlace("vertex")}>
            <circle cx="100" cy="18" r="16" fill={placement === "vertex" ? "rgba(251,191,36,0.3)" : "rgba(251,191,36,0.08)"} stroke="rgb(251,191,36)" strokeWidth={placement === "vertex" ? 2 : 1} strokeDasharray={placement === "vertex" ? "" : "3,3"} />
            <text x="100" y="22" textAnchor="middle" fill="rgb(251,191,36)" fontSize="8" fontWeight="bold">V</text>
          </g>
        )}

        {/* Zona: Mastoides */}
        {showMastoides && (
          <g className="cursor-pointer" onClick={() => onPlace("mastoides")}>
            <circle cx={isRight ? 175 : 25} cy="120" r="14" fill={placement === "mastoides" ? "rgba(168,85,247,0.3)" : "rgba(168,85,247,0.08)"} stroke="rgb(168,85,247)" strokeWidth={placement === "mastoides" ? 2 : 1} strokeDasharray={placement === "mastoides" ? "" : "3,3"} />
            <text x={isRight ? 175 : 25} y="124" textAnchor="middle" fill="rgb(168,85,247)" fontSize="7" fontWeight="bold">VO</text>
          </g>
        )}

        {/* Zona: Conducto auditivo */}
        {showConducto && (
          <g className="cursor-pointer" onClick={() => onPlace("conducto")}>
            <circle cx={isRight ? 155 : 45} cy="85" r="12" fill={placement === "conducto" ? "rgba(34,197,94,0.3)" : "rgba(34,197,94,0.08)"} stroke="rgb(34,197,94)" strokeWidth={placement === "conducto" ? 2 : 1} strokeDasharray={placement === "conducto" ? "" : "3,3"} />
            <text x={isRight ? 155 : 45} y="89" textAnchor="middle" fill="rgb(34,197,94)" fontSize="7" fontWeight="bold">VA</text>
          </g>
        )}
      </svg>
    </div>
  );
}

// ─── Componente principal ───────────────────────────────

export function TuningForkWindow() {
  const audioData = usePatientStore((s) => (s.data.modules.audiometry ?? EMPTY_AUDIO) as AudiometryData);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const hasCaseLoaded = !!patientId;

  const [testType, setTestType] = useState<TestType>("rinne");
  const [ear, setEar] = useState<EarSide>("right");
  const [forkActive, setForkActive] = useState(false);
  const [placement, setPlacement] = useState<Placement>(null);
  const [elapsed, setElapsed] = useState(0);
  const [patientMsg, setPatientMsg] = useState<string | null>(null);
  const [results, setResults] = useState<string[]>([]);

  // Respuestas simuladas
  const [rinneResp, setRinneResp] = useState<RinneResponse | null>(null);
  const [weberResp, setWeberResp] = useState<WeberResponse | null>(null);
  const [schwabachResp, setSchwabachResp] = useState<SchwabachResponse | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const seedBase = (patientId ?? "default").split("").reduce((a, c) => a + c.charCodeAt(0), 0);

  // Timer de vibración
  useEffect(() => {
    if (forkActive && placement) {
      const start = Date.now();
      timerRef.current = setInterval(() => {
        const t = (Date.now() - start) / 1000;
        setElapsed(t);

        // Actualizar respuesta del paciente en tiempo real
        if (testType === "rinne" && rinneResp) {
          const via = placement === "conducto" ? "air" as const : "bone" as const;
          const hears = rinneResp.hearsAtTime(t, via);
          setPatientMsg(hears ? "Escucho..." : "Ya no escucho");
          if (!hears && t > 2) {
            // Dejar de vibrar (paciente ya no escucha)
          }
        } else if (testType === "schwabach" && schwabachResp) {
          const hears = schwabachResp.hearsAtTime(t);
          setPatientMsg(hears ? "Escucho..." : "Ya no escucho");
        }

        // Auto-stop después de 60s
        if (t >= 60) {
          clearInterval(timerRef.current);
          setForkActive(false);
        }
      }, 100);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [forkActive, placement, testType, rinneResp, schwabachResp]);

  const activateFork = useCallback(() => {
    setForkActive(true);
    setElapsed(0);
    setPlacement(null);
    setPatientMsg(null);

    // Pre-calcular respuestas
    const seed = seedBase + Date.now() % 1000;
    if (testType === "rinne") {
      setRinneResp(simulateRinne(ear, audioData, seed));
    } else if (testType === "weber") {
      const resp = simulateWeber(audioData, seed);
      setWeberResp(resp);
    } else {
      setSchwabachResp(simulateSchwabach(ear, audioData, seed));
    }
  }, [testType, ear, audioData, seedBase]);

  const handlePlace = useCallback((p: Placement) => {
    if (!forkActive) return;
    setPlacement(p);
    setElapsed(0);

    // Respuesta inmediata para Weber
    if (testType === "weber" && p === "vertex" && weberResp) {
      setPatientMsg(weberResp.patientSays);
    }
  }, [forkActive, testType, weberResp]);

  const recordResult = useCallback(() => {
    let text = "";
    if (testType === "rinne" && rinneResp) {
      text = `Rinne ${ear === "right" ? "OD" : "OI"}: ${rinneResp.resultado} (VA ${rinneResp.vaDuration}s, VO ${rinneResp.voDuration}s)`;
    } else if (testType === "weber" && weberResp) {
      text = `Weber: lateraliza a ${weberResp.lateralizacion}`;
    } else if (testType === "schwabach" && schwabachResp) {
      text = `Schwabach ${ear === "right" ? "OD" : "OI"}: ${schwabachResp.resultado} (${schwabachResp.durationSecs}s vs normal ${schwabachResp.normalDurationSecs}s)`;
    }
    if (text) setResults((r) => [...r, text]);
  }, [testType, ear, rinneResp, weberResp, schwabachResp]);

  const resetTest = useCallback(() => {
    setForkActive(false);
    setPlacement(null);
    setElapsed(0);
    setPatientMsg(null);
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  return (
    <div className="flex flex-col h-full ls-bg-base ls-text text-xs overflow-hidden">
      <PatientBanner simulatorName="Acumetría" />

      {/* Barra de pruebas */}
      <div className="flex items-center gap-1 border-b ls-border px-3 py-1.5">
        {(["rinne", "weber", "schwabach"] as TestType[]).map((t) => (
          <Button key={t} type="button" size="xs" variant={testType === t ? "default" : "ghost"}
            onClick={() => { setTestType(t); resetTest(); }}
            className={testType === t ? "ls-bg-input ls-text font-bold" : "ls-text-muted"}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </Button>
        ))}

        {testType !== "weber" && (
          <>
            <div className="mx-1 h-4 w-px ls-bg-input" />
            <Button type="button" size="xs" variant={ear === "right" ? "default" : "ghost"}
              onClick={() => { setEar("right"); resetTest(); }}
              className={ear === "right" ? "bg-red-500/20 text-red-400 font-bold" : "ls-text-muted"}>OD</Button>
            <Button type="button" size="xs" variant={ear === "left" ? "default" : "ghost"}
              onClick={() => { setEar("left"); resetTest(); }}
              className={ear === "left" ? "bg-blue-500/20 text-blue-400 font-bold" : "ls-text-muted"}>OI</Button>
          </>
        )}
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Panel principal */}
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-4">
          {/* Diapasón */}
          <div className="flex items-center gap-4">
            <ForkIcon vibrating={forkActive} className="h-20 w-8 text-amber-400" />
            <div className="space-y-1">
              <Button type="button" size="sm" onClick={activateFork} disabled={!hasCaseLoaded || forkActive}
                className="gap-1.5 bg-amber-600 hover:bg-amber-500 text-white">
                <Music className="h-3.5 w-3.5" /> Golpear diapasón
              </Button>
              {forkActive && (
                <Button type="button" size="xs" variant="ghost" onClick={resetTest} className="gap-1 ls-text-muted">
                  <RotateCcw className="h-3 w-3" /> Reiniciar
                </Button>
              )}
            </div>
          </div>

          {/* Instrucciones */}
          {forkActive && !placement && (
            <p className="text-amber-400/80 text-center animate-pulse">
              {testType === "rinne" && "Coloca el diapasón en la mastoides (VO) o frente al conducto (VA)"}
              {testType === "weber" && "Coloca el diapasón en el vértex (centro de la cabeza)"}
              {testType === "schwabach" && "Coloca el diapasón en la mastoides (VO)"}
            </p>
          )}

          {/* Diagrama de cabeza */}
          <HeadDiagram ear={ear} placement={placement} onPlace={handlePlace} testType={testType} />

          {/* Timer */}
          {forkActive && placement && (
            <div className="text-center">
              <span className="font-mono text-lg ls-text">{elapsed.toFixed(1)}s</span>
            </div>
          )}

          {/* Respuesta del paciente */}
          {patientMsg && (
            <div className="rounded-lg border ls-border px-4 py-2 max-w-xs text-center">
              <span className="text-[10px] ls-text-muted block mb-0.5">Paciente dice:</span>
              <span className={`text-sm font-medium ${patientMsg.includes("no") ? "text-red-400" : "text-emerald-400"}`}>
                "{patientMsg}"
              </span>
            </div>
          )}

          {/* Botón registrar */}
          {(rinneResp || weberResp || schwabachResp) && (
            <Button type="button" size="sm" variant="outline" onClick={recordResult} className="gap-1.5">
              Registrar resultado
            </Button>
          )}
        </div>

        {/* Panel lateral: resultados registrados */}
        <div className="w-48 border-l ls-border p-2 space-y-2 overflow-y-auto">
          <h3 className="text-[10px] font-bold ls-text-muted uppercase tracking-wider">Resultados</h3>
          {results.length === 0 && (
            <p className="text-[10px] ls-text-muted italic">Sin resultados registrados</p>
          )}
          {results.map((r, i) => (
            <div key={i} className="rounded border ls-border px-2 py-1 text-[10px] ls-text">
              {r}
            </div>
          ))}
          {results.length > 0 && (
            <Button type="button" size="xs" variant="ghost" onClick={() => setResults([])} className="ls-text-muted text-[10px]">
              Limpiar
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
