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
  BotMessageSquare,
  FolderOpen,
  Trash2,
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
  // ─── Simuladores ───
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
    id: "autoref",
    label: "Autorefractómetro",
    icon: ScanEye,
    component: "autoref",
    color: "text-cyan-400",
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
  // ─── Gestión ───
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
  {
    id: "karime-config",
    label: "Configurar Karime",
    icon: BotMessageSquare,
    component: "karime-config",
    color: "text-rose-400",
    roles: ["admin", "docente"],
    group: "gestion",
  },
];

export const WINDOW_SIZES: Record<string, { width: number; height: number; x?: number; y?: number }> = {
  audiometer: { width: 900, height: 580, x: 40, y: 15 },
  impedance: { width: 950, height: 620 },
  perimetry: { width: 1000, height: 700 },
  oct: { width: 1050, height: 720 },
  retinography: { width: 950, height: 700 },
  "corneal-topography": { width: 1050, height: 720 },
  scheimpflug: { width: 1000, height: 680 },
  vng: { width: 950, height: 650 },
  vhit: { width: 950, height: 650 },
  autoref: { width: 850, height: 680 },
  messaging: { width: 420, height: 620 },
  agenda: { width: 550, height: 500 },
  settings: { width: 680, height: 520 },
  "karime-config": { width: 680, height: 520 },
  "file-explorer": { width: 650, height: 480 },
  "trash": { width: 500, height: 400 },
  "kb-editor": { width: 650, height: 520 },
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
      {/* Simuladores — grid 2 columnas izquierda */}
      <div className="absolute left-0 top-0 grid grid-cols-2 auto-rows-min content-start gap-0.5 p-3">
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
        <div className="absolute right-0 top-0 grid grid-cols-2 auto-rows-min content-start gap-0.5 p-3">
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

      {/* Utilidades — esquina inferior derecha */}
      <div className="absolute bottom-0 right-0 flex flex-col items-end gap-0.5 p-3">
        <DesktopIcon
          label="Mis Documentos"
          icon={FolderOpen}
          color="text-amber-400"
          onOpen={() => openWindow("file-explorer", "Mis Documentos", "file-explorer", WINDOW_SIZES["file-explorer"])}
        />
        <DesktopIcon
          label="Papelera"
          icon={Trash2}
          color="text-slate-400"
          onOpen={() => openWindow("trash", "Papelera", "trash", WINDOW_SIZES.trash)}
        />
      </div>
    </div>
  );
}
