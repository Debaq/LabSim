import { useState, useEffect, useMemo } from "react";
import { TopographyMap } from "@/components/corneal-topography/topography-map";
import { KeratometryPanel } from "@/components/corneal-topography/keratometry-panel";
import { ColorScale } from "@/components/corneal-topography/color-scale";
import { ToggleSwitch } from "@/components/audiometer/toggle-switch";
import {
  generateCurvatureMap,
  generatePachymetryMap,
  computeKeratometricIndices,
  type CornealPathology,
  type MapType,
} from "@/lib/corneal-topography-synthetic";
import { usePatientStore } from "@/stores/patient-store";
import { cn } from "@/lib/utils";
import { RefreshCw, Link2, Link2Off } from "lucide-react";

const MAP_SIZE = 220;

const PATHO_LABELS: Record<CornealPathology, string> = {
  normal: "Normal",
  keratoconus: "Queratocono",
  pellucid: "Pelúcida",
  "wtr-astigmatism": "Ast. Regla",
  "atr-astigmatism": "Ast. c/Regla",
  "oblique-astigmatism": "Ast. Oblicuo",
  "post-lasik": "Post-LASIK",
};

export function CornealTopographyWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [mapType, setMapType] = useState<MapType>("axial");
  const [pathology, setPathology] = useState<CornealPathology>("normal");
  const [seed, setSeed] = useState(42);
  const [qualityOverride, setQualityOverride] = useState<number | null>(null);

  // Read case config from patient store
  const topoConfig = usePatientStore((s) => s.data.cornealTopography);
  const patientId = usePatientStore((s) => s.currentPatientId);
  const hasCaseLoaded = patientId !== null && Object.keys(topoConfig).length > 0;

  // Sync from case when loaded
  useEffect(() => {
    if (!hasCaseLoaded) return;
    const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
    const cfg = (topoConfig as Record<string, Record<string, unknown>>)[eyeKey];
    if (!cfg) return;

    const patho = cfg.patologia as CornealPathology | undefined;
    if (patho && patho !== pathology) setPathology(patho);

    const mapa = cfg.mapaPreferido as MapType | undefined;
    if (mapa) setMapType(mapa);

    const q = cfg.calidadCaptura as number | undefined;
    setQualityOverride(q ?? null);

    const seedBase = patientId ? patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) : 42;
    setSeed(seedBase + (eye === "OI" ? 1000 : 0));
  }, [hasCaseLoaded, eye, topoConfig, patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const regenerate = () => setSeed(Math.floor(Math.random() * 10000));

  const quality = qualityOverride ?? (7 + Math.floor(seed % 3));

  // Compute keratometric indices
  const indices = useMemo(() => {
    const curvMap = generateCurvatureMap(MAP_SIZE, seed, pathology, "axial");
    const pachMap = generatePachymetryMap(MAP_SIZE, seed, pathology);
    return computeKeratometricIndices(curvMap, pachMap, MAP_SIZE, seed);
  }, [seed, pathology]);

  return (
    <div className="flex h-full flex-col ls-bg">
      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">TOPÓGRAFO CORNEAL</span>
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
          <span className={cn("font-bold", eye === "OD" ? "text-red-400/60" : "text-blue-400/60")}>{eye}</span>
          <span>|</span>
          <span>{mapType === "axial" ? "Axial" : mapType === "tangential" ? "Tangencial" : mapType === "elevation" ? "Elevación" : "Paquimetría"}</span>
          <span>|</span>
          <span className={cn(quality >= 7 ? "text-emerald-400/60" : "text-amber-400/60")}>Q:{quality}/10</span>
          <span>|</span>
          <span>{PATHO_LABELS[pathology]}</span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT panel — Controls + Keratometry */}
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
              <div className="mb-0.5 text-xs uppercase ls-text-muted">Mapa</div>
              <div className="grid grid-cols-2 gap-0.5">
                {(["axial", "tangential", "elevation", "pachymetry"] as MapType[]).map((m) => {
                  const labels: Record<MapType, string> = { axial: "Axial", tangential: "Tang.", elevation: "Elev.", pachymetry: "Paqui." };
                  return (
                    <button key={m} onClick={() => setMapType(m)}
                      className={cn("rounded border py-0.5 text-xs font-bold transition",
                        mapType === m ? "border-teal-500/40 bg-teal-500/20 text-teal-300" : "ls-border ls-text-muted hover:ls-text-muted")}>
                      {labels[m]}
                    </button>
                  );
                })}
              </div>
            </div>

            {!hasCaseLoaded && (
              <div>
                <div className="mb-0.5 text-xs uppercase ls-text-muted">Patología</div>
                <div className="grid grid-cols-2 gap-0.5">
                  {(Object.keys(PATHO_LABELS) as CornealPathology[]).map((p) => (
                    <button key={p} onClick={() => { setPathology(p); regenerate(); }}
                      className={cn("rounded border py-0.5 text-[10px] font-bold transition",
                        pathology === p ? "border-amber-500/40 bg-amber-500/20 text-amber-300" : "ls-border ls-text-muted hover:ls-text-muted")}>
                      {PATHO_LABELS[p]}
                    </button>
                  ))}
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

          {/* Keratometric indices */}
          <KeratometryPanel indices={indices} />
        </div>

        {/* CENTER: Main map view */}
        <div className="flex flex-1 flex-col items-center justify-center gap-2 p-3 min-w-0">
          <div className="flex items-center gap-3">
            <TopographyMap seed={seed} pathology={pathology} mapType={mapType} size={MAP_SIZE} />
            <ColorScale mapType={mapType} />
          </div>

          {/* Quick summary below map */}
          <div className="flex items-center gap-4 text-xs ls-text-muted">
            <span>K1: <span className="font-mono font-bold ls-text2">{indices.k1}D</span> @{indices.k1Axis}°</span>
            <span>K2: <span className="font-mono font-bold ls-text2">{indices.k2}D</span> @{indices.k2Axis}°</span>
            <span>Cyl: <span className={cn("font-mono font-bold", indices.cylD > 2 ? "text-amber-400" : "ls-text2")}>{indices.cylD}D</span></span>
            <span>CCT: <span className="font-mono font-bold ls-text2">{indices.cct}µm</span></span>
          </div>
        </div>

        {/* RIGHT panel — Dual map (optional second view) */}
        <div className="flex w-[155px] shrink-0 flex-col gap-1.5 border-l ls-border p-1.5 overflow-y-auto">
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Vista Comparativa</div>
            <div className="flex justify-center">
              <TopographyMap
                seed={seed}
                pathology={pathology}
                mapType={mapType === "axial" ? "tangential" : mapType === "tangential" ? "axial" : mapType === "elevation" ? "pachymetry" : "elevation"}
                size={130}
              />
            </div>
            <div className="mt-1 text-center text-[10px] ls-text-muted">
              {mapType === "axial" ? "Tangencial" : mapType === "tangential" ? "Axial" : mapType === "elevation" ? "Paquimetría" : "Elevación"}
            </div>
          </div>

          {/* Diagnostic suggestion */}
          <div className="rounded border ls-border ls-bg-panel2 p-2">
            <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Sugerencia</div>
            <DiagnosticHint pathology={pathology} indices={indices} />
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex h-5 shrink-0 items-center justify-between ls-bg-panel2 px-3 text-xs ls-text-muted">
        <span>{eye} | {PATHO_LABELS[pathology]} | Kmax {indices.kMax}D</span>
        <span>TCT {indices.tct}µm ({indices.tctX > 0 ? "+" : ""}{indices.tctX}, {indices.tctY > 0 ? "+" : ""}{indices.tctY})mm</span>
      </div>
    </div>
  );
}

function DiagnosticHint({ pathology, indices }: { pathology: CornealPathology; indices: { kMax: number; cylD: number; tct: number; isa: number } }) {
  const flags: string[] = [];

  if (indices.kMax > 47.2) flags.push("Kmax elevado");
  if (indices.cylD > 3) flags.push("Alto astigmatismo");
  if (indices.tct < 490) flags.push("Paquimetría fina");
  if (indices.isa > 1.0) flags.push("Asimetría elevada");

  if (flags.length === 0) {
    return <p className="text-xs text-emerald-400/70">Córnea dentro de parámetros normales</p>;
  }

  return (
    <div className="space-y-0.5">
      {flags.map((f) => (
        <p key={f} className="text-xs text-amber-400/80">⚠ {f}</p>
      ))}
      {pathology === "keratoconus" && (
        <p className="text-xs text-red-400/70 mt-1">Compatible con ectasia corneal</p>
      )}
    </div>
  );
}
