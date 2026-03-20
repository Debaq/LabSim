import { useUIStore } from "@/stores/ui-store";
import { DesktopIcon } from "./desktop-icon";
import {
  Headphones,
  Activity,
  Stethoscope,
  FolderOpen,
  FileText,
  MessageCircle,
  Database,
} from "lucide-react";

const desktopItems = [
  {
    id: "audiometer",
    label: "Audiómetro",
    icon: Headphones,
    component: "audiometer",
    color: "text-blue-400",
  },
  {
    id: "impedance",
    label: "Impedanciómetro",
    icon: Activity,
    component: "impedance",
    color: "text-emerald-400",
  },
  {
    id: "patient-history",
    label: "Historial",
    icon: Database,
    component: "patient-history",
    color: "text-cyan-400",
  },
  {
    id: "clinical",
    label: "Módulo Clínico",
    icon: Stethoscope,
    component: "clinical",
    color: "text-purple-400",
  },
  {
    id: "messaging",
    label: "Mensajes",
    icon: MessageCircle,
    component: "messaging",
    color: "text-green-400",
  },
  {
    id: "file-explorer",
    label: "Explorador",
    icon: FolderOpen,
    component: "file-explorer",
    color: "text-amber-400",
  },
  {
    id: "text-editor",
    label: "Editor de Texto",
    icon: FileText,
    component: "text-editor",
    color: "text-rose-400",
  },
];

interface Props {
  className?: string;
}

export function DesktopArea({ className }: Props) {
  const openWindow = useUIStore((s) => s.openWindow);

  const handleOpen = (item: (typeof desktopItems)[number]) => {
    const opts =
      item.id === "messaging"
        ? { width: 420, height: 620 }
        : undefined;
    openWindow(item.id, item.label, item.component, opts);
  };

  return (
    <div
      className={`grid auto-rows-min grid-cols-1 content-start gap-1 p-3 ${className ?? ""}`}
    >
      {desktopItems.map((item) => (
        <DesktopIcon
          key={item.id}
          label={item.label}
          icon={item.icon}
          color={item.color}
          onOpen={() => handleOpen(item)}
        />
      ))}
    </div>
  );
}
