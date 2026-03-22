import { useEffect, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import "@/stores/theme-store";
import { DesktopArea } from "@/components/layout/desktop-area";
import { Taskbar } from "@/components/layout/taskbar";
import { WindowFrame } from "@/components/layout/window-frame";
import { WindowContent } from "@/components/windows/window-content";
import { DesktopContextMenu } from "@/components/layout/desktop-context-menu";

export default function DesktopPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const windows = useUIStore((s) => s.windows);
  const closeWindow = useUIStore((s) => s.closeWindow);
  const focusWindow = useUIStore((s) => s.focusWindow);

  useEffect(() => {
    if (!isAuthenticated) navigate({ to: "/login" });
  }, [isAuthenticated, navigate]);

  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    // Solo en el fondo del escritorio, no en ventanas ni taskbar
    const target = e.target as HTMLElement;
    if (target.closest("[data-window-frame]") || target.closest("[data-slot='dropdown-menu']")) return;
    e.preventDefault();
    window.dispatchEvent(new CustomEvent("desktop-contextmenu", { detail: { x: e.clientX, y: e.clientY } }));
  }, []);

  if (!isAuthenticated) return null;

  return (
    <div className="relative flex h-full flex-col overflow-hidden"
      style={{ background: "var(--ls-desktop-gradient)" }}
      onContextMenu={handleContextMenu}>
      <div className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{ backgroundImage: "radial-gradient(circle at 1px 1px, var(--ls-text-muted) 0.5px, transparent 0)", backgroundSize: "24px 24px" }} />

      <div className="relative flex-1 overflow-hidden">
        <DesktopArea className="relative z-0" />
        {windows.map((w) =>
          w.minimized ? null : (
            <WindowFrame key={w.id} id={w.id} title={w.title}
              initialX={w.x} initialY={w.y} initialWidth={w.width} initialHeight={w.height}
              zIndex={w.zIndex} onClose={() => closeWindow(w.id)} onFocus={() => focusWindow(w.id)}>
              <WindowContent component={w.component} />
            </WindowFrame>
          ),
        )}
      </div>
      <Taskbar />
      <DesktopContextMenu />
    </div>
  );
}
