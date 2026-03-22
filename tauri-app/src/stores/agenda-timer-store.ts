import { create } from "zustand";
import { useChatStore, nextMsgId, timeNow } from "./chat-store";
import { invoke } from "@tauri-apps/api/core";

/**
 * Monitorea la agenda activa del estudiante y genera:
 * - Avisos de Karime según directrices configuradas
 * - Feedback automático de pacientes (reclamos/felicitaciones)
 *
 * Los mensajes de Karime se adaptan al tono y tratamiento
 * configurado por admin/docente/instructor.
 */

interface ActiveAppointment {
  id: string;
  patientName: string;
  procedureName?: string;
  scheduledTime: string;
  durationMinutes: number;
  startedAt: number | null;
}

/** Directrices resueltas del backend */
interface ResolvedDirectives {
  studentTreatment: string;  // "formal", nombre, custom
  tone: "profesional" | "amigable" | "estricto" | "relajado";
  pressureLevel: number;     // 1-5
  customMessages: Record<string, string[]>;
  rules: string;
}

const DEFAULT_DIRECTIVES: ResolvedDirectives = {
  studentTreatment: "formal",
  tone: "profesional",
  pressureLevel: 2,
  customMessages: {},
  rules: "",
};

// ─── Plantillas de mensajes por tono ────────────────
// {treatment} = forma de dirigirse al estudiante
// {patient} = nombre del paciente

const MESSAGES: Record<string, Record<string, string[]>> = {
  profesional: {
    start: [
      "{treatment}, {patient} ya se encuentra en el box. Procedimiento: {procedure}. Tiempo asignado: {duration} minutos.",
      "{treatment}, el paciente {patient} está listo para ser atendido. Dispone de {duration} minutos.",
    ],
    reminder: [
      "{treatment}, le quedan aproximadamente 5 minutos con {patient}.",
      "{treatment}, el tiempo asignado para {patient} está por finalizar.",
    ],
    warning: [
      "{treatment}, ha excedido el tiempo asignado con {patient} por 5 minutos. El siguiente paciente aguarda.",
      "{treatment}, lleva 5 minutos de retraso con {patient}. Hay pacientes en sala de espera.",
    ],
    urgent: [
      "{treatment}, van 15 minutos de retraso con {patient}. Los pacientes están consultando por la demora.",
      "{treatment}, 15 minutos sobre el tiempo asignado. El supervisor ha sido notificado de la situación.",
    ],
    critical: [
      "{treatment}, lleva 30 minutos de retraso. Un paciente ha solicitado hablar con el encargado del servicio.",
      "{treatment}, alerta de 30 minutos de exceso. Se registrará en el informe de la sesión.",
    ],
    onTime: [
      "{treatment}, {patient} ya se retiró. {nextPatient}",
      "{treatment}, listo con {patient}. {nextPatient}",
    ],
    rescheduleComplaint: [
      "{treatment}, el paciente {patient} presentó una queja por el cambio de horario. Indicó que tuvo dificultades para reorganizar su agenda.",
      "{treatment}, {patient} dejó un reclamo en recepción por el reagendamiento de su cita.",
    ],
  },

  amigable: {
    start: [
      "¡Hola {treatment}! {patient} ya está en el box, viene por {procedure}. Tienes {duration} minutitos 😊",
      "{treatment}, ya llegó {patient}. ¡{duration} min y a darle! 💪",
    ],
    reminder: [
      "{treatment}, ojo que te quedan como 5 min con {patient} ⏰",
      "Hey {treatment}, ya casi se acaba el tiempo con {patient}, ve cerrando 🕐",
    ],
    warning: [
      "{treatment}, ya te pasaste 5 min con {patient}... el que sigue ya está esperando 😅",
      "Eeem {treatment}, van 5 min de más con {patient}, la sala se está llenando",
    ],
    urgent: [
      "¡{treatment}! Ya van 15 min de atraso con {patient} 😰 Los pacientes están preguntando...",
      "{treatment}, 15 minutos extra... hay 2 pacientes esperando y uno está impaciente 😬",
    ],
    critical: [
      "{treatment}... 30 minutos de atraso 😓 Un paciente pidió hablar con el jefe de servicio. Hay que terminar ya.",
      "Ay {treatment}, 30 min de retraso. Un paciente se fue sin atenderse y otro quiere poner un reclamo 😞",
    ],
    onTime: [
      "{treatment}, ya se fue {patient}. {nextPatient}",
      "Listo {treatment}, {patient} terminó. {nextPatient}",
    ],
    rescheduleComplaint: [
      "{treatment}, {patient} no quedó nada contento con el cambio de hora 😕 Dejó un reclamo.",
      "Uf {treatment}, {patient} se molestó por el reagendamiento. Dice que pidió permiso en su trabajo para venir hoy.",
    ],
  },

  estricto: {
    start: [
      "{treatment}, el paciente {patient} está en el box. Tiene exactamente {duration} minutos. Comience.",
      "{treatment}, {patient} aguarda. {duration} minutos asignados. No hay margen de extensión.",
    ],
    reminder: [
      "{treatment}, 5 minutos restantes con {patient}. Vaya cerrando.",
      "{treatment}, le quedan 5 minutos. Administre su tiempo.",
    ],
    warning: [
      "{treatment}, 5 minutos de retraso con {patient}. Esto afecta a todos los pacientes siguientes.",
      "{treatment}, ha excedido su tiempo. El siguiente paciente lleva esperando 5 minutos.",
    ],
    urgent: [
      "{treatment}, 15 minutos de retraso. Esto es inaceptable. Hay pacientes que llevan esperando más de lo razonable.",
      "{treatment}, va 15 minutos tarde. El supervisor será informado. Necesita finalizar inmediatamente.",
    ],
    critical: [
      "{treatment}, 30 minutos de retraso. Esto tendrá consecuencias en su evaluación. Finalice ahora.",
      "{treatment}, alerta crítica: 30 minutos de exceso. Un paciente se retiró y otro presentó queja formal.",
    ],
    onTime: [
      "{treatment}, {patient} se retiró. {nextPatient}",
      "{treatment}, terminó con {patient}. {nextPatient}",
    ],
    rescheduleComplaint: [
      "{treatment}, el paciente {patient} presentó un reclamo formal por el reagendamiento. Esto será informado al docente.",
      "{treatment}, {patient} dejó una queja seria por el cambio de cita. El supervisor será notificado.",
    ],
  },

  relajado: {
    start: [
      "Hola {treatment}, {patient} ya está ahí. Tranqui, tienes {duration} min 😌",
      "{treatment}, viene {patient} por {procedure}. {duration} min, sin apuro.",
    ],
    reminder: [
      "{treatment}, como para ir cerrando con {patient}, quedan unos 5 min.",
      "Aviso suave: quedan 5 min con {patient}, {treatment}.",
    ],
    warning: [
      "{treatment}, te aviso que vas 5 min pasado con {patient}, nada grave pero hay gente esperando.",
      "Oye {treatment}, 5 min extra con {patient}. No pasa nada pero el que sigue ya llegó.",
    ],
    urgent: [
      "{treatment}, ya son 15 min... sería bueno ir cerrando con {patient} cuando puedas.",
      "{treatment}, van 15 min de más. Entiende que a veces pasa, pero conviene apurar un poco.",
    ],
    critical: [
      "{treatment}, 30 min ya es bastante... los pacientes se están quejando. Hay que terminar.",
      "{treatment}, ya son 30 min extra. Lamentablemente un paciente se fue y dejó un reclamo.",
    ],
    onTime: [
      "{treatment}, {patient} ya salió. {nextPatient}",
      "Ya {treatment}, {patient} listo. {nextPatient}",
    ],
    rescheduleComplaint: [
      "{treatment}, {patient} no quedó muy contento con el cambio... dejó un comentario.",
      "Te aviso {treatment}, {patient} se quejó un poco por el reagendamiento.",
    ],
  },
};

