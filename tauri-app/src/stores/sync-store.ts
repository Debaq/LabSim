import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

type ConnectionStatus = "online" | "checking" | "offline";

interface SyncState {
  isOnline: ConnectionStatus;
  lastSync: string | null;
  isSyncing: boolean;

  checkConnection: () => Promise<void>;
  syncCases: (since?: string) => Promise<unknown>;
  pushCase: (caseData: Record<string, unknown>) => Promise<unknown>;
  getAgenda: (from?: string, to?: string) => Promise<unknown>;
  getSessions: (status?: string) => Promise<unknown>;
  getSessionDetail: (sessionId: string) => Promise<unknown>;
  getSubmissions: (sessionId?: string) => Promise<unknown>;
  submitWork: (sessionId: string, caseId: string, data: Record<string, unknown>) => Promise<unknown>;
  checkUpdate: () => Promise<unknown>;
  getMyStats: () => Promise<unknown>;
}

export const useSyncStore = create<SyncState>((set, get) => ({
  isOnline: "offline",
  lastSync: null,
  isSyncing: false,

  checkConnection: async () => {
    set({ isOnline: "checking" });
    try {
      const online = await invoke<boolean>("api_ping");
      set({ isOnline: online ? "online" : "offline" });
    } catch {
      set({ isOnline: "offline" });
    }
  },

  syncCases: async (since) => {
    const effectiveSince = since ?? get().lastSync ?? undefined;
    set({ isSyncing: true });
    try {
      const result = await invoke("api_sync_cases", { since: effectiveSince });
      set({ lastSync: new Date().toISOString(), isSyncing: false });
      return result;
    } catch (e) {
      set({ isSyncing: false });
      throw e;
    }
  },

  pushCase: (caseData) => invoke("api_push_case", { caseData }),
  getAgenda: (from, to) => invoke("api_get_agenda", { from, to }),
  getSessions: (status) => invoke("api_get_sessions", { status }),
  getSessionDetail: (sessionId) => invoke("api_get_session_detail", { sessionId }),
  getSubmissions: (sessionId) => invoke("api_get_submissions", { sessionId }),
  submitWork: (sessionId, caseId, submissionJson) =>
    invoke("api_submit_work", { sessionId, caseId, submissionJson }),
  checkUpdate: () => invoke("api_check_update"),
  getMyStats: () => invoke("api_get_my_stats"),
}));
