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
}

export function TalkbackPanel({ level, onLevelChange, onCommand }: TalkbackPanelProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border ls-border ls-bg/30 p-2">
      <span className="text-[8px] font-bold uppercase tracking-[0.15em] ls-text-muted">Talkback</span>

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
            className="rounded border ls-border ls-bg-input px-1.5 py-1 text-[7px] ls-text-muted transition hover:ls-bg-input hover:ls-text2"
          >
            {cmd}
          </button>
        ))}
      </div>
    </div>
  );
}
