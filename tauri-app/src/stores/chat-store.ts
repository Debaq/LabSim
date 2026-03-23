import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface Contact {
  id: string;
  name: string;
  avatar: string;
  subtitle: string;
  personaId: string;
  color: string;
  online: boolean;
}

export interface Message {
  id: string;
  contactId: string;
  sender: "user" | "other";
  text: string;
  time: string;
  status: "sent" | "delivered" | "read";
  /** ID de voz TTS para reproducir este mensaje (ej: "karime", "male", "female") */
  voiceId?: string;
  /** true si es un mensaje de voz (se muestra como nota de audio, no texto) */
  isVoice?: boolean;
  /** Duración del audio en segundos */
  voiceDurationSecs?: number;
}

interface ChatState {
  contacts: Contact[];
  conversations: Record<string, Message[]>;
  activeContact: string | null;
  unreadCounts: Record<string, number>;
  llmConnected: boolean;
  lastModelId: string | null;
  lastModelFilename: string | null;

  setActiveContact: (id: string | null) => void;
  addMessage: (contactId: string, message: Message) => void;
  markAsRead: (contactId: string) => void;
  setLlmConnected: (connected: boolean) => void;
  setLastModel: (id: string, filename: string) => void;
  setPatientContact: (name: string) => void;
  removePatientContact: () => void;
}

const KARIME_STATUSES = [
  "Disponible",
  "En recepción",
  "Organizando fichas",
  "Tomando un cafecito",
  "Agenda del día lista",
  "Llamando pacientes",
  "Un día a la vez",
  "Ordenando la sala de espera",
  "Hoy es un buen día",
  "Revisando los horarios",
  "Escuchando música bajito",
  "Todo bajo control",
  "Preparando los informes",
  "El café está listo",
  "Lunes con energía",
  "Viernes al fin",
  "Siempre sonriendo",
  "Atendiendo con cariño",
];

export function getKarimeStatus(): string {
  // Cambia cada ~10 minutos basado en la hora
  const idx = Math.floor(Date.now() / (10 * 60 * 1000)) % KARIME_STATUSES.length;
  return KARIME_STATUSES[idx];
}

const CONTACTS: Contact[] = [
  {
    id: "karime",
    name: "Karime",
    avatar: "/img_karime.jpeg",
    subtitle: getKarimeStatus(),
    personaId: "karime",
    color: "from-emerald-400 to-teal-500",
    online: true,
  },
  {
    id: "ayuda",
    name: "Ayuda",
    avatar: "?",
    subtitle: "Bot de ayuda",
    personaId: "ayuda",
    color: "from-blue-500 to-indigo-600",
    online: true,
  },
];

function timeNow(): string {
  return new Date().toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

const INITIAL_CONVERSATIONS: Record<string, Message[]> = {
  karime: [
    {
      id: "k1",
      contactId: "karime",
      sender: "other",
      text: "Buenos días. Ya estoy en recepción, la sala está lista.",
      time: "08:55",
      voiceId: "karime",
      status: "read",
    },
    {
      id: "k2",
      contactId: "karime",
      sender: "other",
      text: "El primer paciente ya llegó, es el Sr. Martínez. Viene por audiometría completa, derivado del otorrino.",
      time: "08:58",
      voiceId: "karime",
      status: "read",
    },
    {
      id: "k3",
      contactId: "karime",
      sender: "other",
      text: "Le dejé los informes del paciente de ayer en el escritorio.",
      time: "09:00",
      voiceId: "karime",
      status: "read",
    },
  ],
  ayuda: [],
};

let globalMsgId = 100;

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      contacts: CONTACTS,
      conversations: INITIAL_CONVERSATIONS,
      activeContact: null,
      unreadCounts: {},
      llmConnected: false,

      setActiveContact: (id) => {
        set({ activeContact: id });
        if (id) get().markAsRead(id);
      },

      lastModelId: null,
      lastModelFilename: null,

      addMessage: (contactId, message) =>
        set((state) => {
          const existing = state.conversations[contactId] ?? [];
          const isActive = state.activeContact === contactId;
          return {
            conversations: {
              ...state.conversations,
              [contactId]: [...existing, message],
            },
            unreadCounts: {
              ...state.unreadCounts,
              [contactId]: isActive
                ? 0
                : (state.unreadCounts[contactId] ?? 0) +
                  (message.sender === "other" ? 1 : 0),
            },
          };
        }),

      markAsRead: (contactId) =>
        set((state) => ({
          unreadCounts: { ...state.unreadCounts, [contactId]: 0 },
        })),

      setLlmConnected: (connected) => set({ llmConnected: connected }),
      setLastModel: (id: string, filename: string) => set({ lastModelId: id, lastModelFilename: filename }),

      setPatientContact: (name) => {
        const contact: Contact = {
          id: "patient",
          name,
          avatar: "🗣",
          subtitle: "Paciente en atención",
          personaId: "patient",
          color: "from-pink-400 to-rose-500",
          online: true,
        };
        set((state) => {
          const filtered = state.contacts.filter((c) => c.id !== "patient");
          return {
            contacts: [contact, ...filtered],
            conversations: {
              ...state.conversations,
              patient: state.conversations.patient ?? [],
            },
          };
        });
      },

      removePatientContact: () => {
        set((state) => ({
          contacts: state.contacts.filter((c) => c.id !== "patient"),
          activeContact: state.activeContact === "patient" ? null : state.activeContact,
        }));
      },
    }),
    {
      name: "labsim-chat",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        conversations: state.conversations,
        lastModelId: state.lastModelId,
        lastModelFilename: state.lastModelFilename,
      }),
    },
  ),
);

export function nextMsgId(): string {
  return `msg-${++globalMsgId}-${Date.now()}`;
}

export { timeNow };
