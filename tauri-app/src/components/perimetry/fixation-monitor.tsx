import { cn } from "@/lib/utils";
import { Eye } from "lucide-react";

interface FixationMonitorProps {
  isFixating: boolean;
  fixationLosses: number;
  total: number;
}

export function FixationMonitor({ isFixating, fixationLosses, total }: FixationMonitorProps) {
  const pct = total > 0 ? Math.round((fixationLosses / total) * 100) : 0;
  const isGood = pct < 20;

  return (
    <div className="rounded border border-white/[0.06] bg-black/30 p-2">
      <div className="mb-1.5 text-[8px] font-bold uppercase tracking-wider text-white/25">
        Monitor de Fijación
      </div>

      {/* Eye indicator */}
      <div className="flex items-center justify-center gap-2 mb-2">
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-full border-2 transition",
          isFixating
            ? "border-emerald-500/50 bg-emerald-500/10"
            : "border-red-500/50 bg-red-500/10 animate-pulse",
        )}>
          <Eye className={cn("h-5 w-5", isFixating ? "text-emerald-400" : "text-red-400")} />
        </div>
        <div className="text-center">
          <div className={cn("text-xs font-bold", isFixating ? "text-emerald-400" : "text-red-400")}>
            {isFixating ? "FIJANDO" : "PÉRDIDA"}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex justify-between text-[9px]">
        <span className="text-white/30">Pérdidas:</span>
        <span className={cn("font-mono font-bold", isGood ? "text-emerald-400/70" : "text-red-400/70")}>
          {fixationLosses}/{total} ({pct}%)
        </span>
      </div>
    </div>
  );
}
