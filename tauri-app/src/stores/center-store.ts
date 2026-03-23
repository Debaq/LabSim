import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";
import { useChatStore, nextMsgId, timeNow } from "./chat-store";
import { useAgendaTimerStore } from "./agenda-timer-store";

interface Box {
  id: string;
  box_number: number;
  name: string;
  student_id?: string;
  student_name?: string;
  student_username?: string;
  equipment_list?: string;
  agenda: AgendaItem[];
  incidents: Incident[];
}

interface AgendaItem {
  id: string;
  patient_name: string;
  scheduled_time: string;
  duration_minutes: number;
  procedure_name?: string;
  status: string;
}

interface Incident {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  affected_box?: number;
  trigger_time_minutes?: number;
  created_at: string;
}

interface IncidentTemplate {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  trigger_time_minutes?: number;
}

interface Meeting {
  id: string;
  title: string;
  status: string;
  caller_name?: string;
  participant_count: number;
  incident_count: number;
  agenda_text?: string;
  minutes_text?: string;
  decisions_text?: string;
}

interface ChatMessage {
  id: string;
  sender_id: string;
  sender_name?: string;
  sender_username?: string;
  recipient_id?: string;
  message: string;
  message_type: string;
  created_at: string;
}

interface CentroSession {
  id: string;
  title: string;
  scheduled_date: string | null;
  end_date: string | null;
  session_type: string | null;
  centro_enabled: number;
  status: string;
}

interface CenterState {
  // Selección de centro
  centroSessions: CentroSession[];
  centroLoading: boolean;

  sessionId: string | null;
  boxes: Box[];
  incidents: Incident[];
  meetings: Meeting[];
  chatMessages: ChatMessage[];
  templates: IncidentTemplate[];
  sessionStartTime: number | null;
  scheduledIncidents: IncidentTemplate[];
  isActive: boolean;

  // Acciones principales
  fetchCentroSessions: () => Promise<void>;
  initCenter: (sessionId: string) => Promise<void>;
  refreshBoxes: () => Promise<void>;
  refreshIncidents: () => Promise<void>;
  refreshMeetings: () => Promise<void>;
  refreshChat: () => Promise<void>;
  stopCenter: () => void;

  // Boxes
  createBoxes: (count: number) => Promise<void>;
  assignStudentToBox: (boxId: string, studentId: string) => Promise<void>;

  // Incidentes
  loadTemplates: () => Promise<void>;
  injectIncident: (templateId?: string, custom?: { title: string; description: string; category: string; severity: string }, affectedBox?: number) => Promise<void>;
  resolveIncident: (incidentId: string, notes?: string) => Promise<void>;
  discussIncident: (incidentId: string) => Promise<void>;
  scheduleIncidents: (incidents: IncidentTemplate[]) => void;

  // Reuniones
  callMeeting: (title: string, agendaText?: string, incidentIds?: string[]) => Promise<void>;
  startMeeting: (meetingId: string) => Promise<void>;
  endMeeting: (meetingId: string, minutes?: string, decisions?: string) => Promise<void>;

  // Chat
  sendChatMessage: (message: string, recipientId?: string) => Promise<void>;

  // Agenda
  startPatientAttention: (agendaItem: AgendaItem) => Promise<void>;
  endPatientAttention: (agendaItemId: string) => Promise<void>;

  // Interno
  _incidentTick: () => void;
}

let refreshInterval: ReturnType<typeof setInterval> | null = null;
let incidentInterval: ReturnType<typeof setInterval> | null = null;

