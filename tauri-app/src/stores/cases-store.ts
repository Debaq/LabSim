import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface CaseSummary {
  id: string;
  title: string;
  description: string | null;
  author_id: string;
  author_username: string;
  author_name: string;
  tags: string;
  difficulty: "easy" | "medium" | "hard";
  is_published: number;
  is_archived: number;
  is_locked: number;
  schema_version: number;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseSummary {
  profile: Record<string, unknown>;
}

type FilterStatus = "all" | "published" | "draft" | "archived";

interface CasesState {
  cases: CaseSummary[];
  totalCases: number;
  currentPage: number;
  totalPages: number;
  loading: boolean;
  error: string | null;

  searchQuery: string;
  filterStatus: FilterStatus;
  filterDifficulty: string | null;
  selectedCaseId: string | null;

  setSearchQuery: (q: string) => void;
  setFilterStatus: (s: FilterStatus) => void;
  setFilterDifficulty: (d: string | null) => void;
  setSelectedCaseId: (id: string | null) => void;

  fetchCases: (page?: number) => Promise<void>;
  getCase: (id: string) => Promise<CaseDetail>;
  deleteCase: (id: string) => Promise<void>;
  duplicateCase: (id: string) => Promise<void>;
  togglePublish: (id: string) => Promise<void>;
  toggleArchive: (id: string) => Promise<void>;
}

export const useCasesStore = create<CasesState>()((set, get) => ({
  cases: [],
  totalCases: 0,
  currentPage: 1,
  totalPages: 1,
  loading: false,
  error: null,

  searchQuery: "",
  filterStatus: "all",
  filterDifficulty: null,
  selectedCaseId: null,

  setSearchQuery: (q) => set({ searchQuery: q }),
  setFilterStatus: (s) => set({ filterStatus: s }),
  setFilterDifficulty: (d) => set({ filterDifficulty: d }),
  setSelectedCaseId: (id) => set({ selectedCaseId: id }),

  fetchCases: async (page = 1) => {
    set({ loading: true, error: null });
    try {
      const { searchQuery, filterStatus, filterDifficulty } = get();

      const params: Record<string, string | number | undefined> = {
        page,
        limit: 50,
      };

      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (filterDifficulty) params.difficulty = filterDifficulty;

      switch (filterStatus) {
        case "published":
          params.published = "1";
          break;
        case "draft":
          params.published = "0";
          break;
        case "archived":
          params.archived = "1";
          break;
        default:
          // "all" → no filter on published, but still hide archived
          break;
      }

      const result = await invoke<{
        items: CaseSummary[];
        pagination: { page: number; limit: number; total: number; pages: number };
      }>("api_list_cases", params);

      set({
        cases: result?.items ?? [],
        totalCases: result?.pagination?.total ?? 0,
        currentPage: result?.pagination?.page ?? 1,
        totalPages: result?.pagination?.pages ?? 1,
      });
    } catch (err) {
      set({ cases: [], error: err instanceof Error ? err.message : String(err) });
    } finally {
      set({ loading: false });
    }
  },

  getCase: async (id) => {
    const result = await invoke<{ case: CaseDetail }>("api_get_case", { caseId: id });
    return result.case;
  },

  deleteCase: async (id) => {
    await invoke("api_delete_case", { caseId: id });
    const { selectedCaseId } = get();
    if (selectedCaseId === id) set({ selectedCaseId: null });
    await get().fetchCases(get().currentPage);
  },

  duplicateCase: async (id) => {
    const detail = await get().getCase(id);
    await invoke("api_push_case", {
      caseData: {
        title: `Copia de ${detail.title}`,
        description: detail.description,
        profile: detail.profile,
        tags: detail.tags,
        difficulty: detail.difficulty,
      },
    });
    await get().fetchCases(get().currentPage);
  },

  togglePublish: async (id) => {
    await invoke("api_toggle_publish", { caseId: id });
    await get().fetchCases(get().currentPage);
  },

  toggleArchive: async (id) => {
    await invoke("api_toggle_archive", { caseId: id });
    await get().fetchCases(get().currentPage);
  },
}));
