import { lazy, Suspense } from "react";
import type { ModuleId } from "@/lib/constants";
import { Loader2 } from "lucide-react";

const modules: Record<ModuleId, React.LazyExoticComponent<React.ComponentType>> = {
  "patient-info": lazy(() => import("@/modules/patient-info")),
  anamnesis: lazy(() => import("@/modules/anamnesis")),
  audiometry: lazy(() => import("@/modules/audiometry")),
  logoaudiometry: lazy(() => import("@/modules/logoaudiometry")),
  supraliminal: lazy(() => import("@/modules/supraliminal")),
  impedance: lazy(() => import("@/modules/impedance")),
  oae: lazy(() => import("@/modules/oae")),
  abr: lazy(() => import("@/modules/abr")),
  electrocochleo: lazy(() => import("@/modules/electrocochleo")),
  "hearing-aids": lazy(() => import("@/modules/hearing-aids")),
  agenda: lazy(() => import("@/modules/agenda")),
  "json-output": lazy(() => import("@/modules/json-output")),
};

interface Props {
  moduleId: ModuleId;
}

export function ModuleLoader({ moduleId }: Props) {
  const Module = modules[moduleId];

  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-white/30" />
        </div>
      }
    >
      <Module />
    </Suspense>
  );
}
