import { lazy, Suspense } from "react";
import type { ModuleId } from "@/lib/constants";
import { Loader2 } from "lucide-react";

const modules: Record<ModuleId, React.LazyExoticComponent<React.ComponentType>> = {
  "patient-info": lazy(() => import("@/modules/patient-info")),
  "patient-personality": lazy(() => import("@/modules/patient-personality")),
  anamnesis: lazy(() => import("@/modules/anamnesis")),
  audiometry: lazy(() => import("@/modules/audiometry")),
  "tuning-fork": lazy(() => import("@/modules/tuning-fork")),
  logoaudiometry: lazy(() => import("@/modules/logoaudiometry")),
  supraliminal: lazy(() => import("@/modules/supraliminal")),
  impedance: lazy(() => import("@/modules/impedance")),
  oae: lazy(() => import("@/modules/oae")),
  abr: lazy(() => import("@/modules/abr")),
  electrocochleo: lazy(() => import("@/modules/electrocochleo")),
  "hearing-aids": lazy(() => import("@/modules/hearing-aids")),
  oct: lazy(() => import("@/modules/oct")),
  "visual-field": lazy(() => import("@/modules/visual-field")),
  "corneal-topography": lazy(() => import("@/modules/corneal-topography")),
  retinography: lazy(() => import("@/modules/retinography")),
  scheimpflug: lazy(() => import("@/modules/scheimpflug")),
  vng: lazy(() => import("@/modules/vng")),
  vhit: lazy(() => import("@/modules/vhit")),
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
          <Loader2 className="h-6 w-6 animate-spin ls-text-muted" />
        </div>
      }
    >
      <Module />
    </Suspense>
  );
}
