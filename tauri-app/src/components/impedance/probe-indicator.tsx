/**
 * Indicador de estado de la sonda del impedanciómetro.
 * En un equipo real hay un LED que indica: desconectada, insertada, sellada, fuga.
 */

export type ProbeStatus = "disconnected" | "inserting" | "sealed" | "leak" | "blocked";

const STATUS_CONFIG: Record<ProbeStatus, { label: string; color: string; blink: boolean }> = {
  disconnected: { label: "Sin sonda", color: "bg-zinc-500", blink: false },
  inserting: { label: "Insertando...", color: "bg-amber-400", blink: true },
  sealed: { label: "Sellado OK", color: "bg-emerald-400", blink: false },
  leak: { label: "Fuga de aire", color: "bg-red-400", blink: true },
  blocked: { label: "Bloqueada", color: "bg-red-400", blink: false },
};

interface Props {
  status: ProbeStatus;
}

export function ProbeIndicator({ status }: Props) {
  const cfg = STATUS_CONFIG[status];

  return (
    <div className="flex items-center gap-1.5">
      <div className={`h-2 w-2 rounded-full ${cfg.color} ${cfg.blink ? "animate-pulse" : ""}`} />
      <span className="text-[10px] ls-text-muted">{cfg.label}</span>
    </div>
  );
}
