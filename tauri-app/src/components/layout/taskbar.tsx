import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import { useSyncStore } from "@/stores/sync-store";
import { useChatStore } from "@/stores/chat-store";
import { useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu";
import {
  Home,
  Power,
  Headphones,
  LogOut,
  Settings,
  User,
  Wifi,
  Volume2,
  Activity,
  ScanEye,
  Layers,
  Database,
  Stethoscope,
  MessageCircle,
  FolderOpen,
  FileText,
  ClipboardList,
  BarChart3,
  CalendarDays,
  ClipboardPen,
  Building2,
  Eye,
  CircleDot,
  Scan,
  BotMessageSquare,
  GraduationCap,
  ShieldCheck,
  Users,
  Trash2,
  BookOpen,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const WINDOW_ICONS: Record<string, LucideIcon> = {
  audiometer: Headphones,
  impedance: Activity,
  perimetry: ScanEye,
  oct: Layers,
  "patient-history": Database,
  clinical: Stethoscope,
  vng: Settings,
  vhit: Settings,
  scheimpflug: Settings,
  courses: ClipboardList,
  supervision: Settings,
  "manage-patients": Stethoscope,
  "clinical-editor": Stethoscope,
  messaging: MessageCircle,
  "file-explorer": FolderOpen,
  "text-editor": FileText,
  settings: Settings,
  "practice-sessions": ClipboardList,
  "my-stats": BarChart3,
  agenda: CalendarDays,
  larissa: ClipboardPen,
  center: Building2,
  retinography: Eye,
  "corneal-topography": CircleDot,
  "trash": Trash2,
  "kb-editor": BookOpen,
};
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { WINDOW_SIZES } from "./desktop-area";

export function Taskbar() {
  const navigate = useNavigate();
  const username = useAuthStore((s) => s.username);
  const role = useAuthStore((s) => s.role);
  const logout = useAuthStore((s) => s.logout);
  const windows = useUIStore((s) => s.windows);
  const openWindow = useUIStore((s) => s.openWindow);
  const focusWindow = useUIStore((s) => s.focusWindow);
  const restoreWindow = useUIStore((s) => s.restoreWindow);
  const isOnline = useSyncStore((s) => s.isOnline);
  const checkConnection = useSyncStore((s) => s.checkConnection);
  const unreadCounts = useChatStore((s) => s.unreadCounts);
  const totalUnread = Object.values(unreadCounts).reduce((sum, c) => sum + c, 0);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Verificar conexión cada 60 segundos
  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate({ to: "/login" });
  };

  const minimizeWindow = useUIStore((s) => s.minimizeWindow);

  const handleTaskbarClick = (id: string, isMinimized: boolean) => {
    if (isMinimized) {
      restoreWindow(id);
    } else {
      // If already focused (highest z), minimize it. Otherwise focus.
      const win = windows.find((w) => w.id === id);
      const maxZ = Math.max(...windows.map((w) => w.zIndex));
      if (win && win.zIndex === maxZ) {
        minimizeWindow(id);
      } else {
        focusWindow(id);
      }
    }
  };

  return (
    <div className="flex h-11 shrink-0 items-center justify-between border-t px-1.5 backdrop-blur-xl"
      style={{ backgroundColor: "var(--ls-taskbar)", borderColor: "var(--ls-border)" }}>
      {/* Start Menu + Accesos directos */}
      <div className="flex items-center gap-1">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex h-8 items-center gap-2 rounded-md px-3 text-sm font-semibold ls-text transition hover:ls-bg-input">
            <Home className="h-4 w-4" style={{ color: "var(--ls-accent)" }} />
            <span>LabSim</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" side="top" className="mb-1 w-64 max-h-[70vh] overflow-y-auto ls-border ls-bg-panel ls-text">
            {/* User */}
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/20">
                <User className="h-4 w-4 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium">{username}</p>
                <p className="text-xs ls-text-muted capitalize">{role}</p>
              </div>
            </div>
            <DropdownMenuSeparator className="ls-bg-input" />

            {/* Equipos */}
            <p className="px-3 pt-1.5 pb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Equipos</p>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="ls-text2 focus:ls-bg-input focus:ls-text">
                <Headphones className="mr-2 h-4 w-4 text-blue-400" />Audiología
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="ls-border ls-bg-panel ls-text">
                <DropdownMenuItem onClick={() => openWindow("audiometer", "Audiómetro", "audiometer", WINDOW_SIZES.audiometer)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Headphones className="mr-2 h-4 w-4 text-blue-400" />Audiómetro
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("impedance", "Impedanciómetro", "impedance", WINDOW_SIZES.impedance)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Activity className="mr-2 h-4 w-4 text-emerald-400" />Impedanciómetro
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="ls-text2 focus:ls-bg-input focus:ls-text">
                <Eye className="mr-2 h-4 w-4 text-red-400" />Oftalmología
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="ls-border ls-bg-panel ls-text">
                <DropdownMenuItem onClick={() => openWindow("perimetry", "Campo Visual", "perimetry", WINDOW_SIZES.perimetry)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <ScanEye className="mr-2 h-4 w-4 text-orange-400" />Campo Visual
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("oct", "OCT", "oct", WINDOW_SIZES.oct)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Layers className="mr-2 h-4 w-4 text-pink-400" />OCT
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("retinography", "Retinógrafo", "retinography", WINDOW_SIZES.retinography)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Eye className="mr-2 h-4 w-4 text-red-400" />Retinógrafo
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("corneal-topography", "Topógrafo Corneal", "corneal-topography", WINDOW_SIZES["corneal-topography"])} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <CircleDot className="mr-2 h-4 w-4 text-teal-400" />Topógrafo Corneal
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("scheimpflug", "Scheimpflug", "scheimpflug", WINDOW_SIZES.scheimpflug)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Scan className="mr-2 h-4 w-4 text-teal-400" />Scheimpflug
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("autoref", "Autorefractómetro", "autoref", WINDOW_SIZES.autoref)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <ScanEye className="mr-2 h-4 w-4 text-cyan-400" />Autorefractómetro
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="ls-text2 focus:ls-bg-input focus:ls-text">
                <Activity className="mr-2 h-4 w-4 text-violet-400" />Otoneurología
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="ls-border ls-bg-panel ls-text">
                <DropdownMenuItem onClick={() => openWindow("vng", "VNG", "vng", WINDOW_SIZES.vng)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Eye className="mr-2 h-4 w-4 text-violet-400" />VNG
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("vhit", "vHIT", "vhit", WINDOW_SIZES.vhit)} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Activity className="mr-2 h-4 w-4 text-orange-400" />vHIT
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>

            <DropdownMenuSeparator className="ls-bg-input" />

            {/* Clínica */}
            <p className="px-3 pt-1.5 pb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Clínica</p>
            <DropdownMenuItem onClick={() => openWindow("larissa", "Larissa", "larissa")} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <ClipboardPen className="mr-2 h-4 w-4 text-cyan-400" />Larissa
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openWindow("agenda", "Agenda", "agenda", WINDOW_SIZES.agenda)} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <CalendarDays className="mr-2 h-4 w-4 text-amber-400" />Agenda
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openWindow("messaging", "Mensajes", "messaging", WINDOW_SIZES.messaging)} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <MessageCircle className="mr-2 h-4 w-4 text-green-400" />Mensajes
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openWindow("my-stats", "Mis Estadísticas", "my-stats")} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <BarChart3 className="mr-2 h-4 w-4 text-teal-400" />Mis Estadísticas
            </DropdownMenuItem>
            <DropdownMenuSeparator className="ls-bg-input" />

            {/* Gestión (solo staff) */}
            {(role === "admin" || role === "docente" || role === "instructor") && (
              <>
                <p className="px-3 pt-1.5 pb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Gestión</p>
                <DropdownMenuItem onClick={() => openWindow("center", "Centro", "center")} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Building2 className="mr-2 h-4 w-4 text-amber-400" />Centro
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("practice-sessions", "Sesiones", "practice-sessions")} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <ClipboardList className="mr-2 h-4 w-4 text-sky-400" />Sesiones
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("courses", "Mis Cursos", "courses")} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <GraduationCap className="mr-2 h-4 w-4 text-sky-400" />Mis Cursos
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("supervision", "Supervisión", "supervision")} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <ShieldCheck className="mr-2 h-4 w-4 text-indigo-400" />Supervisión
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => openWindow("manage-patients", "Gestionar Pacientes", "manage-patients")} className="ls-text2 focus:ls-bg-input focus:ls-text">
                  <Users className="mr-2 h-4 w-4 text-purple-400" />Gestionar Pacientes
                </DropdownMenuItem>
                {(role === "admin" || role === "docente") && (
                  <>
                    <DropdownMenuItem onClick={() => openWindow("karime-config", "Configurar Karime", "karime-config", WINDOW_SIZES["karime-config"])} className="ls-text2 focus:ls-bg-input focus:ls-text">
                      <BotMessageSquare className="mr-2 h-4 w-4 text-rose-400" />Configurar Karime
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => openWindow("kb-editor", "Base de Conocimiento", "kb-editor", WINDOW_SIZES["kb-editor"])} className="ls-text2 focus:ls-bg-input focus:ls-text">
                      <BookOpen className="mr-2 h-4 w-4 text-blue-400" />Base de Conocimiento
                    </DropdownMenuItem>
                  </>
                )}
                <DropdownMenuSeparator className="ls-bg-input" />
              </>
            )}

            {/* Sistema */}
            <p className="px-3 pt-1.5 pb-0.5 text-xs font-bold uppercase tracking-wider ls-text-muted">Sistema</p>
            <DropdownMenuItem onClick={() => openWindow("settings", "Configuración", "settings", WINDOW_SIZES.settings)} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <Settings className="mr-2 h-4 w-4 ls-text-muted" />Configuración
            </DropdownMenuItem>
            <DropdownMenuSeparator className="ls-bg-input" />

            <DropdownMenuItem onClick={handleLogout} className="ls-text2 focus:ls-bg-input focus:ls-text">
              <LogOut className="mr-2 h-4 w-4" />Cerrar Sesión
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { if (window.confirm("¿Salir de LabSim?")) window.close(); }} className="text-red-400 focus:bg-red-500/10 focus:text-red-300">
              <Power className="mr-2 h-4 w-4" />Apagar LabSim
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="mx-0.5 h-5 w-px ls-bg-input" />

        {/* Accesos directos: Chat y Agenda */}
        <Tooltip>
          <TooltipTrigger
            onClick={() => openWindow("messaging", "Mensajes", "messaging", WINDOW_SIZES.messaging)}
            className="relative rounded p-1.5 transition hover:ls-bg-input"
          >
            <MessageCircle className={`h-4 w-4 ${totalUnread > 0 ? "text-green-300 animate-pulse" : "text-green-400"}`} />
            {totalUnread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-0.5 text-[10px] font-bold text-white">
                {totalUnread > 9 ? "9+" : totalUnread}
              </span>
            )}
          </TooltipTrigger>
          <TooltipContent side="top">
            {totalUnread > 0 ? `Mensajes (${totalUnread} sin leer)` : "Mensajes"}
          </TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger
            onClick={() => openWindow("agenda", "Agenda", "agenda", WINDOW_SIZES.agenda)}
            className="rounded p-1.5 transition hover:ls-bg-input"
          >
            <CalendarDays className="h-4 w-4 text-amber-400" />
          </TooltipTrigger>
          <TooltipContent side="top">Agenda</TooltipContent>
        </Tooltip>
      </div>

      {/* Window buttons */}
      <div className="flex flex-1 items-center gap-0.5 overflow-x-auto px-2">
        {windows.map((w) => {
          const Icon = WINDOW_ICONS[w.component] ?? FileText;
          const maxZ = Math.max(...windows.map((x) => x.zIndex));
          const isFocused = !w.minimized && w.zIndex === maxZ;
          return (
            <button
              key={w.id}
              onClick={() => handleTaskbarClick(w.id, w.minimized)}
              className={`flex h-7 items-center gap-1.5 rounded-md px-2 text-xs transition ${
                w.minimized
                  ? "ls-text-muted hover:ls-bg-input"
                  : isFocused
                    ? "ls-bg-input ls-text"
                    : "ls-text2 hover:ls-bg-input"
              }`}
              style={isFocused ? { borderBottom: "2px solid var(--ls-accent)" } : undefined}
            >
              <Icon className="h-3.5 w-3.5 shrink-0" />
              <span className="max-w-20 truncate">{w.title}</span>
            </button>
          );
        })}
      </div>

      {/* System Tray */}
      <div className="flex items-center gap-2 px-2">
        <Tooltip>
          <TooltipTrigger className="cursor-default" onClick={() => checkConnection()}>
            <Wifi className={`h-3.5 w-3.5 ${
              isOnline === "online" ? "text-green-400" :
              isOnline === "checking" ? "text-yellow-400 animate-pulse" :
              "text-red-400"
            }`} />
          </TooltipTrigger>
          <TooltipContent side="top">
            {isOnline === "online" ? "Servidor conectado" :
             isOnline === "checking" ? "Verificando conexión..." :
             "Sin conexión al servidor"}
          </TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger className="cursor-default">
            <Volume2 className="h-3.5 w-3.5 ls-text-muted" />
          </TooltipTrigger>
          <TooltipContent side="top">Audio activo</TooltipContent>
        </Tooltip>

        <div className="ml-1 flex flex-col items-end text-right">
          <span className="text-xs font-medium leading-tight ls-text2">
            {time.toLocaleTimeString("es", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          <span className="text-[10px] leading-tight ls-text-muted">
            {time.toLocaleDateString("es", {
              day: "2-digit",
              month: "short",
            })}
          </span>
        </div>
      </div>
    </div>
  );
}
