import { useCallback, useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface RotaryKnobProps {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  label?: string;
  displayValue?: string;
  size?: "sm" | "md" | "lg";
  marks?: { value: number; label: string }[];
}

export function RotaryKnob({
  value,
  min,
  max,
  step,
  onChange,
  label,
  displayValue,
  size = "md",
}: RotaryKnobProps) {
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  useEffect(() => { valueRef.current = value; }, [value]);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);

  // Visual angle is independent from value — keeps spinning freely
  const [visualAngle, setVisualAngle] = useState(0);
  const prevValue = useRef(value);
  const dragging = useRef(false);
  const lastY = useRef(0);

  // Sync visual rotation when value changes externally (keyboard, etc)
  useEffect(() => {
    if (!dragging.current && value !== prevValue.current) {
      const delta = value - prevValue.current;
      const range = max - min;
      const degreesPerUnit = range > 0 ? 360 / range : 1;
      setVisualAngle((a) => a + delta * degreesPerUnit);
    }
    prevValue.current = value;
  }, [value, min, max]);

  const sizes = {
    sm: { knob: 48, text: "text-[8px]", display: "text-[10px]" },
    md: { knob: 68, text: "text-[9px]", display: "text-xs" },
    lg: { knob: 96, text: "text-[10px]", display: "text-sm" },
  };
  const s = sizes[size];

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragging.current = true;
      lastY.current = e.clientY;

      const onMove = (ev: MouseEvent) => {
        if (!dragging.current) return;
        const dy = lastY.current - ev.clientY;
        lastY.current = ev.clientY;

        // Visual rotation: always spins freely
        setVisualAngle((a) => a + dy * 2);

        // Value: clamped to min/max
        const pixelsPerStep = 3;
        const delta = (dy / pixelsPerStep) * step;
        const next = Math.round((valueRef.current + delta) / step) * step;
        const clamped = Math.max(min, Math.min(max, next));
        if (clamped !== valueRef.current) {
          onChangeRef.current(clamped);
        }
      };

      const onUp = () => {
        dragging.current = false;
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      };

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [min, max, step],
  );

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.stopPropagation();
      const dir = e.deltaY < 0 ? 1 : -1;
      setVisualAngle((a) => a + dir * 15);
      const next = Math.max(min, Math.min(max, valueRef.current + dir * step));
      onChangeRef.current(next);
    },
    [min, max, step],
  );

  // Number of grip ridges around the edge
  const ridges = size === "lg" ? 40 : size === "md" ? 30 : 24;

  return (
    <div className="flex flex-col items-center gap-1">
      {label && (
        <span className={cn("font-semibold uppercase tracking-[0.12em] text-white/30", s.text)}>
          {label}
        </span>
      )}

      {/* Knob */}
      <div
        className="relative cursor-grab rounded-full active:cursor-grabbing"
        style={{
          width: s.knob,
          height: s.knob,
          transform: `rotate(${visualAngle}deg)`,
          background: `conic-gradient(from 0deg, #555a65, #3d424c, #555a65, #3d424c, #555a65)`,
          boxShadow: "0 3px 12px rgba(0,0,0,0.6), inset 0 1px 1px rgba(255,255,255,0.08)",
        }}
        onMouseDown={handleMouseDown}
        onWheel={handleWheel}
      >
        {/* Grip ridges around the edge */}
        {Array.from({ length: ridges }).map((_, i) => {
          const a = (i / ridges) * 360;
          const rad = (a - 90) * (Math.PI / 180);
          const r = s.knob / 2 - 1;
          const x = Math.cos(rad) * r + s.knob / 2;
          const y = Math.sin(rad) * r + s.knob / 2;
          return (
            <div
              key={i}
              className="absolute h-[3px] w-[1px] bg-white/[0.07]"
              style={{
                left: x,
                top: y,
                transform: `translate(-50%, -50%) rotate(${a}deg)`,
              }}
            />
          );
        })}

        {/* Center cap */}
        <div
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            width: s.knob * 0.4,
            height: s.knob * 0.4,
            background: "linear-gradient(180deg, #4a4f58 0%, #35393f 100%)",
            boxShadow: "inset 0 1px 2px rgba(255,255,255,0.06), 0 1px 3px rgba(0,0,0,0.3)",
          }}
        />
      </div>

      {displayValue && (
        <div className="rounded-sm bg-black/70 px-1.5 py-0.5 font-mono">
          <span className={cn("font-bold text-green-400 [text-shadow:0_0_4px_rgb(74_222_128/0.4)]", s.display)}>
            {displayValue}
          </span>
        </div>
      )}
    </div>
  );
}
