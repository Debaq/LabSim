import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

interface TelemetryEvent {
  simulator: string;
  eventType: string;
  eventData: Record<string, unknown>;
  timestamp: string;
}

interface TelemetryState {
  sessionId: string | null;
  eventBuffer: TelemetryEvent[];
  encounterStart: number | null;
  moduleTimers: Record<string, number>;
  windowTimers: Record<string, number>;

  startSession: (caseId?: string, assignmentId?: string) => Promise<void>;
  endSession: () => Promise<void>;
  trackEvent: (simulator: string, eventType: string, data?: Record<string, unknown>) => void;
  trackModuleOpen: (moduleId: string) => void;
  trackModuleClose: (moduleId: string) => void;
  trackWindowOpen: (windowId: string) => void;
  trackWindowClose: (windowId: string) => void;
  flush: () => Promise<void>;
}

let flushInterval: ReturnType<typeof setInterval> | null = null;

export const useTelemetryStore = create<TelemetryState>((set, get) => ({
  sessionId: null,
  eventBuffer: [],
  encounterStart: null,
  moduleTimers: {},
  windowTimers: {},

  startSession: async (caseId, assignmentId) => {
    try {
      const sessionId = await invoke<string>("telemetry_start_session", {
        caseId: caseId ?? null,
        assignmentId: assignmentId ?? null,
        appVersion: "3.0.0",
        os: navigator.platform,
      });
      set({ sessionId, encounterStart: Date.now(), eventBuffer: [] });

      // Auto-flush cada 30 segundos
      if (flushInterval) clearInterval(flushInterval);
      flushInterval = setInterval(() => get().flush(), 30000);
    } catch {
      // Si no hay conexión, sesión local
      set({ sessionId: `local_${Date.now()}`, encounterStart: Date.now(), eventBuffer: [] });
    }
  },

  endSession: async () => {
    const { sessionId, encounterStart } = get();
    if (!sessionId) return;

    // Flush final
    await get().flush();

    const duration = encounterStart ? Math.round((Date.now() - encounterStart) / 1000) : 0;
    try {
      await invoke("telemetry_end_session", { sessionId, durationSecs: duration });
    } catch {
      // Offline: se enviará después
    }

    if (flushInterval) {
      clearInterval(flushInterval);
      flushInterval = null;
    }
    set({ sessionId: null, encounterStart: null, moduleTimers: {}, windowTimers: {} });
  },

  trackEvent: (simulator, eventType, data = {}) => {
    const event: TelemetryEvent = {
      simulator,
      eventType,
      eventData: data,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({ eventBuffer: [...state.eventBuffer, event] }));
  },

  trackModuleOpen: (moduleId) => {
    set((state) => ({
      moduleTimers: { ...state.moduleTimers, [moduleId]: Date.now() },
    }));
    get().trackEvent("module", "module.opened", { moduleId });
  },

  trackModuleClose: (moduleId) => {
    const startTime = get().moduleTimers[moduleId];
    if (startTime) {
      const secs = Math.round((Date.now() - startTime) / 1000);
      get().trackEvent("module", "module.time_spent", { moduleId, seconds: secs });
    }
  },

  trackWindowOpen: (windowId) => {
    set((state) => ({
      windowTimers: { ...state.windowTimers, [windowId]: Date.now() },
    }));
    get().trackEvent("session", "session.window_opened", { windowId });
  },

  trackWindowClose: (windowId) => {
    const startTime = get().windowTimers[windowId];
    if (startTime) {
      const secs = Math.round((Date.now() - startTime) / 1000);
      get().trackEvent("session", "session.window_closed", { windowId, timeSpent: secs });
    }
  },

  flush: async () => {
    const { sessionId, eventBuffer } = get();
    if (!sessionId || eventBuffer.length === 0) return;

    const events = [...eventBuffer];
    set({ eventBuffer: [] });

    try {
      await invoke("telemetry_push_events", {
        sessionId,
        events: events.map((e) => ({
          simulator: e.simulator,
          event_type: e.eventType,
          event_data: e.eventData,
          timestamp: e.timestamp,
        })),
      });
    } catch {
      // Re-agregar al buffer si falló
      set((state) => ({ eventBuffer: [...events, ...state.eventBuffer] }));
    }
  },
}));
