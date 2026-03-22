import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { invoke } from "@tauri-apps/api/core";
import { HELP_KB, type KBCategory, type KBArticle } from "@/data/help-kb";

interface KBState {
  categories: KBCategory[];
  lastModified: string | null;
  loading: boolean;
  serverAvailable: boolean;

  fetchAll: () => Promise<void>;
  createArticle: (categoryId: string, article: Omit<KBArticle, "id">) => Promise<void>;
  updateArticle: (articleId: string, data: Partial<KBArticle>) => Promise<void>;
  deleteArticle: (articleId: string, categoryId: string) => Promise<void>;
}

export const useKBStore = create<KBState>()(
  persist(
    (set, get) => ({
      categories: HELP_KB,
      lastModified: null,
      loading: false,
      serverAvailable: false,

      fetchAll: async () => {
        set({ loading: true });
        try {
          const since = get().lastModified;
          const resp = await invoke<{
            changed: boolean;
            lastModified: string | null;
            categories?: KBCategory[];
          }>("api_list_kb_articles", { since });

          if (resp.changed && resp.categories?.length) {
            set({
              categories: resp.categories,
              lastModified: resp.lastModified,
              serverAvailable: true,
            });
          } else if (!resp.changed) {
            // Sin cambios, mantener datos actuales
            set({ serverAvailable: true });
          }
        } catch {
          // Sin conexión, usar datos cacheados o fallback local
          const cached = get().categories;
          if (!cached?.length) {
            set({ categories: HELP_KB });
          }
          set({ serverAvailable: false });
        } finally {
          set({ loading: false });
        }
      },

      createArticle: async (categoryId, article) => {
        try {
          await invoke("api_create_kb_article", {
            data: { categoryId, ...article },
          });
          // Forzar descarga completa (invalidar cache)
          set({ lastModified: null });
          await get().fetchAll();
        } catch {
          set((state) => ({
            categories: state.categories.map((cat) =>
              cat.id === categoryId
                ? { ...cat, articles: [...cat.articles, { ...article, id: `local-${Date.now()}` }] }
                : cat,
            ),
          }));
        }
      },

      updateArticle: async (articleId, data) => {
        try {
          await invoke("api_update_kb_article", { articleId, data });
          set({ lastModified: null });
          await get().fetchAll();
        } catch {
          set((state) => ({
            categories: state.categories.map((cat) => ({
              ...cat,
              articles: cat.articles.map((a) =>
                a.id === articleId ? { ...a, ...data } : a,
              ),
            })),
          }));
        }
      },

      deleteArticle: async (articleId, categoryId) => {
        try {
          await invoke("api_delete_kb_article", { articleId });
          set({ lastModified: null });
          await get().fetchAll();
        } catch {
          set((state) => ({
            categories: state.categories.map((cat) =>
              cat.id === categoryId
                ? { ...cat, articles: cat.articles.filter((a) => a.id !== articleId) }
                : cat,
            ),
          }));
        }
      },
    }),
    {
      name: "labsim-kb",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        categories: state.categories,
        lastModified: state.lastModified,
      }),
    },
  ),
);
