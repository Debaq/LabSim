import type { KeratometricIndices } from "@/lib/corneal-topography-synthetic";
import { cn } from "@/lib/utils";

interface Props {
  indices: KeratometricIndices;
}

function kColor(val: number): string {
  if (val < 41) return "text-blue-400";
  if (val < 43) return "text-cyan-400";
  if (val < 45) return "text-emerald-400";
  if (val < 47) return "text-amber-400";
  if (val < 50) return "text-orange-400";
  return "text-red-400";
}

function cctColor(val: number): string {
  if (val >= 540) return "text-emerald-400";
  if (val >= 500) return "text-amber-400";
  if (val >= 470) return "text-orange-400";
  return "text-red-400";
}

export function KeratometryPanel({ indices }: Props) {
  return (
    <div className="space-y-1.5">
      {/* SimK */}
      <div className="rounded border ls-border ls-bg-panel2 p-2">
        <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">SimK</div>
        <div className="space-y-0.5">
          <Row label="K1 (flat)" value={`${indices.k1} D`} sub={`@ ${indices.k1Axis}°`} color={kColor(indices.k1)} />
          <Row label="K2 (steep)" value={`${indices.k2} D`} sub={`@ ${indices.k2Axis}°`} color={kColor(indices.k2)} />
          <Row label="Kavg" value={`${indices.kAvg} D`} color={kColor(indices.kAvg)} />
          <Row label="Kmax" value={`${indices.kMax} D`} color={kColor(indices.kMax)} />
          <div className="border-t ls-border my-1" />
          <Row label="Cyl" value={`${indices.cylD} D`} color={indices.cylD > 2 ? "text-amber-400" : "ls-text2"} />
        </div>
      </div>

      {/* Indices */}
      <div className="rounded border ls-border ls-bg-panel2 p-2">
        <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Índices</div>
        <div className="space-y-0.5">
          <Row label="ISA" value={indices.isa.toFixed(2)} color={indices.isa > 1.5 ? "text-red-400" : indices.isa > 0.7 ? "text-amber-400" : "ls-text2"} />
          <Row label="IHD" value={indices.ihd.toFixed(2)} color={indices.ihd > 1.0 ? "text-red-400" : indices.ihd > 0.5 ? "text-amber-400" : "ls-text2"} />
        </div>
      </div>

      {/* Pachymetry */}
      <div className="rounded border ls-border ls-bg-panel2 p-2">
        <div className="mb-1 text-xs font-bold uppercase tracking-wider ls-text-muted">Paquimetría</div>
        <div className="space-y-0.5">
          <Row label="CCT" value={`${indices.cct} µm`} color={cctColor(indices.cct)} />
          <Row label="TCT" value={`${indices.tct} µm`} color={cctColor(indices.tct)} />
          <Row label="TCT pos" value={`(${indices.tctX}, ${indices.tctY})`} sub="mm" color="ls-text-muted" />
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="flex items-center justify-between py-px">
      <span className="text-xs ls-text-muted">{label}</span>
      <span className={cn("text-xs font-mono font-bold", color)}>
        {value}
        {sub && <span className="ml-0.5 text-xs font-normal ls-text-muted">{sub}</span>}
      </span>
    </div>
  );
}
