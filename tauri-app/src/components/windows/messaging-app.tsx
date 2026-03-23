import { useState, useCallback, useRef, useEffect } from "react";
import { useChatStore, nextMsgId, timeNow, getKarimeStatus, type Contact } from "@/stores/chat-store";
import { ChatBubble, type ChatMessage as ChatBubbleMsg } from "@/components/chat/chat-bubble";
import { ChatInput } from "@/components/chat/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { invoke } from "@tauri-apps/api/core";
import {
  ArrowLeft,
  Circle,
  Wifi,
  WifiOff,
  BrainCircuit,
} from "lucide-react";
import { toast } from "sonner";
import { ContactAvatar } from "@/components/chat/contact-avatar";
import { HelpBotView } from "@/components/chat/help-bot-view";

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

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b ls-border ls-bg-panel px-4 py-3">
        <h3 className="text-sm font-semibold ls-text">Mensajes</h3>
        <div className="flex items-center gap-1">
          {llmConnected ? (
            <Wifi className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <WifiOff className="h-3.5 w-3.5 ls-text-muted" />
          )}
        </div>
      </div>

      {/* LLM status banner */}
      {!llmConnected && (
        <div className="flex items-center gap-2 border-b border-amber-500/10 bg-amber-500/5 px-4 py-2">
          <BrainCircuit className="h-4 w-4 shrink-0 text-amber-400" />
          <span className="text-xs text-amber-300/80">
            IA desactivada — actívala en Configuración
          </span>
        </div>
      )}

      {/* Contact list */}
      <ScrollArea className="flex-1">
        {contacts.map((contact) => {
          const unread = unreadCounts[contact.id] ?? 0;
          return (
            <button
              key={contact.id}
              onClick={() => setActiveContact(contact.id)}
              className="flex w-full items-center gap-3 border-b border-white/[0.03] px-4 py-3 text-left transition hover:ls-bg-input"
            >
              <div className="relative shrink-0">
                <ContactAvatar avatar={contact.avatar} color={contact.color} size="lg" />
                {contact.online && (
                  <Circle className="absolute -right-0.5 -bottom-0.5 h-3.5 w-3.5 fill-emerald-400 stroke-slate-800 stroke-2" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium ls-text">
                    {contact.name}
                  </span>
                  <span className="text-xs ls-text-muted">
                    {getLastTime(contact.id)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="truncate text-xs ls-text-muted">
                    {getLastMessage(contact.id)}
                  </p>
                  {unread > 0 && (
                    <Badge className="h-5 min-w-5 justify-center bg-emerald-500 px-1.5 text-xs ls-text">
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
    async (text: string, voiceInfo?: { isVoice: boolean; durationSecs: number }) => {
      const userMsg = {
        id: nextMsgId(),
        contactId: contact.id,
        sender: "user" as const,
        text,
        time: timeNow(),
        status: "read" as const,
        ...(voiceInfo ? { isVoice: true, voiceDurationSecs: voiceInfo.durationSecs } : {}),
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

      // Limpiar símbolos raros del LLM (markdown, emojis de texto, asteriscos, etc.)
      responseText = responseText
        .replace(/[*_~`#>|]/g, "")        // markdown
        .replace(/\[.*?\]/g, "")           // [links]
        .replace(/\(https?:\/\/.*?\)/g, "") // (urls)
        .replace(/:\w+:/g, "")             // :emoji_codes:
        .replace(/\n{3,}/g, "\n\n")        // múltiples saltos
        .trim();

      // Delay realista — simular que Karime "piensa" y "escribe"
      const typingDelay = 1200 + Math.min(responseText.length * 15, 3000) + Math.random() * 800;
      await new Promise((r) => setTimeout(r, typingDelay));

      // Asignar voz según contacto
      const voiceId = contact.personaId === "karime" ? "karime"
        : contact.personaId === "patient" ? undefined
        : undefined;

      // Si el usuario envió voz, Karime responde con voz también
      const respondWithVoice = voiceInfo?.isVoice && voiceId;
      let voiceDurationSecs = 0;

      // Pre-generar TTS para conocer la duración si es mensaje de voz
      if (respondWithVoice) {
        try {
          const durationMs = await invoke<number>("tts_speak", { text: responseText, voiceId });
          voiceDurationSecs = Math.round(durationMs / 1000);
        } catch { /* TTS no disponible */ }
      }

      const botMsg = {
        id: nextMsgId(),
        contactId: contact.id,
        sender: "other" as const,
        text: responseText,
        time: timeNow(),
        status: "read" as const,
        voiceId,
        ...(respondWithVoice ? { isVoice: true, voiceDurationSecs: Math.max(1, voiceDurationSecs) } : {}),
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
    voiceId: m.voiceId,
    isVoice: m.isVoice,
    voiceDurationSecs: m.voiceDurationSecs,
  }));

  return (
    <div className="flex h-full flex-col overflow-hidden ls-bg">
      {/* Header */}
      <div className="shrink-0 flex items-center gap-3 border-b ls-border ls-bg-panel/90 px-3 py-2">
        <button
          onClick={() => setActiveContact(null)}
          className="rounded p-1 ls-text-muted transition hover:ls-bg-input hover:ls-text"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="relative">
          <ContactAvatar avatar={contact.avatar} color={contact.color} size="md" />
          {contact.online && (
            <Circle className="absolute -right-0.5 -bottom-0.5 h-3 w-3 fill-emerald-400 stroke-slate-900 stroke-2" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold ls-text">{contact.name}</p>
          <p className="text-xs ls-text-muted">
            {typing ? "escribiendo..." : contact.id === "karime" ? getKarimeStatus() : contact.subtitle}
          </p>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0">
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
              <div className="shrink-0">
                <ContactAvatar avatar={contact.avatar} color={contact.color} size="sm" />
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
        onSend={(text) => handleSend(text)}
        onSendVoice={(text, durationSecs) => handleSend(text, { isVoice: true, durationSecs })}
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

  if (activeContact === "ayuda") {
    return <HelpBotView onBack={() => useChatStore.getState().setActiveContact(null)} />;
  }

  if (contact) {
    return <ConversationView contact={contact} />;
  }

  return <ContactList />;
}
