import { useState } from "react";
import { Send, Smile } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  placeholder = "Escribe un mensaje...",
  disabled = false,
}: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t ls-border ls-bg-panel/80 px-3 py-2"
    >
      <button
        type="button"
        className="shrink-0 rounded-full p-2 ls-text-muted transition hover:ls-bg-input hover:ls-text2"
      >
        <Smile className="h-5 w-5" />
      </button>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="max-h-24 min-h-9 flex-1 resize-none rounded-2xl border ls-border ls-bg-input px-4 py-2 text-sm text-white outline-none placeholder:ls-text-muted focus:border-emerald-500/30"
      />

      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white transition hover:bg-emerald-500 disabled:opacity-30"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}
