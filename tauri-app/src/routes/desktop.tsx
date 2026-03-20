import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import { DesktopArea } from "@/components/layout/desktop-area";
import { Taskbar } from "@/components/layout/taskbar";
import { WindowFrame } from "@/components/layout/window-frame";
import { WindowContent } from "@/components/windows/window-content";

export default function DesktopPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const windows = useUIStore((s) => s.windows);
  const closeWindow = useUIStore((s) => s.closeWindow);
  const focusWindow = useUIStore((s) => s.focusWindow);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate({ to: "/login" });
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-gradient-to-br from-slate-800 via-blue-950 to-indigo-950">
      {/* Wallpaper pattern */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03]">
        <div
          className="h-full w-full"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
      </div>

      {/* Desktop area + Windows */}
      <div className="relative flex-1 overflow-hidden">
        <DesktopArea className="relative z-0" />

        {/* Window manager */}
        {windows.map((w) =>
          w.minimized ? null : (
            <WindowFrame
              key={w.id}
              id={w.id}
              title={w.title}
              initialX={w.x}
              initialY={w.y}
              initialWidth={w.width}
              initialHeight={w.height}
              zIndex={w.zIndex}
              onClose={() => closeWindow(w.id)}
              onFocus={() => focusWindow(w.id)}
            >
              <WindowContent component={w.component} />
            </WindowFrame>
          ),
        )}
      </div>

      {/* Taskbar */}
      <Taskbar />
    </div>
  );
}
