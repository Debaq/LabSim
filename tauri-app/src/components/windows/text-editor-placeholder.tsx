import { FileText } from "lucide-react";

export function TextEditorPlaceholder() {
  return (
    <div className="flex h-full flex-col bg-slate-800">
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2">
        <FileText className="h-4 w-4 text-rose-400" />
        <span className="text-xs text-white/50">Sin título.txt</span>
      </div>
      <textarea
        className="flex-1 resize-none bg-transparent p-3 font-mono text-sm text-white/80 outline-none placeholder:text-white/20"
        placeholder="Escriba aquí..."
        defaultValue=""
      />
      <div className="flex items-center justify-between border-t border-white/5 px-3 py-1 text-[10px] text-white/30">
        <span>UTF-8</span>
        <span>Ln 1, Col 1</span>
      </div>
    </div>
  );
}
