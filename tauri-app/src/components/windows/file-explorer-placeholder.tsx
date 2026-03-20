import { FolderOpen, File, Folder } from "lucide-react";

export function FileExplorerPlaceholder() {
  const items = [
    { name: "Pacientes", type: "folder" },
    { name: "Exportaciones", type: "folder" },
    { name: "Configuración", type: "folder" },
    { name: "calibration.json", type: "file" },
    { name: "README.txt", type: "file" },
  ];

  return (
    <div className="flex h-full flex-col bg-slate-800">
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2">
        <FolderOpen className="h-4 w-4 text-amber-400" />
        <span className="text-xs text-white/50">/home/labsim/</span>
      </div>
      <div className="flex-1 p-2">
        {items.map((item) => (
          <button
            key={item.name}
            className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-white/70 transition hover:bg-white/5"
          >
            {item.type === "folder" ? (
              <Folder className="h-4 w-4 text-amber-400" />
            ) : (
              <File className="h-4 w-4 text-white/30" />
            )}
            {item.name}
          </button>
        ))}
      </div>
    </div>
  );
}
