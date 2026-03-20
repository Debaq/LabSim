import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export type UserRole = "admin" | "docente" | "estudiante";

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  role: UserRole;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  username: null,
  role: "estudiante",
  isAdmin: false,

  login: async (username: string, password: string) => {
    const result = await invoke<{ success: boolean; role: string }>("login", {
      username,
      password,
    });
    if (!result.success) throw new Error("Credenciales inválidas");
    const role = (result.role ?? "estudiante") as UserRole;
    set({
      isAuthenticated: true,
      username,
      role,
      isAdmin: role === "admin" || role === "docente",
    });
  },

  logout: () => {
    set({
      isAuthenticated: false,
      username: null,
      role: "estudiante",
      isAdmin: false,
    });
  },
}));
