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
    <div className="flex flex-col items-center gap-2 rounded-lg border border-white/5 bg-slate-800/30 p-2">
      <span className="text-[8px] font-bold uppercase tracking-[0.15em] text-white/25">Talkback</span>

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
            className="rounded border border-white/5 bg-white/[0.03] px-1.5 py-1 text-[7px] text-white/30 transition hover:bg-white/5 hover:text-white/50"
          >
            {cmd}
          </button>
        ))}
      </div>
    </div>
  );
}
