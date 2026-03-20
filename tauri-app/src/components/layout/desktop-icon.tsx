import { useState, useMemo } from "react";
import type { LucideIcon } from "lucide-react";

interface DesktopIconProps {
  label: string;
  icon: LucideIcon;
  color: string; // tailwind class like "text-blue-400"
  onOpen: () => void;
}

// Extract RGB from a CSS color string (hex or computed)
function parseColor(str: string): [number, number, number] | null {
  const m = str.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (m) return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
  const m2 = str.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (m2) return [parseInt(m2[1]), parseInt(m2[2]), parseInt(m2[3])];
  return null;
}

// Check if two colors are too similar (low contrast)
function hasConflict(iconColor: string, bgColor: string): boolean {
  const ic = parseColor(iconColor);
  const bg = parseColor(bgColor);
  if (!ic || !bg) return false;
  // Simple color distance
  const dist = Math.sqrt((ic[0] - bg[0]) ** 2 + (ic[1] - bg[1]) ** 2 + (ic[2] - bg[2]) ** 2);
  return dist < 120; // too close = conflict
}

export function DesktopIcon({ label, icon: Icon, color, onOpen }: DesktopIconProps) {
  const [selected, setSelected] = useState(false);

  // Check if icon color conflicts with desktop background
  const safeColor = useMemo(() => {
    const bg = getComputedStyle(document.documentElement).getPropertyValue("--ls-desktop-bg").trim();
    const desktopText = getComputedStyle(document.documentElement).getPropertyValue("--ls-desktop-text").trim();
    if (!bg) return color;

    // Map tailwind color classes to approximate hex
    const colorMap: Record<string, string> = {
      "text-blue-400": "#60a5fa", "text-emerald-400": "#34d399",
      "text-purple-400": "#c084fc", "text-green-400": "#4ade80",
      "text-amber-400": "#fbbf24", "text-rose-400": "#fb7185",
      "text-cyan-400": "#22d3ee", "text-orange-400": "#fb923c",
      "text-pink-400": "#f472b6", "text-slate-400": "#94a3b8",
    };
    const iconHex = colorMap[color];
    if (!iconHex) return color;

    if (hasConflict(iconHex, bg)) {
      // Use the contrasting desktop text color instead
      return undefined; // signal to use inline style
    }
    return color;
  }, [color]);

  const useDesktopText = safeColor === undefined;

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
        className={`flex h-12 w-12 items-center justify-center rounded-xl ls-bg-input ${useDesktopText ? "" : safeColor}`}
      >
        <Icon className="h-6 w-6" style={useDesktopText ? { color: "var(--ls-desktop-text)" } : undefined} />
      </div>
      <span className="text-[11px] leading-tight font-medium drop-shadow-md"
        style={{ color: "var(--ls-desktop-text)" }}>
        {label}
      </span>
    </button>
  );
}
