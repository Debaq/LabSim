import { useState, useEffect } from "react";
import { useThemeStore, THEMES, type ThemeName } from "@/stores/theme-store";
import { useAuthStore } from "@/stores/auth-store";
import { useChatStore } from "@/stores/chat-store";
import { invoke } from "@tauri-apps/api/core";
import { cn } from "@/lib/utils";
import { Check, Palette, User, Info, BrainCircuit, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ModelInfo { id: string; name: string; sizeMb: number; filename: string; }

export function SettingsWindow() {
  const { theme, setTheme } = useThemeStore();
  const username = useAuthStore((s) => s.username);
  const role = useAuthStore((s) => s.role);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const setLlmConnected = useChatStore((s) => s.setLlmConnected);
  const setLastModel = useChatStore((s) => s.setLastModel);

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    invoke<ModelInfo[]>("llm_list_models").then(setModels).catch(() => {});
  }, []);

  const handleDownload = async (model: ModelInfo) => {
    setDownloading(true);
    setDownloadingId(model.id);
    toast.info(`Descargando ${model.name}...`);
    try {
      const path = await invoke<string>("llm_download_model", { modelId: model.id, filename: model.filename });
      toast.info("Cargando modelo en memoria...");
      await invoke<boolean>("llm_load_model_async", { path });
      setLlmConnected(true);
      setLastModel(model.id, model.filename);
      toast.success(`${model.name} — IA lista`);
    } catch (err) {
      toast.error(`Error: ${err}`);
    } finally {
      setDownloading(false);
      setDownloadingId(null);
    }
  };

  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      <div className="flex items-center gap-2 border-b px-4 py-3" style={{ borderColor: "var(--ls-border)" }}>
        <span className="text-sm font-semibold" style={{ color: "var(--ls-text)" }}>Configuración</span>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-5">

          {/* User */}
          <section>
            <SectionHeader icon={<User className="h-4 w-4 text-blue-400" />} title="Usuario" />
            <div className="rounded-lg border p-3" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/20 text-sm font-bold text-blue-400">
                  {username?.[0]?.toUpperCase() ?? "?"}
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>{username ?? "Sin sesión"}</p>
                  <p className="text-xs capitalize" style={{ color: "var(--ls-text-muted)" }}>{role}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Themes */}
          <section>
            <SectionHeader icon={<Palette className="h-4 w-4 text-purple-400" />} title="Tema" />
            <div className="grid grid-cols-1 gap-1.5">
              {(Object.entries(THEMES) as [ThemeName, (typeof THEMES)[ThemeName]][]).map(([key, t]) => {
                const active = theme === key;
                return (
                  <button key={key} onClick={() => setTheme(key)}
                    className={cn("flex items-center gap-3 rounded-lg border p-2.5 text-left transition",
                      active ? "border-blue-500/40" : "hover:opacity-80")}
                    style={{ borderColor: active ? undefined : "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
                    <div className="flex gap-px shrink-0 rounded overflow-hidden">
                      <div className="h-7 w-4" style={{ backgroundColor: t.vars["--ls-desktop-bg"] }} />
                      <div className="h-7 w-4" style={{ backgroundColor: t.vars["--ls-window-bg"] }} />
                      <div className="h-7 w-4" style={{ backgroundColor: t.vars["--ls-accent"] }} />
                      <div className="h-7 w-4" style={{ backgroundColor: t.vars["--ls-window-header"] }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold" style={{ color: active ? "var(--ls-accent)" : "var(--ls-text)" }}>{t.label}</p>
                      <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{t.desc}</p>
                    </div>
                    {active && <Check className="h-4 w-4 shrink-0 text-blue-400" />}
                  </button>
                );
              })}
            </div>
          </section>

          {/* LLM */}
          <section>
            <SectionHeader icon={<BrainCircuit className="h-4 w-4 text-violet-400" />} title="Modelo de IA" />
            <div className="rounded-lg border p-3 space-y-2" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              <div className="flex items-center gap-2 mb-2">
                <div className={cn("h-2.5 w-2.5 rounded-full", llmConnected ? "bg-emerald-400" : "bg-white/20")} />
                <span className="text-xs font-medium" style={{ color: llmConnected ? "#22c55e" : "var(--ls-text-muted)" }}>
                  {llmConnected ? "IA activa" : "IA desactivada"}
                </span>
              </div>

              {models.map((model) => {
                const isDownloading = downloadingId === model.id;
                return (
                  <button key={model.id} disabled={downloading} onClick={() => handleDownload(model)}
                    className="flex w-full items-center gap-2 rounded border p-2 text-left transition hover:opacity-80"
                    style={{ borderColor: "var(--ls-border)" }}>
                    {isDownloading ? <Loader2 className="h-4 w-4 shrink-0 animate-spin text-violet-400" />
                      : <Download className="h-4 w-4 shrink-0" style={{ color: "var(--ls-text-muted)" }} />}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium" style={{ color: "var(--ls-text)" }}>{model.name}</p>
                      <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{model.sizeMb} MB</p>
                    </div>
                  </button>
                );
              })}

              <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>
                Se descarga de HuggingFace (~1 vez). Se usa para Karime y el Docente.
              </p>
            </div>
          </section>

          {/* About */}
          <section>
            <SectionHeader icon={<Info className="h-4 w-4 text-amber-400" />} title="Acerca de" />
            <div className="rounded-lg border p-3 space-y-1" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              <p className="text-xs" style={{ color: "var(--ls-text)" }}><span className="font-semibold">LabSim</span> v3.0.0</p>
              <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>Simulador Audiológico Educativo</p>
              <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>Tauri + React + Rust + llama.cpp</p>
              <p className="text-xs pt-1" style={{ color: "var(--ls-text-muted)", opacity: 0.5 }}>Nicolás Quezada Quezada</p>
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      {icon}
      <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--ls-text-muted)" }}>{title}</h3>
    </div>
  );
}
