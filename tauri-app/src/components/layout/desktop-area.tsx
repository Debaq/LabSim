import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { DesktopIcon } from "./desktop-icon";
import {
  Headphones,
  Activity,
  Stethoscope,
  FolderOpen,
  FileText,
  MessageCircle,
  Database,
  ShieldCheck,
} from "lucide-react";

interface DesktopItem {
  id: string;
  label: string;
  icon: typeof Headphones;
  component: string;
  color: string;
  adminOnly?: boolean;
}

const desktopItems: DesktopItem[] = [
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
    label: "Crear Casos",
    icon: ShieldCheck,
    component: "clinical",
    color: "text-purple-400",
    adminOnly: true,
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
  const isAdmin = useAuthStore((s) => s.isAdmin);

  const visibleItems = desktopItems.filter(
    (item) => !item.adminOnly || isAdmin,
  );

  const handleOpen = (item: DesktopItem) => {
    const opts =
      item.id === "messaging"
        ? { width: 420, height: 620 }
        : item.id === "audiometer"
          ? { width: 780, height: 520, x: 60, y: 20 }
          : item.id === "impedance"
            ? { width: 800, height: 500 }
            : undefined;
    openWindow(item.id, item.label, item.component, opts);
  };

  return (
    <div
      className={`grid auto-rows-min grid-cols-1 content-start gap-1 p-3 ${className ?? ""}`}
    >
      {visibleItems.map((item) => (
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
