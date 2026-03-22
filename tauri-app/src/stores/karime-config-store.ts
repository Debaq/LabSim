import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export type DirectiveScope = "global" | "docente" | "instructor" | "session";
export type KarimeTone = "profesional" | "amigable" | "estricto" | "relajado";

export interface KarimeDirective {
  id: string;
  scope: DirectiveScope;
  author_id: string;
  target_session_id: string | null;
  title: string;
  student_treatment: string;
  tone: KarimeTone;
  pressure_level: number;
  custom_messages_json: string | null;
  rules_text: string | null;
  is_locked: number;
  approved_by: string | null;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface DirectiveFormData {
  title: string;
  tone: KarimeTone;
  pressure_level: number;
  student_treatment: string;
  rules_text: string;
  locked_fields: string[];
}

export interface ResolvedPreview {
  studentTreatment: string;
  tone: KarimeTone;
  pressureLevel: number;
  customMessages: Record<string, string[]>;
  rules: string;
  lockedFields?: string[];
}

interface KarimeConfigState {
  directives: KarimeDirective[];
  globalDirective: KarimeDirective | null;
  myDirective: KarimeDirective | null;
  resolvedPreview: ResolvedPreview | null;
  loading: boolean;
  error: string | null;

  fetchDirectives: () => Promise<void>;
  fetchResolvedPreview: (sessionId?: string) => Promise<void>;
  saveDirective: (data: DirectiveFormData, scope: DirectiveScope) => Promise<void>;
  updateDirective: (id: string, data: DirectiveFormData) => Promise<void>;
  deleteDirective: (id: string) => Promise<void>;
}

export const useKarimeConfigStore = create<KarimeConfigState>()((set, get) => ({
  directives: [],
  globalDirective: null,
  myDirective: null,
  resolvedPreview: null,
  loading: false,
  error: null,

  fetchDirectives: async () => {
    set({ loading: true, error: null });
    try {
      const result = await invoke<{ data: KarimeDirective[] }>("api_get_directives");
      const list = result?.data ?? [];
      const global = list.find((d) => d.scope === "global") ?? null;
      const mine = list.find((d) => d.scope === "docente") ?? null;
      set({ directives: list, globalDirective: global, myDirective: mine });
    } catch (err) {
      set({ directives: [], error: String(err) });
    } finally {
      set({ loading: false });
    }
  },

  fetchResolvedPreview: async (sessionId) => {
    try {
      const result = await invoke<{ directives: ResolvedPreview }>(
        "api_resolve_directives",
        { sessionId: sessionId ?? null },
      );
      set({ resolvedPreview: result?.directives ?? null });
    } catch {
      set({ resolvedPreview: null });
    }
  },

  saveDirective: async (data, scope) => {
    await invoke("api_save_directive", {
      directive: {
        scope,
        title: data.title,
        tone: data.tone,
        pressure_level: data.pressure_level,
        student_treatment: data.student_treatment,
        rules_text: data.rules_text || null,
        is_locked: data.locked_fields.length > 0 ? 1 : 0,
        custom_messages_json: JSON.stringify(
          Object.fromEntries(data.locked_fields.map((f) => [f, true])),
        ),
      },
    });
    await get().fetchDirectives();
    await get().fetchResolvedPreview();
  },

  updateDirective: async (id, data) => {
    await invoke("api_update_directive", {
      directiveId: id,
      directive: {
        title: data.title,
        tone: data.tone,
        pressure_level: data.pressure_level,
        student_treatment: data.student_treatment,
        rules_text: data.rules_text || null,
        is_locked: data.locked_fields.length > 0 ? 1 : 0,
        custom_messages_json: JSON.stringify(
          Object.fromEntries(data.locked_fields.map((f) => [f, true])),
        ),
      },
    });
    await get().fetchDirectives();
    await get().fetchResolvedPreview();
  },

  deleteDirective: async (id) => {
    await invoke("api_delete_directive", { directiveId: id });
    await get().fetchDirectives();
  },
}));
