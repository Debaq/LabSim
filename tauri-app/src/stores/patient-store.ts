import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ─── CORE: siempre existe, estructura fija ───────────

export interface PatientIdentity {
  firstName?: string;
  lastName?: string;
  displayName?: string;     // "Sra. Rosa Martínez" — cómo se presenta
  documentId?: string;      // RUN, cédula, etc.
  birthDate?: string;
  age?: number;
  gender?: string;          // "masculino" | "femenino" | "otro"
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  occupation?: string;
  referredBy?: string;
  healthInsurance?: string; // FONASA, Isapre, etc.
  notes?: string;
}

export interface PatientPersonality {
  personalityType?: string;       // "colaborador" | "ansioso" | "impaciente" | "timido" | "agresivo" | "confuso"
  communicationStyle?: string;    // "detallista" | "breve" | "evasivo"
  toneOfVoice?: string;          // "formal" | "informal" | "coloquial"
  cooperationLevel?: string;     // "total" | "parcial" | "dificil"
}

export interface PatientClinicalHistory {
  // Motivo de consulta — lo que el paciente cuenta
  mainComplaint?: string;         // Síntoma principal
  complaintDescription?: string;  // Historia detallada (lo que el paciente narra)
  evolutionTime?: string;         // "3 meses", "2 años"
  severity?: string;              // "leve" | "moderado" | "severo"

  // Antecedentes
  medicalHistory?: string[];      // ["diabetes", "hipertensión", ...]
  surgicalHistory?: string;
  familyHistory?: string;
  medications?: string;
  allergies?: string;

  // Específico audiología (ejemplo — cada especialidad agrega los suyos)
  noiseExposure?: string;
  noiseYears?: number;
  hearingProtection?: boolean;
  tinnitus?: boolean;
  tinnitusDescription?: string;
  vertigo?: boolean;
  vertigoDescription?: string;
}

export interface PatientCore {
  identity: PatientIdentity;
  personality: PatientPersonality;
  clinicalHistory: PatientClinicalHistory;
}

// ─── MÓDULOS CLÍNICOS: dinámicos, extensibles ────────

/**
 * Los módulos clínicos son un diccionario abierto.
 * Cada simulador registra su propio ID y schema.
 * Agregar un nuevo simulador = agregar un nuevo key, sin tocar PatientData.
 */
export type ClinicalModules = Record<string, Record<string, unknown>>;

// ─── PATIENT DATA: core + módulos ────────────────────

export interface PatientData {
  core: PatientCore;
  modules: ClinicalModules;
}

// ─── MÓDULOS CORE (propagables al estudiante) ────────

const CORE_KEYS: (keyof PatientCore)[] = ["identity", "personality", "clinicalHistory"];

/** Prefijos de configuración que se copian de módulos clínicos al estudiante */
const CONFIG_PREFIXES = ["config_", "pathology", "pattern", "strategy", "stimulus", "eye"];
const CONFIG_EXACT_KEYS = new Set(["patologia", "severidad", "scanPreferido", "calidadSenal", "defecto", "patron", "estrategia", "tamanoEstimulo", "mapaPreferido", "calidadCaptura"]);

function isConfigKey(key: string): boolean {
  if (CONFIG_EXACT_KEYS.has(key)) return true;
  return CONFIG_PREFIXES.some((p) => key.startsWith(p));
}

// ─── STORE ───────────────────────────────────────────

interface CaseInfo {
  caseId: string;
  sessionId?: string;
  title: string;
  authorId?: string;
  baseProfile: PatientData;
}

interface PatientState {
  currentPatientId: string | null;
  data: PatientData;
  caseInfo: CaseInfo | null;
  mode: "free" | "session";

  // Core operations
  updateCore: <K extends keyof PatientCore>(key: K, values: Partial<PatientCore[K]>) => void;
  updateModule: (moduleId: string, values: Record<string, unknown>) => void;
  resetData: () => void;
  setPatientId: (id: string | null) => void;

  // Case operations
  loadCase: (caseInfo: CaseInfo) => void;
  loadCaseForEditing: (caseId: string, title: string, profile: Record<string, unknown>) => void;
  applyDocenteUpdate: (updates: Partial<PatientCore>) => void;
  getSubmissionSnapshot: () => { caseId: string | null; sessionId?: string; data: PatientData };

  // Helpers
  getDisplayName: () => string;
  getModuleData: (moduleId: string) => Record<string, unknown>;
}

const emptyCore: PatientCore = {
  identity: {},
  personality: {},
  clinicalHistory: {},
};

const emptyData: PatientData = {
  core: { ...emptyCore },
  modules: {},
};

