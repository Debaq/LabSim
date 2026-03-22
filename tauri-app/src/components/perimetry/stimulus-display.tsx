/**
 * Indicador del estímulo que se está presentando.
 * Muestra: punto actual, intensidad, si el paciente respondió.
 */

interface Props {
  pointX: number | null;
  pointY: number | null;
  stimulusDb: number | null;
  responded: boolean | null;
  isPresenting: boolean;
}

export function StimulusDisplay({ pointX, pointY, stimulusDb, responded, isPresenting }: Props) {
  return (
    <div className="flex items-center gap-3 px-2 py-1 text-[10px] font-mono">
      <div className="flex items-center gap-1">
        <div className={`h-2 w-2 rounded-full ${isPresenting ? "bg-amber-400 animate-pulse" : "bg-zinc-600"}`} />
        <span className="ls-text-muted">
          {isPresenting ? "PRESENTANDO" : "ESPERA"}
        </span>
      </div>
      {pointX !== null && pointY !== null && (
        <span className="ls-text-muted">
          ({pointX}°, {pointY}°)
        </span>
      )}
      {stimulusDb !== null && (
        <span className="ls-text2">{stimulusDb} dB</span>
      )}
      {responded !== null && (
        <span className={responded ? "text-emerald-400" : "text-red-400"}>
          {responded ? "✓ Respuesta" : "✗ No respuesta"}
        </span>
      )}
    </div>
  );
}
