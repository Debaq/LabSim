import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface PatientData {
  patientInfo: Record<string, unknown>;
  anamnesis: Record<string, unknown>;
  audiometry: Record<string, unknown>;
  logoaudiometry: Record<string, unknown>;
  supraliminal: Record<string, unknown>;
  impedance: Record<string, unknown>;
  oae: Record<string, unknown>;
  abr: Record<string, unknown>;
  electrocochleo: Record<string, unknown>;
  hearingAids: Record<string, unknown>;
  oct: Record<string, unknown>;
  visualField: Record<string, unknown>;
  retinography: Record<string, unknown>;
  cornealTopography: Record<string, unknown>;
}

/**
 * Información del caso base (creado por docente).
 * Contiene el perfil completo del paciente — la "respuesta correcta".
 */
interface CaseInfo {
  caseId: string;
  sessionId?: string;
  title: string;
  authorId?: string;
  /** Datos base del caso que el docente definió (solo lectura para estudiantes) */
  baseProfile: PatientData;
}

interface PatientState {
  currentPatientId: string | null;
  /** Datos de trabajo del estudiante (su versión del paciente) */
  data: PatientData;
  /** Info del caso base si se cargó desde una sesión práctica */
  caseInfo: CaseInfo | null;
  /** Modo de operación: "free" = práctica libre, "session" = dentro de sesión */
  mode: "free" | "session";

  updateModule: (moduleId: keyof PatientData, values: Record<string, unknown>) => void;
  resetData: () => void;
  setPatientId: (id: string | null) => void;

  /**
   * Cargar un caso de sesión práctica.
   * El estudiante recibe patientInfo + anamnesis + config simuladores,
   * pero los módulos de resultados llegan VACÍOS (los debe completar).
   */
  loadCase: (caseInfo: CaseInfo) => void;

  /**
   * Aplicar una actualización del docente (propagación).
   * Mergea los datos en los módulos especificados sin borrar el trabajo del estudiante.
   */
  applyDocenteUpdate: (updates: Partial<PatientData>) => void;

  /**
   * Exportar la versión actual del estudiante como snapshot para entrega.
   */
  getSubmissionSnapshot: () => { caseId: string | null; sessionId?: string; data: PatientData };
}

const emptyData: PatientData = {
  patientInfo: {},
  anamnesis: {},
  audiometry: {},
  logoaudiometry: {},
  supraliminal: {},
  impedance: {},
  oae: {},
  abr: {},
  electrocochleo: {},
  hearingAids: {},
  oct: {},
  visualField: {},
  retinography: {},
  cornealTopography: {},
};

/** Módulos que el docente puede propagar a los estudiantes */
const PROPAGABLE_MODULES: (keyof PatientData)[] = [
  "patientInfo",
  "anamnesis",
];

/** Módulos que el estudiante debe completar (llegan vacíos) */
const STUDENT_WORK_MODULES: (keyof PatientData)[] = [
  "audiometry",
  "logoaudiometry",
  "supraliminal",
  "impedance",
  "oae",
  "abr",
  "electrocochleo",
  "hearingAids",
  "oct",
  "visualField",
  "retinography",
  "cornealTopography",
];

export const usePatientStore = create<PatientState>()(
  persist(
    (set, get) => ({
      currentPatientId: null,
      data: { ...emptyData },
      caseInfo: null,
      mode: "free",

      updateModule: (moduleId, values) =>
        set((state) => ({
          data: { ...state.data, [moduleId]: values },
        })),

      resetData: () =>
        set({
          data: { ...emptyData },
          currentPatientId: null,
          caseInfo: null,
          mode: "free",
        }),

      setPatientId: (id) => set({ currentPatientId: id }),

      loadCase: (caseInfo) => {
        const studentData: PatientData = { ...emptyData };

        // Copiar datos base que el estudiante SÍ recibe (patientInfo, anamnesis)
        for (const mod of PROPAGABLE_MODULES) {
          if (caseInfo.baseProfile[mod]) {
            studentData[mod] = { ...caseInfo.baseProfile[mod] };
          }
        }

        // Los módulos de resultados quedan vacíos — el estudiante los completa
        // Pero sí copiamos configuración de simuladores si existe
        // (ej: qué patología OCT mostrar, qué defecto de campo visual)
        for (const mod of STUDENT_WORK_MODULES) {
          const base = caseInfo.baseProfile[mod];
          if (base && typeof base === "object") {
            // Solo copiar campos de configuración (prefijo "config_" o "pathology" o "pattern")
            const config: Record<string, unknown> = {};
            for (const [key, val] of Object.entries(base)) {
              if (
                key.startsWith("config_") ||
                key === "pathology" ||
                key === "pattern" ||
                key === "strategy" ||
                key === "stimulus" ||
                key === "eye"
              ) {
                config[key] = val;
              }
            }
            if (Object.keys(config).length > 0) {
              studentData[mod] = config;
            }
          }
        }

        set({
          currentPatientId: caseInfo.caseId,
          data: studentData,
          caseInfo,
          mode: "session",
        });
      },

      applyDocenteUpdate: (updates) =>
        set((state) => {
          const newData = { ...state.data };

          for (const [moduleId, moduleData] of Object.entries(updates)) {
            const mod = moduleId as keyof PatientData;
            // Solo propagar módulos permitidos
            if (!PROPAGABLE_MODULES.includes(mod)) continue;

            // Merge: datos del docente + lo que el estudiante ya tenía
            newData[mod] = {
              ...state.data[mod],
              ...moduleData,
            };
          }

          return { data: newData };
        }),

      getSubmissionSnapshot: () => {
        const state = get();
        return {
          caseId: state.caseInfo?.caseId ?? state.currentPatientId,
          sessionId: state.caseInfo?.sessionId,
          data: { ...state.data },
        };
      },
    }),
    {
      name: "labsim-patient",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
