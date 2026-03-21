import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { DesktopIcon } from "./desktop-icon";
import {
  Headphones,
  Activity,
  ShieldCheck,
  ScanEye,
  Layers,
  ClipboardList,
  BarChart3,
  ClipboardPen,
  Building2,
  Eye,
} from "lucide-react";

interface DesktopItem {
  id: string;
  label: string;
  icon: typeof Headphones;
  component: string;
  color: string;
  /** Roles que pueden ver este icono. Si no se define, todos lo ven. */
  roles?: string[];
}

// Solo simuladores y apps esenciales en el escritorio
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
    id: "perimetry",
    label: "Campo Visual",
    icon: ScanEye,
    component: "perimetry",
    color: "text-orange-400",
  },
  {
    id: "oct",
    label: "OCT",
    icon: Layers,
    component: "oct",
    color: "text-pink-400",
  },
  {
    id: "retinography",
    label: "Retinógrafo",
    icon: Eye,
    component: "retinography",
    color: "text-red-400",
  },
  {
    id: "larissa",
    label: "Larissa",
    icon: ClipboardPen,
    component: "larissa",
    color: "text-cyan-400",
  },
  {
    id: "center",
    label: "Centro",
    icon: Building2,
    component: "center",
    color: "text-amber-400",
  },
  {
    id: "practice-sessions",
    label: "Sesiones",
    icon: ClipboardList,
    component: "practice-sessions",
    color: "text-sky-400",
  },
  {
    id: "my-stats",
    label: "Mis Estadísticas",
    icon: BarChart3,
    component: "my-stats",
    color: "text-teal-400",
  },
  {
    id: "clinical",
    label: "Crear Casos",
    icon: ShieldCheck,
    component: "clinical",
    color: "text-purple-400",
    roles: ["admin", "docente", "instructor"],
  },
];

interface Props {
  className?: string;
}

export function DesktopArea({ className }: Props) {
  const openWindow = useUIStore((s) => s.openWindow);
  const role = useAuthStore((s) => s.role);

  const visibleItems = desktopItems.filter(
    (item) => !item.roles || item.roles.includes(role),
  );

  const handleOpen = (item: DesktopItem) => {
    const opts =
      item.id === "audiometer"
        ? { width: 780, height: 520, x: 60, y: 20 }
        : item.id === "impedance"
          ? { width: 800, height: 500 }
          : item.id === "perimetry"
            ? { width: 750, height: 550 }
            : item.id === "oct"
              ? { width: 800, height: 520 }
              : item.id === "retinography"
                ? { width: 720, height: 540 }
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
