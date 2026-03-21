import { RotaryKnob } from "./rotary-knob";
import { cn } from "@/lib/utils";
import { Mic, MicOff } from "lucide-react";

const COMMANDS = [
  "Coloca los fonos",
  "Coloca el vibrador",
  "Levanta tu mano",
  "Cambie de volumen",
  "Pa pa pa",
];

interface TalkbackPanelProps {
  level: number;
  onLevelChange: (level: number) => void;
  onCommand: (command: string) => void;
  isActive: boolean;
  onToggle: () => void;
}

export function TalkbackPanel({ level, onLevelChange, onCommand, isActive, onToggle }: TalkbackPanelProps) {
  return (
    <div className={cn(
      "flex flex-col items-center gap-2 rounded-lg border p-2",
      isActive ? "border-emerald-500/40 bg-emerald-900/10" : "ls-border ls-bg/30"
    )}>
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold uppercase tracking-[0.15em] ls-text-muted">Talkback</span>
        <button
          onClick={onToggle}
          className={cn(
            "rounded p-1 transition",
            isActive
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
              : "ls-bg-input ls-text-muted border ls-border hover:ls-text2"
          )}
          title={isActive ? "Desactivar talkback" : "Activar talkback"}
        >
          {isActive ? <Mic className="w-3.5 h-3.5" /> : <MicOff className="w-3.5 h-3.5" />}
        </button>
      </div>

      <RotaryKnob
        value={level}
        min={0}
        max={20}
        step={1}
        onChange={onLevelChange}
        size="sm"
        displayValue={`${level}`}
      />

      <div className="flex flex-wrap justify-center gap-1">
        {COMMANDS.map((cmd) => (
          <button
            key={cmd}
            onClick={() => onCommand(cmd)}
            disabled={!isActive}
            className={cn(
              "rounded border px-1.5 py-1 text-xs transition",
              isActive
                ? "ls-border ls-bg-input ls-text-muted hover:ls-text2"
                : "ls-border ls-bg-input ls-text-muted opacity-40 cursor-not-allowed"
            )}
          >
            {cmd}
          </button>
        ))}
      </div>
    </div>
  );
}
