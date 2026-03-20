import { useRef, useEffect } from "react";
import { ChatBubble, type ChatMessage } from "./chat-bubble";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  headerTitle: string;
  headerSubtitle?: string;
  headerAvatar: React.ReactNode;
  inputPlaceholder?: string;
  inputDisabled?: boolean;
  typing?: boolean;
}

export function ChatPanel({
  messages,
  onSend,
  headerTitle,
  headerSubtitle,
  headerAvatar,
  inputPlaceholder,
  inputDisabled,
  typing,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  return (
    <div className="flex h-full flex-col bg-slate-800">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/5 bg-slate-900/90 px-4 py-2.5">
        {headerAvatar}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-white">
            {headerTitle}
          </p>
          {headerSubtitle && (
            <p className="text-[11px] text-white/40">{headerSubtitle}</p>
          )}
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
          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}

          {typing && (
            <div className="flex gap-2">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 text-xs font-bold text-white">
                K
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
        onSend={onSend}
        placeholder={inputPlaceholder}
        disabled={inputDisabled}
      />
    </div>
  );
}
