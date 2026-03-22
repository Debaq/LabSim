import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

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
  status: "scheduled" | "in_progress" | "completed" | "cancelled" | "rescheduled" | "no_show";
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

export interface CaseProfile {
  patientInfo: Record<string, unknown>;
  anamnesis: Record<string, unknown>;
  [key: string]: Record<string, unknown>;
}

type LarissaTab = "evoluciones" | "interconsultas" | "examenes" | "ficha-base";

interface LarissaState {
  // Agenda
  agendaItems: AgendaItem[];
  agendaLoading: boolean;

  // Selección
  selectedItemId: string | null;
  selectedCase: CaseProfile | null;
  caseLoading: boolean;

  // Evoluciones e interconsultas
  evolutions: Evolution[];
  interconsultations: Interconsultation[];
  detailLoading: boolean;

  // UI
  activeTab: LarissaTab;

  // Acciones
  setActiveTab: (tab: LarissaTab) => void;
  fetchAgenda: () => Promise<void>;
  selectItem: (id: string | null) => Promise<void>;
  createEvolution: (data: Record<string, string>) => Promise<void>;
  updateEvolution: (id: string, data: Record<string, string>) => Promise<void>;
  createInterconsultation: (data: { targetSpecialty: string; reason: string; priority?: string }) => Promise<void>;
  refreshDetail: () => Promise<void>;
}

export const useLarissaStore = create<LarissaState>()((set, get) => ({
  agendaItems: [],
  agendaLoading: false,
  selectedItemId: null,
  selectedCase: null,
  caseLoading: false,
  evolutions: [],
  interconsultations: [],
  detailLoading: false,
  activeTab: "evoluciones",

  setActiveTab: (tab) => set({ activeTab: tab }),

  fetchAgenda: async () => {
    set({ agendaLoading: true });
    try {
      // Cargar próximos 60 días
      const today = new Date();
      const future = new Date(today);
      future.setDate(future.getDate() + 60);
      const from = today.toISOString().split("T")[0];
      const to = future.toISOString().split("T")[0];

      const result = await invoke<{ data: AgendaItem[] }>("api_get_agenda", { from, to });
      set({ agendaItems: result.data ?? [] });
    } catch {
      set({ agendaItems: [] });
    } finally {
      set({ agendaLoading: false });
    }
  },

  selectItem: async (id) => {
    if (!id) {
      set({ selectedItemId: null, selectedCase: null, evolutions: [], interconsultations: [] });
      return;
    }

    set({ selectedItemId: id, detailLoading: true, caseLoading: true });

    const item = get().agendaItems.find((a) => a.id === id);

    // Cargar caso vinculado si existe
    if (item?.case_id) {
      try {
        const result = await invoke<{ case: { profile: CaseProfile } }>("api_get_case", {
          caseId: item.case_id,
        });
        set({ selectedCase: result.case.profile ?? null });
      } catch {
        set({ selectedCase: null });
      }
    } else {
      set({ selectedCase: null });
    }
    set({ caseLoading: false });

    // Cargar evoluciones e interconsultas en paralelo
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

  refreshDetail: async () => {
    const { selectedItemId } = get();
    if (!selectedItemId) return;
    try {
      const [evosResult, icsResult] = await Promise.all([
        invoke<{ data: Evolution[] }>("api_list_evolutions", { agendaItemId: selectedItemId }),
        invoke<{ data: Interconsultation[] }>("api_list_interconsultations", {
          agendaItemId: selectedItemId,
        }),
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
