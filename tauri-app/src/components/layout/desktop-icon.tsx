import { useState } from "react";
import type { LucideIcon } from "lucide-react";

interface DesktopIconProps {
  label: string;
  icon: LucideIcon;
  color: string;
  onOpen: () => void;
}

export function DesktopIcon({ label, icon: Icon, color, onOpen }: DesktopIconProps) {
  const [selected, setSelected] = useState(false);

  return (
    <button
      className={`flex w-20 flex-col items-center gap-1.5 rounded-lg p-2 text-center transition select-none ${
        selected ? "ls-bg-input" : "hover:bg-white/8"
      }`}
      onClick={() => setSelected(true)}
      onDoubleClick={onOpen}
      onBlur={() => setSelected(false)}
    >
      <div
        className={`flex h-12 w-12 items-center justify-center rounded-xl ls-bg-input ${color}`}
      >
        <Icon className="h-6 w-6" />
      </div>
      <span className="text-[11px] leading-tight font-medium drop-shadow-md"
        style={{ color: "var(--ls-desktop-text)" }}>
        {label}
      </span>
    </button>
  );
}
