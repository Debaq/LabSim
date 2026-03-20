import { useThemeStore, THEMES, type ThemeName } from "@/stores/theme-store";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";
import { Check, Palette, User, Info, Volume2 } from "lucide-react";

export function SettingsWindow() {
  const { theme, setTheme } = useThemeStore();
  const username = useAuthStore((s) => s.username);
  const role = useAuthStore((s) => s.role);

  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--settings-bg, #1e293b)" }}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-3" style={{ borderColor: "var(--settings-border, rgba(255,255,255,0.06))" }}>
        <span className="text-sm font-semibold" style={{ color: "var(--settings-text, #e2e8f0)" }}>Configuración</span>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-6">

        {/* User info */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <User className="h-4 w-4 text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Usuario</h3>
          </div>
          <div className="rounded-lg border border-white/[0.06] bg-black/20 p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/20 text-sm font-bold text-blue-400">
                {username?.[0]?.toUpperCase() ?? "?"}
              </div>
              <div>
                <p className="text-sm font-medium text-white/80">{username ?? "Sin sesión"}</p>
                <p className="text-xs text-white/30 capitalize">{role}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Theme selector */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Palette className="h-4 w-4 text-purple-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Tema de Interfaz</h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {(Object.entries(THEMES) as [ThemeName, (typeof THEMES)[ThemeName]][]).map(([key, t]) => {
              const isActive = theme === key;
              return (
                <button
                  key={key}
                  onClick={() => setTheme(key)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg border p-3 text-left transition",
                    isActive
                      ? "border-blue-500/40 bg-blue-500/10"
                      : "border-white/[0.06] bg-black/10 hover:bg-white/[0.03]",
                  )}
                >
                  {/* Color preview swatches */}
                  <div className="flex gap-0.5 shrink-0">
                    <div className="h-8 w-5 rounded-l" style={{ backgroundColor: t.colors.bg }} />
                    <div className="h-8 w-5" style={{ backgroundColor: t.colors.bgSecondary }} />
                    <div className="h-8 w-5" style={{ backgroundColor: t.colors.accent }} />
                    <div className="h-8 w-5 rounded-r" style={{ backgroundColor: t.colors.headerBg }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={cn("text-sm font-medium", isActive ? "text-blue-400" : "text-white/70")}>
                      {t.label}
                    </p>
                    <p className="text-[10px] text-white/25">
                      {key === "dark" && "Tema por defecto, ideal para ambientes oscuros"}
                      {key === "light" && "Fondo claro, ideal para entornos clínicos bien iluminados"}
                      {key === "dracula" && "Púrpura y rosa, popular entre desarrolladores"}
                      {key === "clinical" && "Tonos azul-gris profesionales para uso clínico"}
                      {key === "solarized" && "Paleta Solarized, cómodo para sesiones largas"}
                    </p>
                  </div>
                  {isActive && <Check className="h-4 w-4 shrink-0 text-blue-400" />}
                </button>
              );
            })}
          </div>
        </section>

        {/* Audio */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Volume2 className="h-4 w-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Audio</h3>
          </div>
          <div className="rounded-lg border border-white/[0.06] bg-black/20 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/50">Sample rate</span>
              <span className="text-xs font-mono text-white/70">48000 Hz</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/50">Backend</span>
              <span className="text-xs font-mono text-white/70">cpal (ALSA)</span>
            </div>
          </div>
        </section>

        {/* About */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-amber-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Acerca de</h3>
          </div>
          <div className="rounded-lg border border-white/[0.06] bg-black/20 p-3 space-y-1 text-xs text-white/40">
            <p><span className="text-white/60 font-semibold">LabSim</span> v3.0.0</p>
            <p>Simulador Audiológico Educativo</p>
            <p>Tauri + React + Rust</p>
            <p className="text-white/20 pt-1">Nicolás Quezada Quezada</p>
          </div>
        </section>
      </div>
    </div>
  );
}
