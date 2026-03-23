import { useState, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Send, Smile, Mic, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (text: string) => void;
  onSendVoice?: (text: string, durationSecs: number) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onSendVoice,
  placeholder = "Escribe un mensaje...",
  disabled = false,
}: ChatInputProps) {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recordStart, setRecordStart] = useState(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const startRecording = useCallback(async () => {
    if (disabled) return;
    try {
      await invoke("speech_start_recording");
      setRecording(true);
      setRecordStart(Date.now());
    } catch { /* micrófono no disponible */ }
  }, [disabled]);

  const stopRecording = useCallback(async () => {
    if (!recording) return;
    const durationSecs = Math.round((Date.now() - recordStart) / 1000);
    try {
      await invoke("speech_stop_recording");
      setRecording(false);
      setTranscribing(true);

      const transcript = await invoke<string>("speech_transcribe", { language: "es" });
      setTranscribing(false);

      if (transcript && transcript.trim().length > 0) {
        if (onSendVoice) {
          onSendVoice(transcript.trim(), Math.max(1, durationSecs));
        } else {
          onSend(transcript.trim());
        }
      }
    } catch {
      setRecording(false);
      setTranscribing(false);
    }
  }, [recording, recordStart, onSend, onSendVoice]);

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t ls-border ls-bg-panel/80 px-3 py-2"
    >
      <button
        type="button"
        className="shrink-0 rounded-full p-2 ls-text-muted transition hover:ls-bg-input hover:ls-text2"
      >
        <Smile className="h-5 w-5" />
      </button>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={recording ? "Grabando..." : transcribing ? "Transcribiendo..." : placeholder}
        disabled={disabled || recording || transcribing}
        rows={1}
        className="max-h-24 min-h-9 flex-1 resize-none rounded-2xl border ls-border ls-bg-input px-4 py-2 text-sm ls-text outline-none placeholder:ls-text-muted focus:border-emerald-500/30"
      />

      {/* Botón micrófono: mantener presionado para hablar */}
      <button
        type="button"
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={() => { if (recording) stopRecording(); }}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={disabled || transcribing}
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition cursor-pointer",
          recording
            ? "bg-red-500 text-white animate-pulse"
            : transcribing
              ? "bg-amber-500/20 text-amber-400"
              : "ls-bg-input ls-text-muted hover:text-emerald-400 hover:bg-emerald-500/10",
        )}
        title="Mantener presionado para enviar mensaje de voz"
      >
        {transcribing
          ? <Loader2 className="h-4 w-4 animate-spin" />
          : <Mic className="h-4 w-4" />
        }
      </button>

      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 ls-text transition hover:bg-emerald-500 disabled:opacity-30"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}
