/**
 * Tomógrafo Scheimpflug LabSim — LabSim SA-1
 *
 * Simula un tomógrafo de cámara anterior con cámara Scheimpflug rotativa.
 * Muestra: corte de cámara anterior, mapas elevación anterior/posterior,
 * paquimetría punto a punto, índices de cámara anterior.
 */

import { useState, useMemo } from "react";
import { usePatientStore } from "@/stores/patient-store";
import { useLiveSessionStore } from "@/stores/live-session-store";
import { PatientBanner } from "@/components/ui/patient-banner";
import { CrossSectionView } from "@/components/scheimpflug/cross-section-view";
import { ACIndicesPanel } from "@/components/scheimpflug/ac-indices-panel";
import {
  generateCrossSection,
  generateElevationMaps,
  generatePachymetryMap,
  computeIndices,
} from "@/lib/scheimpflug-synthetic";
import type { ScheimpflugEyeConfig } from "@/modules/scheimpflug/schema";
import { renderMapToImage, type MapType } from "@/lib/corneal-topography-synthetic";
import { ColorScale } from "@/components/corneal-topography/color-scale";
import { useRef, useEffect } from "react";
import { RefreshCw, Link2, Link2Off } from "lucide-react";

type ViewTab = "scheimpflug" | "elev-ant" | "elev-post" | "pachymetry";
const MAP_SIZE = 128;

/** Renders a pre-generated Float32Array map onto a canvas */
function PreRenderedMap({ map, size, mapType }: { map: Float32Array; size: number; mapType: MapType }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageData = useMemo(() => renderMapToImage(map, size, mapType), [map, size, mapType]);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.putImageData(imageData, 0, 0);
  }, [imageData, size]);
  return <canvas ref={canvasRef} className="rounded" style={{ width: 220, height: 220, imageRendering: "pixelated" }} />;
}

export function ScheimpflugWindow() {
  const [eye, setEye] = useState<"OD" | "OI">("OD");
  const [viewTab, setViewTab] = useState<ViewTab>("scheimpflug");
  const [seed, setSeed] = useState(42);

  const config = usePatientStore((s) => s.data.modules.scheimpflug ?? {});
  const patientId = usePatientStore((s) => s.currentPatientId);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const hasCaseLoaded = patientId !== null && Object.keys(config).length > 0;

  const eyeKey = eye === "OD" ? "ojoDerecho" : "ojoIzquierdo";
  const eyeCfg: ScheimpflugEyeConfig = (config[eyeKey] as ScheimpflugEyeConfig) ?? {};

  // Sync seed from patient
  useMemo(() => {
    if (!patientId) return;
    const s = patientId.split("").reduce((a, c) => a + c.charCodeAt(0), 0) + (eye === "OI" ? 2000 : 0);
    setSeed(s);
  }, [patientId, eye]);

  const regenerate = () => {
    setSeed(Math.floor(Math.random() * 10000));
    addEvent({ type: "test_start", simulator: "scheimpflug", details: `Captura ${eye}` });
  };

  // Generate data
  const crossSection = useMemo(() => generateCrossSection(eyeCfg, seed), [eyeCfg, seed]);
  const elevMaps = useMemo(() => generateElevationMaps(eyeCfg, MAP_SIZE, seed), [eyeCfg, seed]);
  const pachMap = useMemo(() => generatePachymetryMap(eyeCfg, MAP_SIZE, seed), [eyeCfg, seed]);
  const indices = useMemo(() => computeIndices(eyeCfg, pachMap, MAP_SIZE, seed), [eyeCfg, pachMap, seed]);

  const TABS: { value: ViewTab; label: string }[] = [
    { value: "scheimpflug", label: "Corte" },
    { value: "elev-ant", label: "Elev. Ant." },
    { value: "elev-post", label: "Elev. Post." },
    { value: "pachymetry", label: "Paquimetría" },
  ];

  return (
    <div className="flex h-full flex-col ls-bg">
      <PatientBanner simulatorName="Tomógrafo Scheimpflug" />

      {/* Header */}
      <div className="flex h-7 shrink-0 items-center justify-between ls-bg-panel2 px-3">
        <span className="text-xs font-bold tracking-[0.2em] ls-text-muted">
          LABSIM <span className="font-normal ls-text-muted">SA-1 SCHEIMPFLUG</span>
        </span>
        <div className="flex items-center gap-2 text-xs ls-text-muted">
          {hasCaseLoaded ? (
            <span className="flex items-center gap-1 text-emerald-400/70"><Link2 className="h-3 w-3" /> Caso</span>
          ) : (
            <span className="flex items-center gap-1"><Link2Off className="h-3 w-3" /> Libre</span>
          )}
        </div>
      </div>

      {/* Controls bar */}
      <div className="flex items-center gap-2 border-b ls-border px-3 py-1.5">
        <div className="flex gap-0.5">
          <button onClick={() => setEye("OD")} className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${eye === "OD" ? "bg-red-500/20 text-red-400" : "ls-text-muted hover:ls-bg-input"}`}>OD</button>
          <button onClick={() => setEye("OI")} className={`rounded px-2.5 py-0.5 text-xs font-bold transition ${eye === "OI" ? "bg-blue-500/20 text-blue-400" : "ls-text-muted hover:ls-bg-input"}`}>OI</button>
        </div>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <div className="flex gap-0.5">
          {TABS.map((t) => (
            <button key={t.value} onClick={() => setViewTab(t.value)}
              className={`rounded px-2 py-0.5 text-[10px] transition ${viewTab === t.value ? "bg-teal-500/20 text-teal-400" : "ls-text-muted hover:ls-bg-input"}`}
            >{t.label}</button>
          ))}
        </div>
        <button onClick={regenerate} className="ml-auto rounded p-1 hover:ls-bg-input ls-text-muted" title="Nueva captura">
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Center: visualization */}
        <div className="flex-1 flex items-center justify-center p-3">
          {viewTab === "scheimpflug" && (
            <CrossSectionView data={crossSection} width={400} height={220} />
          )}
          {viewTab === "elev-ant" && (
            <div className="flex items-center gap-2">
              <PreRenderedMap map={elevMaps.anterior} size={MAP_SIZE} mapType="elevation" />
              <ColorScale mapType="elevation" />
            </div>
          )}
          {viewTab === "elev-post" && (
            <div className="flex items-center gap-2">
              <PreRenderedMap map={elevMaps.posterior} size={MAP_SIZE} mapType="elevation" />
              <ColorScale mapType="elevation" />
            </div>
          )}
          {viewTab === "pachymetry" && (
            <div className="flex items-center gap-2">
              <PreRenderedMap map={pachMap} size={MAP_SIZE} mapType="pachymetry" />
              <ColorScale mapType="pachymetry" />
            </div>
          )}
        </div>

        {/* Right: indices */}
        <div className="w-[170px] shrink-0 border-l ls-border overflow-auto">
          <ACIndicesPanel indices={indices} />
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t ls-border ls-bg-panel2 px-3 py-1 text-[9px] font-mono ls-text-muted">
        <span>{eye} | {(eyeCfg.cornealPathology ?? "normal").toUpperCase()}</span>
        <span>CCT: {indices.cct}µm | ACD: {indices.acd}mm | Densidad: {indices.lensDensity}%</span>
      </div>
    </div>
  );
}
