import { useState, useEffect } from "react";
import { FundusView } from "@/components/retinography/fundus-view";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import {
  type RetinopathyType,
  type FundusFilter,
  RETINOPATHY_LABELS,
  getCDRatio,
} from "@/lib/retinography-synthetic";
import { usePatientStore } from "@/stores/patient-store";
import { cn } from "@/lib/utils";
import { Link2, Link2Off } from "lucide-react";
import { AlignmentPanel, DEFAULT_ALIGNMENT, isAligned, type AlignmentState } from "@/components/ui/alignment-panel";

const EMPTY_CONFIG = {};

const FILTER_OPTIONS: { value: FundusFilter; label: string }[] = [
  { value: "color", label: "Color" },
  { value: "red-free", label: "Aneritra" },
  { value: "blue", label: "Azul" },
  { value: "infrared", label: "IR" },
];

const ANGLE_OPTIONS = [30, 45, 60] as const;

export function RetinographyWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [pathology, setPathology] = useState<RetinopathyType>("normal");
  const [seed, setSeed] = useState(42);
  const [signalOverride, setSignalOverride] = useState<number | null>(null);
  const [captured, setCaptured] = useState<{ OD: boolean; OI: boolean }>({ OD: false, OI: false });
  const [flash, setFlash] = useState(false);
  const [filter, setFilter] = useState<FundusFilter>("color");
  const [diopterOffset, setDiopterOffset] = useState(0);
  const [flashIntensity, setFlashIntensity] = useState(50);
  const [captureAngle, setCaptureAngle] = useState<number>(45);
  const [alignment, setAlignment] = useState<AlignmentState>(DEFAULT_ALIGNMENT);

  const retConfig = usePatientStore((s) => s.data.modules.retinography ?? EMPTY_CONFIG);
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
    const seedBase = patientId ? patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) : 42;
    setSeed(seedBase + (eye === "OI" ? 1000 : 0));
  }, [hasCaseLoaded, eye, retConfig, patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));
  const signalQ = signalOverride ?? (7 + Math.floor((seed % 3)));
  const cdRatio = getCDRatio(pathology, seed + (eye === "OI" ? 1000 : 0));
  const isFocused = Math.abs(diopterOffset) <= 1;
  const canCapture = hasCaseLoaded && isAligned(alignment);

  const handleCapture = () => {
    if (!canCapture) return;
    setFlash(true);
    setTimeout(() => setFlash(false), 200);
    setCaptured((prev) => ({ ...prev, [eye]: true }));
    regenerate();
  };

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">RETINÓGRAFO</span>
        </span>
        <div className="flex items-center gap-2 text-xs ls-text-muted">
          {hasCaseLoaded ? (
            <span className="flex items-center gap-1 text-emerald-400/70"><Link2 className="h-3 w-3" /> Caso</span>
          ) : (
            <span className="flex items-center gap-1"><Link2Off className="h-3 w-3" /> Libre</span>
          )}
          <span>|</span>
          <span className={cn("font-bold", eye === "OD" ? "text-red-400/60" : "text-blue-400/60")}>{eye}</span>
          <span>|</span>
          <span>{captureAngle}°</span>
          <span>|</span>
          <span>{FILTER_OPTIONS.find((f) => f.value === filter)?.label}</span>
          {hasCaseLoaded && (
            <>
              <span>|</span>
              <span className={cn(signalQ >= 7 ? "text-emerald-400/60" : "text-amber-400/60")}>Q:{signalQ}/10</span>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Controles del equipo (compactos) */}
        <div className="flex w-[130px] shrink-0 flex-col gap-1.5 overflow-y-auto border-r ls-border p-1.5">
          {/* Ojo */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5 space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">Ojo</div>
            <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); if (hasCaseLoaded) regenerate(); }}
              options={[
                { value: "OD", label: "OD", color: "bg-red-600 ls-text" },
                { value: "OI", label: "OI", color: "bg-blue-600 ls-text" },
              ]} />
          </div>

          {/* Filtro */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5 space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">Filtro</div>
            <div className="grid grid-cols-2 gap-0.5">
              {FILTER_OPTIONS.map((f) => (
                <button key={f.value} onClick={() => setFilter(f.value)}
                  className={cn("rounded border py-0.5 text-xs font-bold transition",
                    filter === f.value ? "border-red-500/40 bg-red-500/20 text-red-300" : "ls-border ls-text-muted hover:ls-bg-input")}
                >{f.label}</button>
              ))}
            </div>
          </div>

          {/* Campo */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5 space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">Campo</div>
            <div className="flex gap-0.5">
              {ANGLE_OPTIONS.map((a) => (
                <button key={a} onClick={() => setCaptureAngle(a)}
                  className={cn("flex-1 rounded border py-0.5 text-xs font-bold transition",
                    captureAngle === a ? "border-red-500/40 bg-red-500/20 text-red-300" : "ls-border ls-text-muted hover:ls-bg-input")}
                >{a}°</button>
              ))}
            </div>
          </div>

          {/* Dioptrías */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5 space-y-0.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider ls-text-muted">Dioptrías</span>
              <span className={cn("text-xs font-mono font-bold", isFocused ? "text-emerald-400" : "text-amber-400")}>
                {diopterOffset > 0 ? "+" : ""}{diopterOffset}D
              </span>
            </div>
            <input type="range" min={-20} max={20} step={0.5} value={diopterOffset}
              onChange={(e) => setDiopterOffset(parseFloat(e.target.value))}
              className="w-full h-1.5 appearance-none rounded bg-zinc-700 accent-red-500 cursor-pointer" />
          </div>

          {/* Flash */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5 space-y-0.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider ls-text-muted">Flash</span>
              <span className="text-xs font-mono ls-text-muted">{flashIntensity}%</span>
            </div>
            <input type="range" min={10} max={100} step={5} value={flashIntensity}
              onChange={(e) => setFlashIntensity(parseInt(e.target.value))}
              className="w-full h-1.5 appearance-none rounded bg-zinc-700 accent-red-500 cursor-pointer" />
          </div>

          {/* Hallazgos */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5">
            <div className="mb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Hallazgos</div>
            <div className="space-y-0.5 text-xs">
              <div className="flex justify-between"><span className="ls-text-muted">C/D</span><span className="font-mono ls-text2">{hasCaseLoaded ? cdRatio.toFixed(2) : "---"}</span></div>
              <div className="flex justify-between"><span className="ls-text-muted">Q</span><span className="font-mono ls-text2">{hasCaseLoaded ? `${signalQ}/10` : "---"}</span></div>
            </div>
          </div>

          {/* Capturas */}
          <div className="rounded border ls-border ls-bg-panel2 p-1.5">
            <div className="mb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Capturas</div>
            <div className="flex gap-2 justify-center">
              {(["OD", "OI"] as const).map((e) => (
                <div key={e} className="flex flex-col items-center gap-0.5">
                  <div className={cn("h-3 w-3 rounded-full border", captured[e] ? "border-emerald-500 bg-emerald-500/40" : "ls-border")} />
                  <span className="text-xs ls-text-muted">{e}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CENTER + BOTTOM: Imagen arriba, joystick abajo */}
        <div className="flex flex-1 flex-col min-w-0">
          {/* Imagen */}
          <div className="relative flex flex-1 items-center justify-center p-2 min-h-0">
            {flash && <div className="absolute inset-0 z-10 bg-white/30 animate-pulse pointer-events-none" />}
            {hasCaseLoaded && !isFocused && (
              <div className="absolute top-2 right-2 z-10 rounded bg-amber-500/20 border border-amber-500/30 px-2 py-0.5">
                <span className="text-xs font-mono text-amber-400">DESENFOCADO</span>
              </div>
            )}
            <div className="flex-1 flex items-center justify-center min-h-0 w-full max-h-full">
              {hasCaseLoaded ? (
                <FundusView seed={seed} pathology={pathology} eye={eye} signalQuality={signalQ}
                  filter={filter} diopterOffset={diopterOffset} flashIntensity={flashIntensity} captureAngle={captureAngle} />
              ) : (
                <div className="h-[280px] w-[280px] rounded-full bg-black/80 flex items-center justify-center">
                  <span className="text-xs font-mono ls-text-muted">SIN CAPTURA</span>
                </div>
              )}
            </div>
          </div>

          {/* BOTTOM: Joystick centrado */}
          <div className="shrink-0 border-t ls-border px-3 py-2">
            <AlignmentPanel state={alignment} onChange={setAlignment} onCapture={handleCapture} compact />
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-5 shrink-0 items-center justify-between ls-bg-panel2 px-3 text-xs ls-text-muted">
        <span>{eye} | {captureAngle}° | {FILTER_OPTIONS.find((f) => f.value === filter)?.label} | {diopterOffset > 0 ? "+" : ""}{diopterOffset}D</span>
        <span>{hasCaseLoaded ? `${RETINOPATHY_LABELS[pathology]} | C/D: ${cdRatio.toFixed(2)} | Q:${signalQ}` : "---"}</span>
      </div>
    </div>
  );
}
