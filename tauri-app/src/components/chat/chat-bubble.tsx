import { cn } from "@/lib/utils";
import { Check, CheckCheck } from "lucide-react";

export interface ChatMessage {
  id: string;
  sender: "user" | "other";
  text: string;
  time: string;
  status?: "sent" | "delivered" | "read";
  avatar?: string;
  senderName?: string;
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
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 text-xs font-bold text-white">
          {message.avatar ?? message.senderName?.[0] ?? "?"}
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          "relative max-w-[75%] rounded-2xl px-3 py-2 text-sm",
          isUser
            ? "rounded-br-md bg-emerald-600 text-white"
            : "rounded-bl-md bg-slate-700 text-white/90",
        )}
      >
        {!isUser && message.senderName && (
          <p className="mb-0.5 text-[10px] font-semibold text-emerald-400">
            {message.senderName}
          </p>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>
        <div
          className={cn(
            "mt-1 flex items-center gap-1 text-[10px]",
            isUser ? "justify-end text-white/50" : "text-white/30",
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
