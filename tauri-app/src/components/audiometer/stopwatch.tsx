import { useState, useRef, useCallback } from "react";
import { Play, Square, RotateCcw } from "lucide-react";

export function Stopwatch() {
  const [time, setTime] = useState(0);
  const [running, setRunning] = useState(false);
  const interval = useRef<ReturnType<typeof setInterval>>(undefined);

  const start = useCallback(() => {
    if (running) return;
    setRunning(true);
    interval.current = setInterval(() => setTime((t) => t + 1), 1000);
  }, [running]);

  const stop = useCallback(() => {
    setRunning(false);
    if (interval.current) clearInterval(interval.current);
  }, []);

  const reset = useCallback(() => {
    stop();
    setTime(0);
  }, [stop]);

  const mins = Math.floor(time / 60);
  const secs = time % 60;

  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border ls-border ls-bg/30 p-2">
      <span className="text-[8px] font-bold uppercase tracking-[0.15em] ls-text-muted">Cronómetro</span>

      <div className="rounded bg-black/60 px-2 py-0.5 font-mono text-lg font-bold tabular-nums text-green-400 [text-shadow:0_0_6px_rgb(74_222_128/0.4)]">
        {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
      </div>

      <div className="flex gap-1">
        <button
          onClick={start}
          disabled={running}
          className="rounded border ls-border p-1 text-emerald-400/60 transition hover:ls-bg-input disabled:opacity-30"
        >
          <Play className="h-3 w-3" />
        </button>
        <button
          onClick={stop}
          disabled={!running}
          className="rounded border ls-border p-1 text-amber-400/60 transition hover:ls-bg-input disabled:opacity-30"
        >
          <Square className="h-3 w-3" />
        </button>
        <button
          onClick={reset}
          className="rounded border ls-border p-1 ls-text-muted transition hover:ls-bg-input"
        >
          <RotateCcw className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
