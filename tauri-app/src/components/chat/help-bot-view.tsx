import { useState, useEffect } from "react";
import { useKBStore } from "@/stores/kb-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  Monitor,
  Headphones,
  Activity,
  Eye,
  Brain,
  ClipboardList,
  Settings,
  Ear,
  HelpCircle,
  ChevronRight,
} from "lucide-react";
import type { KBArticle, KBCategory } from "@/data/help-kb";

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  app: <Monitor className="h-5 w-5" />,
  audiometria: <Headphones className="h-5 w-5" />,
  impedanciometria: <Activity className="h-5 w-5" />,
  oftalmologia: <Eye className="h-5 w-5" />,
  otoneurologia: <Brain className="h-5 w-5" />,
  clinica: <ClipboardList className="h-5 w-5" />,
  equipos: <Settings className="h-5 w-5" />,
  rehabilitacion: <Ear className="h-5 w-5" />,
};

const CATEGORY_COLORS: Record<string, string> = {
  app: "text-blue-400 bg-blue-500/10",
  audiometria: "text-sky-400 bg-sky-500/10",
  impedanciometria: "text-emerald-400 bg-emerald-500/10",
  oftalmologia: "text-red-400 bg-red-500/10",
  otoneurologia: "text-violet-400 bg-violet-500/10",
  clinica: "text-amber-400 bg-amber-500/10",
  equipos: "text-slate-400 bg-slate-500/10",
  rehabilitacion: "text-pink-400 bg-pink-500/10",
};

type View = { type: "home" } | { type: "category"; category: KBCategory } | { type: "article"; article: KBArticle; category: KBCategory };

export function HelpBotView({ onBack }: { onBack: () => void }) {
  const categories = useKBStore((s) => s.categories);
  const fetchAll = useKBStore((s) => s.fetchAll);
  const [view, setView] = useState<View>({ type: "home" });

  useEffect(() => { fetchAll(); }, []);

  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "var(--ls-window-bg)" }}>
      {/* Header */}
      <div className="flex items-center gap-3 border-b px-3 py-2" style={{ borderColor: "var(--ls-border)", backgroundColor: "var(--ls-panel)" }}>
        <button
          onClick={() => {
            if (view.type === "article") setView({ type: "category", category: view.category });
            else if (view.type === "category") setView({ type: "home" });
            else onBack();
          }}
          className="rounded p-1 ls-text-muted transition hover:ls-bg-input"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600">
          <HelpCircle className="h-4 w-4 text-white" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold" style={{ color: "var(--ls-text)" }}>Ayuda</p>
          <p className="text-xs ls-text-muted">
            {view.type === "home" && "Selecciona un tema"}
            {view.type === "category" && view.category.label}
            {view.type === "article" && view.category.label}
          </p>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {view.type === "home" && (
          <div className="p-3 space-y-1.5">
            <p className="px-2 py-2 text-sm" style={{ color: "var(--ls-text)" }}>
              Selecciona un tema para ver artículos de ayuda:
            </p>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setView({ type: "category", category: cat })}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition hover:ls-bg-input"
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${CATEGORY_COLORS[cat.id] ?? "text-slate-400 bg-slate-500/10"}`}>
                  {CATEGORY_ICONS[cat.id] ?? <HelpCircle className="h-5 w-5" />}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium" style={{ color: "var(--ls-text)" }}>{cat.label}</p>
                  <p className="text-xs ls-text-muted">{cat.articles.length} artículo{cat.articles.length !== 1 ? "s" : ""}</p>
                </div>
                <ChevronRight className="h-4 w-4 ls-text-muted" />
              </button>
            ))}
          </div>
        )}

        {view.type === "category" && (
          <div className="p-3 space-y-1">
            {view.category.articles.map((article) => (
              <button
                key={article.id}
                onClick={() => setView({ type: "article", article, category: view.category })}
                className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-left transition hover:ls-bg-input"
              >
                <div className={`h-1.5 w-1.5 shrink-0 rounded-full ${CATEGORY_COLORS[view.category.id]?.split(" ")[0] ?? "bg-slate-400"}`} style={{ backgroundColor: "currentColor" }} />
                <span className="text-sm" style={{ color: "var(--ls-text)" }}>{article.title}</span>
                <ChevronRight className="ml-auto h-3.5 w-3.5 shrink-0 ls-text-muted" />
              </button>
            ))}
          </div>
        )}

        {view.type === "article" && (
          <div className="p-4">
            <h3 className="mb-3 text-base font-semibold" style={{ color: "var(--ls-text)" }}>
              {view.article.title}
            </h3>
            <div className="whitespace-pre-wrap text-sm leading-relaxed" style={{ color: "var(--ls-text-secondary)" }}>
              {view.article.content}
            </div>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
