import { useState, useCallback, useRef, useEffect } from "react";
import { useChatStore, nextMsgId, timeNow, type Contact } from "@/stores/chat-store";
import { ChatBubble, type ChatMessage as ChatBubbleMsg } from "@/components/chat/chat-bubble";
import { ChatInput } from "@/components/chat/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import {
  ArrowLeft,
  Circle,
  Settings,
  Wifi,
  WifiOff,
  Download,
  Loader2,
  Check,
  BrainCircuit,
  ChevronLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface ModelInfo {
  id: string;
  name: string;
  sizeMb: number;
  filename: string;
}

// Fallback responses when LLM is not connected
const FALLBACK: Record<string, string[]> = {
  karime: [
    "Buenos días doc! ¿En qué le puedo ayudar?",
    "El siguiente paciente ya está en sala de espera",
    "Anotado doc, me encargo de eso 📝",
    "La paciente pregunta cuánto falta para que la atiendan",
    "Le dejé los formularios en el escritorio",
    "Perfecto, le aviso al paciente entonces",
    "Uy doc, va un poco atrasado... 😬",
  ],
  docente: [
    "Buena pregunta. ¿Podrías ser más específico sobre qué aspecto te gustaría profundizar?",
    "Para responder de forma detallada, necesitaría conectarme con el modelo de IA. Ve a configuración para activar llama-server.",
    "Te recomiendo revisar el material sobre este tema. Cuando el LLM esté activo, puedo darte explicaciones más completas.",
  ],
};

function pickFallback(personaId: string): string {
  const arr = FALLBACK[personaId] ?? FALLBACK.karime;
  return arr[Math.floor(Math.random() * arr.length)];
}

