import { create } from "zustand";

export interface WindowState {
  id: string;
  title: string;
  component: string;
  x: number;
  y: number;
  width: number;
  height: number;
  minimized: boolean;
  zIndex: number;
}

interface UIState {
  activeTab: string;
  windows: WindowState[];
  nextZ: number;

  setActiveTab: (tab: string) => void;

  openWindow: (id: string, title: string, component: string, opts?: Partial<WindowState>) => void;
  closeWindow: (id: string) => void;
  focusWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  restoreWindow: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: "patient-info",
  windows: [],
  nextZ: 100,

  setActiveTab: (tab) => set({ activeTab: tab }),

  openWindow: (id, title, component, opts) =>
    set((state) => {
      const existing = state.windows.find((w) => w.id === id);
      if (existing) {
        // Si ya existe, restaurar y enfocar
        return {
          windows: state.windows.map((w) =>
            w.id === id ? { ...w, minimized: false, zIndex: state.nextZ } : w,
          ),
          nextZ: state.nextZ + 1,
        };
      }
      const offsetIndex = state.windows.length;
      const newWindow: WindowState = {
        id,
        title,
        component,
        x: 80 + offsetIndex * 30,
        y: 40 + offsetIndex * 30,
        width: 850,
        height: 570,
        minimized: false,
        zIndex: state.nextZ,
        ...opts,
      };
      return {
        windows: [...state.windows, newWindow],
        nextZ: state.nextZ + 1,
      };
    }),

  closeWindow: (id) =>
    set((state) => ({
      windows: state.windows.filter((w) => w.id !== id),
    })),

  focusWindow: (id) =>
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, zIndex: state.nextZ } : w,
      ),
      nextZ: state.nextZ + 1,
    })),

  minimizeWindow: (id) =>
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, minimized: true } : w,
      ),
    })),

  restoreWindow: (id) =>
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, minimized: false, zIndex: state.nextZ } : w,
      ),
      nextZ: state.nextZ + 1,
    })),
}));
