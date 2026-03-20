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
}

interface PatientState {
  currentPatientId: string | null;
  data: PatientData;
  updateModule: (moduleId: keyof PatientData, values: Record<string, unknown>) => void;
  resetData: () => void;
  setPatientId: (id: string | null) => void;
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
};

export const usePatientStore = create<PatientState>()(
  persist(
    (set) => ({
      currentPatientId: null,
      data: { ...emptyData },

      updateModule: (moduleId, values) =>
        set((state) => ({
          data: { ...state.data, [moduleId]: values },
        })),

      resetData: () =>
        set({ data: { ...emptyData }, currentPatientId: null }),

      setPatientId: (id) => set({ currentPatientId: id }),
    }),
    {
      name: "labsim-patient",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