function ContactList() {
  const contacts = useChatStore((s) => s.contacts);
  const unreadCounts = useChatStore((s) => s.unreadCounts);
  const conversations = useChatStore((s) => s.conversations);
  const setActiveContact = useChatStore((s) => s.setActiveContact);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const [showSettings, setShowSettings] = useState(false);

  const getLastMessage = (id: string): string => {
    const msgs = conversations[id];
    if (!msgs?.length) return "Sin mensajes";
    const last = msgs[msgs.length - 1];
    const prefix = last.sender === "user" ? "Tú: " : "";
    const text = last.text.length > 40 ? last.text.slice(0, 40) + "..." : last.text;
    return prefix + text;
  };

  const getLastTime = (id: string): string => {
    const msgs = conversations[id];
    if (!msgs?.length) return "";
    return msgs[msgs.length - 1].time;
  };

  if (showSettings) {
    return <LlmSettingsPanel onBack={() => setShowSettings(false)} />;
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 bg-slate-900 px-4 py-3">
        <h3 className="text-sm font-semibold text-white">Mensajes</h3>
        <div className="flex items-center gap-2">
          {llmConnected ? (
            <Wifi className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <WifiOff className="h-3.5 w-3.5 text-white/20" />
          )}
          <button
            onClick={() => setShowSettings(true)}
            className="rounded p-1 text-white/30 transition hover:bg-white/5 hover:text-white/60"
            title="Configurar IA"
          >
            <Settings className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* LLM status banner */}
      {!llmConnected && (
        <button
          onClick={() => setShowSettings(true)}
          className="flex items-center gap-2 border-b border-amber-500/10 bg-amber-500/5 px-4 py-2 text-left transition hover:bg-amber-500/10"
        >
          <BrainCircuit className="h-4 w-4 shrink-0 text-amber-400" />
          <span className="text-xs text-amber-300/80">
            IA desactivada — toca para configurar modelo
          </span>
        </button>
      )}

      {/* Contact list */}
      <ScrollArea className="flex-1">
        {contacts.map((contact) => {
          const unread = unreadCounts[contact.id] ?? 0;
          return (
            <button
              key={contact.id}
              onClick={() => setActiveContact(contact.id)}
              className="flex w-full items-center gap-3 border-b border-white/[0.03] px-4 py-3 text-left transition hover:bg-white/5"
            >
              <div className="relative shrink-0">
                <div
                  className={cn(
                    "flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br text-sm font-bold text-white",
                    contact.color,
                  )}
                >
                  {contact.avatar}
                </div>
                {contact.online && (
                  <Circle className="absolute -right-0.5 -bottom-0.5 h-3.5 w-3.5 fill-emerald-400 stroke-slate-800 stroke-2" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">
                    {contact.name}
                  </span>
                  <span className="text-[10px] text-white/30">
                    {getLastTime(contact.id)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="truncate text-xs text-white/40">
                    {getLastMessage(contact.id)}
                  </p>
                  {unread > 0 && (
                    <Badge className="h-5 min-w-5 justify-center bg-emerald-500 px-1.5 text-[10px] text-white">
                      {unread}
                    </Badge>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </ScrollArea>
    </div>
  );
}

function LlmSettingsPanel({ onBack }: { onBack: () => void }) {
  const llmConnected = useChatStore((s) => s.llmConnected);
  const setLlmConnected = useChatStore((s) => s.setLlmConnected);
  const setLastModel = useChatStore((s) => s.setLastModel);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [phase, setPhase] = useState<"idle" | "downloading" | "loading" | "ready">(
    llmConnected ? "ready" : "idle",
  );
  const [progress, setProgress] = useState(0);
  const [downloadInfo, setDownloadInfo] = useState("");

  // Load available models
  useEffect(() => {
    invoke<ModelInfo[]>("llm_list_models").then(setModels).catch(() => {});
  }, []);

  // Listen for download progress events
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    listen<{ status: string; filename: string; progress: number }>(
      "llm-download-progress",
      (event) => {
        setProgress(event.payload.progress);
        setDownloadInfo(event.payload.filename);
      },
    ).then((fn) => {
      unlisten = fn;
    });
    return () => unlisten?.();
  }, []);

  const handleDownloadAndLoad = async (model: ModelInfo) => {
    setSelectedModel(model.id);

    // Phase 1: Download
    setPhase("downloading");
    setProgress(0);
    setDownloadInfo(`${model.filename} (${model.sizeMb} MB)`);

    // Simulate progress since hf-hub doesn't give us granular progress
    const progressInterval = setInterval(() => {
      setProgress((p) => {
        if (p >= 95) return 95;
        // Estimate: ~2MB/s on average connection
        const increment = (2 / model.sizeMb) * 100;
        return Math.min(95, p + increment);
      });
    }, 1000);

    try {
      const modelPath = await invoke<string>("llm_download_model", {
        modelId: model.id,
        filename: model.filename,
      });

      clearInterval(progressInterval);
      setProgress(100);

      // Phase 2: Load
      setPhase("loading");
      setDownloadInfo("Cargando modelo en memoria...");

      await invoke<boolean>("llm_load_model_async", { path: modelPath });

      setPhase("ready");
      setLlmConnected(true);
      setLastModel(model.id, model.filename);
      toast.success(`${model.name} — IA lista`);
    } catch (err) {
      clearInterval(progressInterval);
      setPhase("idle");
      setProgress(0);
      toast.error(`Error: ${err}`);
    }
  };

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/5 bg-slate-900 px-3 py-3">
        <button
          onClick={onBack}
          className="rounded p-1 text-white/40 transition hover:bg-white/5 hover:text-white"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <BrainCircuit className="h-4 w-4 text-violet-400" />
        <h3 className="text-sm font-semibold text-white">Configurar IA</h3>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">
          {/* Status */}
          <div
            className={cn(
              "flex items-center gap-2 rounded-lg p-3",
              phase === "ready"
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-white/5 text-white/50",
            )}
          >
            {phase === "ready" ? (
              <Check className="h-4 w-4" />
            ) : (
              <WifiOff className="h-4 w-4" />
            )}
            <span className="text-xs font-medium">
              {phase === "ready"
                ? "IA activa — respuestas inteligentes habilitadas"
                : "IA desactivada — selecciona un modelo para activar"}
            </span>
          </div>

          {/* Download progress */}
          {(phase === "downloading" || phase === "loading") && (
            <div className="space-y-2 rounded-lg border border-violet-500/20 bg-violet-500/5 p-4">
              <div className="flex items-center gap-2">
                {phase === "downloading" ? (
                  <Download className="h-4 w-4 animate-bounce text-violet-400" />
                ) : (
                  <Loader2 className="h-4 w-4 animate-spin text-violet-400" />
                )}
                <span className="text-sm font-medium text-white">
                  {phase === "downloading" ? "Descargando..." : "Cargando en memoria..."}
                </span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-[11px] text-white/40">{downloadInfo}</p>
              {phase === "downloading" && (
                <p className="text-[10px] text-white/30">
                  {progress < 100
                    ? `${Math.round(progress)}% — primera descarga, luego se cachea`
                    : "Descarga completa"}
                </p>
              )}
            </div>
          )}

          {/* Model selector */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium tracking-wider text-white/40 uppercase">
              Modelos disponibles
            </h4>
            {models.map((model) => {
              const isSelected = selectedModel === model.id;
              const isActive = phase === "ready" && isSelected;
              const isBusy = (phase === "downloading" || phase === "loading") && isSelected;

              return (
                <button
                  key={model.id}
                  disabled={isBusy || phase === "loading"}
                  onClick={() => handleDownloadAndLoad(model)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg border p-3 text-left transition",
                    isActive
                      ? "border-emerald-500/30 bg-emerald-500/5"
                      : isBusy
                        ? "border-violet-500/30 bg-violet-500/5"
                        : "border-white/5 bg-white/[0.02] hover:bg-white/5",
                  )}
                >
                  <div
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                      isActive
                        ? "bg-emerald-500/20"
                        : "bg-white/5",
                    )}
                  >
                    {isActive ? (
                      <Check className="h-5 w-5 text-emerald-400" />
                    ) : isBusy ? (
                      <Loader2 className="h-5 w-5 animate-spin text-violet-400" />
                    ) : (
                      <BrainCircuit className="h-5 w-5 text-white/30" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-white">{model.name}</p>
                    <p className="text-[11px] text-white/30">
                      {model.sizeMb} MB — {model.sizeMb < 700 ? "Rápido en CPU" : model.sizeMb < 1200 ? "Moderado" : "Más lento, mejor calidad"}
                    </p>
                  </div>
                  {!isActive && !isBusy && (
                    <Download className="h-4 w-4 shrink-0 text-white/20" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Info */}
          <div className="rounded-lg bg-white/[0.02] p-3 text-[11px] text-white/30">
            <p>Los modelos se descargan de HuggingFace y se guardan en caché local (~/.cache/huggingface/). Solo se descargan una vez.</p>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

function ConversationView({ contact }: { contact: Contact }) {
  const messages = useChatStore((s) => s.conversations[contact.id] ?? []);
  const addMessage = useChatStore((s) => s.addMessage);
  const setActiveContact = useChatStore((s) => s.setActiveContact);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const typingTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Auto-scroll
  const scrollToBottom = useCallback(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      const userMsg = {
        id: nextMsgId(),
        contactId: contact.id,
        sender: "user" as const,
        text,
        time: timeNow(),
        status: "read" as const,
      };
      addMessage(contact.id, userMsg);
      scrollToBottom();

      setTyping(true);

      if (typingTimeout.current) clearTimeout(typingTimeout.current);

      // Try LLM first, fallback to scripted
      let responseText: string;

      if (llmConnected) {
        try {
          // Build conversation history (last 10 messages for context)
          const history = [...messages.slice(-10), userMsg].map((m) => ({
            role: m.sender === "user" ? "user" : "assistant",
            content: m.text,
          }));

          responseText = await invoke<string>("llm_chat", {
            request: {
              personaId: contact.personaId,
              messages: history,
            },
          });
        } catch {
          responseText = pickFallback(contact.personaId);
        }
      } else {
        // Simulate delay for fallback
        await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));
        responseText = pickFallback(contact.personaId);
      }

      const botMsg = {
        id: nextMsgId(),
        contactId: contact.id,
        sender: "other" as const,
        text: responseText,
        time: timeNow(),
        status: "read" as const,
      };

      setTyping(false);
      addMessage(contact.id, botMsg);
      scrollToBottom();
    },
    [contact, messages, addMessage, llmConnected, scrollToBottom],
  );

  // Convert store messages to ChatBubble format
  const bubbleMessages: ChatBubbleMsg[] = messages.map((m) => ({
    id: m.id,
    sender: m.sender,
    text: m.text,
    time: m.time,
    status: m.status,
    senderName: m.sender === "other" ? contact.name : undefined,
    avatar: m.sender === "other" ? contact.avatar : undefined,
  }));

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/5 bg-slate-900/90 px-3 py-2">
        <button
          onClick={() => setActiveContact(null)}
          className="rounded p-1 text-white/40 transition hover:bg-white/5 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="relative">
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br text-xs font-bold text-white",
              contact.color,
            )}
          >
            {contact.avatar}
          </div>
          {contact.online && (
            <Circle className="absolute -right-0.5 -bottom-0.5 h-3 w-3 fill-emerald-400 stroke-slate-900 stroke-2" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white">{contact.name}</p>
          <p className="text-[10px] text-white/40">
            {typing ? "escribiendo..." : contact.subtitle}
          </p>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div
          className="space-y-3 p-4"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.015) 1px, transparent 0)",
            backgroundSize: "24px 24px",
          }}
        >
          {bubbleMessages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}

          {typing && (
            <div className="flex gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-xs font-bold text-white",
                  contact.color,
                )}
              >
                {contact.avatar}
              </div>
              <div className="rounded-2xl rounded-bl-md bg-slate-700 px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-white/40 [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-white/40 [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-white/40 [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        placeholder={`Escríbele a ${contact.name}...`}
      />
    </div>
  );
}

export function MessagingApp() {
  const activeContact = useChatStore((s) => s.activeContact);
  const contacts = useChatStore((s) => s.contacts);
  const llmConnected = useChatStore((s) => s.llmConnected);
  const lastModelId = useChatStore((s) => s.lastModelId);
  const lastModelFilename = useChatStore((s) => s.lastModelFilename);
  const setLlmConnected = useChatStore((s) => s.setLlmConnected);
  const autoLoadAttempted = useRef(false);

  // Auto-load last used model on mount
  useEffect(() => {
    if (llmConnected || autoLoadAttempted.current || !lastModelId || !lastModelFilename) return;
    autoLoadAttempted.current = true;

    (async () => {
      try {
        // Model should already be cached, so download is instant
        const modelPath = await invoke<string>("llm_download_model", {
          modelId: lastModelId,
          filename: lastModelFilename,
        });
        await invoke<boolean>("llm_load_model_async", { path: modelPath });
        setLlmConnected(true);
        toast.success("IA cargada automáticamente");
      } catch {
        // Silently fail - user can manually activate
      }
    })();
  }, [llmConnected, lastModelId, lastModelFilename, setLlmConnected]);

  const contact = contacts.find((c) => c.id === activeContact);

  if (contact) {
    return <ConversationView contact={contact} />;
  }

  return <ContactList />;
}
