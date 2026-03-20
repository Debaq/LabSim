import { invoke } from "@tauri-apps/api/core";

// Auth
export const login = (username: string, password: string) =>
  invoke<boolean>("login", { username, password });

// Patients
export const listPatients = () =>
  invoke<PatientSummary[]>("list_patients");

export const getPatient = (id: string) =>
  invoke<PatientProfile>("get_patient", { id });

export const savePatient = (data: PatientProfile) =>
  invoke<string>("save_patient", { data });

export const deletePatient = (id: string) =>
  invoke<void>("delete_patient", { id });

// Audio
export const playTone = (params: ToneParams) =>
  invoke<void>("play_tone", { params });

export const playNoise = (params: NoiseParams) =>
  invoke<void>("play_noise", { params });

export const stopPlayback = () =>
  invoke<void>("stop_playback");

// Types
export interface PatientSummary {
  id: string;
  name: string;
  age: number;
  createdAt: string;
}

export interface PatientProfile {
  id: string;
  metadata: Record<string, unknown>;
  modules: Record<string, unknown>;
}

export interface ToneParams {
  frequency: number;
  duration: number;
  levelDbfs: number;
  pulsatileHz?: number;
  dutyCycle?: number;
}

export interface NoiseParams {
  noiseType: "white" | "pink" | "speech" | "narrowband";
  duration: number;
  levelDbfs: number;
  centerHz?: number;
  bandwidthHz?: number;
}
