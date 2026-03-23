import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

// ─── Tipos ──────────────────────────────────────────

interface Course {
  id: string;
  name: string;
  code: string | null;
  period: string | null;
  student_count: number;
}

export interface CourseMember {
  id: string;
  username: string;
  full_name: string | null;
  role: string;
  email?: string | null;
  student_id_number?: string | null;
}

interface SessionDraft {
  title: string;
  description: string;
  startDate: string;
  endDate: string;
  scheduledTime: string;
  durationMinutes: number;
  location: string;
  instructions: string;
  sessionType: "conjunto" | "grupal";
  centroEnabled: boolean;
}

export interface GroupDraft {
  name: string;
  studentIds: string[];
  instructorId: string | null;
}

// ─── Estado ─────────────────────────────────────────

type Step = 1 | 2 | 3 | 4 | 5;

interface ActivitiesState {
  currentStep: Step;

  // Step 1: Curso
  courses: Course[];
  coursesLoading: boolean;
  selectedCourseId: string | null;
  courseMembers: CourseMember[];

  // Step 2: Participantes
  selectedDocentes: string[];
  selectedInstructores: string[];
  selectedEstudiantes: string[];

  // Step 3: Sesión
  sessionDraft: SessionDraft;
  sessionId: string | null;
  saving: boolean;

  // Step 4: Grupos
  groups: GroupDraft[];
  groupsSaved: boolean;

  // General
  error: string | null;

  // Actions — navigation
  setStep: (step: Step) => void;

  // Actions — Step 1
  fetchCourses: () => Promise<void>;
  selectCourse: (courseId: string) => Promise<void>;

  // Actions — Step 2
  toggleParticipant: (id: string, role: "docente" | "instructor" | "estudiante") => void;
  selectAllParticipants: () => void;
  removeFromCourse: (userId: string) => Promise<void>;
  changeParticipantRole: (userId: string, newRole: "docente" | "instructor" | "estudiante") => Promise<void>;

  // Actions — Step 3
  updateDraft: (fields: Partial<SessionDraft>) => void;
  createSession: () => Promise<void>;

  // Actions — Step 4
  addGroup: () => void;
  removeGroup: (index: number) => void;
  renameGroup: (index: number, name: string) => void;
  assignStudentToGroup: (studentId: string, groupIndex: number) => void;
  removeStudentFromGroup: (studentId: string, groupIndex: number) => void;
  assignInstructorToGroup: (instructorId: string | null, groupIndex: number) => void;
  distributeGroups: (count: number) => void;
  saveGroups: () => Promise<void>;

  // Actions — general
  reset: () => void;
}

const emptyDraft: SessionDraft = {
  title: "",
  description: "",
  startDate: "",
  endDate: "",
  scheduledTime: "08:30",
  durationMinutes: 90,
  location: "",
  instructions: "",
  sessionType: "conjunto",
  centroEnabled: false,
};

// ─── Store ──────────────────────────────────────────

