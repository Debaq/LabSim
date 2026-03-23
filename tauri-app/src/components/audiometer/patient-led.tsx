/**
 * Indicador de respuesta del paciente.
 *
 * Simula el botón que el paciente presiona cuando escucha el tono.
 * En un audiómetro real, hay una luz que se enciende mientras
 * el paciente mantiene presionado su pulsador.
 */

import { cn } from "@/lib/utils";

interface PatientLedProps {
  active: boolean;
  className?: string;
}

export function PatientLed({ active, className }: PatientLedProps) {
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <div
        className={cn(
          "h-4 w-4 rounded-full border-2 transition-all duration-100",
          active
            ? "bg-emerald-400 border-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.7)] scale-110"
            : "bg-zinc-800 border-zinc-600",
        )}
      />
      <span className={cn(
        "text-[9px] font-bold uppercase tracking-wider transition-colors",
        active ? "text-emerald-400" : "ls-text-muted",
      )}>
        Resp
      </span>
    </div>
  );
}
