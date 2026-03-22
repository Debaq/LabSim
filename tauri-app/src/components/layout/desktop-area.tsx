import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { DesktopIcon } from "./desktop-icon";
import {
  Headphones,
  Activity,
  Users,
  ScanEye,
  Layers,
  ClipboardList,
  BarChart3,
  ClipboardPen,
  Building2,
  Eye,
  CircleDot,
  GraduationCap,
  ShieldCheck,
  Scan,
} from "lucide-react";

interface DesktopItem {
  id: string;
  label: string;
  icon: typeof Headphones;
  component: string;
  color: string;
  roles?: string[];
  group: "simuladores" | "gestion";
}

const desktopItems: DesktopItem[] = [
  // ─── Simuladores (columna izquierda) ───
  {
    id: "audiometer",
    label: "Audiómetro",
    icon: Headphones,
    component: "audiometer",
    color: "text-blue-400",
    group: "simuladores",
  },
  {
    id: "impedance",
    label: "Impedanciómetro",
    icon: Activity,
    component: "impedance",
    color: "text-emerald-400",
    group: "simuladores",
  },
  {
    id: "perimetry",
    label: "Campo Visual",
    icon: ScanEye,
    component: "perimetry",
    color: "text-orange-400",
    group: "simuladores",
  },
  {
    id: "oct",
    label: "OCT",
    icon: Layers,
    component: "oct",
    color: "text-pink-400",
    group: "simuladores",
  },
  {
    id: "retinography",
    label: "Retinógrafo",
    icon: Eye,
    component: "retinography",
    color: "text-red-400",
    group: "simuladores",
  },
  {
    id: "corneal-topography",
    label: "Topógrafo Corneal",
    icon: CircleDot,
    component: "corneal-topography",
    color: "text-teal-400",
    group: "simuladores",
  },
  {
    id: "vng",
    label: "VNG",
    icon: Eye,
    component: "vng",
    color: "text-violet-400",
    group: "simuladores",
  },
  {
    id: "vhit",
    label: "vHIT",
    icon: Activity,
    component: "vhit",
    color: "text-orange-400",
    group: "simuladores",
  },
  {
    id: "scheimpflug",
    label: "Scheimpflug",
    icon: Scan,
    component: "scheimpflug",
    color: "text-teal-400",
    group: "simuladores",
  },
  {
    id: "larissa",
    label: "Larissa",
    icon: ClipboardPen,
    component: "larissa",
    color: "text-cyan-400",
    group: "simuladores",
  },
  {
    id: "my-stats",
    label: "Mis Estadísticas",
    icon: BarChart3,
    component: "my-stats",
    color: "text-teal-400",
    group: "simuladores",
  },
  // ─── Gestión (fila horizontal arriba derecha) ───
  {
    id: "center",
    label: "Centro",
    icon: Building2,
    component: "center",
    color: "text-amber-400",
    group: "gestion",
  },
  {
    id: "practice-sessions",
    label: "Sesiones",
    icon: ClipboardList,
    component: "practice-sessions",
    color: "text-sky-400",
    group: "gestion",
  },
  {
    id: "courses",
    label: "Mis Cursos",
    icon: GraduationCap,
    component: "courses",
    color: "text-sky-400",
    roles: ["admin", "docente", "instructor"],
    group: "gestion",
  },
  {
    id: "supervision",
    label: "Supervisión",
    icon: ShieldCheck,
    component: "supervision",
    color: "text-indigo-400",
    roles: ["admin", "docente", "instructor"],
    group: "gestion",
  },
  {
    id: "manage-patients",
    label: "Gestionar Pacientes",
    icon: Users,
    component: "manage-patients",
    color: "text-purple-400",
    roles: ["admin", "docente", "instructor"],
    group: "gestion",
  },
];

const WINDOW_SIZES: Record<string, { width: number; height: number; x?: number; y?: number }> = {
  audiometer: { width: 780, height: 520, x: 60, y: 20 },
  impedance: { width: 800, height: 500 },
  perimetry: { width: 750, height: 550 },
  oct: { width: 800, height: 520 },
  retinography: { width: 720, height: 540 },
  "corneal-topography": { width: 800, height: 520 },
};

interface Props {
  className?: string;
}

export function DesktopArea({ className }: Props) {
  const openWindow = useUIStore((s) => s.openWindow);
  const role = useAuthStore((s) => s.role);

  const visibleItems = desktopItems.filter(
    (item) => !item.roles || item.roles.includes(role),
  );

  const simuladores = visibleItems.filter((i) => i.group === "simuladores");
  const gestion = visibleItems.filter((i) => i.group === "gestion");

  const handleOpen = (item: DesktopItem) => {
    openWindow(item.id, item.label, item.component, WINDOW_SIZES[item.id]);
  };

  return (
    <div className={`relative h-full ${className ?? ""}`}>
      {/* Simuladores — columna izquierda */}
      <div className="absolute left-0 top-0 grid auto-rows-min grid-cols-1 content-start gap-1 p-3">
        {simuladores.map((item) => (
          <DesktopIcon
            key={item.id}
            label={item.label}
            icon={item.icon}
            color={item.color}
            onOpen={() => handleOpen(item)}
          />
        ))}
      </div>

      {/* Gestión — fila horizontal arriba derecha */}
      {gestion.length > 0 && (
        <div className="absolute right-0 top-0 flex items-start gap-1 p-3">
          {gestion.map((item) => (
            <DesktopIcon
              key={item.id}
              label={item.label}
              icon={item.icon}
              color={item.color}
              onOpen={() => handleOpen(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
