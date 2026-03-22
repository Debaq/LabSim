import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { invoke } from "@tauri-apps/api/core";
import type { SessionConfig } from "@/lib/session-config";

export interface SessionEvent {
  timestamp: number;
  type: "attention_start" | "test_start" | "test_end" | "evolution_created" | "referral" | "attention_end";
  simulator?: string;
  details?: string;
}

type PatientMood = "normal" | "ansioso" | "frustrado" | "satisfecho" | "confuso";

interface LiveSessionState {
  // Paciente actual en atención
  activePatientId: string | null;
  activeCaseId: string | null;
  agendaItemId: string | null;
  patientDisplayName: string | null;

  /** Configuración de sesión (artefactos, cooperación) definida por el docente */
  sessionConfig: SessionConfig;

  // Estado emocional
  patientMood: PatientMood;

  // Timeline de eventos de la sesión
  events: SessionEvent[];

  // Memoria acumulada (resúmenes cortos)
  patientMemory: string[];

  // Timestamp de inicio
  startedAt: number | null;

  // Acciones
  startAttention: (params: {
    patientId: string;
    caseId: string;
    agendaItemId: string;
    displayName: string;
    sessionConfig?: SessionConfig;
  }) => void;
  endAttention: () => Promise<void>;
  addEvent: (event: Omit<SessionEvent, "timestamp">) => void;
  updateMood: (mood: PatientMood) => void;
  addMemory: (memory: string) => void;
  getTestsPerformed: () => string[];
  getDurationMinutes: () => number;
}

export const useLiveSessionStore = create<LiveSessionState>()(
  persist(
    (set, get) => ({
      activePatientId: null,
      activeCaseId: null,
      agendaItemId: null,
      patientDisplayName: null,
      sessionConfig: {},
      patientMood: "normal",
      events: [],
      patientMemory: [],
      startedAt: null,

      startAttention: ({ patientId, caseId, agendaItemId, displayName, sessionConfig }) => {
        set({
          activePatientId: patientId,
          activeCaseId: caseId,
          agendaItemId,
          patientDisplayName: displayName,
          sessionConfig: sessionConfig ?? {},
          patientMood: "normal",
          events: [{ timestamp: Date.now(), type: "attention_start" }],
          patientMemory: [],
          startedAt: Date.now(),
        });
      },

      endAttention: async () => {
        const state = get();
        if (!state.activeCaseId || !state.startedAt) {
          set({
            activePatientId: null,
            activeCaseId: null,
            agendaItemId: null,
            patientDisplayName: null,
            patientMood: "normal",
            events: [],
            patientMemory: [],
            startedAt: null,
          });
          return;
        }

        // Registrar evento de fin
        const tests = state.getTestsPerformed();
        const duration = state.getDurationMinutes();

        // Generar resumen automático
        const summary = [
          `Atención de ${duration} min`,
          tests.length > 0 ? `Exámenes: ${tests.join(", ")}` : "Sin exámenes",
          `Estado final: ${state.patientMood}`,
          ...state.patientMemory,
        ].join(". ");

        // Guardar log en servidor
        try {
          await invoke("api_create_patient_log", {
            data: {
              caseId: state.activeCaseId,
              agendaItemId: state.agendaItemId,
              summary,
              moodAtEnd: state.patientMood,
              testsPerformed: tests,
              durationMinutes: duration,
            },
          });
        } catch {
          // silencioso — no bloquear si falla
        }

        set({
          activePatientId: null,
          activeCaseId: null,
          agendaItemId: null,
          patientDisplayName: null,
          patientMood: "normal",
          events: [],
          patientMemory: [],
          startedAt: null,
        });
      },

      addEvent: (event) => {
        set((s) => ({
          events: [...s.events, { ...event, timestamp: Date.now() }],
        }));
      },

      updateMood: (mood) => set({ patientMood: mood }),

      addMemory: (memory) => {
        set((s) => ({
          patientMemory: [...s.patientMemory, memory],
        }));
      },

      getTestsPerformed: () => {
        const events = get().events;
        const tests = new Set<string>();
        for (const e of events) {
          if (e.type === "test_start" && e.simulator) {
            tests.add(e.simulator);
          }
        }
        return Array.from(tests);
      },

      getDurationMinutes: () => {
        const started = get().startedAt;
        if (!started) return 0;
        return Math.round((Date.now() - started) / 60000);
      },
    }),
    {
      name: "labsim-live-session",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
