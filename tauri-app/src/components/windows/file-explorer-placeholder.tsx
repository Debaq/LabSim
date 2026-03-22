import { useState } from "react";
import { FolderOpen, File, Folder, ChevronRight, ArrowLeft, Home } from "lucide-react";

interface FsEntry {
  name: string;
  type: "folder" | "file";
  children?: FsEntry[];
  size?: string;
  date?: string;
}

const FILE_TREE: FsEntry[] = [
  { name: "Exámenes", type: "folder", children: [
    { name: "Audiometrías", type: "folder", children: [] },
    { name: "Impedanciometrías", type: "folder", children: [] },
    { name: "Campos Visuales", type: "folder", children: [] },
    { name: "OCT", type: "folder", children: [] },
  ]},
  { name: "Informes", type: "folder", children: [] },
  { name: "Evoluciones", type: "folder", children: [] },
  { name: "Interconsultas", type: "folder", children: [] },
  { name: "Notas", type: "folder", children: [] },
];

export function FileExplorerPlaceholder() {
  const [path, setPath] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const current = path.reduce<FsEntry[]>((entries, segment) => {
    const folder = entries.find((e) => e.name === segment && e.type === "folder");
    return folder?.children ?? [];
  }, FILE_TREE);

  const goTo = (entry: FsEntry) => {
    if (entry.type === "folder") {
      setPath([...path, entry.name]);
      setSelected(null);
    }
  };

  const goBack = () => {
    setPath(path.slice(0, -1));
    setSelected(null);
  };

  const goHome = () => {
    setPath([]);
    setSelected(null);
  };

  const breadcrumb = ["Mis Documentos", ...path];

  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      {/* Toolbar */}
      <div className="flex items-center gap-1 border-b px-2 py-1.5" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)" }}>
        <button
          onClick={goBack}
          disabled={path.length === 0}
          className="rounded p-1 transition hover:ls-bg-input disabled:opacity-30"
        >
          <ArrowLeft className="h-4 w-4 ls-text-muted" />
        </button>
        <button onClick={goHome} className="rounded p-1 transition hover:ls-bg-input">
          <Home className="h-4 w-4 ls-text-muted" />
        </button>
        <div className="mx-1 h-4 w-px ls-bg-input" />
        <div className="flex items-center gap-0.5 text-xs ls-text2">
          {breadcrumb.map((seg, i) => (
            <span key={i} className="flex items-center gap-0.5">
              {i > 0 && <ChevronRight className="h-3 w-3 ls-text-muted" />}
              <button
                onClick={() => { setPath(path.slice(0, i)); setSelected(null); }}
                className="rounded px-1 py-0.5 transition hover:ls-bg-input"
              >
                {seg}
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {current.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm ls-text-muted">Carpeta vacía</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {current.map((entry) => (
              <button
                key={entry.name}
                className={`flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition ${
                  selected === entry.name ? "ls-bg-input" : "hover:ls-bg-input"
                }`}
                style={{ color: "var(--ls-text)" }}
                onClick={() => setSelected(entry.name)}
                onDoubleClick={() => goTo(entry)}
              >
                {entry.type === "folder" ? (
                  <Folder className="h-4 w-4 shrink-0 text-amber-400" />
                ) : (
                  <File className="h-4 w-4 shrink-0 ls-text-muted" />
                )}
                <span className="flex-1 text-left truncate">{entry.name}</span>
                {entry.size && <span className="text-xs ls-text-muted">{entry.size}</span>}
                {entry.date && <span className="text-xs ls-text-muted">{entry.date}</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t px-3 py-1" style={{ borderColor: "var(--ls-border)" }}>
        <span className="text-xs ls-text-muted">{current.length} elemento{current.length !== 1 ? "s" : ""}</span>
        {selected && <span className="text-xs ls-text-muted">{selected}</span>}
      </div>
    </div>
  );
}
