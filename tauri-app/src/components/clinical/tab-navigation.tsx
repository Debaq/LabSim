import { MODULE_IDS, MODULE_LABELS, type ModuleId } from "@/lib/constants";
import { usePatientStore } from "@/stores/patient-store";
import { Badge } from "@/components/ui/badge";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  User,
  SmilePlus,
  ClipboardList,
  AudioLines,
  MessageSquare,
  Zap,
  Activity,
  Waves,
  BrainCircuit,
  Cable,
  Ear,
  ScanEye,
  Target,
  CircleDot,
  Camera,
  Box,
  MonitorSmartphone,
  Rotate3d,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const moduleIcons: Record<ModuleId, LucideIcon> = {
  "patient-info": User,
  "patient-personality": SmilePlus,
  anamnesis: ClipboardList,
  audiometry: AudioLines,
  logoaudiometry: MessageSquare,
  supraliminal: Zap,
  impedance: Activity,
  oae: Waves,
  abr: BrainCircuit,
  electrocochleo: Cable,
  "hearing-aids": Ear,
  oct: ScanEye,
  "visual-field": Target,
  "corneal-topography": CircleDot,
  retinography: Camera,
  scheimpflug: Box,
  vng: MonitorSmartphone,
  vhit: Rotate3d,
};

interface TabNavigationProps {
  activeTab: ModuleId;
  onTabChange: (tab: ModuleId) => void;
}

export function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  const data = usePatientStore((s) => s.data);

  const isModuleComplete = (id: ModuleId): boolean => {
    const key = id === "patient-info" ? "patientInfo" : id.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const moduleData = data[key as keyof typeof data];
    return moduleData != null && Object.keys(moduleData).length > 0;
  };

  const completedCount = MODULE_IDS.filter(isModuleComplete).length;

  return (
    <div className="border-b ls-border ls-bg-panel/80">
      {/* Progress indicator */}
      <div className="flex items-center justify-between px-4 pt-2 pb-1">
        <span className="text-xs font-medium tracking-wider ls-text-muted uppercase">
          Módulos Clínicos
        </span>
        <Badge variant="secondary" className="h-5 text-xs">
          {completedCount}/{MODULE_IDS.length}
        </Badge>
      </div>

      {/* Tabs */}
      <ScrollArea className="w-full">
        <div className="flex gap-0.5 px-2 pb-0">
          {MODULE_IDS.map((id) => {
            const Icon = moduleIcons[id];
            const isActive = id === activeTab;
            const isComplete = isModuleComplete(id);

            return (
              <button
                key={id}
                onClick={() => onTabChange(id)}
                className={cn(
                  "group flex shrink-0 items-center gap-1.5 rounded-t-lg px-3 py-2 text-xs font-medium transition",
                  isActive
                    ? "ls-bg ls-text"
                    : "ls-text-muted hover:ls-bg-input hover:ls-text2",
                )}
              >
                <Icon
                  className={cn(
                    "h-3.5 w-3.5",
                    isComplete && !isActive && "text-emerald-400/60",
                  )}
                />
                <span className="hidden lg:inline">{MODULE_LABELS[id]}</span>
                {isComplete && !isActive && (
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                )}
              </button>
            );
          })}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
