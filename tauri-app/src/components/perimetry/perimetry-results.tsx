/**
 * Panel de resultados del campímetro.
 * Muestra MD, PSD, confiabilidad — solo datos, sin interpretación.
 */

import type { TestState } from "./perimetry-test-engine";
import { calculateMD, calculatePSD, getProgress } from "./perimetry-test-engine";

interface Props {
  state: TestState;
  elapsed: number; // segundos
}

export function PerimetryResults({ state, elapsed }: Props) {
  const md = calculateMD(state.points);
  const psd = calculatePSD(state.points);
  const progress = getProgress(state);
  const tested = state.points.filter((p) => p.done).length;
  const total = state.points.length;
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  const flPct = state.fixationLossesTotal > 0
    ? Math.round((state.fixationLosses / state.fixationLossesTotal) * 100)
    : 0;
  const fpPct = state.falsePositivesTotal > 0
    ? Math.round((state.falsePositives / state.falsePositivesTotal) * 100)
    : 0;
  const fnPct = state.falseNegativesTotal > 0
    ? Math.round((state.falseNegatives / state.falseNegativesTotal) * 100)
    : 0;

  return (
    <div className="space-y-2 p-2">
      {/* Progreso */}
      <div className="space-y-0.5">
        <div className="flex justify-between text-[9px] ls-text-muted">
          <span>Progreso</span>
          <span>{tested}/{total}</span>
        </div>
        <div className="h-1.5 rounded-full ls-bg-input overflow-hidden">
          <div
            className="h-full rounded-full bg-violet-500 transition-all"
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>
      </div>

      {/* Tiempo */}
      <div className="flex justify-between text-[9px]">
        <span className="ls-text-muted">Tiempo</span>
        <span className="font-mono ls-text2">{mins}:{secs.toString().padStart(2, "0")}</span>
      </div>

      {/* Presentaciones */}
      <div className="flex justify-between text-[9px]">
        <span className="ls-text-muted">Presentaciones</span>
        <span className="font-mono ls-text2">{state.presentationCount}</span>
      </div>

      <div className="h-px ls-bg-input" />

      {/* Confiabilidad */}
      <div className="space-y-0.5">
        <span className="text-[8px] ls-text-muted uppercase tracking-wider">Confiabilidad</span>
        <Stat label="Pérd. fijación" value={`${state.fixationLosses}/${state.fixationLossesTotal}`} pct={flPct} warn={flPct > 20} />
        <Stat label="Falsos +" value={`${state.falsePositives}/${state.falsePositivesTotal}`} pct={fpPct} warn={fpPct > 15} />
        <Stat label="Falsos -" value={`${state.falseNegatives}/${state.falseNegativesTotal}`} pct={fnPct} warn={fnPct > 15} />
      </div>

      <div className="h-px ls-bg-input" />

      {/* Índices globales */}
      <div className="space-y-0.5">
        <span className="text-[8px] ls-text-muted uppercase tracking-wider">Índices</span>
        <div className="flex justify-between text-[10px]">
          <span className="ls-text-muted">MD</span>
          <span className={`font-mono font-medium ${md !== null && md < -6 ? "text-red-400" : md !== null && md < -2 ? "text-amber-400" : "ls-text2"}`}>
            {md !== null ? `${md > 0 ? "+" : ""}${md} dB` : "—"}
          </span>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="ls-text-muted">PSD</span>
          <span className={`font-mono font-medium ${psd !== null && psd > 4 ? "text-red-400" : psd !== null && psd > 2 ? "text-amber-400" : "ls-text2"}`}>
            {psd !== null ? `${psd} dB` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, pct, warn }: { label: string; value: string; pct: number; warn: boolean }) {
  return (
    <div className="flex justify-between text-[10px]">
      <span className="ls-text-muted">{label}</span>
      <span className={`font-mono ${warn ? "text-red-400" : "ls-text2"}`}>
        {value} ({pct}%)
      </span>
    </div>
  );
}
