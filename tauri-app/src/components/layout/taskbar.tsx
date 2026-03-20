import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import { useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Headphones,
  LogOut,
  Settings,
  User,
  Wifi,
  Volume2,
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function Taskbar() {
  const navigate = useNavigate();
  const username = useAuthStore((s) => s.username);
  const logout = useAuthStore((s) => s.logout);
  const windows = useUIStore((s) => s.windows);
  const focusWindow = useUIStore((s) => s.focusWindow);
  const restoreWindow = useUIStore((s) => s.restoreWindow);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate({ to: "/login" });
  };

  const handleTaskbarClick = (id: string, minimized: boolean) => {
    if (minimized) {
      restoreWindow(id);
    } else {
      focusWindow(id);
    }
  };

  return (
    <div className="flex h-11 shrink-0 items-center justify-between border-t border-white/5 bg-slate-900/95 px-1.5 backdrop-blur-xl">
      {/* Start Menu */}
      <DropdownMenu>
        <DropdownMenuTrigger className="flex h-8 items-center gap-2 rounded-md px-3 text-sm font-semibold text-white transition hover:bg-white/10">
          <Headphones className="h-4 w-4 text-blue-400" />
          <span>LabSim</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          side="top"
          className="mb-1 w-56 border-white/10 bg-slate-900 text-white"
        >
          <div className="flex items-center gap-2 px-2 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/20">
              <User className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium">{username}</p>
              <p className="text-xs text-white/40">Audiología</p>
            </div>
          </div>
          <DropdownMenuSeparator className="bg-white/10" />
          <DropdownMenuItem className="text-white/70 focus:bg-white/10 focus:text-white">
            <Settings className="mr-2 h-4 w-4" />
            Configuración
          </DropdownMenuItem>
          <DropdownMenuSeparator className="bg-white/10" />
          <DropdownMenuItem
            onClick={handleLogout}
            className="text-red-400 focus:bg-red-500/10 focus:text-red-300"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Cerrar Sesión
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Window buttons */}
      <div className="flex flex-1 items-center gap-0.5 overflow-x-auto px-2">
        {windows.map((w) => (
          <button
            key={w.id}
            onClick={() => handleTaskbarClick(w.id, w.minimized)}
            className={`flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs transition ${
              w.minimized
                ? "text-white/40 hover:bg-white/5 hover:text-white/70"
                : "bg-white/10 text-white/90"
            }`}
          >
            <div className="h-1.5 w-1.5 rounded-full bg-blue-400" />
            <span className="max-w-24 truncate">{w.title}</span>
          </button>
        ))}
      </div>

      {/* System Tray */}
      <div className="flex items-center gap-2 px-2">
        <Tooltip>
          <TooltipTrigger className="cursor-default">
            <Wifi className="h-3.5 w-3.5 text-white/40" />
          </TooltipTrigger>
          <TooltipContent side="top">Conectado</TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger className="cursor-default">
            <Volume2 className="h-3.5 w-3.5 text-white/40" />
          </TooltipTrigger>
          <TooltipContent side="top">Audio activo</TooltipContent>
        </Tooltip>

        <div className="ml-1 flex flex-col items-end text-right">
          <span className="text-xs font-medium leading-tight text-white/70">
            {time.toLocaleTimeString("es", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          <span className="text-[10px] leading-tight text-white/40">
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
