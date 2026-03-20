import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeName = "dark" | "light" | "dracula" | "clinical" | "solarized";

// Each theme defines CSS custom properties
export interface ThemeVars {
  // Desktop
  "--ls-desktop-bg": string;
  "--ls-desktop-gradient": string;
  // Shell
  "--ls-taskbar": string;
  "--ls-window-bg": string;
  "--ls-window-header": string;
  "--ls-border": string;
  // Panels (instrument chrome)
  "--ls-panel": string;
  "--ls-panel-secondary": string;
  "--ls-input": string;
  // Text
  "--ls-text": string;
  "--ls-text-secondary": string;
  "--ls-text-muted": string;
  // Accent
  "--ls-accent": string;
}

export const THEMES: Record<ThemeName, { label: string; desc: string; vars: ThemeVars }> = {
  dark: {
    label: "Oscuro",
    desc: "Tema por defecto",
    vars: {
      "--ls-desktop-bg": "#0f172a",
      "--ls-desktop-gradient": "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #172554 100%)",
      "--ls-taskbar": "rgba(15,23,42,0.92)",
      "--ls-window-bg": "#1e293b",
      "--ls-window-header": "#0f172a",
      "--ls-border": "rgba(255,255,255,0.08)",
      "--ls-panel": "#1a2332",
      "--ls-panel-secondary": "#0f1923",
      "--ls-input": "rgba(255,255,255,0.05)",
      "--ls-text": "#e2e8f0",
      "--ls-text-secondary": "#94a3b8",
      "--ls-text-muted": "#475569",
      "--ls-accent": "#3b82f6",
    },
  },
  light: {
    label: "Claro",
    desc: "Para entornos bien iluminados",
    vars: {
      "--ls-desktop-bg": "#c7d2e0",
      "--ls-desktop-gradient": "linear-gradient(135deg, #b0c4de 0%, #87ceeb 40%, #c7d2e0 100%)",
      "--ls-taskbar": "rgba(220,228,238,0.95)",
      "--ls-window-bg": "#f0f3f7",
      "--ls-window-header": "#dce4ee",
      "--ls-border": "rgba(0,0,0,0.12)",
      "--ls-panel": "#e8edf4",
      "--ls-panel-secondary": "#f5f7fa",
      "--ls-input": "rgba(0,0,0,0.04)",
      "--ls-text": "#1e293b",
      "--ls-text-secondary": "#475569",
      "--ls-text-muted": "#94a3b8",
      "--ls-accent": "#2563eb",
    },
  },
  dracula: {
    label: "Dracula",
    desc: "Púrpura y rosa",
    vars: {
      "--ls-desktop-bg": "#282a36",
      "--ls-desktop-gradient": "linear-gradient(135deg, #282a36 0%, #44475a 50%, #282a36 100%)",
      "--ls-taskbar": "rgba(33,34,44,0.95)",
      "--ls-window-bg": "#2d2f3d",
      "--ls-window-header": "#21222c",
      "--ls-border": "rgba(98,114,164,0.25)",
      "--ls-panel": "#2a2c3a",
      "--ls-panel-secondary": "#22232e",
      "--ls-input": "rgba(255,255,255,0.06)",
      "--ls-text": "#f8f8f2",
      "--ls-text-secondary": "#bd93f9",
      "--ls-text-muted": "#6272a4",
      "--ls-accent": "#ff79c6",
    },
  },
  clinical: {
    label: "Clínico",
    desc: "Profesional azul-gris",
    vars: {
      "--ls-desktop-bg": "#d4dfe8",
      "--ls-desktop-gradient": "linear-gradient(135deg, #c0d0e0 0%, #d4e4f0 50%, #e0e8f0 100%)",
      "--ls-taskbar": "rgba(195,210,228,0.95)",
      "--ls-window-bg": "#eaf0f6",
      "--ls-window-header": "#d4e0ec",
      "--ls-border": "rgba(0,0,0,0.1)",
      "--ls-panel": "#dce6f0",
      "--ls-panel-secondary": "#eef3f8",
      "--ls-input": "rgba(0,0,0,0.04)",
      "--ls-text": "#1a2e44",
      "--ls-text-secondary": "#4a6080",
      "--ls-text-muted": "#8a9fb8",
      "--ls-accent": "#0077b6",
    },
  },
  solarized: {
    label: "Solarized",
    desc: "Cómodo para sesiones largas",
    vars: {
      "--ls-desktop-bg": "#002b36",
      "--ls-desktop-gradient": "linear-gradient(135deg, #002b36 0%, #073642 50%, #002b36 100%)",
      "--ls-taskbar": "rgba(0,43,54,0.95)",
      "--ls-window-bg": "#073642",
      "--ls-window-header": "#002b36",
      "--ls-border": "rgba(147,161,161,0.15)",
      "--ls-panel": "#05303b",
      "--ls-panel-secondary": "#002830",
      "--ls-input": "rgba(255,255,255,0.05)",
      "--ls-text": "#93a1a1",
      "--ls-text-secondary": "#839496",
      "--ls-text-muted": "#586e75",
      "--ls-accent": "#268bd2",
    },
  },
};

interface ThemeState {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
}

// Apply CSS variables to :root
function applyTheme(theme: ThemeName) {
  const vars = THEMES[theme].vars;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(vars)) {
    root.style.setProperty(key, value);
  }
  // Set a class for conditional CSS
  root.classList.remove("theme-dark", "theme-light", "theme-dracula", "theme-clinical", "theme-solarized");
  root.classList.add(`theme-${theme}`);
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "dark",
      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },
    }),
    {
      name: "labsim-theme",
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme);
      },
    },
  ),
);

// Initialize on load
if (typeof window !== "undefined") {
  const stored = localStorage.getItem("labsim-theme");
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.theme) applyTheme(state.theme);
    } catch { /* */ }
  } else {
    applyTheme("dark");
  }
}
