import { cn } from "@/lib/utils";
import type { ReliabilityIndices } from "@/lib/perimetry-config";

interface ReliabilityPanelProps {
  indices: ReliabilityIndices;
}

function Stat({ label, num, den, warnThreshold }: { label: string; num: number; den: number; warnThreshold: number }) {
  const pct = den > 0 ? Math.round((num / den) * 100) : 0;
  const warn = pct > warnThreshold;
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs ls-text-muted">{label}</span>
      <span className={cn("font-mono text-xs font-bold", warn ? "text-red-400/80" : "text-emerald-400/70")}>
        {num}/{den} <span className="ls-text-muted">({pct}%)</span>
      </span>
    </div>
  );
}

export function ReliabilityPanel({ indices }: ReliabilityPanelProps) {
  return (
    <div className="rounded border ls-border ls-bg-panel2 p-2">
      <div className="mb-1.5 text-xs font-bold uppercase tracking-wider ls-text-muted">
        Confiabilidad
      </div>
      <div className="space-y-1">
        <Stat label="Pérd. fijación" num={indices.fixationLosses} den={indices.fixationLossesTotal} warnThreshold={20} />
        <Stat label="Falsos +" num={indices.falsePositives} den={indices.falsePositivesTotal} warnThreshold={15} />
        <Stat label="Falsos −" num={indices.falseNegatives} den={indices.falseNegativesTotal} warnThreshold={33} />
      </div>
    </div>
  );
}
