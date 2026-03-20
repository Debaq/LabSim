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
      "--ls-text": "#111318",
      "--ls-text-secondary": "#2a3040",
      "--ls-text-muted": "#5a6578",
      "--ls-accent": "#0b5fa5",
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

export type FontSize = "small" | "medium" | "large";

const FONT_SCALES: Record<FontSize, string> = {
  small: "0.85",
  medium: "1",
  large: "1.15",
};

interface ThemeState {
  theme: ThemeName;
  fontSize: FontSize;
  wallpaperColor: string | null; // null = use theme default
  setTheme: (theme: ThemeName) => void;
  setFontSize: (size: FontSize) => void;
  setWallpaperColor: (color: string | null) => void;
}

function applyTheme(theme: ThemeName, fontSize: FontSize = "medium", wallpaper: string | null = null) {
  const t = THEMES[theme];
  if (!t) return;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(t.vars)) {
    root.style.setProperty(key, value);
  }
  // Custom wallpaper overrides the theme gradient
  if (wallpaper) {
    root.style.setProperty("--ls-desktop-gradient", wallpaper);
    root.style.setProperty("--ls-desktop-bg", wallpaper);
  }
  root.style.setProperty("--ls-font-scale", FONT_SCALES[fontSize]);
  root.style.fontSize = `${parseFloat(FONT_SCALES[fontSize]) * 100}%`;
  root.className = root.className.replace(/theme-\S+/g, "").trim();
  root.classList.add(`theme-${theme}`);
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "midnight",
      fontSize: "medium",
      wallpaperColor: null,
      setTheme: (theme) => { set({ theme, wallpaperColor: null }); applyTheme(theme, get().fontSize, null); },
      setFontSize: (fontSize) => { set({ fontSize }); applyTheme(get().theme, fontSize, get().wallpaperColor); },
      setWallpaperColor: (color) => { set({ wallpaperColor: color }); applyTheme(get().theme, get().fontSize, color); },
    }),
    {
      name: "labsim-theme",
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme, state.fontSize, state.wallpaperColor);
      },
    },
  ),
);

if (typeof window !== "undefined") {
  const stored = localStorage.getItem("labsim-theme");
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.theme && THEMES[state.theme as ThemeName]) applyTheme(state.theme, state.fontSize ?? "medium", state.wallpaperColor ?? null);
      else applyTheme("midnight");
    } catch { applyTheme("midnight"); }
  } else {
    applyTheme("midnight");
  }
}
