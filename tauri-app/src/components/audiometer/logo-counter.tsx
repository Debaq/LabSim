import { cn } from "@/lib/utils";
import { Plus, Minus, RotateCcw } from "lucide-react";

interface LogoCounterProps {
  correct: number;
  total: number;
  onCorrect: () => void;
  onIncorrect: () => void;
  onReset: () => void;
}

export function LogoCounter({ correct, total, onCorrect, onIncorrect, onReset }: LogoCounterProps) {
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0;

  return (
    <div className="flex flex-col items-center gap-1.5 rounded-lg border ls-border ls-bg/30 p-2">
      <span className="text-[8px] font-bold uppercase tracking-[0.15em] ls-text-muted">
        Logoaudiometría
      </span>

      <div className="rounded bg-black/60 px-2 py-0.5 font-mono text-sm">
        <span className="font-bold text-green-400">{correct}</span>
        <span className="ls-text-muted">/</span>
        <span className="ls-text2">{total}</span>
        <span className="ls-text-muted"> : </span>
        <span className={cn(
          "font-bold",
          pct >= 80 ? "text-green-400" : pct >= 50 ? "text-amber-400" : "text-red-400",
        )}>
          {pct}%
        </span>
      </div>

      <div className="flex gap-1">
        <button
          onClick={onCorrect}
          className="flex h-7 w-7 items-center justify-center rounded border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 transition hover:bg-emerald-500/20"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={onIncorrect}
          className="flex h-7 w-7 items-center justify-center rounded border border-red-500/30 bg-red-500/10 text-red-400 transition hover:bg-red-500/20"
        >
          <Minus className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={onReset}
          className="flex h-7 w-7 items-center justify-center rounded border ls-border ls-text-muted transition hover:ls-bg-input"
        >
          <RotateCcw className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
