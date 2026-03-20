import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  username: null,

  login: async (username: string, password: string) => {
    const result = await invoke<boolean>("login", { username, password });
    if (!result) throw new Error("Credenciales inválidas");
    set({ isAuthenticated: true, username });
  },

  logout: () => {
    set({ isAuthenticated: false, username: null });
  },
}));