export const usePatientStore = create<PatientState>()(
  persist(
    (set, get) => ({
      currentPatientId: null,
      data: { ...emptyData, core: { ...emptyCore } },
      caseInfo: null,
      mode: "free",

      updateCore: (key, values) =>
        set((state) => ({
          data: {
            ...state.data,
            core: {
              ...state.data.core,
              [key]: { ...state.data.core[key], ...values },
            },
          },
        })),

      updateModule: (moduleId, values) =>
        set((state) => ({
          data: {
            ...state.data,
            modules: { ...state.data.modules, [moduleId]: values },
          },
        })),

      resetData: () =>
        set({
          data: { core: { ...emptyCore, identity: {}, personality: {}, clinicalHistory: {} }, modules: {} },
          currentPatientId: null,
          caseInfo: null,
          mode: "free",
        }),

      setPatientId: (id) => set({ currentPatientId: id }),

      loadCase: (caseInfo) => {
        const studentData: PatientData = {
          core: { identity: {}, personality: {}, clinicalHistory: {} },
          modules: {},
        };

        // Copiar core completo (identity, personality, clinicalHistory)
        for (const key of CORE_KEYS) {
          if (caseInfo.baseProfile.core?.[key]) {
            studentData.core[key] = { ...caseInfo.baseProfile.core[key] } as any;
          }
        }

        // Módulos clínicos: solo copiar configuración (patología, patrón, etc.)
        if (caseInfo.baseProfile.modules) {
          for (const [modId, modData] of Object.entries(caseInfo.baseProfile.modules)) {
            if (!modData || typeof modData !== "object") continue;
            const config: Record<string, unknown> = {};
            for (const [key, val] of Object.entries(modData)) {
              if (isConfigKey(key)) {
                config[key] = val;
              } else if (typeof val === "object" && val !== null) {
                // Nested objects (ej: ojoDerecho.patologia)
                const nested: Record<string, unknown> = {};
                for (const [nk, nv] of Object.entries(val as Record<string, unknown>)) {
                  if (isConfigKey(nk)) nested[nk] = nv;
                }
                if (Object.keys(nested).length > 0) config[key] = nested;
              }
            }
            if (Object.keys(config).length > 0) {
              studentData.modules[modId] = config;
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

      loadCaseForEditing: (caseId, _title, profile) => {
        // Cargar profile completo — puede venir en formato nuevo (core+modules) o viejo (flat)
        const newData: PatientData = {
          core: { identity: {}, personality: {}, clinicalHistory: {} },
          modules: {},
        };

        if (profile.core && typeof profile.core === "object") {
          // Formato nuevo
          const core = profile.core as Record<string, unknown>;
          for (const key of CORE_KEYS) {
            if (core[key] && typeof core[key] === "object") {
              newData.core[key] = core[key] as any;
            }
          }
          if (profile.modules && typeof profile.modules === "object") {
            newData.modules = profile.modules as ClinicalModules;
          }
        } else {
          // Formato viejo (flat): migrar automáticamente
          if (profile.patientInfo) newData.core.identity = profile.patientInfo as PatientIdentity;
          if (profile.personality) newData.core.personality = profile.personality as PatientPersonality;
          if (profile.anamnesis) newData.core.clinicalHistory = profile.anamnesis as PatientClinicalHistory;
          // El resto son módulos clínicos
          const coreKeys = new Set(["patientInfo", "personality", "anamnesis"]);
          for (const [key, val] of Object.entries(profile)) {
            if (!coreKeys.has(key) && val && typeof val === "object" && Object.keys(val as object).length > 0) {
              newData.modules[key] = val as Record<string, unknown>;
            }
          }
        }

        set({
          currentPatientId: caseId,
          data: newData,
          caseInfo: null,
          mode: "free",
        });
      },

      applyDocenteUpdate: (updates) =>
        set((state) => {
          const newCore = { ...state.data.core };
          for (const [key, val] of Object.entries(updates)) {
            const k = key as keyof PatientCore;
            if (CORE_KEYS.includes(k)) {
              newCore[k] = { ...state.data.core[k], ...val } as any;
            }
          }
          return { data: { ...state.data, core: newCore } };
        }),

      getSubmissionSnapshot: () => {
        const state = get();
        return {
          caseId: state.caseInfo?.caseId ?? state.currentPatientId,
          sessionId: state.caseInfo?.sessionId,
          data: { ...state.data },
        };
      },

      getDisplayName: () => {
        const { identity } = get().data.core;
        if (identity.displayName) return identity.displayName;
        if (identity.firstName || identity.lastName) {
          return `${identity.firstName ?? ""} ${identity.lastName ?? ""}`.trim();
        }
        return "Paciente";
      },

      getModuleData: (moduleId) => {
        return get().data.modules[moduleId] ?? {};
      },
    }),
    {
      name: "labsim-patient",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
