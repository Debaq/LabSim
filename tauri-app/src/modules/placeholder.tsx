import { Construction } from "lucide-react";

interface Props {
  name: string;
  phase: string;
}

export function ModulePlaceholder({ name, phase }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <Construction className="h-10 w-10 text-white/20" />
      <h3 className="text-lg font-semibold text-white/60">{name}</h3>
      <p className="text-sm text-white/30">Se implementará en {phase}</p>
    </div>
  );
}
