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
        <span className="w-8 shrink-0 text-[6px] font-semibold uppercase tracking-wider ls-text-muted">
          {label}
        </span>
      )}
      <div
        className={cn(
          "flex rounded-[2px] border ls-border ls-bg-panel/80",
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
                  : "ls-text-muted hover:ls-text-muted",
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