export const useActivitiesStore = create<ActivitiesState>()((set, get) => ({
  currentStep: 1 as Step,

  courses: [],
  coursesLoading: false,
  selectedCourseId: null,
  courseMembers: [],

  selectedDocentes: [],
  selectedInstructores: [],
  selectedEstudiantes: [],

  sessionDraft: { ...emptyDraft },
  sessionId: null,
  saving: false,

  groups: [],
  groupsSaved: false,

  error: null,

  // ─── Navigation ────────────────────────────────────

  setStep: (step) => set({ currentStep: step }),

  // ─── Step 1: Curso ─────────────────────────────────

  fetchCourses: async () => {
    set({ coursesLoading: true, error: null });
    try {
      const result = await invoke<{ data: Course[] }>("api_list_courses", {});
      set({ courses: result?.data ?? [] });
    } catch (e) {
      set({ error: String(e) });
    } finally {
      set({ coursesLoading: false });
    }
  },

  selectCourse: async (courseId) => {
    set({ selectedCourseId: courseId, error: null });
    try {
      const result = await invoke<{ course: Course; members: CourseMember[] }>(
        "api_get_course",
        { courseId },
      );
      const members = result?.members ?? [];

      // Preseleccionar todos los participantes
      set({
        courseMembers: members,
        selectedDocentes: members.filter((m) => m.role === "docente").map((m) => m.id),
        selectedInstructores: members.filter((m) => m.role === "instructor").map((m) => m.id),
        selectedEstudiantes: members.filter((m) => m.role === "estudiante").map((m) => m.id),
        currentStep: 2,
      });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  // ─── Step 2: Participantes ─────────────────────────

  toggleParticipant: (id, role) =>
    set((s) => {
      const key =
        role === "docente"
          ? "selectedDocentes"
          : role === "instructor"
            ? "selectedInstructores"
            : "selectedEstudiantes";
      const current = s[key];
      const next = current.includes(id)
        ? current.filter((x) => x !== id)
        : [...current, id];
      return { [key]: next } as Partial<ActivitiesState>;
    }),

  selectAllParticipants: () =>
    set((s) => ({
      selectedDocentes: s.courseMembers.filter((m) => m.role === "docente").map((m) => m.id),
      selectedInstructores: s.courseMembers.filter((m) => m.role === "instructor").map((m) => m.id),
      selectedEstudiantes: s.courseMembers.filter((m) => m.role === "estudiante").map((m) => m.id),
    })),

  removeFromCourse: async (userId) => {
    const { selectedCourseId } = get();
    if (!selectedCourseId) return;
    await invoke("api_remove_student", { courseId: selectedCourseId, userId });
    // Quitar del estado local
    set((s) => ({
      courseMembers: s.courseMembers.filter((m) => m.id !== userId),
      selectedDocentes: s.selectedDocentes.filter((id) => id !== userId),
      selectedInstructores: s.selectedInstructores.filter((id) => id !== userId),
      selectedEstudiantes: s.selectedEstudiantes.filter((id) => id !== userId),
    }));
  },

  changeParticipantRole: async (userId, newRole) => {
    const { selectedCourseId } = get();
    if (!selectedCourseId) return;

    // Actualizar en servidor: quitar y re-inscribir con nuevo rol
    try {
      await invoke("api_remove_student", { courseId: selectedCourseId, userId });
      await invoke("api_enroll_student", { courseId: selectedCourseId, userId, role: newRole });
    } catch {
      // Si falla el servidor, no cambiar estado local
      return;
    }

    // Actualizar estado local
    set((s) => {
      const cleaned = {
        selectedDocentes: s.selectedDocentes.filter((id) => id !== userId),
        selectedInstructores: s.selectedInstructores.filter((id) => id !== userId),
        selectedEstudiantes: s.selectedEstudiantes.filter((id) => id !== userId),
      };
      const key =
        newRole === "docente"
          ? "selectedDocentes"
          : newRole === "instructor"
            ? "selectedInstructores"
            : "selectedEstudiantes";
      cleaned[key] = [...cleaned[key], userId];
      return {
        ...cleaned,
        courseMembers: s.courseMembers.map((m) =>
          m.id === userId ? { ...m, role: newRole } : m,
        ),
      };
    });
  },

  // ─── Step 3: Sesión ────────────────────────────────

  updateDraft: (fields) =>
    set((s) => ({ sessionDraft: { ...s.sessionDraft, ...fields } })),

  createSession: async () => {
    const { sessionDraft, selectedCourseId } = get();
    if (!sessionDraft.title.trim()) throw new Error("El título es obligatorio");

    set({ saving: true, error: null });
    try {
      const result = await invoke<{ session: { id: string } }>(
        "api_create_session",
        {
          data: {
            title: sessionDraft.title,
            description: sessionDraft.description || undefined,
            scheduledDate: sessionDraft.startDate || undefined,
            scheduledTime: sessionDraft.scheduledTime || undefined,
            durationMinutes: sessionDraft.durationMinutes,
            location: sessionDraft.location || undefined,
            instructions: sessionDraft.instructions || undefined,
            sessionType: sessionDraft.sessionType,
            courseId: selectedCourseId,
            centroEnabled: sessionDraft.centroEnabled ? 1 : 0,
          },
        },
      );

      const sessionId = result?.session?.id;
      if (!sessionId) throw new Error("No se pudo crear la sesión");

      // Si conjunto → paso 5, si grupal → paso 4
      const nextStep: Step = sessionDraft.sessionType === "grupal" ? 4 : 5;
      set({ sessionId, currentStep: nextStep });
    } catch (e) {
      set({ error: String(e) });
      throw e;
    } finally {
      set({ saving: false });
    }
  },

  // ─── Step 4: Grupos ────────────────────────────────

  addGroup: () =>
    set((s) => ({
      groups: [
        ...s.groups,
        { name: `Grupo ${s.groups.length + 1}`, studentIds: [], instructorId: null },
      ],
    })),

  removeGroup: (index) =>
    set((s) => ({
      groups: s.groups.filter((_, i) => i !== index),
    })),

  renameGroup: (index, name) =>
    set((s) => ({
      groups: s.groups.map((g, i) => (i === index ? { ...g, name } : g)),
    })),

  assignStudentToGroup: (studentId, groupIndex) =>
    set((s) => ({
      groups: s.groups.map((g, i) => {
        // Quitar de otros grupos
        const withoutStudent = { ...g, studentIds: g.studentIds.filter((id) => id !== studentId) };
        if (i === groupIndex) {
          return { ...withoutStudent, studentIds: [...withoutStudent.studentIds, studentId] };
        }
        return withoutStudent;
      }),
    })),

  removeStudentFromGroup: (studentId, groupIndex) =>
    set((s) => ({
      groups: s.groups.map((g, i) =>
        i === groupIndex ? { ...g, studentIds: g.studentIds.filter((id) => id !== studentId) } : g,
      ),
    })),

  assignInstructorToGroup: (instructorId, groupIndex) =>
    set((s) => ({
      groups: s.groups.map((g, i) =>
        i === groupIndex ? { ...g, instructorId } : g,
      ),
    })),

  distributeGroups: (count) =>
    set((s) => {
      if (count < 1) return {};
      const students = [...s.selectedEstudiantes];
      const newGroups: GroupDraft[] = [];
      for (let i = 0; i < count; i++) {
        newGroups.push({
          name: `Grupo ${i + 1}`,
          studentIds: [],
          instructorId: null,
        });
      }
      // Distribuir equitativamente
      students.forEach((sid, idx) => {
        newGroups[idx % count].studentIds.push(sid);
      });
      return { groups: newGroups };
    }),

  saveGroups: async () => {
    const { groups, sessionId } = get();
    if (!sessionId) throw new Error("No hay sesión creada");

    set({ saving: true, error: null });
    try {
      for (const group of groups) {
        // Crear grupo
        const result = await invoke<{ group: { id: string } }>(
          "api_create_group",
          {
            data: {
              name: group.name,
              description: `Sesión: ${sessionId}`,
            },
          },
        );
        const groupId = result?.group?.id;
        if (!groupId) continue;

        // Agregar estudiantes
        for (const studentId of group.studentIds) {
          await invoke("api_add_group_member", {
            groupId,
            data: { userId: studentId, role: "student" },
          });
        }

        // Agregar instructor si hay
        if (group.instructorId) {
          await invoke("api_add_group_member", {
            groupId,
            data: { userId: group.instructorId, role: "instructor" },
          });
        }
      }

      set({ groupsSaved: true, currentStep: 5 });
    } catch (e) {
      set({ error: String(e) });
      throw e;
    } finally {
      set({ saving: false });
    }
  },

  // ─── Reset ─────────────────────────────────────────

  reset: () =>
    set({
      currentStep: 1 as Step,
      selectedCourseId: null,
      courseMembers: [],
      selectedDocentes: [],
      selectedInstructores: [],
      selectedEstudiantes: [],
      sessionDraft: { ...emptyDraft },
      sessionId: null,
      groups: [],
      groupsSaved: false,
      error: null,
    }),
}));
