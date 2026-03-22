import { useState, useEffect } from "react";
import { FundusView } from "@/components/retinography/fundus-view";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import {
  type RetinopathyType,
  RETINOPATHY_LABELS,
  getCDRatio,
} from "@/lib/retinography-synthetic";
import { usePatientStore } from "@/stores/patient-store";
import { cn } from "@/lib/utils";
import { RefreshCw, Link2, Link2Off, Camera } from "lucide-react";

export function RetinographyWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [pathology, setPathology] = useState<RetinopathyType>("normal");
  const [seed, setSeed] = useState(42);
  const [signalOverride, setSignalOverride] = useState<number | null>(null);
  const [captured, setCaptured] = useState<{ OD: boolean; OI: boolean }>({ OD: false, OI: false });
  const [flash, setFlash] = useState(false);

  const retConfig = usePatientStore((s) => s.data.modules.retinography ?? {});
  const patientId = usePatientStore((s) => s.currentPatientId);
  const hasCaseLoaded = patientId !== null && Object.keys(retConfig).length > 0;

  useEffect(() => {
    if (!hasCaseLoaded) return;
    const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
    const cfg = (retConfig as Record<string, Record<string, unknown>>)[eyeKey];
    if (!cfg) return;

    const patho = cfg.patologia as RetinopathyType | undefined;
    if (patho && patho !== pathology) setPathology(patho);

    const q = cfg.calidadSenal as number | undefined;
    setSignalOverride(q ?? null);

    const seedBase = patientId
      ? patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0)
      : 42;
    setSeed(seedBase + (eye === "OI" ? 1000 : 0));
  }, [hasCaseLoaded, eye, retConfig, patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));

  const signalQ = signalOverride ?? (7 + Math.floor((seed % 3)));
  const cdRatio = getCDRatio(pathology, seed + (eye === "OI" ? 1000 : 0));

  const handleCapture = () => {
    setFlash(true);
    setTimeout(() => setFlash(false), 200);
    setCaptured((prev) => ({ ...prev, [eye]: true }));
  };

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM{" "}
          <span className="font-normal ls-text-muted">RETINÓGRAFO</span>
        </span>
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
          <span
            className={cn(
              "font-bold",
              eye === "OD" ? "text-red-400/60" : "text-blue-400/60",
            )}
          >
            {eye}
          </span>
          <span>|</span>
          <span
            className={cn(
              signalQ >= 7 ? "text-emerald-400/60" : "text-amber-400/60",
            )}
          >
            Q:{signalQ}/10
          </span>
          <span>|</span>
          <span className="capitalize">
            {RETINOPATHY_LABELS[pathology]}
          </span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Controles */}
        <div className="flex w-[155px] shrink-0 flex-col gap-1.5 overflow-y-auto border-r ls-border p-1.5">
          {/* Configuración */}
          <div className="rounded border ls-border ls-bg-panel2 p-2 space-y-1.5">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">
              Configuración
            </div>
            <div>
              <div className="mb-0.5 text-xs uppercase ls-text-muted">Ojo</div>
              <ToggleSwitch
                value={eye}
                onChange={(v) => {
                  setEye(v as "OD" | "OI");
                  regenerate();
                }}
                options={[
                  { value: "OD", label: "OD", color: "bg-red-600 ls-text" },
                  { value: "OI", label: "OI", color: "bg-blue-600 ls-text" },
                ]}
              />
            </div>

            {!hasCaseLoaded && (
              <div>
                <div className="mb-0.5 text-xs uppercase ls-text-muted">
                  Patología
                </div>
                <div className="grid grid-cols-2 gap-0.5">
                  {(Object.keys(RETINOPATHY_LABELS) as RetinopathyType[]).map(
                    (p) => (
                      <button
                        key={p}
                        onClick={() => {
                          setPathology(p);
                          regenerate();
                        }}
                        className={cn(
                          "rounded border py-0.5 text-[10px] font-bold transition",
                          pathology === p
                            ? "border-amber-500/40 bg-amber-500/20 text-amber-300"
                            : "ls-border ls-text-muted hover:ls-text2",
                        )}
                      >
                        {RETINOPATHY_LABELS[p]}
                      </button>
                    ),
                  )}
                </div>
              </div>
            )}

            {hasCaseLoaded && (
              <div className="rounded border border-emerald-500/20 bg-emerald-500/5 p-1.5">
                <span className="text-xs text-emerald-400/80">
                  Patología definida por el caso clínico
                </span>
              </div>
            )}

            <button
              onClick={regenerate}
              className="flex w-full items-center justify-center gap-1 rounded border ls-border py-1 text-xs ls-text-muted hover:ls-bg-input"
            >
              <RefreshCw className="h-2.5 w-2.5" /> Regenerar
            </button>
          </div>

          {/* Hallazgos */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">
              Hallazgos
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs ls-text-muted">C/D ratio</span>
                <span
                  className={cn(
                    "text-xs font-mono font-bold",
                    cdRatio > 0.6
                      ? "text-red-400"
                      : cdRatio > 0.4
                        ? "text-amber-400"
                        : "text-emerald-400",
                  )}
                >
                  {cdRatio.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs ls-text-muted">Calidad</span>
                <span
                  className={cn(
                    "text-xs font-mono font-bold",
                    signalQ >= 7
                      ? "text-emerald-400"
                      : signalQ >= 5
                        ? "text-amber-400"
                        : "text-red-400",
                  )}
                >
                  {signalQ}/10
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs ls-text-muted">Mácula</span>
                <span className="text-xs font-bold ls-text2">
                  {pathology === "normal" ||
                  pathology === "glaucoma" ||
                  pathology === "hta"
                    ? "Normal"
                    : "Alterada"}
                </span>
              </div>
            </div>
          </div>

          {/* Capturas */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">
              Capturas
            </div>
            <div className="flex gap-2">
              <div className="flex flex-col items-center gap-0.5">
                <div
                  className={cn(
                    "h-3 w-3 rounded-full border",
                    captured.OD
                      ? "border-emerald-500 bg-emerald-500/40"
                      : "ls-border",
                  )}
                />
                <span className="text-[10px] ls-text-muted">OD</span>
              </div>
              <div className="flex flex-col items-center gap-0.5">
                <div
                  className={cn(
                    "h-3 w-3 rounded-full border",
                    captured.OI
                      ? "border-emerald-500 bg-emerald-500/40"
                      : "ls-border",
                  )}
                />
                <span className="text-[10px] ls-text-muted">OI</span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER: Vista del fondo de ojo */}
        <div className="relative flex flex-1 flex-col items-center justify-center gap-2 p-3 min-w-0">
          {/* Flash overlay */}
          {flash && (
            <div className="absolute inset-0 z-10 bg-white/30 animate-pulse pointer-events-none" />
          )}

          <div className="flex-1 flex items-center justify-center min-h-0 w-full">
            <FundusView
              seed={seed}
              pathology={pathology}
              eye={eye}
              signalQuality={signalQ}
            />
          </div>

          {/* Botón de captura */}
          <button
            onClick={handleCapture}
            className="flex items-center gap-1.5 rounded-lg border ls-border px-4 py-1.5 text-xs font-bold ls-text2 transition hover:ls-bg-input hover:ls-text"
          >
            <Camera className="h-3.5 w-3.5" /> Capturar {eye}
          </button>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-5 shrink-0 items-center justify-between ls-bg-panel2 px-3 text-xs ls-text-muted">
        <span>
          {eye} | Retinografía | {RETINOPATHY_LABELS[pathology]}
        </span>
        <span>C/D: {cdRatio.toFixed(2)}</span>
      </div>
    </div>
  );
}
