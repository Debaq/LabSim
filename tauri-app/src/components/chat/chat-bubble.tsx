import { cn } from "@/lib/utils";
import { Check, CheckCheck } from "lucide-react";
import { ContactAvatar } from "./contact-avatar";
import { VoiceBubble } from "./voice-bubble";

export interface ChatMessage {
  id: string;
  sender: "user" | "other";
  text: string;
  time: string;
  status?: "sent" | "delivered" | "read";
  avatar?: string;
  senderName?: string;
  voiceId?: string;
  isVoice?: boolean;
  voiceDurationSecs?: number;
}

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.sender === "user";

  return (
    <div
      className={cn("flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="shrink-0">
          <ContactAvatar
            avatar={message.avatar ?? message.senderName?.[0] ?? "?"}
            color="from-emerald-400 to-teal-500"
            size="sm"
          />
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          "relative max-w-[75%] rounded-2xl px-3 py-2 text-sm",
          isUser
            ? "rounded-br-md bg-emerald-600 ls-text"
            : "rounded-bl-md bg-slate-700 text-white/90",
        )}
      >
        {!isUser && message.senderName && (
          <p className="mb-0.5 text-xs font-semibold text-emerald-400">
            {message.senderName}
          </p>
        )}

        {/* Contenido: voz o texto */}
        {message.isVoice ? (
          <VoiceBubble
            text={message.text}
            voiceId={message.voiceId}
            durationSecs={message.voiceDurationSecs ?? 3}
            isUser={isUser}
          />
        ) : (
          <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>
        )}

        <div
          className={cn(
            "mt-1 flex items-center gap-1 text-xs",
            isUser ? "justify-end ls-text2" : "ls-text-muted",
          )}
        >
          <span>{message.time}</span>
          {isUser && message.status === "read" && (
            <CheckCheck className="h-3 w-3 text-blue-300" />
          )}
          {isUser && message.status === "delivered" && (
            <CheckCheck className="h-3 w-3" />
          )}
          {isUser && message.status === "sent" && (
            <Check className="h-3 w-3" />
          )}
        </div>
      </div>
    </div>
  );
}
