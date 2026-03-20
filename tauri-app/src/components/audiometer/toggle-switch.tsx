import { cn } from "@/lib/utils";

interface ToggleSwitchProps {
  value: string;
  options: { value: string; label: string; color?: string }[];
  onChange: (value: string) => void;
  label?: string;
  vertical?: boolean;
}

export function ToggleSwitch({
  value,
  options,
  onChange,
  label,
  vertical = false,
}: ToggleSwitchProps) {
  return (
    <div className={cn("flex items-center gap-1", vertical && "flex-col")}>
      {label && (
        <span className="w-8 shrink-0 text-[6px] font-semibold uppercase tracking-wider text-white/25">
          {label}
        </span>
      )}
      <div
        className={cn(
          "flex rounded-[2px] border border-white/[0.06] bg-slate-900/80",
          vertical ? "flex-col" : "flex-row",
        )}
      >
        {options.map((opt) => {
          const isActive = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className={cn(
                "px-1.5 py-[2px] text-[7px] font-bold uppercase tracking-wider transition-all",
                isActive
                  ? cn("shadow-inner", opt.color ?? "bg-amber-500/80 text-black")
                  : "text-white/20 hover:text-white/40",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
