import { cn } from "@/lib/utils";

interface StimulusButtonProps {
  active: boolean;
  onPress: () => void;
  onRelease: () => void;
  label?: string;
  color?: "red" | "blue";
}

export function StimulusButton({
  active,
  onPress,
  onRelease,
  label = "ESTÍMULO",
  color = "red",
}: StimulusButtonProps) {
  const colors = {
    red: {
      bg: active ? "bg-red-600 shadow-red-500/50" : "bg-red-900/60 hover:bg-red-800/60",
      ring: active ? "ring-2 ring-red-400/50" : "",
      led: active ? "bg-red-400 shadow-red-400/80" : "bg-red-900/50",
    },
    blue: {
      bg: active ? "bg-blue-600 shadow-blue-500/50" : "bg-blue-900/60 hover:bg-blue-800/60",
      ring: active ? "ring-2 ring-blue-400/50" : "",
      led: active ? "bg-blue-400 shadow-blue-400/80" : "bg-blue-900/50",
    },
  };
  const c = colors[color];

  return (
    <div className="flex flex-col items-center gap-1.5">
      {/* LED indicator */}
      <div
        className={cn(
          "h-2 w-2 rounded-full transition-all shadow-sm",
          c.led,
        )}
      />

      {/* Button */}
      <button
        onMouseDown={onPress}
        onMouseUp={onRelease}
        onMouseLeave={onRelease}
        className={cn(
          "h-12 w-12 rounded-full border-2 border-white/10 transition-all select-none",
          "flex items-center justify-center",
          "shadow-lg shadow-black/50",
          "active:translate-y-0.5 active:shadow-sm",
          c.bg,
          c.ring,
        )}
      >
        <span className="text-[8px] font-bold uppercase tracking-wider text-white/80">
          {label}
        </span>
      </button>
    </div>
  );
}
