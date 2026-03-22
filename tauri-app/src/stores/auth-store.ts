import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export type UserRole = "admin" | "docente" | "instructor" | "estudiante";

interface UserInfo {
  id: string;
  username: string;
  role: UserRole;
  fullName?: string;
  email?: string;
  institution?: string;
  mustChangePassword?: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  role: UserRole;
  isAdmin: boolean;
  isOnline: boolean;
  loginSource: "server" | "local" | null;
  userInfo: UserInfo | null;
  mustChangePassword: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearMustChangePassword: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  username: null,
  role: "estudiante",
  isAdmin: false,
  isOnline: false,
  loginSource: null,
  userInfo: null,
  mustChangePassword: false,

  login: async (username: string, password: string) => {
    // Login exclusivamente contra el servidor
    const result = await invoke<{
      success: boolean;
      user: UserInfo | null;
      source: string;
    }>("api_login", { username, password });

    if (!result.success || !result.user) {
      throw new Error("Credenciales inválidas");
    }

    const role = (result.user.role ?? "estudiante") as UserRole;
    const needsPasswordChange = !!result.user.mustChangePassword;

    set({
      // No autenticar si debe cambiar contraseña — queda en login
      isAuthenticated: !needsPasswordChange,
      username: result.user.username,
      role,
      isAdmin: role === "admin" || role === "docente",
      isOnline: true,
      loginSource: "server",
      userInfo: result.user,
      mustChangePassword: needsPasswordChange,
    });
  },

  logout: async () => {
    try {
      await invoke("api_logout");
    } catch {
      // Ignorar si no hay conexión
    }
    set({
      isAuthenticated: false,
      username: null,
      role: "estudiante",
      isAdmin: false,
      isOnline: false,
      loginSource: null,
      userInfo: null,
      mustChangePassword: false,
    });
  },

  clearMustChangePassword: () => set({ mustChangePassword: false, isAuthenticated: true }),
}));
