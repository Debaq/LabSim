/**
 * Panel de posicionamiento — layout horizontal compacto.
 * Va DEBAJO de la imagen central en todos los simuladores oftálmicos.
 *
 * Joystick: drag XY, scroll=Z, click/espacio=disparar.
 * Teclas: WASD (XY), QE (Z), R (centrar), F (frente), Espacio (disparo).
 */

import { useRef, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Plus, Minus } from "lucide-react";

export interface AlignmentState {
  chinHeight: number;
  joystickX: number;
  joystickY: number;
  joystickZ: number;
  foreheadContact: boolean;
}

export const DEFAULT_ALIGNMENT: AlignmentState = {
  chinHeight: 50,
  joystickX: 0,
  joystickY: 0,
  joystickZ: 0,
  foreheadContact: false,
};

export function getAlignmentQuality(a: AlignmentState): number {
  if (!a.foreheadContact) return 0;
  const xErr = Math.abs(a.joystickX);
  const yErr = Math.abs(a.joystickY);
  const zErr = Math.abs(a.joystickZ);
  const chinErr = Math.abs(a.chinHeight - 50) / 50;
  const totalErr = (xErr + yErr + zErr) / 30 + chinErr * 0.3;
  return Math.max(0, Math.round((1 - totalErr) * 100));
}

export function isAligned(a: AlignmentState): boolean {
  return getAlignmentQuality(a) >= 70;
}

interface Props {
  state: AlignmentState;
  onChange: (state: AlignmentState) => void;
  onCapture?: () => void;
  compact?: boolean;
}

