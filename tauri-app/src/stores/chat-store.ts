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
}

const CONTACTS: Contact[] = [
  {
    id: "karime",
    name: "Karime",
    avatar: "K",
    subtitle: "Secretaria",
    personaId: "karime",
    color: "from-emerald-400 to-teal-500",
    online: true,
  },
  {
    id: "docente",
    name: "Prof. Audiología",
    avatar: "📚",
    subtitle: "Docente Bot",
    personaId: "docente",
    color: "from-violet-500 to-purple-600",
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
      text: "Buenos días doc! ☀️ Ya estoy en recepción, la sala está lista.",
      time: "08:55",
      status: "read",
    },
    {
      id: "k2",
      contactId: "karime",
      sender: "other",
      text: "El primer paciente ya llegó, es el Sr. Martínez. Viene por audiometría completa, derivado del otorrino.",
      time: "08:58",
      status: "read",
    },
    {
      id: "k3",
      contactId: "karime",
      sender: "other",
      text: "Ah, y le dejé los informes del paciente de ayer en el escritorio 📋",
      time: "09:00",
      status: "read",
    },
  ],
  docente: [
    {
      id: "d1",
      contactId: "docente",
      sender: "other",
      text: "Hola! Soy tu asistente de enseñanza audiológica. Puedes preguntarme sobre cualquier tema clínico: audiometría, impedanciometría, OAE, ABR, audífonos, diagnóstico diferencial, enmascaramiento y más.\n\n¿En qué puedo ayudarte hoy?",
      time: "09:00",
      status: "read",
    },
  ],
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