export const useCenterStore = create<CenterState>((set, get) => ({
  centroSessions: [],
  centroLoading: false,

  sessionId: null,
  boxes: [],
  incidents: [],
  meetings: [],
  chatMessages: [],
  templates: [],
  sessionStartTime: null,
  scheduledIncidents: [],
  isActive: false,

  fetchCentroSessions: async () => {
    set({ centroLoading: true });
    try {
      const result = await invoke<{ items: CentroSession[] }>("api_get_sessions", {});
      const all = result?.items ?? [];
      const sessions = all.filter((s) => {
        const ce = (s as any).centro_enabled ?? (s as any).centroEnabled;
        return (ce === 1 || ce === true || ce === "1" || ce === "true") && s.status !== "cancelled";
      });
      set({ centroSessions: sessions });
    } catch {
      set({ centroSessions: [] });
    } finally {
      set({ centroLoading: false });
    }
  },

  initCenter: async (sessionId) => {
    set({ sessionId, sessionStartTime: Date.now(), isActive: true });

    // Cargar datos iniciales en paralelo
    await Promise.all([
      get().refreshBoxes(),
      get().refreshIncidents(),
      get().refreshMeetings(),
      get().loadTemplates(),
      get().refreshChat(),
    ]);

    // Cargar directrices de Karime para esta sesión
    useAgendaTimerStore.getState().loadDirectives(sessionId);

    // Refresh automático cada 10 segundos
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
      if (get().isActive) {
        get().refreshIncidents();
        get().refreshChat();
      }
    }, 10000);

    // Check de incidentes programados cada 30 segundos
    if (incidentInterval) clearInterval(incidentInterval);
    incidentInterval = setInterval(() => get()._incidentTick(), 30000);
  },

  stopCenter: () => {
    if (refreshInterval) { clearInterval(refreshInterval); refreshInterval = null; }
    if (incidentInterval) { clearInterval(incidentInterval); incidentInterval = null; }
    set({ isActive: false, sessionId: null, sessionStartTime: null });
  },

  refreshBoxes: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const result = await invoke<{ boxes: Box[] }>("api_get_boxes", { sessionId });
      set({ boxes: result?.boxes ?? [] });
    } catch { /* offline */ }
  },

  refreshIncidents: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const result = await invoke<{ incidents: Incident[] }>("api_get_incidents", { sessionId });
      set({ incidents: result?.incidents ?? [] });
    } catch { /* offline */ }
  },

  refreshMeetings: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const result = await invoke<{ meetings: Meeting[] }>("api_get_meetings", { sessionId });
      set({ meetings: result?.meetings ?? [] });
    } catch { /* offline */ }
  },

  refreshChat: async () => {
    const { sessionId, chatMessages } = get();
    if (!sessionId) return;
    try {
      const lastMsg = chatMessages[chatMessages.length - 1];
      const since = lastMsg?.created_at;
      const result = await invoke<{ messages: ChatMessage[] }>("api_get_chat", {
        sessionId, since,
      });
      if (result?.messages?.length) {
        set((s) => ({
          chatMessages: [...s.chatMessages, ...result.messages],
        }));
        // Notificar mensajes nuevos via Karime si son de sistema
        for (const msg of result.messages) {
          if (msg.message_type === "meeting_call" || msg.message_type === "incident") {
            useChatStore.getState().addMessage("karime", {
              id: nextMsgId(),
              contactId: "karime",
              sender: "other",
              text: msg.message,
              time: timeNow(),
              status: "delivered",
            });
          }
        }
      }
    } catch { /* offline */ }
  },

  loadTemplates: async () => {
    try {
      const result = await invoke<{ templates: IncidentTemplate[] }>("api_get_incident_templates", {
        category: null,
      });
      set({ templates: result?.templates ?? [] });
    } catch { /* offline */ }
  },

  createBoxes: async (count) => {
    const { sessionId } = get();
    if (!sessionId) return;
    await invoke("api_create_boxes", { sessionId, boxCount: count });
    await get().refreshBoxes();
  },

  assignStudentToBox: async (boxId, studentId) => {
    await invoke("api_assign_box", { boxId, studentId });
    await get().refreshBoxes();
  },

  injectIncident: async (templateId, custom, affectedBox) => {
    const { sessionId } = get();
    if (!sessionId) return;

    const payload: Record<string, unknown> = { sessionId };
    if (templateId) {
      payload.templateId = templateId;
    } else if (custom) {
      payload.title = custom.title;
      payload.description = custom.description;
      payload.category = custom.category;
      payload.severity = custom.severity;
    }
    if (affectedBox != null) payload.affectedBox = affectedBox;

    await invoke("api_inject_incident", { incident: payload });
    await get().refreshIncidents();

    // Notificar por Karime
    const title = custom?.title ?? "Nuevo incidente";
    useChatStore.getState().addMessage("karime", {
      id: nextMsgId(),
      contactId: "karime",
      sender: "other",
      text: `⚠️ ATENCIÓN: ${title}${affectedBox ? ` (Box ${affectedBox})` : ""}`,
      time: timeNow(),
      status: "delivered",
    });
  },

  resolveIncident: async (incidentId, notes) => {
    await invoke("api_resolve_incident", { incidentId, notes });
    await get().refreshIncidents();
  },

  discussIncident: async (incidentId) => {
    await invoke("api_discuss_incident", { incidentId });
    await get().refreshIncidents();
  },

  scheduleIncidents: (incidents) => {
    set({ scheduledIncidents: incidents });
  },

  callMeeting: async (title, agendaText, incidentIds) => {
    const { sessionId } = get();
    if (!sessionId) return;
    await invoke("api_call_meeting", {
      meeting: { sessionId, title, agendaText, incidentIds: incidentIds ?? [] },
    });
    await get().refreshMeetings();
  },

  startMeeting: async (meetingId) => {
    await invoke("api_start_meeting", { meetingId });
    await get().refreshMeetings();
  },

  endMeeting: async (meetingId, minutes, decisions) => {
    await invoke("api_end_meeting", { meetingId, minutes, decisions });
    await get().refreshMeetings();
  },

  sendChatMessage: async (message, recipientId) => {
    const { sessionId } = get();
    if (!sessionId) return;
    await invoke("api_send_chat", {
      message: { sessionId, message, recipientId },
    });
    await get().refreshChat();
  },

  startPatientAttention: async (agendaItem) => {
    await invoke("api_update_appointment_status", {
      appointmentId: agendaItem.id,
      status: "in_progress",
      notes: null,
    });

    // Iniciar timer de Karime
    useAgendaTimerStore.getState().startAppointment({
      id: agendaItem.id,
      patientName: agendaItem.patient_name,
      procedureName: agendaItem.procedure_name,
      scheduledTime: agendaItem.scheduled_time,
      durationMinutes: agendaItem.duration_minutes,
      startedAt: null,
    });

    await get().refreshBoxes();
  },

  endPatientAttention: async (agendaItemId) => {
    await invoke("api_update_appointment_status", {
      appointmentId: agendaItemId,
      status: "completed",
      notes: null,
    });

    useAgendaTimerStore.getState().endAppointment();
    await get().refreshBoxes();
  },

  _incidentTick: () => {
    const { sessionStartTime, scheduledIncidents, sessionId } = get();
    if (!sessionStartTime || !sessionId || scheduledIncidents.length === 0) return;

    const elapsedMinutes = Math.round((Date.now() - sessionStartTime) / 60000);

    const toInject = scheduledIncidents.filter(
      (inc) => inc.trigger_time_minutes != null && inc.trigger_time_minutes <= elapsedMinutes,
    );

    if (toInject.length > 0) {
      // Remover los inyectados de la cola
      set({
        scheduledIncidents: scheduledIncidents.filter(
          (inc) => !toInject.includes(inc),
        ),
      });

      // Inyectar cada uno
      for (const inc of toInject) {
        get().injectIncident(inc.id);
      }
    }
  },
}));
