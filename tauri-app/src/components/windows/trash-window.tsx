import { Trash2 } from "lucide-react";

export function TrashWindow() {
  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      <div className="flex items-center gap-2 border-b px-3 py-2" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)" }}>
        <Trash2 className="h-4 w-4 ls-text-muted" />
        <span className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>Papelera</span>
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-2">
        <Trash2 className="h-10 w-10 ls-text-muted opacity-30" />
        <p className="text-sm ls-text-muted">La papelera está vacía</p>
      </div>
    </div>
  );
}
