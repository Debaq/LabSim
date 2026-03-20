import { useState } from "react";
import { BScanView } from "@/components/oct/bscan-view";
import { RNFLTSNIT } from "@/components/oct/rnfl-tsnit";
import { ThicknessMap } from "@/components/oct/thickness-map";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import { generateRNFLProfile, RNFL_NORMAL, normativeColor, type Pathology } from "@/lib/oct-synthetic";
import { cn } from "@/lib/utils";
import { RefreshCw } from "lucide-react";

type ScanMode = "macula" | "disc";
type ViewTab = "bscan" | "maps" | "rnfl";

export function OCTWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [scanMode, setScanMode] = useState<ScanMode>("disc");
  const [viewTab, setViewTab] = useState<ViewTab>("bscan");
  const [pathology, setPathology] = useState<Pathology>("normal");
  const [seed, setSeed] = useState(42);
  const [signalQuality, setSignalQuality] = useState(8);

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));

  // RNFL sector averages for the table
  const profile = generateRNFLProfile(seed, pathology === "glaucoma" ? "glaucoma" : "normal");
  const sectorAvg = (start: number, end: number) => {
    const pts = profile.filter((p) => p.angle >= start && p.angle < end);
    return pts.length > 0 ? Math.round(pts.reduce((s, p) => s + p.thickness, 0) / pts.length) : 0;
  };

  const sectors = [
    { label: "T", avg: sectorAvg(0, 45), norm: RNFL_NORMAL.T },
    { label: "TS", avg: sectorAvg(45, 90), norm: RNFL_NORMAL.TS },
    { label: "S", avg: sectorAvg(90, 135), norm: RNFL_NORMAL.S },
    { label: "NS", avg: sectorAvg(135, 180), norm: RNFL_NORMAL.NS },
    { label: "N", avg: sectorAvg(180, 225), norm: RNFL_NORMAL.N },
    { label: "NI", avg: sectorAvg(225, 270), norm: RNFL_NORMAL.NI },
    { label: "I", avg: sectorAvg(270, 315), norm: RNFL_NORMAL.I },
    { label: "TI", avg: sectorAvg(315, 360), norm: RNFL_NORMAL.TI },
  ];

  const globalAvg = Math.round(profile.reduce((s, p) => s + p.thickness, 0) / profile.length);

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#12151a] to-[#0d0f13]">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between bg-[#0a0c10] px-3">
        <span className="text-[9px] font-bold tracking-[0.2em] text-white/30">
          LABSIM <span className="font-normal text-white/12">OCT SPECTRALIS</span>
        </span>
        <div className="flex items-center gap-2 text-[8px] text-white/20">
          <span className={cn("font-bold", eye === "OD" ? "text-red-400/60" : "text-blue-400/60")}>{eye}</span>
          <span>|</span>
          <span>{scanMode === "disc" ? "Disco Óptico" : "Mácula"}</span>
          <span>|</span>
          <span>Q: {signalQuality}/10</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Config panel */}
        <div className="flex w-[150px] shrink-0 flex-col gap-2 border-r border-white/[0.04] p-2">
          <div className="rounded border border-white/[0.06] bg-black/30 p-2 space-y-1.5">
            <div className="text-[8px] font-bold uppercase tracking-wider text-white/25">Configuración</div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Ojo</div>
              <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); regenerate(); }} options={[
                { value: "OD", label: "OD", color: "bg-red-600 text-white" },
                { value: "OI", label: "OI", color: "bg-blue-600 text-white" },
              ]} />
            </div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Tipo de Scan</div>
              <ToggleSwitch value={scanMode} onChange={(v) => setScanMode(v as ScanMode)} options={[
                { value: "disc", label: "Disco" },
                { value: "macula", label: "Mácula" },
              ]} />
            </div>

            <div>
              <div className="mb-0.5 text-[7px] uppercase text-white/15">Caso</div>
              <ToggleSwitch value={pathology} onChange={(v) => { setPathology(v as Pathology); regenerate(); }} options={[
                { value: "normal", label: "Norm" },
                { value: "glaucoma", label: "Glau" },
              ]} />
              <div className="mt-1">
                <ToggleSwitch value={pathology} onChange={(v) => { setPathology(v as Pathology); regenerate(); }} options={[
                  { value: "edema", label: "Edema" },
                  { value: "drusen", label: "Drus" },
                ]} />
              </div>
            </div>

            <button onClick={regenerate}
              className="flex w-full items-center justify-center gap-1 rounded border border-white/10 py-1 text-[8px] text-white/30 hover:bg-white/5 hover:text-white/50">
              <RefreshCw className="h-3 w-3" />
              Regenerar
            </button>
          </div>

          {/* Signal quality */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[8px] font-bold uppercase tracking-wider text-white/25">Señal</div>
            <div className="flex items-center gap-1">
              <div className="h-2 flex-1 rounded-full bg-black/40">
                <div className={cn("h-full rounded-full transition-all",
                  signalQuality >= 7 ? "bg-emerald-500/60" : signalQuality >= 5 ? "bg-amber-500/60" : "bg-red-500/60"
                )} style={{ width: `${signalQuality * 10}%` }} />
              </div>
              <span className="text-[9px] font-mono font-bold text-white/50">{signalQuality}</span>
            </div>
          </div>

          {/* RNFL sector table */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[8px] font-bold uppercase tracking-wider text-white/25">RNFL Sectores</div>
            <div className="space-y-px">
              {sectors.map((s) => (
                <div key={s.label} className="flex items-center justify-between">
                  <span className="text-[8px] text-white/30 w-5">{s.label}</span>
                  <div className="h-2 flex-1 mx-1 rounded-sm" style={{ backgroundColor: normativeColor(s.avg, s.norm), opacity: 0.5 }} />
                  <span className="text-[8px] font-mono font-bold" style={{ color: normativeColor(s.avg, s.norm) }}>{s.avg}</span>
                </div>
              ))}
              <div className="mt-1 flex items-center justify-between border-t border-white/[0.06] pt-1">
                <span className="text-[8px] font-bold text-white/40">Prom</span>
                <span className="text-[9px] font-mono font-bold text-white/60">{globalAvg} µm</span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTER: Main view */}
        <div className="flex flex-1 flex-col p-2 gap-2 min-w-0">
          {/* Tab selector */}
          <div className="flex items-center justify-center shrink-0">
            <ToggleSwitch value={viewTab} onChange={(v) => setViewTab(v as ViewTab)} options={[
              { value: "bscan", label: "B-Scan" },
              { value: "maps", label: "Mapas" },
              { value: "rnfl", label: "RNFL" },
            ]} />
          </div>

          {/* Content */}
          <div className="flex-1 min-h-0">
            {viewTab === "bscan" && (
              <BScanView seed={seed} isMacular={scanMode === "macula"} pathology={pathology} />
            )}
            {viewTab === "maps" && (
              <div className="flex h-full items-center justify-center gap-3">
                <ThicknessMap seed={seed} pathology={pathology} type="macular" />
                <ThicknessMap seed={seed + 1} pathology={pathology} type="rnfl" />
              </div>
            )}
            {viewTab === "rnfl" && (
              <RNFLTSNIT seed={seed} pathology={pathology} />
            )}
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex h-5 shrink-0 items-center justify-between bg-black/30 px-3 text-[7px] text-white/15">
        <span>{eye} | {scanMode === "disc" ? "Disco Óptico" : "Mácula"} | {pathology}</span>
        <span>Seed: {seed} | Signal: {signalQuality}/10</span>
      </div>
    </div>
  );
}
