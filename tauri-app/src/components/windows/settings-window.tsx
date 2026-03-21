import { useState, useEffect } from "react";
import { useThemeStore, THEMES, type ThemeName, type FontSize } from "@/stores/theme-store";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuthStore } from "@/stores/auth-store";
import { useChatStore } from "@/stores/chat-store";
import { invoke } from "@tauri-apps/api/core";
import { cn } from "@/lib/utils";
import { Check, Palette, User, Info, BrainCircuit, Download, Loader2, Type, Monitor, Mic, Maximize, Minimize } from "lucide-react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ModelInfo { id: string; name: string; sizeMb: number; filename: string; }

type SettingsPage = "apariencia" | "ia" | "voz" | "cuenta" | "acerca";

const PAGES: { id: SettingsPage; label: string; icon: React.ReactNode }[] = [
  { id: "apariencia", label: "Apariencia", icon: <Palette className="h-4 w-4" /> },
  { id: "ia", label: "Inteligencia Artificial", icon: <BrainCircuit className="h-4 w-4" /> },
  { id: "voz", label: "Reconocimiento de Voz", icon: <Mic className="h-4 w-4" /> },
  { id: "cuenta", label: "Cuenta", icon: <User className="h-4 w-4" /> },
  { id: "acerca", label: "Acerca de", icon: <Info className="h-4 w-4" /> },
];

export function SettingsWindow() {
  const { theme, setTheme, fontSize, setFontSize, wallpaperColor, setWallpaperColor, autoLoadLlm, setAutoLoadLlm, autoLoadSpeech, setAutoLoadSpeech } = useThemeStore();
  const username = useAuthStore((s) => s.username);
  const role = useAuthStore((s) => s.role);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const setLlmConnected = useChatStore((s) => s.setLlmConnected);
  const setLastModel = useChatStore((s) => s.setLastModel);
  const [page, setPage] = useState<SettingsPage>("apariencia");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [speechLoaded, setSpeechLoaded] = useState(false);
  const [speechLoading, setSpeechLoading] = useState(false);

  useEffect(() => { invoke<boolean>("speech_status").then(setSpeechLoaded).catch(() => {}); }, []);

  useEffect(() => { invoke<ModelInfo[]>("llm_list_models").then(setModels).catch(() => {}); }, []);

  const handleDownload = async (model: ModelInfo) => {
    setDownloading(true); setDownloadingId(model.id);
    toast.info(`Descargando ${model.name}...`);
    try {
      const path = await invoke<string>("llm_download_model", { modelId: model.id, filename: model.filename });
      toast.info("Cargando modelo en memoria...");
      await invoke<boolean>("llm_load_model_async", { path });
      setLlmConnected(true); setLastModel(model.id, model.filename);
      toast.success(`${model.name} — IA lista`);
    } catch (err) { toast.error(`Error: ${err}`); }
    finally { setDownloading(false); setDownloadingId(null); }
  };

  return (
    <div className="flex h-full" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      {/* Sidebar */}
      <div className="flex w-[160px] shrink-0 flex-col border-r" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)" }}>
        <div className="px-3 py-3">
          <p className="text-sm font-bold" style={{ color: "var(--ls-text)" }}>Configuración</p>
        </div>
        <nav className="flex-1 px-2 space-y-0.5">
          {PAGES.map((p) => (
            <button key={p.id} onClick={() => setPage(p.id)}
              className={cn("flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-xs font-medium transition",
                page === p.id ? "ls-bg-input" : "hover:ls-bg-input")}
              style={{ color: page === p.id ? "var(--ls-accent)" : "var(--ls-text-secondary)" }}>
              {p.icon}
              {p.label}
            </button>
          ))}
        </nav>
        {/* User at bottom */}
        <div className="border-t p-3 flex items-center gap-2" style={{ borderColor: "var(--ls-border)" }}>
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-400">
            {username?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium truncate" style={{ color: "var(--ls-text)" }}>{username}</p>
            <p className="text-[10px] capitalize" style={{ color: "var(--ls-text-muted)" }}>{role}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-5 space-y-5">
          {page === "apariencia" && <PageApariencia
            theme={theme} setTheme={setTheme}
            fontSize={fontSize} setFontSize={setFontSize}
            wallpaperColor={wallpaperColor} setWallpaperColor={setWallpaperColor} />}
          {page === "ia" && <PageIA
            models={models} llmConnected={llmConnected}
            downloading={downloading} downloadingId={downloadingId}
            onDownload={handleDownload}
            autoLoad={autoLoadLlm} setAutoLoad={setAutoLoadLlm} />}
          {page === "voz" && <PageVoz speechLoaded={speechLoaded} speechLoading={speechLoading}
            autoLoad={autoLoadSpeech} setAutoLoad={setAutoLoadSpeech}
            onLoad={async () => {
              setSpeechLoading(true);
              toast.info("Descargando Whisper tiny (75 MB)...");
              try {
                await invoke<boolean>("speech_load_model");
                setSpeechLoaded(true);
                toast.success("Reconocimiento de voz listo");
              } catch (err) { toast.error(`Error: ${err}`); }
              finally { setSpeechLoading(false); }
            }} />}
          {page === "cuenta" && <PageCuenta username={username} role={role} />}
          {page === "acerca" && <PageAcerca />}
        </div>
      </ScrollArea>
    </div>
  );
}

