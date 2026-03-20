import { Stethoscope } from "lucide-react";
import { MODULE_IDS, MODULE_LABELS } from "@/lib/constants";

export function ClinicalPlaceholder() {
  return (
    <div className="flex h-full flex-col ls-bg">
      <div className="flex items-center gap-3 border-b ls-border p-4">
        <Stethoscope className="h-5 w-5 text-purple-400" />
        <h3 className="text-sm font-semibold ls-text">Módulos Clínicos</h3>
      </div>
      <div className="grid grid-cols-3 gap-2 p-4">
        {MODULE_IDS.map((id) => (
          <button
            key={id}
            className="rounded-lg ls-bg-input p-3 text-left transition hover:ls-bg-input"
          >
            <p className="text-xs font-medium ls-text">
              {MODULE_LABELS[id]}
            </p>
            <p className="mt-0.5 text-[10px] ls-text-muted">Fase 2-4</p>
          </button>
        ))}
      </div>
    </div>
  );
}
