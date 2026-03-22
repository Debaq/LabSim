import { useLiveSessionStore } from "@/stores/live-session-store";
import { User, Activity } from "lucide-react";

interface PatientBannerProps {
  simulatorName: string;
}

/**
 * Banner que aparece en los simuladores cuando hay un paciente en atención.
 * Muestra nombre del paciente y el simulador que se está usando.
 * Si no hay paciente activo, no renderiza nada.
 */
export function PatientBanner({ simulatorName }: PatientBannerProps) {
  const displayName = useLiveSessionStore((s) => s.patientDisplayName);
  const mood = useLiveSessionStore((s) => s.patientMood);
  const addEvent = useLiveSessionStore((s) => s.addEvent);
  const activePatientId = useLiveSessionStore((s) => s.activePatientId);

  if (!activePatientId) return null;

  return (
    <div className="flex items-center gap-2 border-b ls-border px-3 py-1.5 bg-cyan-500/5">
      <User className="h-3.5 w-3.5 text-cyan-400" />
      <span className="text-[11px] font-medium text-cyan-300">
        Atendiendo a: {displayName ?? "Paciente"}
      </span>
      <span className="text-[10px] ls-text-muted">— {simulatorName}</span>
      {mood !== "normal" && (
        <span className="text-[10px] text-amber-400 flex items-center gap-0.5">
          <Activity className="h-3 w-3" />
          {mood}
        </span>
      )}
    </div>
  );
}
