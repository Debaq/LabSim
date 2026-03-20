import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ThemeName = "midnight" | "clinical" | "nord";

export interface ThemeVars {
  "--ls-desktop-bg": string;
  "--ls-desktop-gradient": string;
  "--ls-taskbar": string;
  "--ls-window-bg": string;
  "--ls-window-header": string;
  "--ls-border": string;
  "--ls-panel": string;
  "--ls-panel-secondary": string;
  "--ls-input": string;
  "--ls-text": string;
  "--ls-text-secondary": string;
  "--ls-text-muted": string;
  "--ls-accent": string;
}

export const THEMES: Record<ThemeName, { label: string; desc: string; vars: ThemeVars }> = {
  midnight: {
    label: "Midnight",
    desc: "Oscuro profesional — ideal para cabinas y uso prolongado",
    vars: {
      "--ls-desktop-bg": "#0c1220",
      "--ls-desktop-gradient": "linear-gradient(145deg, #0c1220 0%, #141e30 40%, #1a1a2e 100%)",
      "--ls-taskbar": "rgba(10,15,28,0.94)",
      "--ls-window-bg": "#161d2e",
      "--ls-window-header": "#101728",
      "--ls-border": "rgba(130,160,210,0.12)",
      "--ls-panel": "#131a28",
      "--ls-panel-secondary": "#0e1420",
      "--ls-input": "rgba(140,170,220,0.07)",
      "--ls-text": "#d0d8e8",
      "--ls-text-secondary": "#8898b4",
      "--ls-text-muted": "#506080",
      "--ls-accent": "#4d8ef7",
    },
  },
  clinical: {
    label: "Clínico",
    desc: "Claro profesional — entornos bien iluminados",
    vars: {
      "--ls-desktop-bg": "#c8d4e0",
      "--ls-desktop-gradient": "linear-gradient(145deg, #b8c8d8 0%, #c8d8e8 40%, #d0dce8 100%)",
      "--ls-taskbar": "rgba(200,212,228,0.96)",
      "--ls-window-bg": "#e8eef5",
      "--ls-window-header": "#d0dae8",
      "--ls-border": "rgba(60,80,120,0.15)",
      "--ls-panel": "#dde5f0",
      "--ls-panel-secondary": "#e8eff7",
      "--ls-input": "rgba(40,60,100,0.06)",
      "--ls-text": "#1c2d44",
      "--ls-text-secondary": "#3d5575",
      "--ls-text-muted": "#7a8da4",
      "--ls-accent": "#1a6db5",
    },
  },
  nord: {
    label: "Nord",
    desc: "Aurora boreal — cómodo para sesiones largas",
    vars: {
      "--ls-desktop-bg": "#242933",
      "--ls-desktop-gradient": "linear-gradient(145deg, #242933 0%, #2e3440 40%, #2a303c 100%)",
      "--ls-taskbar": "rgba(36,41,51,0.96)",
      "--ls-window-bg": "#2e3440",
      "--ls-window-header": "#272c36",
      "--ls-border": "rgba(160,180,210,0.1)",
      "--ls-panel": "#2a3040",
      "--ls-panel-secondary": "#252b36",
      "--ls-input": "rgba(140,170,210,0.06)",
      "--ls-text": "#d8dee9",
      "--ls-text-secondary": "#8892a4",
      "--ls-text-muted": "#5c6578",
      "--ls-accent": "#88c0d0",
    },
  },
};

interface ThemeState {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
}

function applyTheme(theme: ThemeName) {
  const t = THEMES[theme];
  if (!t) return;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(t.vars)) {
    root.style.setProperty(key, value);
  }
  root.className = root.className.replace(/theme-\S+/g, "").trim();
  root.classList.add(`theme-${theme}`);
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "midnight",
      setTheme: (theme) => { applyTheme(theme); set({ theme }); },
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

if (typeof window !== "undefined") {
  const stored = localStorage.getItem("labsim-theme");
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.theme && THEMES[state.theme as ThemeName]) applyTheme(state.theme);
      else applyTheme("midnight");
    } catch { applyTheme("midnight"); }
  } else {
    applyTheme("midnight");
  }
}
