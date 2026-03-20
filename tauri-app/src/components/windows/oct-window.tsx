import { useState } from "react";
import { BScanView } from "@/components/oct/bscan-view";
import { RNFLTSNIT } from "@/components/oct/rnfl-tsnit";
import { ThicknessMap } from "@/components/oct/thickness-map";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import { generateRNFLProfile, generateGCLIPL, RNFL_CLOCK_HOURS, RNFL_QUADRANTS, GCL_IPL_SECTORS, normativeColor, type Pathology } from "@/lib/oct-synthetic";
import { cn } from "@/lib/utils";
import { RefreshCw } from "lucide-react";

type ScanMode = "macula" | "disc";
type ViewTab = "bscan" | "thickness" | "rnfl" | "gcl";

export function OCTWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [scanMode, setScanMode] = useState<ScanMode>("disc");
  const [viewTab, setViewTab] = useState<ViewTab>("bscan");
  const [pathology, setPathology] = useState<Pathology>("normal");
  const [seed, setSeed] = useState(42);

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));

  const profile = generateRNFLProfile(seed, pathology);
  const gclData = generateGCLIPL(seed, pathology);

  // Clock hour averages
  const clockAvg = (start: number, end: number) => {
    const pts = profile.filter((p) => p.angle >= start && p.angle < end);
    return pts.length > 0 ? Math.round(pts.reduce((s, p) => s + p.thickness, 0) / pts.length) : 0;
  };

  const globalAvg = Math.round(profile.reduce((s, p) => s + p.thickness, 0) / profile.length);
  const signalQ = 7 + Math.floor((seed % 3));

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#12151a] to-[#0d0f13]">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between bg-[#0a0c10] px-3">
        <span className="text-[9px] font-bold tracking-[0.2em] text-white/30">LABSIM <span className="font-normal text-white/12">OCT SPECTRALIS</span></span>
        <div className="flex items-center gap-2 text-[8px] text-white/20">
          <span className={cn("font-bold", eye === "OD" ? "text-red-400/60" : "text-blue-400/60")}>{eye}</span>
          <span>|</span>
          <span>{scanMode === "disc" ? "Disco Óptico" : "Mácula"}</span>
          <span>|</span>
          <span className={cn(signalQ >= 7 ? "text-emerald-400/60" : "text-amber-400/60")}>Q:{signalQ}/10</span>
          <span>|</span>
          <span className="capitalize">{pathology}</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT panel */}
        <div className="flex w-[155px] shrink-0 flex-col gap-1.5 border-r border-white/[0.04] p-1.5 overflow-y-auto">
          {/* Config */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2 space-y-1.5">
            <div className="text-[7px] font-bold uppercase tracking-wider text-white/25">Configuración</div>
            <div>
              <div className="mb-0.5 text-[6px] uppercase text-white/15">Ojo</div>
              <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); regenerate(); }} options={[
                { value: "OD", label: "OD", color: "bg-red-600 text-white" },
                { value: "OI", label: "OI", color: "bg-blue-600 text-white" },
              ]} />
            </div>
            <div>
              <div className="mb-0.5 text-[6px] uppercase text-white/15">Scan</div>
              <ToggleSwitch value={scanMode} onChange={(v) => setScanMode(v as ScanMode)} options={[
                { value: "disc", label: "Disco" },
                { value: "macula", label: "Mácula" },
              ]} />
            </div>
            <div>
              <div className="mb-0.5 text-[6px] uppercase text-white/15">Patología</div>
              <div className="grid grid-cols-2 gap-0.5">
                {(["normal", "glaucoma", "edema", "drusen", "epiretinal", "amd-dry", "amd-wet"] as Pathology[]).map((p) => {
                  const labels: Record<Pathology, string> = { normal: "Normal", glaucoma: "Glauc", edema: "Edema", drusen: "Drusen", epiretinal: "ERM", "amd-dry": "DMAE-s", "amd-wet": "DMAE-h" };
                  return <button key={p} onClick={() => { setPathology(p); regenerate(); }}
                    className={cn("rounded border py-0.5 text-[7px] font-bold transition",
                      pathology === p ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "border-white/[0.06] text-white/20 hover:text-white/40")}>{labels[p]}</button>;
                })}
              </div>
            </div>
            <button onClick={regenerate} className="flex w-full items-center justify-center gap-1 rounded border border-white/10 py-1 text-[7px] text-white/25 hover:bg-white/5">
              <RefreshCw className="h-2.5 w-2.5" /> Regenerar
            </button>
          </div>

          {/* RNFL Quadrants */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[7px] font-bold uppercase tracking-wider text-white/25">RNFL Cuadrantes</div>
            {(["S", "N", "I", "T"] as const).map((q) => {
              const avg = clockAvg(q === "S" ? 45 : q === "N" ? 135 : q === "I" ? 225 : 315, q === "S" ? 135 : q === "N" ? 225 : q === "I" ? 315 : 405 > 360 ? 45 : 405);
              const norm = RNFL_QUADRANTS[q];
              return (
                <div key={q} className="flex items-center justify-between py-px">
                  <span className="text-[8px] font-bold text-white/30 w-4">{q}</span>
                  <div className="h-2.5 flex-1 mx-1 rounded-sm" style={{ backgroundColor: normativeColor(avg, norm), opacity: 0.4 }} />
                  <span className="text-[9px] font-mono font-bold" style={{ color: normativeColor(avg, norm) }}>{avg}</span>
                </div>
              );
            })}
            <div className="mt-1 pt-1 border-t border-white/[0.06] flex justify-between">
              <span className="text-[7px] font-bold text-white/30">Global</span>
              <span className="text-[9px] font-mono font-bold text-white/60">{globalAvg} µm</span>
            </div>
          </div>

          {/* Clock Hours */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[7px] font-bold uppercase tracking-wider text-white/25">Horas del Reloj</div>
            <div className="grid grid-cols-4 gap-px">
              {[12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((hr) => {
                const avg = clockAvg((hr - 1) * 30, hr * 30);
                const norm = RNFL_CLOCK_HOURS[hr];
                return (
                  <div key={hr} className="flex flex-col items-center rounded p-0.5" style={{ backgroundColor: normativeColor(avg, norm) + "22" }}>
                    <span className="text-[6px] text-white/30">{hr}h</span>
                    <span className="text-[8px] font-mono font-bold" style={{ color: normativeColor(avg, norm) }}>{avg}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* GCL+IPL */}
          <div className="rounded border border-white/[0.06] bg-black/30 p-2">
            <div className="mb-1 text-[7px] font-bold uppercase tracking-wider text-white/25">GCL+IPL</div>
            {Object.entries(gclData).map(([sec, val]) => {
              const norm = GCL_IPL_SECTORS[sec];
              return (
                <div key={sec} className="flex items-center justify-between py-px">
                  <span className="text-[7px] text-white/25 w-5">{sec}</span>
                  <div className="h-2 flex-1 mx-1 rounded-sm" style={{ backgroundColor: norm ? normativeColor(val, norm) : "#555", opacity: 0.4 }} />
                  <span className="text-[8px] font-mono font-bold" style={{ color: norm ? normativeColor(val, norm) : "#aaa" }}>{val}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* CENTER: Main view */}
        <div className="flex flex-1 flex-col p-2 gap-1.5 min-w-0">
          <div className="flex items-center justify-center shrink-0">
            <ToggleSwitch value={viewTab} onChange={(v) => setViewTab(v as ViewTab)} options={[
              { value: "bscan", label: "B-Scan" },
              { value: "thickness", label: "Espesor" },
              { value: "rnfl", label: "RNFL" },
              { value: "gcl", label: "GCL" },
            ]} />
          </div>

          <div className="flex-1 min-h-0">
            {viewTab === "bscan" && <BScanView seed={seed} isMacular={scanMode === "macula"} pathology={pathology} />}
            {viewTab === "rnfl" && <RNFLTSNIT seed={seed} pathology={pathology} />}
            {viewTab === "thickness" && (
              <div className="flex h-full items-center justify-center">
                <ThicknessMap seed={seed} pathology={pathology} />
              </div>
            )}
            {viewTab === "gcl" && (
              <div className="flex h-full items-center justify-center">
                <ThicknessMap seed={seed + 100} pathology={pathology} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex h-5 shrink-0 items-center justify-between bg-black/30 px-3 text-[7px] text-white/15">
        <span>{eye} | {scanMode === "disc" ? "Optic Disc" : "Macula"} | {pathology}</span>
        <div className="flex items-center gap-2">
          <span className="text-[6px]">
            <span className="inline-block h-1.5 w-3 rounded-sm bg-emerald-500/60" /> ≥p5
            <span className="ml-1 inline-block h-1.5 w-3 rounded-sm bg-amber-500/60" /> p1-p5
            <span className="ml-1 inline-block h-1.5 w-3 rounded-sm bg-red-500/60" /> &lt;p1
          </span>
        </div>
      </div>
    </div>
  );
}
