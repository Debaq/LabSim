import { useState, useRef, useCallback, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { cn } from "@/lib/utils";
import { Mic, MicOff, Volume2, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import {
  INSTRUCTIONS, CATEGORY_LABELS, getInstructionsByCategory,
  matchVoiceToInstruction,
  type Instruction, type InstructionCategory,
} from "@/lib/audiometer-instructions";

// ─── Subtítulos estilo película ─────────────────────────

function Subtitles({ text, fading }: { text: string | null; fading: boolean }) {
  if (!text) return null;
  return (
    <div className={cn(
      "px-3 py-1 text-center transition-opacity duration-700",
      fading ? "opacity-0" : "opacity-100",
    )}>
      <span className="bg-black/60 px-3 py-1 rounded text-[11px] text-white/90 leading-relaxed">
        {text}
      </span>
    </div>
  );
}

// ─── Props ──────────────────────────────────────────────

interface TalkbackPanelProps {
  level: number;
  onLevelChange: (level: number) => void;
  onCommand: (command: string) => void;
  isActive: boolean;
  onToggle: () => void;
  activeInstruction: string | null;
  onInstruction: (instruction: Instruction) => void;
}

export function TalkbackPanel({
  level, onLevelChange, onCommand,
  isActive, onToggle,
  activeInstruction, onInstruction,
}: TalkbackPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // Subtítulos
  const [subtitle, setSubtitle] = useState<string | null>(null);
  const [subtitleFading, setSubtitleFading] = useState(false);
  const subtitleTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const grouped = getInstructionsByCategory();

  const showSubtitle = useCallback((text: string, durationMs = 5000) => {
    setSubtitle(text);
    setSubtitleFading(false);
    if (subtitleTimer.current) clearTimeout(subtitleTimer.current);
    // Empezar fade out antes de desaparecer
    subtitleTimer.current = setTimeout(() => {
      setSubtitleFading(true);
      subtitleTimer.current = setTimeout(() => setSubtitle(null), 700);
    }, durationMs);
  }, []);

  // Limpiar timers al desmontar
  useEffect(() => () => { if (subtitleTimer.current) clearTimeout(subtitleTimer.current); }, []);

  const handleInstruction = useCallback((inst: Instruction) => {
    onInstruction(inst);
    showSubtitle(inst.speech);
    onCommand(inst.speech);
  }, [onInstruction, onCommand, showSubtitle]);

  // ─── Voz: mantener presionado para hablar ─────────
  const startRecording = useCallback(async () => {
    if (!isActive) return;
    setVoiceError(null);
    try {
      await invoke("speech_start_recording");
      setRecording(true);
      showSubtitle("...", 30000); // Puntos suspensivos mientras graba
    } catch {
      setVoiceError("Micrófono no disponible");
    }
  }, [isActive, showSubtitle]);

  const stopRecording = useCallback(async () => {
    if (!recording) return;
    try {
      await invoke("speech_stop_recording");
      setRecording(false);
      setTranscribing(true);
      showSubtitle("...", 30000);

      const transcript = await invoke<string>("speech_transcribe", { language: "es" });
      setTranscribing(false);

      if (!transcript || transcript.trim().length === 0) {
        showSubtitle("(silencio)", 2000);
        return;
      }

      // Mostrar lo que dijo como subtítulo
      showSubtitle(transcript, 4000);

      // Matchear con instrucción
      const matched = matchVoiceToInstruction(transcript);
      if (matched) {
        onInstruction(matched);
        onCommand(matched.speech);
        // Después de un momento, mostrar la instrucción reconocida
        setTimeout(() => showSubtitle(`→ ${matched.label}`, 3000), 1500);
      } else {
        setTimeout(() => showSubtitle("(el paciente no entendió)", 3000), 1500);
      }
    } catch {
      setRecording(false);
      setTranscribing(false);
      showSubtitle("(error de micrófono)", 2000);
    }
  }, [recording, onInstruction, onCommand, showSubtitle]);

  return (
    <div className={cn(
      "flex flex-col gap-1 rounded-lg border p-1.5",
      isActive ? "border-emerald-500/40 bg-emerald-900/10" : "ls-border ls-bg/30"
    )}>
      {/* Header compacto */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <button
            onClick={onToggle}
            className={cn(
              "rounded p-1 transition cursor-pointer",
              isActive
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                : "ls-bg-input ls-text-muted border ls-border hover:ls-text2"
            )}
          >
            {isActive ? <Mic className="w-3 h-3" /> : <MicOff className="w-3 h-3" />}
          </button>
          <span className="text-[9px] font-bold uppercase tracking-[0.15em] ls-text-muted">Talkback</span>
          {activeInstruction && (
            <span className="rounded bg-amber-500/15 border border-amber-500/30 px-1.5 py-0.5 text-[8px] font-medium text-amber-400">
              {INSTRUCTIONS.find((i) => i.id === activeInstruction)?.label}
            </span>
          )}

          {/* Botón de voz inline */}
          {isActive && (
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={() => { if (recording) stopRecording(); }}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={transcribing}
              className={cn(
                "flex items-center gap-1 rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider transition select-none cursor-pointer ml-1",
                recording
                  ? "border-red-500 bg-red-500/20 text-red-300 animate-pulse"
                  : transcribing
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
              )}
            >
              {recording ? (
                <><Mic className="h-3 w-3" /> Grabando</>
              ) : transcribing ? (
                <><Loader2 className="h-3 w-3 animate-spin" /> ...</>
              ) : (
                <><Mic className="h-3 w-3" /> Hablar</>
              )}
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <Volume2 className="h-2.5 w-2.5 ls-text-muted" />
          <input type="range" min={0} max={20} value={level} onChange={(e) => onLevelChange(+e.target.value)}
            className="h-1 w-12 accent-emerald-500" />
          <button onClick={() => setExpanded(!expanded)} className="ml-0.5 ls-text-muted hover:ls-text2 cursor-pointer">
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Subtítulos — estilo película */}
      <Subtitles text={subtitle} fading={subtitleFading} />

      {/* Error de voz */}
      {voiceError && (
        <span className="text-[9px] text-red-400 text-center">{voiceError}</span>
      )}

      {/* Botones de instrucciones expandidos */}
      {expanded && (
        <div className="space-y-1.5 pt-0.5">
          {(Object.keys(grouped) as InstructionCategory[]).map((cat) => (
            <div key={cat}>
              <div className="mb-0.5 text-[8px] font-bold uppercase tracking-wider ls-text-muted">
                {CATEGORY_LABELS[cat]}
              </div>
              <div className="flex flex-wrap gap-0.5">
                {grouped[cat].map((inst) => (
                  <button
                    key={inst.id}
                    onClick={() => handleInstruction(inst)}
                    disabled={!isActive}
                    className={cn(
                      "rounded border px-1.5 py-0.5 text-[9px] transition cursor-pointer",
                      activeInstruction === inst.id
                        ? "border-amber-500/40 bg-amber-500/20 text-amber-300 font-bold"
                        : isActive
                          ? "ls-border ls-bg-input ls-text-muted hover:ls-text2 hover:border-amber-500/20"
                          : "ls-border ls-bg-input ls-text-muted opacity-40 cursor-not-allowed"
                    )}
                    title={inst.speech}
                  >
                    {inst.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Instrucciones rápidas colapsadas */}
      {!expanded && (
        <div className="flex flex-wrap gap-0.5">
          {INSTRUCTIONS.filter((i) => i.category === "preparacion").map((inst) => (
            <button
              key={inst.id}
              onClick={() => handleInstruction(inst)}
              disabled={!isActive}
              className={cn(
                "rounded border px-1.5 py-0.5 text-[9px] transition cursor-pointer",
                activeInstruction === inst.id
                  ? "border-amber-500/40 bg-amber-500/20 text-amber-300 font-bold"
                  : isActive
                    ? "ls-border ls-bg-input ls-text-muted hover:ls-text2"
                    : "ls-border ls-bg-input ls-text-muted opacity-40 cursor-not-allowed"
              )}
            >
              {inst.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
