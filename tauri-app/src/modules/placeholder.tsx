import { Construction } from "lucide-react";

interface Props {
  name: string;
  phase: string;
}

export function ModulePlaceholder({ name, phase }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <Construction className="h-10 w-10 ls-text-muted" />
      <h3 className="text-lg font-semibold ls-text2">{name}</h3>
      <p className="text-sm ls-text-muted">Se implementará en {phase}</p>
    </div>
  );
}
