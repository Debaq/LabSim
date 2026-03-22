import { useState, useEffect } from "react";
import { useKBStore } from "@/stores/kb-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BookOpen, Plus, Pencil, Trash2, Save, X, ChevronRight } from "lucide-react";
import type { KBArticle, KBCategory } from "@/data/help-kb";

type View =
  | { type: "list" }
  | { type: "category"; category: KBCategory }
  | { type: "edit"; article: KBArticle; categoryId: string }
  | { type: "new"; categoryId: string };

export function KBEditorWindow() {
  const categories = useKBStore((s) => s.categories);
  const fetchAll = useKBStore((s) => s.fetchAll);
  const createArticle = useKBStore((s) => s.createArticle);
  const updateArticle = useKBStore((s) => s.updateArticle);
  const deleteArticle = useKBStore((s) => s.deleteArticle);
  const serverAvailable = useKBStore((s) => s.serverAvailable);

  const [view, setView] = useState<View>({ type: "list" });
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => { fetchAll(); }, []);

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) return;
    if (view.type === "new") {
      await createArticle(view.categoryId, { title: title.trim(), content: content.trim() });
      const cat = categories.find((c) => c.id === view.categoryId);
      if (cat) setView({ type: "category", category: cat });
    } else if (view.type === "edit") {
      await updateArticle(view.article.id, { title: title.trim(), content: content.trim() });
      const cat = categories.find((c) => c.id === view.categoryId);
      if (cat) setView({ type: "category", category: cat });
    }
  };

  const handleDelete = async (articleId: string, categoryId: string) => {
    await deleteArticle(articleId, categoryId);
    // Refresh de la categoría actual
    const updated = useKBStore.getState().categories.find((c) => c.id === categoryId);
    if (updated) setView({ type: "category", category: updated });
  };

  const startEdit = (article: KBArticle, categoryId: string) => {
    setTitle(article.title);
    setContent(article.content);
    setView({ type: "edit", article, categoryId });
  };

  const startNew = (categoryId: string) => {
    setTitle("");
    setContent("");
    setView({ type: "new", categoryId });
  };

  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-3 py-2" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)" }}>
        <BookOpen className="h-4 w-4 text-blue-400" />
        <span className="flex-1 text-sm font-medium" style={{ color: "var(--ls-text)" }}>
          Base de Conocimiento
        </span>
        {!serverAvailable && (
          <span className="rounded-md bg-amber-500/10 px-1.5 py-0.5 text-xs text-amber-400">
            Modo local
          </span>
        )}
      </div>

      {/* Content */}
      {view.type === "list" && (
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-1">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setView({ type: "category", category: cat })}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 transition hover:ls-bg-input"
              >
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>{cat.label}</p>
                  <p className="text-xs ls-text-muted">{cat.articles.length} artículo{cat.articles.length !== 1 ? "s" : ""}</p>
                </div>
                <ChevronRight className="h-4 w-4 ls-text-muted" />
              </button>
            ))}
          </div>
        </ScrollArea>
      )}

      {view.type === "category" && (
        <div className="flex flex-1 flex-col">
          <div className="flex items-center gap-2 border-b px-3 py-2" style={{ borderColor: "var(--ls-border)" }}>
            <button onClick={() => setView({ type: "list" })} className="rounded p-1 transition hover:ls-bg-input">
              <X className="h-4 w-4 ls-text-muted" />
            </button>
            <span className="flex-1 text-sm font-medium" style={{ color: "var(--ls-text)" }}>{view.category.label}</span>
            <button
              onClick={() => startNew(view.category.id)}
              className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-blue-400 transition hover:bg-blue-500/10"
            >
              <Plus className="h-3.5 w-3.5" /> Nuevo
            </button>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-0.5">
              {view.category.articles.map((article) => (
                <div
                  key={article.id}
                  className="flex items-center gap-2 rounded-md px-3 py-2 transition hover:ls-bg-input"
                >
                  <span className="flex-1 text-sm truncate" style={{ color: "var(--ls-text)" }}>{article.title}</span>
                  <button
                    onClick={() => startEdit(article, view.category.id)}
                    className="rounded p-1 transition hover:ls-bg-input"
                    title="Editar"
                  >
                    <Pencil className="h-3.5 w-3.5 text-blue-400" />
                  </button>
                  <button
                    onClick={() => handleDelete(article.id, view.category.id)}
                    className="rounded p-1 transition hover:bg-red-500/10"
                    title="Eliminar"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-red-400" />
                  </button>
                </div>
              ))}
              {view.category.articles.length === 0 && (
                <p className="px-3 py-4 text-center text-sm ls-text-muted">Sin artículos en esta categoría</p>
              )}
            </div>
          </ScrollArea>
        </div>
      )}

      {(view.type === "edit" || view.type === "new") && (
        <div className="flex flex-1 flex-col">
          <div className="flex items-center gap-2 border-b px-3 py-2" style={{ borderColor: "var(--ls-border)" }}>
            <button
              onClick={() => {
                const cat = categories.find((c) => c.id === (view.type === "edit" ? view.categoryId : view.categoryId));
                if (cat) setView({ type: "category", category: cat });
              }}
              className="rounded p-1 transition hover:ls-bg-input"
            >
              <X className="h-4 w-4 ls-text-muted" />
            </button>
            <span className="flex-1 text-sm font-medium" style={{ color: "var(--ls-text)" }}>
              {view.type === "new" ? "Nuevo artículo" : "Editar artículo"}
            </span>
            <button
              onClick={handleSave}
              disabled={!title.trim() || !content.trim()}
              className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-emerald-400 transition hover:bg-emerald-500/10 disabled:opacity-30"
            >
              <Save className="h-3.5 w-3.5" /> Guardar
            </button>
          </div>
          <div className="flex flex-1 flex-col gap-2 p-3">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Título del artículo"
              className="rounded-md border px-3 py-2 text-sm outline-none ls-bg-input"
              style={{ borderColor: "var(--ls-border)", color: "var(--ls-text)" }}
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Contenido del artículo..."
              className="flex-1 resize-none rounded-md border px-3 py-2 text-sm leading-relaxed outline-none ls-bg-input"
              style={{ borderColor: "var(--ls-border)", color: "var(--ls-text)" }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
