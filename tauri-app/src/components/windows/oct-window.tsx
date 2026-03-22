import { useState, useEffect } from "react";
import { BScanView } from "@/components/oct/bscan-view";
import { RNFLTSNIT } from "@/components/oct/rnfl-tsnit";
import { ThicknessMap } from "@/components/oct/thickness-map";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import { generateRNFLProfile, generateGCLIPL, RNFL_CLOCK_HOURS, RNFL_QUADRANTS, GCL_IPL_SECTORS, normativeColor, type Pathology, type OctSeverity, type OctPatientParams } from "@/lib/oct-synthetic";
import { usePatientStore } from "@/stores/patient-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { cn } from "@/lib/utils";
import { RefreshCw, Link2, Link2Off } from "lucide-react";

type ScanMode = "macula" | "disc";
type ViewTab = "bscan" | "thickness" | "rnfl" | "gcl";

export function OCTWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [scanMode, setScanMode] = useState<ScanMode>("disc");
  const [viewTab, setViewTab] = useState<ViewTab>("bscan");
  const [pathology, setPathology] = useState<Pathology>("normal");
  const [severity, setSeverity] = useState<OctSeverity>("moderado");
  const [seed, setSeed] = useState(42);
  const [signalOverride, setSignalOverride] = useState<number | null>(null);

  // Read case config from patient store
  const octConfig = usePatientStore((s) => s.data.modules.oct ?? {});
  const patientId = usePatientStore((s) => s.currentPatientId);
  const hasCaseLoaded = patientId !== null && Object.keys(octConfig).length > 0;

  // Sync from case when loaded
  useEffect(() => {
    if (!hasCaseLoaded) return;
    const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
    const cfg = (octConfig as Record<string, Record<string, unknown>>)[eyeKey];
    if (!cfg) return;

    const patho = cfg.patologia as Pathology | undefined;
    if (patho && patho !== pathology) setPathology(patho);

    const sev = cfg.severidad as OctSeverity | undefined;
    if (sev) setSeverity(sev);

    const scan = cfg.scanPreferido as string | undefined;
    if (scan === "disco" || scan === "macula") setScanMode(scan === "disco" ? "disc" : "macula");

    const q = cfg.calidadSenal as number | undefined;
    setSignalOverride(q ?? null);

    // Generate a deterministic seed from patient + eye for reproducibility
    const seedBase = patientId ? patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) : 42;
    setSeed(seedBase + (eye === "OI" ? 1000 : 0));
  }, [hasCaseLoaded, eye, octConfig, patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));

  // Extraer parámetros fisiológicos del paciente
  const eyeKey2 = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
  const eyeCfg = (octConfig as Record<string, Record<string, unknown>>)[eyeKey2] ?? {};
  const patientParams: OctPatientParams = {
    rnflAvg: eyeCfg.rnflAvg as number | undefined,
    gclIplAvg: eyeCfg.gclIplAvg as number | undefined,
    centralMacularThickness: eyeCfg.centralMacularThickness as number | undefined,
    cooperationLevel: eyeCfg.cooperationLevel as number | undefined,
    tearFilmQuality: eyeCfg.tearFilmQuality as number | undefined,
  };

  const profile = generateRNFLProfile(seed, pathology, severity, patientParams);
  const gclData = generateGCLIPL(seed, pathology, severity, patientParams);

  const clockAvg = (start: number, end: number) => {
    const pts = profile.filter((p) => p.angle >= start && p.angle < end);
    return pts.length > 0 ? Math.round(pts.reduce((s, p) => s + p.thickness, 0) / pts.length) : 0;
  };

  const globalAvg = Math.round(profile.reduce((s, p) => s + p.thickness, 0) / profile.length);
  const signalQ = signalOverride ?? (7 + Math.floor((seed % 3)));

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="OCT" />
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">LABSIM <span className="font-normal ls-text-muted">OCT SPECTRALIS</span></span>
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
        <div className="flex w-[155px] shrink-0 flex-col gap-1.5 border-r ls-border p-1.5 overflow-y-auto">
          {/* Config */}
          <div className="rounded border ls-border ls-bg-panel2 p-2 space-y-1.5">
            <div className="text-xs font-bold uppercase tracking-wider ls-text-muted">Configuración</div>
            <div>
              <div className="mb-0.5 text-xs uppercase ls-text-muted">Ojo</div>
              <ToggleSwitch value={eye} onChange={(v) => { setEye(v as "OD" | "OI"); regenerate(); }} options={[
                { value: "OD", label: "OD", color: "bg-red-600 ls-text" },
                { value: "OI", label: "OI", color: "bg-blue-600 ls-text" },
              ]} />
            </div>
            <div>
              <div className="mb-0.5 text-xs uppercase ls-text-muted">Scan</div>
              <ToggleSwitch value={scanMode} onChange={(v) => setScanMode(v as ScanMode)} options={[
                { value: "disc", label: "Disco" },
                { value: "macula", label: "Mácula" },
              ]} />
            </div>

            {!hasCaseLoaded && (
              <div>
                <div className="mb-0.5 text-xs uppercase ls-text-muted">Patología</div>
                <div className="grid grid-cols-2 gap-0.5">
                  {(["normal", "glaucoma", "edema", "drusen", "epiretinal", "amd-dry", "amd-wet"] as Pathology[]).map((p) => {
                    const labels: Record<Pathology, string> = { normal: "Normal", glaucoma: "Glauc", edema: "Edema", drusen: "Drusen", epiretinal: "ERM", "amd-dry": "DMAE-s", "amd-wet": "DMAE-h" };
                    return <button key={p} onClick={() => { setPathology(p); regenerate(); }}
                      className={cn("rounded border py-0.5 text-xs font-bold transition",
                        pathology === p ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "ls-border ls-text-muted hover:ls-text-muted")}>{labels[p]}</button>;
                  })}
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

            <button onClick={regenerate} className="flex w-full items-center justify-center gap-1 rounded border ls-border py-1 text-xs ls-text-muted hover:ls-bg-input">
              <RefreshCw className="h-2.5 w-2.5" /> Regenerar
            </button>
          </div>

          {/* RNFL Quadrants */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">RNFL Cuadrantes</div>
            {(["S", "N", "I", "T"] as const).map((q) => {
              const avg = clockAvg(q === "S" ? 45 : q === "N" ? 135 : q === "I" ? 225 : 315, q === "S" ? 135 : q === "N" ? 225 : q === "I" ? 315 : 405 > 360 ? 45 : 405);
              const norm = RNFL_QUADRANTS[q];
              return (
                <div key={q} className="flex items-center justify-between py-px">
                  <span className="text-xs font-bold ls-text-muted w-4">{q}</span>
                  <div className="h-2.5 flex-1 mx-1 rounded-sm" style={{ backgroundColor: normativeColor(avg, norm), opacity: 0.4 }} />
                  <span className="text-xs font-mono font-bold" style={{ color: normativeColor(avg, norm) }}>{avg}</span>
                </div>
              );
            })}
            <div className="mt-1 pt-1 border-t ls-border flex justify-between">
              <span className="text-xs font-bold ls-text-muted">Global</span>
              <span className="text-xs font-mono font-bold ls-text2">{globalAvg} µm</span>
            </div>
          </div>

          {/* Clock Hours */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Horas del Reloj</div>
            <div className="grid grid-cols-4 gap-px">
              {[12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((hr) => {
                const avg = clockAvg((hr - 1) * 30, hr * 30);
                const norm = RNFL_CLOCK_HOURS[hr];
                return (
                  <div key={hr} className="flex flex-col items-center rounded p-0.5" style={{ backgroundColor: normativeColor(avg, norm) + "22" }}>
                    <span className="text-xs ls-text-muted">{hr}h</span>
                    <span className="text-xs font-mono font-bold" style={{ color: normativeColor(avg, norm) }}>{avg}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* GCL+IPL */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">GCL+IPL</div>
            {Object.entries(gclData).map(([sec, val]) => {
              const norm = GCL_IPL_SECTORS[sec];
              return (
                <div key={sec} className="flex items-center justify-between py-px">
                  <span className="text-xs ls-text-muted w-5">{sec}</span>
                  <div className="h-2 flex-1 mx-1 rounded-sm" style={{ backgroundColor: norm ? normativeColor(val, norm) : "#555", opacity: 0.4 }} />
                  <span className="text-xs font-mono font-bold" style={{ color: norm ? normativeColor(val, norm) : "#aaa" }}>{val}</span>
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
      <div className="flex h-5 shrink-0 items-center justify-between ls-bg-panel2 px-3 text-xs ls-text-muted">
        <span>{eye} | {scanMode === "disc" ? "Optic Disc" : "Macula"} | {pathology}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs">
            <span className="inline-block h-1.5 w-3 rounded-sm bg-emerald-500/60" /> ≥p5
            <span className="ml-1 inline-block h-1.5 w-3 rounded-sm bg-amber-500/60" /> p1-p5
            <span className="ml-1 inline-block h-1.5 w-3 rounded-sm bg-red-500/60" /> &lt;p1
          </span>
        </div>
      </div>
    </div>
  );
}
