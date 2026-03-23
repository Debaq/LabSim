import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

// ─── Tipos ──────────────────────────────────────────

export interface CaseSummary {
  id: string;
  title: string;
  description: string | null;
  tags: string;
  difficulty: string;
  is_published: number;
  is_locked: number;
}

export interface CaseProfile {
  core?: {
    identity?: Record<string, unknown>;
    personality?: Record<string, unknown>;
    clinicalHistory?: Record<string, unknown>;
  };
  modules?: Record<string, Record<string, unknown>>;
  [key: string]: unknown;
}

export interface AgendaItem {
  id: string;
  patient_name: string;
  patient_age: number | null;
  patient_gender: string | null;
  patient_notes: string | null;
  case_id: string | null;
  procedure_name: string | null;
  procedure_code: string | null;
  procedure_category: string | null;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  status: string;
  assigned_to: string | null;
  assigned_name: string | null;
  author_name: string | null;
  session_id: string | null;
  completion_notes: string | null;
}

export interface Evolution {
  id: string;
  agenda_item_id: string;
  student_id: string;
  student_name: string | null;
  student_username: string | null;
  motivo_consulta: string | null;
  anamnesis_proxima: string | null;
  examen_fisico: string | null;
  hipotesis_diagnostica: string | null;
  plan_estudio: string | null;
  plan_terapeutico: string | null;
  observaciones: string | null;
  created_at: string;
  updated_at: string;
}

export interface Interconsultation {
  id: string;
  agenda_item_id: string;
  requester_id: string;
  requester_name: string | null;
  requester_username: string | null;
  target_specialty: string;
  reason: string;
  priority: "normal" | "urgente";
  response_text: string | null;
  responder_id: string | null;
  responder_name: string | null;
  responder_username: string | null;
  status: "solicitada" | "respondida" | "completada";
  created_at: string;
  responded_at: string | null;
}

export interface AgendaSession {
  id: string;
  title: string;
  scheduled_date: string | null;
  session_type: string | null;
  status: string;
  block_count: number;
}

// ─── Estado ─────────────────────────────────────────

type MainView = "fichas" | "agenda";
type AgendaView = "list" | "detail";
type PatientTab = "ficha-base" | "examenes";

interface LarissaState {
  // Navegación principal
  mainView: MainView;

  // Fichas Clínicas
  patients: CaseSummary[];
  patientsLoading: boolean;
  searchQuery: string;
  selectedPatientId: string | null;
  patientProfile: CaseProfile | null;
  patientLoading: boolean;
  patientTab: PatientTab;

  // Agenda
  agendaSessions: AgendaSession[];
  agendaSessionsLoading: boolean;
  agendaView: AgendaView;
  selectedAgendaSessionId: string | null;
  agendaItems: AgendaItem[];
  agendaLoading: boolean;
  selectedItemId: string | null;
  evolutions: Evolution[];
  interconsultations: Interconsultation[];
  detailLoading: boolean;

  // Acciones — navegación
  setMainView: (view: MainView) => void;

  // Acciones — fichas
  fetchPatients: () => Promise<void>;
  selectPatient: (caseId: string | null) => Promise<void>;
  setSearchQuery: (q: string) => void;
  setPatientTab: (tab: PatientTab) => void;

  // Acciones — agenda
  fetchAgendaSessions: () => Promise<void>;
  selectAgendaSession: (sessionId: string | null) => Promise<void>;
  setAgendaView: (view: AgendaView) => void;
  assignPatientToSlot: (agendaItemId: string, patientName: string, caseId?: string) => Promise<void>;
  deleteAgendaSession: (sessionId: string) => Promise<void>;
  fetchAgenda: () => Promise<void>;
  selectItem: (id: string | null) => Promise<void>;
  createEvolution: (data: Record<string, string>) => Promise<void>;
  updateEvolution: (id: string, data: Record<string, string>) => Promise<void>;
  createInterconsultation: (data: { targetSpecialty: string; reason: string; priority?: string }) => Promise<void>;
  respondInterconsultation: (id: string, responseText: string) => Promise<void>;
  refreshDetail: () => Promise<void>;
}