function randomPick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function formatMessage(template: string, vars: Record<string, string>): string {
  let msg = template;
  for (const [key, val] of Object.entries(vars)) {
    msg = msg.replaceAll(`{${key}}`, val);
  }
  return msg;
}

interface AgendaTimerState {
  activeAppointment: ActiveAppointment | null;
  directives: ResolvedDirectives;
  alertsSent: Record<string, string[]>;
  checkInterval: ReturnType<typeof setInterval> | null;

  loadDirectives: (sessionId?: string) => Promise<void>;
  startAppointment: (appointment: ActiveAppointment) => void;
  endAppointment: (nextPatientName?: string) => void;
  triggerRescheduleConsequence: (patientName: string, agendaItemId: string) => void;
  _tick: () => void;
  _sendKarime: (category: string, extraVars?: Record<string, string>) => void;
}

export const useAgendaTimerStore = create<AgendaTimerState>((set, get) => ({
  activeAppointment: null,
  directives: { ...DEFAULT_DIRECTIVES },
  alertsSent: {},
  checkInterval: null,

  loadDirectives: async (sessionId) => {
    try {
      const result = await invoke<{ directives: ResolvedDirectives }>("api_resolve_directives", {
        sessionId: sessionId ?? null,
      });
      if (result?.directives) {
        set({ directives: result.directives });
      }
    } catch {
      // Usar directrices por defecto
    }
  },

  _sendKarime: (category, extraVars = {}) => {
    const { activeAppointment, directives } = get();
    const tone = directives.tone || "profesional";
    const toneMessages = MESSAGES[tone] ?? MESSAGES.profesional;
    const templates = toneMessages[category];
    if (!templates || templates.length === 0) return;

    // Resolver tratamiento
    let treatment = directives.studentTreatment || "formal";
    if (treatment === "formal") treatment = "Estimado/a";

    const vars: Record<string, string> = {
      treatment,
      patient: activeAppointment?.patientName ?? "el paciente",
      procedure: activeAppointment?.procedureName ?? "evaluación",
      duration: String(activeAppointment?.durationMinutes ?? 30),
      ...extraVars,
    };

    const msg = formatMessage(randomPick(templates), vars);

    useChatStore.getState().addMessage("karime", {
      id: nextMsgId(),
      contactId: "karime",
      sender: "other",
      text: msg,
      time: timeNow(),
      status: "delivered",
    });
  },

  startAppointment: (appointment) => {
    const prev = get().checkInterval;
    if (prev) clearInterval(prev);

    const appt = { ...appointment, startedAt: Date.now() };
    const interval = setInterval(() => get()._tick(), 30000);

    set({
      activeAppointment: appt,
      checkInterval: interval,
      alertsSent: { ...get().alertsSent, [appt.id]: [] },
    });

    get()._sendKarime("start");
  },

  endAppointment: (nextPatientName?: string) => {
    const { activeAppointment, checkInterval } = get();
    if (!activeAppointment?.startedAt) return;

    if (checkInterval) clearInterval(checkInterval);

    // Karime avisa del siguiente paciente (o que no hay más)
    const nextInfo = nextPatientName
      ? `El siguiente es ${nextPatientName}, ya está en sala de espera.`
      : "No hay más pacientes por ahora.";
    get()._sendKarime("onTime", { nextPatient: nextInfo });

    set({ activeAppointment: null, checkInterval: null });
  },

  triggerRescheduleConsequence: (patientName, agendaItemId) => {
    const { directives } = get();
    // Probabilidad de queja depende del nivel de presión (1=20%, 5=80%)
    const complainChance = 0.1 + (directives.pressureLevel * 0.14);
    if (Math.random() > complainChance) return;

    get()._sendKarime("rescheduleComplaint", { patient: patientName });

    sendFeedback(agendaItemId, "complaint", "rescheduled",
      `Paciente ${patientName} se quejó por reagendamiento de cita`
    ).catch(() => {});
  },

  _tick: () => {
    const { activeAppointment, alertsSent, directives } = get();
    if (!activeAppointment?.startedAt) return;

    const elapsed = Math.round((Date.now() - activeAppointment.startedAt) / 60000);
    const limit = activeAppointment.durationMinutes;
    const remaining = limit - elapsed;
    const over = elapsed - limit;
    const sent = alertsSent[activeAppointment.id] ?? [];

    // Ajustar umbrales según pressureLevel (1=relajado, 5=estricto)
    const pl = directives.pressureLevel;
    const reminderAt = Math.max(2, 8 - pl);       // pl=1→7min, pl=5→3min antes
    const warningAt = Math.max(2, 8 - pl);         // pl=1→7min, pl=5→3min después
    const urgentAt = Math.max(8, 20 - pl * 2);     // pl=1→18min, pl=5→10min después
    const criticalAt = Math.max(15, 35 - pl * 3);  // pl=1→32min, pl=5→20min después

    // Recordatorio
    if (remaining <= reminderAt && remaining > 0 && !sent.includes("reminder")) {
      get()._sendKarime("reminder");
      set({ alertsSent: { ...alertsSent, [activeAppointment.id]: [...sent, "reminder"] } });
      return;
    }

    // Warning
    if (over >= warningAt && !sent.includes("warning")) {
      get()._sendKarime("warning");
      set({ alertsSent: { ...alertsSent, [activeAppointment.id]: [...sent, "warning"] } });
      return;
    }

    // Urgent
    if (over >= urgentAt && !sent.includes("urgent")) {
      get()._sendKarime("urgent");
      const newSent = [...sent, "urgent"];
      set({ alertsSent: { ...alertsSent, [activeAppointment.id]: newSent } });
      sendFeedback(activeAppointment.id, "complaint", "overtime",
        `${over} minutos de exceso con paciente ${activeAppointment.patientName}`, 2
      ).catch(() => {});
      return;
    }

    // Critical
    if (over >= criticalAt && !sent.includes("critical")) {
      get()._sendKarime("critical");
      const newSent = [...sent, "critical"];
      set({ alertsSent: { ...alertsSent, [activeAppointment.id]: newSent } });
      sendFeedback(activeAppointment.id, "complaint", "overtime",
        `${over} minutos de exceso (crítico) con paciente ${activeAppointment.patientName}`, 3
      ).catch(() => {});
      return;
    }
  },
}));

async function sendFeedback(
  agendaItemId: string,
  type: "complaint" | "compliment",
  reason: string,
  message: string,
  severity = 1,
): Promise<void> {
  try {
    await invoke("api_send_feedback", {
      feedback: { agendaItemId, studentId: "", feedbackType: type, reason, message, severity },
    });
  } catch {
    // offline
  }
}
