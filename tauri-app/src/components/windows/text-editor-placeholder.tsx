import { FileText } from "lucide-react";

export function TextEditorPlaceholder() {
  return (
    <div className="flex h-full flex-col ls-bg">
      <div className="flex items-center gap-2 border-b ls-border px-3 py-2">
        <FileText className="h-4 w-4 text-rose-400" />
        <span className="text-xs ls-text2">Sin título.txt</span>
      </div>
      <textarea
        className="flex-1 resize-none bg-transparent p-3 font-mono text-sm ls-text outline-none placeholder:ls-text-muted"
        placeholder="Escriba aquí..."
        defaultValue=""
      />
      <div className="flex items-center justify-between border-t ls-border px-3 py-1 text-[10px] ls-text-muted">
        <span>UTF-8</span>
        <span>Ln 1, Col 1</span>
      </div>
    </div>
  );
}
