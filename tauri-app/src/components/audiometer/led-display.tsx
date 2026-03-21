import { cn } from "@/lib/utils";

interface LedDisplayProps {
  value: string;
  label?: string;
  color?: "green" | "red" | "amber" | "blue";
  size?: "sm" | "md" | "lg";
}

export function LedDisplay({
  value,
  label,
  color = "green",
  size = "md",
}: LedDisplayProps) {
  const colors = {
    green: "text-green-400 [text-shadow:0_0_8px_rgb(74_222_128/0.6)]",
    red: "text-red-400 [text-shadow:0_0_8px_rgb(248_113_113/0.6)]",
    amber: "text-amber-400 [text-shadow:0_0_8px_rgb(251_191_36/0.6)]",
    blue: "text-blue-400 [text-shadow:0_0_8px_rgb(96_165_250/0.6)]",
  };

  const sizes = {
    sm: "text-lg px-2 py-0.5",
    md: "text-2xl px-3 py-1",
    lg: "text-4xl px-4 py-2",
  };

  return (
    <div className="flex flex-col items-center gap-0.5">
      {label && (
        <span className="text-xs font-medium uppercase tracking-[0.15em] ls-text-muted">
          {label}
        </span>
      )}
      <div
        className={cn(
          "rounded-sm border ls-border bg-black/80 font-mono font-bold tabular-nums",
          sizes[size],
          colors[color],
        )}
      >
        {value}
      </div>
    </div>
  );
}