// ─── Store ──────────────────────────────────────────

export const useLarissaStore = create<LarissaState>()((set, get) => ({
  mainView: "fichas",

  patients: [],
  patientsLoading: false,
  searchQuery: "",
  selectedPatientId: null,
  patientProfile: null,
  patientLoading: false,
  patientTab: "ficha-base",

  agendaSessions: [],
  agendaSessionsLoading: false,
  agendaView: "list" as AgendaView,
  selectedAgendaSessionId: null,
  agendaItems: [],
  agendaLoading: false,
  selectedItemId: null,
  evolutions: [],
  interconsultations: [],
  detailLoading: false,

  // ─── Navegación ────────────────────────────────────

  setMainView: (view) => set({ mainView: view }),

  // ─── Fichas Clínicas ──────────────────────────────

  fetchPatients: async () => {
    set({ patientsLoading: true });
    try {
      const result = await invoke<{ items: CaseSummary[] }>(
        "api_list_cases",
        { published: "1", limit: 200 },
      );
      set({ patients: result?.items ?? [] });
    } catch {
      set({ patients: [] });
    } finally {
      set({ patientsLoading: false });
    }
  },

  selectPatient: async (caseId) => {
    if (!caseId) {
      set({ selectedPatientId: null, patientProfile: null });
      return;
    }
    set({ selectedPatientId: caseId, patientLoading: true, patientTab: "ficha-base" });
    try {
      const result = await invoke<{ case: { profile: CaseProfile } }>(
        "api_get_case",
        { caseId },
      );
      set({ patientProfile: result?.case?.profile ?? null });
    } catch {
      set({ patientProfile: null });
    } finally {
      set({ patientLoading: false });
    }
  },

  setSearchQuery: (q) => set({ searchQuery: q }),
  setPatientTab: (tab) => set({ patientTab: tab }),

  // ─── Agenda ─────────────────────────────────────────

  fetchAgendaSessions: async () => {
    set({ agendaSessionsLoading: true });
    try {
      // Listar sesiones que tienen bloques de agenda
      const result = await invoke<{ items: Array<{
        id: string; title: string; scheduled_date: string | null;
        session_type: string | null; status: string; course_id: string | null;
      }> }>("api_get_sessions", {});
      const sessions = result?.items ?? [];
      // Para cada sesión, contar bloques
      const allAgenda = await invoke<{ items: AgendaItem[] }>("api_get_agenda", { from: "2020-01-01", to: "2099-12-31" });
      const allItems = allAgenda?.items ?? [];
      const countBySession: Record<string, number> = {};
      for (const item of allItems) {
        if (item.session_id) countBySession[item.session_id] = (countBySession[item.session_id] ?? 0) + 1;
      }
      const agendaSessions: AgendaSession[] = sessions
        .filter((s) => countBySession[s.id] > 0 || s.status === "approved" || s.status === "active")
        .map((s) => ({
          id: s.id,
          title: s.title,
          scheduled_date: s.scheduled_date,
          session_type: s.session_type,
          status: s.status,
          block_count: countBySession[s.id] ?? 0,
        }));
      set({ agendaSessions });
    } catch {
      set({ agendaSessions: [] });
    } finally {
      set({ agendaSessionsLoading: false });
    }
  },

  selectAgendaSession: async (sessionId) => {
    if (!sessionId) {
      set({ selectedAgendaSessionId: null, agendaItems: [], agendaView: "list" });
      return;
    }
    set({ selectedAgendaSessionId: sessionId, agendaLoading: true, agendaView: "detail" });
    try {
      const result = await invoke<{ items: AgendaItem[] }>("api_get_agenda", { from: "2020-01-01", to: "2099-12-31" });
      const items = (result?.items ?? []).filter((a) => a.session_id === sessionId);
      set({ agendaItems: items });
    } catch {
      set({ agendaItems: [] });
    } finally {
      set({ agendaLoading: false });
    }
  },

  setAgendaView: (view) => set({ agendaView: view }),

  assignPatientToSlot: async (agendaItemId, patientName, caseId) => {
    await invoke("api_update_agenda_item", {
      itemId: agendaItemId,
      data: {
        patientName,
        caseId: caseId ?? undefined,
      },
    });
    set((s) => ({
      agendaItems: s.agendaItems.map((a) =>
        a.id === agendaItemId
          ? { ...a, patient_name: patientName, case_id: caseId ?? null }
          : a
      ),
    }));
  },

  deleteAgendaSession: async (sessionId) => {
    await invoke("api_delete_session", { sessionId });
    set((s) => ({
      agendaSessions: s.agendaSessions.filter((a) => a.id !== sessionId),
      selectedAgendaSessionId: s.selectedAgendaSessionId === sessionId ? null : s.selectedAgendaSessionId,
      agendaView: s.selectedAgendaSessionId === sessionId ? "list" as AgendaView : s.agendaView,
    }));
  },

  fetchAgenda: async () => {
    set({ agendaLoading: true });
    try {
      const today = new Date();
      const future = new Date(today);
      future.setDate(future.getDate() + 60);
      const from = today.toISOString().split("T")[0];
      const to = future.toISOString().split("T")[0];
      const result = await invoke<{ items: AgendaItem[] }>("api_get_agenda", { from, to });
      set({ agendaItems: result?.items ?? [] });
    } catch {
      set({ agendaItems: [] });
    } finally {
      set({ agendaLoading: false });
    }
  },

  selectItem: async (id) => {
    if (!id) {
      set({ selectedItemId: null, evolutions: [], interconsultations: [] });
      return;
    }
    set({ selectedItemId: id, detailLoading: true });
    try {
      const [evosResult, icsResult] = await Promise.all([
        invoke<{ data: Evolution[] }>("api_list_evolutions", { agendaItemId: id }),
        invoke<{ data: Interconsultation[] }>("api_list_interconsultations", { agendaItemId: id }),
      ]);
      set({
        evolutions: evosResult.data ?? [],
        interconsultations: icsResult.data ?? [],
      });
    } catch {
      set({ evolutions: [], interconsultations: [] });
    } finally {
      set({ detailLoading: false });
    }
  },

  createEvolution: async (data) => {
    const { selectedItemId } = get();
    if (!selectedItemId) return;
    await invoke("api_create_evolution", {
      evolution: { agendaItemId: selectedItemId, ...data },
    });
    await get().refreshDetail();
  },

  updateEvolution: async (id, data) => {
    await invoke("api_update_evolution", { evolutionId: id, data });
    await get().refreshDetail();
  },

  createInterconsultation: async (data) => {
    const { selectedItemId } = get();
    if (!selectedItemId) return;
    await invoke("api_create_interconsultation", {
      data: { agendaItemId: selectedItemId, ...data },
    });
    await get().refreshDetail();
  },

  respondInterconsultation: async (id, responseText) => {
    await invoke("api_respond_interconsultation", {
      interconsultationId: id,
      data: { responseText },
    });
    await get().refreshDetail();
  },

  refreshDetail: async () => {
    const { selectedItemId } = get();
    if (!selectedItemId) return;
    try {
      const [evosResult, icsResult] = await Promise.all([
        invoke<{ data: Evolution[] }>("api_list_evolutions", { agendaItemId: selectedItemId }),
        invoke<{ data: Interconsultation[] }>("api_list_interconsultations", { agendaItemId: selectedItemId }),
      ]);
      set({
        evolutions: evosResult.data ?? [],
        interconsultations: icsResult.data ?? [],
      });
    } catch {
      // silent
    }
  },
}));
