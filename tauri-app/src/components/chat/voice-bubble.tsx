/**
 * Burbuja de mensaje de voz estilo WhatsApp.
 * Muestra barras de waveform, botón play, duración.
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Play, Pause } from "lucide-react";
import { cn } from "@/lib/utils";

interface VoiceBubbleProps {
  text: string;
  voiceId?: string;
  durationSecs: number;
  isUser: boolean;
}

/** Genera barras de waveform pseudo-aleatorias pero consistentes para un texto */
function generateBars(text: string, count: number): number[] {
  let seed = 0;
  for (let i = 0; i < text.length; i++) seed = (seed * 31 + text.charCodeAt(i)) & 0xffff;
  const bars: number[] = [];
  for (let i = 0; i < count; i++) {
    seed = (seed * 1664525 + 1013904223) & 0xffffffff;
    const h = 0.15 + ((seed >>> 0) / 0xffffffff) * 0.85;
    bars.push(h);
  }
  return bars;
}

function formatDuration(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function VoiceBubble({ text, voiceId, durationSecs, isUser }: VoiceBubbleProps) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const progressTimer = useRef<ReturnType<typeof setInterval>>(undefined);
  const bars = useMemo(() => generateBars(text, 32), [text]);

  // Limpiar timer al desmontar
  useEffect(() => () => { if (progressTimer.current) clearInterval(progressTimer.current); }, []);

  const handlePlay = useCallback(async () => {
    if (playing) return;
    setPlaying(true);
    setProgress(0);

    // Animar progreso
    const startTime = Date.now();
    const totalMs = durationSecs * 1000;
    progressTimer.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const p = Math.min(1, elapsed / totalMs);
      setProgress(p);
      if (p >= 1) {
        clearInterval(progressTimer.current);
        setPlaying(false);
      }
    }, 50);

    if (voiceId) {
      try {
        await invoke("tts_speak", { text, voiceId });
      } catch { /* TTS no disponible */ }
    }
  }, [playing, text, voiceId, durationSecs]);

  const handlePause = useCallback(() => {
    if (progressTimer.current) clearInterval(progressTimer.current);
    setPlaying(false);
    try { invoke("stop_playback"); } catch { /* */ }
  }, []);

  const playedBars = Math.floor(progress * bars.length);

  return (
    <div className="flex items-center gap-2.5 min-w-[200px]">
      {/* Play/Pause */}
      <button
        onClick={playing ? handlePause : handlePlay}
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition cursor-pointer",
          isUser
            ? "bg-white/20 text-white hover:bg-white/30"
            : "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30",
        )}
      >
        {playing
          ? <Pause className="h-3.5 w-3.5" />
          : <Play className="h-3.5 w-3.5 ml-0.5" />
        }
      </button>

      {/* Waveform */}
      <div className="flex flex-1 items-center gap-[2px] h-6">
        {bars.map((h, i) => (
          <div
            key={i}
            className={cn(
              "w-[3px] rounded-full transition-colors duration-100",
              i < playedBars
                ? isUser ? "bg-white/80" : "bg-emerald-400"
                : isUser ? "bg-white/25" : "bg-white/20",
            )}
            style={{ height: `${h * 100}%` }}
          />
        ))}
      </div>

      {/* Duración */}
      <span className={cn(
        "text-[10px] shrink-0 tabular-nums",
        isUser ? "text-white/60" : "ls-text-muted",
      )}>
        {playing ? formatDuration(progress * durationSecs) : formatDuration(durationSecs)}
      </span>
    </div>
  );
}
