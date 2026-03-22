import { useEffect, useState, useCallback, useRef } from "react";
import { useUIStore } from "@/stores/ui-store";
import { useChatStore } from "@/stores/chat-store";
import { useSyncStore } from "@/stores/sync-store";
import { invoke } from "@tauri-apps/api/core";
import { WINDOW_SIZES } from "./desktop-area";
import {
  Palette,
  Settings,
  BrainCircuit,
  Mic,
  Volume2,
  RefreshCw,
  Info,
} from "lucide-react";

interface MenuPos {
  x: number;
  y: number;
}

export function DesktopContextMenu() {
  const [pos, setPos] = useState<MenuPos | null>(null);
  const [adjusted, setAdjusted] = useState<MenuPos | null>(null);
  const [speechReady, setSpeechReady] = useState(false);
  const [ttsReady, setTtsReady] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const openWindow = useUIStore((s) => s.openWindow);
  const setSettingsPage = useUIStore((s) => s.setSettingsPage);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const checkConnection = useSyncStore((s) => s.checkConnection);

  const close = useCallback(() => { setPos(null); setAdjusted(null); }, []);

  // Ajustar posición si queda fuera de la pantalla
  useEffect(() => {
    if (!pos || !menuRef.current) return;
    const rect = menuRef.current.getBoundingClientRect();
    let { x, y } = pos;
    if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 8;
    if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 8;
    if (x < 0) x = 8;
    if (y < 0) y = 8;
    setAdjusted({ x, y });
  }, [pos]);

  // Cerrar con click o Escape
  useEffect(() => {
    if (!pos) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    window.addEventListener("click", close);
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("click", close);
      window.removeEventListener("keydown", handleKey);
    };
  }, [pos, close]);

  // Escuchar evento custom desde desktop.tsx
  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent<MenuPos>;
      invoke<boolean>("speech_status").then(setSpeechReady).catch(() => {});
      invoke<boolean>("tts_status").then(setTtsReady).catch(() => {});
      setPos(ce.detail);
    };
    window.addEventListener("desktop-contextmenu", handler);
    return () => window.removeEventListener("desktop-contextmenu", handler);
  }, []);

  if (!pos) return null;

  const openSettings = (page: string) => {
    setSettingsPage(page);
    openWindow("settings", "Configuración", "settings", WINDOW_SIZES.settings);
    close();
  };

  const showIaItems = !llmConnected || !speechReady || !ttsReady;
  const finalPos = adjusted ?? pos;

  return (
    <div
      ref={menuRef}
      className="fixed z-[9999] min-w-[220px] rounded-lg border p-1 shadow-xl backdrop-blur-xl"
      style={{
        left: finalPos.x,
        top: finalPos.y,
        backgroundColor: "var(--ls-panel)",
        borderColor: "var(--ls-border)",
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <MenuItem icon={<Palette className="h-4 w-4 text-purple-400" />} label="Personalizar escritorio" onClick={() => openSettings("apariencia")} />

      <Separator />

      {showIaItems && (
        <>
          {!llmConnected && (
            <MenuItem icon={<BrainCircuit className="h-4 w-4 text-amber-400" />} label="Instalar IA (LLM)" onClick={() => openSettings("ia")} />
          )}
          {!speechReady && (
            <MenuItem icon={<Mic className="h-4 w-4 text-sky-400" />} label="Instalar Reconocimiento de Voz" onClick={() => openSettings("voz")} />
          )}
          {!ttsReady && (
            <MenuItem icon={<Volume2 className="h-4 w-4 text-emerald-400" />} label="Instalar Síntesis de Voz" onClick={() => openSettings("tts")} />
          )}
          <Separator />
        </>
      )}

      <MenuItem
        icon={<RefreshCw className="h-4 w-4 ls-text-muted" />}
        label="Actualizar conexión"
        onClick={() => { checkConnection(); close(); }}
      />
      <MenuItem icon={<Settings className="h-4 w-4 ls-text-muted" />} label="Configuración" onClick={() => openSettings("apariencia")} />

      <Separator />

      <MenuItem icon={<Info className="h-4 w-4 ls-text-muted" />} label="Acerca de LabSim" onClick={() => openSettings("acerca")} />
    </div>
  );
}

function MenuItem({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition hover:ls-bg-input"
      style={{ color: "var(--ls-text)" }}
    >
      {icon}
      {label}
    </button>
  );
}

function Separator() {
  return <div className="my-1 h-px" style={{ backgroundColor: "var(--ls-border)" }} />;
}