// === PAGES ===

function PageApariencia({ theme, setTheme, fontSize, setFontSize, wallpaperColor, setWallpaperColor }: {
  theme: ThemeName; setTheme: (t: ThemeName) => void;
  fontSize: FontSize; setFontSize: (s: FontSize) => void;
  wallpaperColor: string | null; setWallpaperColor: (c: string | null) => void;
}) {
  return (<>
    <PageTitle icon={<Palette className="h-5 w-5 text-purple-400" />} title="Apariencia" subtitle="Tema, fondo de escritorio y tamaño de texto" />

    {/* Theme */}
    <Card title="Tema de colores">
      <div className="space-y-1.5">
        {(Object.entries(THEMES) as [ThemeName, (typeof THEMES)[ThemeName]][]).map(([key, t]) => {
          const active = theme === key;
          return (
            <button key={key} onClick={() => setTheme(key)}
              className={cn("flex w-full items-center gap-3 rounded-lg border p-3 text-left transition",
                active ? "border-blue-500/40" : "hover:opacity-80")}
              style={{ borderColor: active ? undefined : "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              <div className="flex gap-px shrink-0 rounded overflow-hidden">
                <div className="h-8 w-5 rounded-l" style={{ backgroundColor: t.vars["--ls-desktop-bg"] }} />
                <div className="h-8 w-5" style={{ backgroundColor: t.vars["--ls-window-bg"] }} />
                <div className="h-8 w-5" style={{ backgroundColor: t.vars["--ls-accent"] }} />
                <div className="h-8 w-5 rounded-r" style={{ backgroundColor: t.vars["--ls-window-header"] }} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold" style={{ color: active ? "var(--ls-accent)" : "var(--ls-text)" }}>{t.label}</p>
                <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{t.desc}</p>
              </div>
              {active && <Check className="h-4 w-4 shrink-0 text-blue-400" />}
            </button>
          );
        })}
      </div>
    </Card>

    {/* Wallpaper */}
    <Card title="Fondo de escritorio">
      <div className="flex items-center gap-3">
        <input type="color"
          value={wallpaperColor ?? THEMES[theme].vars["--ls-desktop-bg"]}
          onChange={(e) => setWallpaperColor(e.target.value)}
          className="h-10 w-14 cursor-pointer rounded border-0 bg-transparent" />
        <div className="flex-1">
          <p className="text-sm" style={{ color: "var(--ls-text)" }}>Color personalizado</p>
          <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>
            {wallpaperColor ? wallpaperColor.toUpperCase() : "Usando color del tema"}
          </p>
        </div>
        {wallpaperColor && (
          <button onClick={() => setWallpaperColor(null)}
            className="rounded-md border px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
            style={{ borderColor: "var(--ls-border)", color: "var(--ls-text-secondary)" }}>
            Restablecer
          </button>
        )}
      </div>
    </Card>

    {/* Font size */}
    <Card title="Tamaño de texto">
      <div className="flex gap-2">
        {(["small", "medium", "large"] as FontSize[]).map((size) => {
          const labels: Record<FontSize, string> = { small: "Pequeño", medium: "Normal", large: "Grande" };
          const previewSizes: Record<FontSize, string> = { small: "text-sm", medium: "text-base", large: "text-lg" };
          const active = fontSize === size;
          return (
            <button key={size} onClick={() => setFontSize(size)}
              className={cn("flex-1 flex flex-col items-center gap-1.5 rounded-lg border p-3 transition",
                active ? "border-blue-500/40" : "hover:opacity-80")}
              style={{ borderColor: active ? undefined : "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              <span className={cn("font-bold", previewSizes[size])} style={{ color: active ? "var(--ls-accent)" : "var(--ls-text)" }}>Aa</span>
              <span className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{labels[size]}</span>
              {active && <Check className="h-3.5 w-3.5 text-blue-400" />}
            </button>
          );
        })}
      </div>
    </Card>

    {/* Fullscreen */}
    <FullscreenToggle />
  </>);
}

function FullscreenToggle() {
  const [isFullscreen, setIsFullscreen] = useState(true);

  useEffect(() => {
    getCurrentWindow().isFullscreen().then(setIsFullscreen).catch(() => {});
  }, []);

  const toggle = async () => {
    const win = getCurrentWindow();
    const next = !isFullscreen;
    await win.setFullscreen(next);
    setIsFullscreen(next);
  };

  return (
    <Card title="Pantalla">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isFullscreen ? <Maximize className="h-4 w-4" style={{ color: "var(--ls-accent)" }} /> : <Minimize className="h-4 w-4" style={{ color: "var(--ls-text-muted)" }} />}
          <div>
            <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>Pantalla completa</p>
            <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{isFullscreen ? "Activado — F11 para alternar" : "Desactivado"}</p>
          </div>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox checked={isFullscreen} onCheckedChange={() => toggle()} />
        </label>
      </div>
    </Card>
  );
}

function PageIA({ models, llmConnected, downloading, downloadingId, onDownload, autoLoad, setAutoLoad }: {
  models: ModelInfo[]; llmConnected: boolean; downloading: boolean; downloadingId: string | null;
  onDownload: (m: ModelInfo) => void; autoLoad: boolean; setAutoLoad: (v: boolean) => void;
}) {
  const [testPrompt, setTestPrompt] = useState("");
  const [testResult, setTestResult] = useState("");
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!testPrompt.trim()) return;
    setTesting(true); setTestResult("");
    try {
      const result = await invoke<string>("llm_chat", {
        request: { personaId: "docente", messages: [{ role: "user", content: testPrompt }] },
      });
      setTestResult(result);
    } catch (err) { setTestResult(`Error: ${err}`); }
    finally { setTesting(false); }
  };

  return (<>
    <PageTitle icon={<BrainCircuit className="h-5 w-5 text-violet-400" />} title="Inteligencia Artificial" subtitle="Modelo local para chat con Karime y el Docente" />

    <Card title="Estado">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn("h-3 w-3 rounded-full", llmConnected ? "bg-emerald-400" : "ls-bg-input")} />
          <span className="text-sm font-medium" style={{ color: llmConnected ? "#22c55e" : "var(--ls-text-muted)" }}>
            {llmConnected ? "Modelo activo" : "Sin modelo"}
          </span>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox checked={autoLoad} onCheckedChange={(v) => setAutoLoad(v === true)} />
          <span className="text-xs" style={{ color: "var(--ls-text-secondary)" }}>Cargar al iniciar</span>
        </label>
      </div>
    </Card>

    <Card title="Modelos disponibles">
      <div className="space-y-1.5">
        {models.map((model) => {
          const isDownloading = downloadingId === model.id;
          return (
            <button key={model.id} disabled={downloading} onClick={() => onDownload(model)}
              className="flex w-full items-center gap-3 rounded-lg border p-3 text-left transition hover:opacity-80"
              style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
              {isDownloading
                ? <Loader2 className="h-5 w-5 shrink-0 animate-spin text-violet-400" />
                : <Download className="h-5 w-5 shrink-0" style={{ color: "var(--ls-text-muted)" }} />}
              <div className="flex-1">
                <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>{model.name}</p>
                <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>
                  {model.sizeMb} MB · {model.sizeMb < 700 ? "Rápido en CPU" : model.sizeMb < 1200 ? "Moderado" : "Mejor calidad"}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </Card>

    {llmConnected && (
      <Card title="Probar modelo">
        <div className="space-y-2">
          <textarea value={testPrompt} onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Escribe algo para probar el modelo..."
            className="w-full rounded-lg border p-2 text-sm resize-none h-16 ls-bg-input ls-border ls-text"
            style={{ backgroundColor: "var(--ls-input)" }} />
          <button onClick={handleTest} disabled={testing || !testPrompt.trim()}
            className="rounded-lg border px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
            style={{ borderColor: "var(--ls-accent)", color: "var(--ls-accent)" }}>
            {testing ? "Generando..." : "Enviar"}
          </button>
          {testResult && (
            <div className="rounded-lg border p-3 text-sm whitespace-pre-wrap" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)", color: "var(--ls-text)" }}>
              {testResult}
            </div>
          )}
        </div>
      </Card>
    )}
  </>);
}

function PageVoz({ speechLoaded, speechLoading, onLoad, autoLoad, setAutoLoad }: {
  speechLoaded: boolean; speechLoading: boolean; onLoad: () => void;
  autoLoad: boolean; setAutoLoad: (v: boolean) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [transcribing, setTranscribing] = useState(false);

  const handleRecord = async () => {
    if (recording) {
      // Stop and transcribe
      try {
        await invoke("speech_stop_recording");
        setRecording(false);
        setTranscribing(true);
        const text = await invoke<string>("speech_transcribe", { language: "es" });
        setTranscription(text || "(silencio)");
      } catch (err) { setTranscription(`Error: ${err}`); }
      finally { setTranscribing(false); }
    } else {
      // Start recording
      setTranscription("");
      try {
        await invoke("speech_start_recording");
        setRecording(true);
      } catch (err) { setTranscription(`Error: ${err}`); }
    }
  };

  return (<>
    <PageTitle icon={<Mic className="h-5 w-5 text-rose-400" />} title="Reconocimiento de Voz" subtitle="Whisper para logoaudiometría y comandos de voz" />

    <Card title="Estado">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn("h-3 w-3 rounded-full", speechLoaded ? "bg-emerald-400" : "ls-bg-input")} />
          <span className="text-sm font-medium" style={{ color: speechLoaded ? "#22c55e" : "var(--ls-text-muted)" }}>
            {speechLoaded ? "Whisper activo" : "Sin modelo"}
          </span>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <Checkbox checked={autoLoad} onCheckedChange={(v) => setAutoLoad(v === true)} />
          <span className="text-xs" style={{ color: "var(--ls-text-secondary)" }}>Cargar al iniciar</span>
        </label>
      </div>
    </Card>

    <Card title="Modelo">
      <button disabled={speechLoading || speechLoaded} onClick={onLoad}
        className="flex w-full items-center gap-3 rounded-lg border p-3 text-left transition hover:opacity-80"
        style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
        {speechLoading
          ? <Loader2 className="h-5 w-5 shrink-0 animate-spin text-rose-400" />
          : speechLoaded
            ? <Check className="h-5 w-5 shrink-0 text-emerald-400" />
            : <Download className="h-5 w-5 shrink-0" style={{ color: "var(--ls-text-muted)" }} />}
        <div className="flex-1">
          <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>Whisper Tiny</p>
          <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>75 MB · Multiidioma · Rápido en CPU</p>
        </div>
      </button>
    </Card>

    {speechLoaded && (
      <Card title="Probar micrófono">
        <div className="space-y-3">
          <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>
            Presiona para grabar, habla, y presiona de nuevo para transcribir.
          </p>
          <button onClick={handleRecord} disabled={transcribing}
            className={cn("flex items-center justify-center gap-2 rounded-lg border w-full py-3 text-sm font-medium transition",
              recording ? "border-red-500/40 bg-red-500/10 text-red-400 animate-pulse" : "hover:opacity-80")}
            style={recording ? undefined : { borderColor: "var(--ls-accent)", color: "var(--ls-accent)" }}>
            <Mic className="h-4 w-4" />
            {transcribing ? "Transcribiendo..." : recording ? "Detener grabación" : "Grabar"}
          </button>
          {transcription && (
            <div className="rounded-lg border p-3 text-sm" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)", color: "var(--ls-text)" }}>
              <p className="text-xs mb-1 font-bold" style={{ color: "var(--ls-text-muted)" }}>Transcripción:</p>
              {transcription}
            </div>
          )}
        </div>
      </Card>
    )}

    <Card title="Usos">
      <div className="space-y-2 text-sm" style={{ color: "var(--ls-text-secondary)" }}>
        <div className="flex items-start gap-2">
          <span style={{ color: "var(--ls-accent)" }}>•</span>
          <span><b>Logoaudiometría:</b> reconoce palabras del paciente</span>
        </div>
        <div className="flex items-start gap-2">
          <span style={{ color: "var(--ls-accent)" }}>•</span>
          <span><b>Comandos:</b> "siguiente", "registrar", "sin respuesta"</span>
        </div>
        <div className="flex items-start gap-2">
          <span style={{ color: "var(--ls-accent)" }}>•</span>
          <span><b>Talkback:</b> detecta voz del audiólogo</span>
        </div>
      </div>
    </Card>
  </>);
}

function PageCuenta({ username, role }: { username: string | null; role: string }) {
  return (<>
    <PageTitle icon={<User className="h-5 w-5 text-blue-400" />} title="Cuenta" subtitle="Información del usuario actual" />
    <Card title="Perfil">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-500/20 text-lg font-bold text-blue-400">
          {username?.[0]?.toUpperCase() ?? "?"}
        </div>
        <div>
          <p className="text-base font-semibold" style={{ color: "var(--ls-text)" }}>{username ?? "Sin sesión"}</p>
          <p className="text-sm capitalize" style={{ color: "var(--ls-text-muted)" }}>{role}</p>
        </div>
      </div>
    </Card>
  </>);
}

function PageAcerca() {
  return (<>
    <PageTitle icon={<Monitor className="h-5 w-5 text-amber-400" />} title="Acerca de LabSim" subtitle="Información del sistema" />
    <Card title="Aplicación">
      <div className="space-y-2">
        <Row label="Nombre" value="LabSim" />
        <Row label="Versión" value="3.0.0" />
        <Row label="Framework" value="Tauri v2 + React 19" />
        <Row label="Backend" value="Rust" />
        <Row label="Audio" value="cpal (ALSA)" />
        <Row label="IA" value="llama.cpp (llama-cpp-2)" />
        <Row label="Autor" value="Nicolás Quezada Quezada" />
      </div>
    </Card>
  </>);
}

// === Shared Components ===

function PageTitle({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <div className="flex items-center gap-3 pb-2">
      {icon}
      <div>
        <h2 className="text-base font-bold" style={{ color: "var(--ls-text)" }}>{title}</h2>
        <p className="text-xs" style={{ color: "var(--ls-text-muted)" }}>{subtitle}</p>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border p-4" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel-secondary)" }}>
      <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--ls-text-muted)" }}>{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-sm" style={{ color: "var(--ls-text-muted)" }}>{label}</span>
      <span className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>{value}</span>
    </div>
  );
}
