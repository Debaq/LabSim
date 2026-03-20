import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeName = "dark" | "light" | "dracula" | "clinical" | "solarized";

export interface ThemeColors {
  bg: string;
  bgSecondary: string;
  bgPanel: string;
  bgInput: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  border: string;
  accent: string;
  accentHover: string;
  headerBg: string;
  headerText: string;
  taskbarBg: string;
  windowBg: string;
  windowHeader: string;
}

export const THEMES: Record<ThemeName, { label: string; colors: ThemeColors }> = {
  dark: {
    label: "Oscuro",
    colors: {
      bg: "#0f172a", bgSecondary: "#1e293b", bgPanel: "#1e293b",
      bgInput: "rgba(255,255,255,0.05)", text: "#e2e8f0", textSecondary: "#94a3b8",
      textMuted: "#475569", border: "rgba(255,255,255,0.08)", accent: "#3b82f6",
      accentHover: "#2563eb", headerBg: "#0f172a", headerText: "#94a3b8",
      taskbarBg: "rgba(15,23,42,0.95)", windowBg: "#1e293b", windowHeader: "#0f172a",
    },
  },
  light: {
    label: "Claro",
    colors: {
      bg: "#f8fafc", bgSecondary: "#ffffff", bgPanel: "#f1f5f9",
      bgInput: "rgba(0,0,0,0.04)", text: "#1e293b", textSecondary: "#475569",
      textMuted: "#94a3b8", border: "rgba(0,0,0,0.1)", accent: "#2563eb",
      accentHover: "#1d4ed8", headerBg: "#e2e8f0", headerText: "#334155",
      taskbarBg: "rgba(226,232,240,0.95)", windowBg: "#ffffff", windowHeader: "#f1f5f9",
    },
  },
  dracula: {
    label: "Dracula",
    colors: {
      bg: "#282a36", bgSecondary: "#343746", bgPanel: "#2d2f3d",
      bgInput: "rgba(255,255,255,0.06)", text: "#f8f8f2", textSecondary: "#bd93f9",
      textMuted: "#6272a4", border: "rgba(98,114,164,0.3)", accent: "#ff79c6",
      accentHover: "#ff92d0", headerBg: "#21222c", headerText: "#bd93f9",
      taskbarBg: "rgba(33,34,44,0.95)", windowBg: "#282a36", windowHeader: "#21222c",
    },
  },
  clinical: {
    label: "Clínico",
    colors: {
      bg: "#f0f4f8", bgSecondary: "#ffffff", bgPanel: "#e8eef4",
      bgInput: "rgba(0,0,0,0.03)", text: "#1a2332", textSecondary: "#4a5c6e",
      textMuted: "#8a9bb0", border: "rgba(0,0,0,0.08)", accent: "#0077b6",
      accentHover: "#005f8f", headerBg: "#d4e4f0", headerText: "#1a3a5c",
      taskbarBg: "rgba(212,228,240,0.95)", windowBg: "#ffffff", windowHeader: "#e8eef4",
    },
  },
  solarized: {
    label: "Solarized",
    colors: {
      bg: "#002b36", bgSecondary: "#073642", bgPanel: "#073642",
      bgInput: "rgba(255,255,255,0.05)", text: "#839496", textSecondary: "#586e75",
      textMuted: "#657b83", border: "rgba(147,161,161,0.15)", accent: "#268bd2",
      accentHover: "#2aa198", headerBg: "#002b36", headerText: "#93a1a1",
      taskbarBg: "rgba(0,43,54,0.95)", windowBg: "#073642", windowHeader: "#002b36",
    },
  },
};

interface ThemeState {
  theme: ThemeName;
  colors: ThemeColors;
  setTheme: (theme: ThemeName) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "dark",
      colors: THEMES.dark.colors,
      setTheme: (theme) => set({ theme, colors: THEMES[theme].colors }),
    }),
    {
      name: "labsim-theme",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