export function AlignmentPanel({ state, onChange, onCapture, compact }: Props) {
  const quality = getAlignmentQuality(state);
  const aligned = isAligned(state);
  const joystickRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

  const update = useCallback((partial: Partial<AlignmentState>) => {
    onChange({ ...state, ...partial });
  }, [state, onChange]);

  const handleJoystickMove = useCallback((clientX: number, clientY: number) => {
    const el = joystickRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const rawX = (clientX - cx) / (rect.width / 2);
    const rawY = -(clientY - cy) / (rect.height / 2);
    onChange({
      ...state,
      joystickX: clamp(Math.round(rawX * 10), -10, 10),
      joystickY: clamp(Math.round(rawY * 10), -10, 10),
    });
  }, [state, onChange]);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    dragging.current = true;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    handleJoystickMove(e.clientX, e.clientY);
  }, [handleJoystickMove]);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    handleJoystickMove(e.clientX, e.clientY);
  }, [handleJoystickMove]);

  const onPointerUp = useCallback(() => { dragging.current = false; }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    onChange({ ...state, joystickZ: clamp(state.joystickZ + (e.deltaY > 0 ? -1 : 1), -10, 10) });
  }, [state, onChange]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      switch (e.key.toLowerCase()) {
        case "w": onChange({ ...state, joystickY: clamp(state.joystickY + 1, -10, 10) }); e.preventDefault(); break;
        case "s": onChange({ ...state, joystickY: clamp(state.joystickY - 1, -10, 10) }); e.preventDefault(); break;
        case "a": onChange({ ...state, joystickX: clamp(state.joystickX - 1, -10, 10) }); e.preventDefault(); break;
        case "d": onChange({ ...state, joystickX: clamp(state.joystickX + 1, -10, 10) }); e.preventDefault(); break;
        case "q": onChange({ ...state, joystickZ: clamp(state.joystickZ - 1, -10, 10) }); e.preventDefault(); break;
        case "e": onChange({ ...state, joystickZ: clamp(state.joystickZ + 1, -10, 10) }); e.preventDefault(); break;
        case "r": onChange({ ...state, joystickX: 0, joystickY: 0, joystickZ: 0 }); e.preventDefault(); break;
        case "f": onChange({ ...state, foreheadContact: !state.foreheadContact }); e.preventDefault(); break;
        case " ": if (onCapture && aligned) { onCapture(); e.preventDefault(); } break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state, onChange, onCapture, aligned]);

  const JS = compact ? 72 : 84;
  const KNOB = 16;
  const half = JS / 2;
  const kx = half + (state.joystickX / 10) * (half - KNOB / 2);
  const ky = half - (state.joystickY / 10) * (half - KNOB / 2);

  return (
    <div className="flex items-center gap-4 justify-center py-1">
      {/* Izquierda: paciente */}
      <div className="flex flex-col gap-1.5 items-center w-[120px]">
        <button
          onClick={() => update({ foreheadContact: !state.foreheadContact })}
          className={cn("w-full rounded border py-1 text-xs font-bold transition",
            state.foreheadContact ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "ls-border text-amber-400 hover:bg-amber-500/10")}
        >{state.foreheadContact ? "Frente OK" : "Frente (F)"}</button>

        <div className="w-full">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-xs ls-text-muted">Mentonera</span>
            <span className="text-xs font-mono ls-text2">{state.chinHeight}</span>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => update({ chinHeight: clamp(state.chinHeight - 3, 0, 100) })}
              className="p-0.5 ls-text-muted hover:ls-bg-input rounded"><Minus className="h-3.5 w-3.5" /></button>
            <input type="range" min={0} max={100} value={state.chinHeight}
              onChange={(e) => update({ chinHeight: parseInt(e.target.value) })}
              className="flex-1 h-1.5 appearance-none rounded bg-zinc-700 accent-emerald-500 cursor-pointer" />
            <button onClick={() => update({ chinHeight: clamp(state.chinHeight + 3, 0, 100) })}
              className="p-0.5 ls-text-muted hover:ls-bg-input rounded"><Plus className="h-3.5 w-3.5" /></button>
          </div>
        </div>

        <span className={cn("text-xs font-bold px-2 py-0.5 rounded",
          aligned ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400")}>{quality}%</span>
      </div>

      {/* Centro: joystick */}
      <div className="flex flex-col items-center gap-1.5">
        <div
          ref={joystickRef}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onWheel={onWheel}
          className="relative rounded-full border-2 border-zinc-600 bg-gradient-to-b from-zinc-800 to-zinc-900 cursor-crosshair select-none touch-none"
          style={{ width: JS, height: JS }}
        >
          <div className="absolute left-1/2 top-2 bottom-2 w-px bg-zinc-700/40 -translate-x-1/2" />
          <div className="absolute top-1/2 left-2 right-2 h-px bg-zinc-700/40 -translate-y-1/2" />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-4 w-4 rounded-full border border-zinc-600/40" />
          <div
            className={cn("absolute rounded-full border-2 pointer-events-none transition-shadow bg-gradient-to-b",
              aligned ? "from-emerald-400 to-emerald-600 border-emerald-300 shadow-[0_0_8px_rgba(52,211,153,0.4)]"
                      : "from-zinc-300 to-zinc-500 border-zinc-200 shadow-[0_0_4px_rgba(161,161,170,0.2)]")}
            style={{ width: KNOB, height: KNOB, left: kx - KNOB / 2, top: ky - KNOB / 2 }}
          />
        </div>
        <span className="text-[10px] ls-text-muted">WASD · Scroll=Z</span>
      </div>

      {/* Derecha: Z + disparo */}
      <div className="flex flex-col gap-1.5 items-center w-[120px]">
        <div className="w-full">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-xs ls-text-muted">Enfoque (Z)</span>
            <span className="text-xs font-mono ls-text2">{state.joystickZ > 0 ? "+" : ""}{state.joystickZ}</span>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => update({ joystickZ: clamp(state.joystickZ - 1, -10, 10) })}
              className="p-0.5 ls-text-muted hover:ls-bg-input rounded"><Minus className="h-3.5 w-3.5" /></button>
            <div className="flex-1 relative h-2.5 rounded-full bg-zinc-800 border border-zinc-700">
              <div className={cn("absolute top-1/2 -translate-y-1/2 h-4 w-4 rounded-full border-2 transition-all",
                  aligned ? "bg-emerald-500 border-emerald-400" : "bg-zinc-400 border-zinc-300")}
                style={{ left: `calc(${((state.joystickZ + 10) / 20) * 100}% - 8px)` }} />
            </div>
            <button onClick={() => update({ joystickZ: clamp(state.joystickZ + 1, -10, 10) })}
              className="p-0.5 ls-text-muted hover:ls-bg-input rounded"><Plus className="h-3.5 w-3.5" /></button>
          </div>
        </div>

        {onCapture ? (
          <button onClick={() => { if (aligned) onCapture(); }} disabled={!aligned}
            className={cn("w-full rounded-full border-2 py-1 text-xs font-bold transition",
              aligned ? "border-emerald-500 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                      : "border-zinc-600 ls-text-muted opacity-50 cursor-not-allowed")}>
            DISPARAR
          </button>
        ) : (
          <button onClick={() => update({ joystickX: 0, joystickY: 0, joystickZ: 0 })}
            className="w-full text-xs ls-text-muted hover:ls-text2 transition py-1 rounded border ls-border hover:ls-bg-input">
            Centrar (R)
          </button>
        )}
      </div>
    </div>
  );
}
