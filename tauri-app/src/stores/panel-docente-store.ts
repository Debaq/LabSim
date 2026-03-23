import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

// ─── Tipos ──────────────────────────────────────────

export interface Course {
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
}

export interface Session {
  id: string;
  title: string;
  description: string | null;
  status: string;
  scheduled_date: string | null;
  end_date: string | null;
  scheduled_time: string | null;
  duration_minutes: number;
  location: string | null;
  session_type: string | null;
  centro_enabled: number;
  course_id: string | null;
  case_count: number;
  pending_submissions: number;
  creator_name: string | null;
  created_at: string;
}

export interface SessionDetail extends Session {
  instructions: string | null;
  cases: Array<{ id: string; title: string; difficulty: string }>;
  submissions: Array<{ id: string; case_id: string; student_id: string; status: string; student_name: string | null }>;
}

export interface Procedure {
  id: string;
  name: string;
  code: string | null;
  default_duration_minutes: number;
  category: string;
}

export interface ScheduleBlock {
  date: string;
  time: string;
  durationMinutes: number;
  procedureId: string | null;
  procedureName: string;
}

export interface SessionDraft {
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

type View =
  | { page: "courses" }
  | { page: "activities"; courseId: string }
  | { page: "activity-detail"; courseId: string; sessionId: string }
  | { page: "activity-config"; courseId: string; sessionId: string | null };

// ─── Estado ─────────────────────────────────────────

interface PanelDocenteState {
  view: View;

  // Cursos
  courses: Course[];
  coursesLoading: boolean;
  currentCourse: Course | null;

  // Actividades
  sessions: Session[];
  sessionsLoading: boolean;
  sessionsTab: "active" | "past";

  // Detalle
  sessionDetail: SessionDetail | null;
  detailLoading: boolean;

  // Config (crear/editar)
  courseMembers: CourseMember[];
  selectedDocentes: string[];
  selectedInstructores: string[];
  selectedEstudiantes: string[];
  sessionDraft: SessionDraft;
  groups: GroupDraft[];
  saving: boolean;

  // Planificación
  procedures: Procedure[];
  scheduleBlocks: ScheduleBlock[];

  // General
  error: string | null;

  // Navegación
  navigate: (view: View) => void;

  // Cursos
  fetchCourses: () => Promise<void>;

  // Actividades
  fetchSessions: (courseId: string) => Promise<void>;
  setSessionsTab: (tab: "active" | "past") => void;

  // Detalle
  fetchSessionDetail: (sessionId: string) => Promise<void>;

  // Participantes
  loadCourseMembers: (courseId: string) => Promise<void>;
  toggleParticipant: (id: string, role: "docente" | "instructor" | "estudiante") => void;
  selectAllParticipants: () => void;
  removeFromCourse: (userId: string, courseId: string) => Promise<void>;
  changeParticipantRole: (userId: string, newRole: "docente" | "instructor" | "estudiante", courseId: string) => Promise<void>;

  // Config
  updateDraft: (fields: Partial<SessionDraft>) => void;
  loadSessionForEdit: (session: SessionDetail) => void;
  resetDraft: () => void;
  createSession: (courseId: string) => Promise<string>;
  updateSession: (sessionId: string) => Promise<void>;

  // Grupos
  addGroup: () => void;
  removeGroup: (index: number) => void;
  renameGroup: (index: number, name: string) => void;
  assignStudentToGroup: (studentId: string, groupIndex: number) => void;
  removeStudentFromGroup: (studentId: string, groupIndex: number) => void;
  assignInstructorToGroup: (instructorId: string | null, groupIndex: number) => void;
  distributeGroups: (count: number) => void;
  saveGroups: (sessionId: string) => Promise<void>;

  // Planificación
  fetchProcedures: () => Promise<void>;
  loadScheduleBlocks: (sessionId: string) => Promise<void>;
  addBlock: (block: ScheduleBlock) => void;
  removeBlock: (index: number) => void;
  repeatWeek: () => void;
  saveSchedule: (sessionId: string) => Promise<void>;
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

export const usePanelDocenteStore = create<PanelDocenteState>()((set, get) => ({
  view: { page: "courses" } as View,

  courses: [],
  coursesLoading: false,
  currentCourse: null,

  sessions: [],
  sessionsLoading: false,
  sessionsTab: "active",

  sessionDetail: null,
  detailLoading: false,

  courseMembers: [],
  selectedDocentes: [],
  selectedInstructores: [],
  selectedEstudiantes: [],
  sessionDraft: { ...emptyDraft },
  groups: [],
  saving: false,

  procedures: [],
  scheduleBlocks: [],

  error: null,

  // ─── Navegación ────────────────────────────────────

  navigate: (view) => {
    set({ view, error: null });
    // Auto-fetch al navegar
    if (view.page === "courses") get().fetchCourses();
    if (view.page === "activities") get().fetchSessions(view.courseId);
    if (view.page === "activity-detail") get().fetchSessionDetail(view.sessionId);
    if (view.page === "activity-config") {
      get().loadCourseMembers(view.courseId);
      get().fetchProcedures();
      if (view.sessionId) {
        get().fetchSessionDetail(view.sessionId);
        get().loadScheduleBlocks(view.sessionId);
      } else {
        get().resetDraft();
      }
    }
  },

  // ─── Cursos ────────────────────────────────────────

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

  // ─── Actividades ───────────────────────────────────

  fetchSessions: async (courseId) => {
    set({ sessionsLoading: true, error: null });
    try {
      const result = await invoke<{ items: Session[] }>("api_get_sessions", {});
      // Filtrar por courseId (el backend no tiene filtro directo por course_id en sessions)
      const all = result?.items ?? [];
      const filtered = all.filter((s) => s.course_id === courseId);
      // Guardar curso actual
      const course = get().courses.find((c) => c.id === courseId) ?? null;
      set({ sessions: filtered, currentCourse: course });
    } catch (e) {
      set({ error: String(e) });
    } finally {
      set({ sessionsLoading: false });
    }
  },

  setSessionsTab: (tab) => set({ sessionsTab: tab }),

  // ─── Detalle ───────────────────────────────────────

  fetchSessionDetail: async (sessionId) => {
    set({ detailLoading: true });
    try {
      const result = await invoke<{ session: SessionDetail }>("api_get_session_detail", { sessionId });
      const detail = result?.session ?? null;
      set({ sessionDetail: detail });
      if (detail) get().loadSessionForEdit(detail);
    } catch (e) {
      set({ error: String(e) });
    } finally {
      set({ detailLoading: false });
    }
  },

  // ─── Participantes ─────────────────────────────────

  loadCourseMembers: async (courseId) => {
    try {
      const result = await invoke<{ course: Course; members: CourseMember[] }>("api_get_course", { courseId });
      const members = result?.members ?? [];
      set({
        courseMembers: members,
        currentCourse: result?.course ?? null,
        selectedDocentes: members.filter((m) => m.role === "docente").map((m) => m.id),
        selectedInstructores: members.filter((m) => m.role === "instructor").map((m) => m.id),
        selectedEstudiantes: members.filter((m) => m.role === "estudiante").map((m) => m.id),
      });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  toggleParticipant: (id, role) =>
    set((s) => {
      const key = role === "docente" ? "selectedDocentes" : role === "instructor" ? "selectedInstructores" : "selectedEstudiantes";
      const current = s[key];
      const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
      return { [key]: next } as Partial<PanelDocenteState>;
    }),

  selectAllParticipants: () =>
    set((s) => ({
      selectedDocentes: s.courseMembers.filter((m) => m.role === "docente").map((m) => m.id),
      selectedInstructores: s.courseMembers.filter((m) => m.role === "instructor").map((m) => m.id),
      selectedEstudiantes: s.courseMembers.filter((m) => m.role === "estudiante").map((m) => m.id),
    })),

  removeFromCourse: async (userId, courseId) => {
    await invoke("api_remove_student", { courseId, userId });
    set((s) => ({
      courseMembers: s.courseMembers.filter((m) => m.id !== userId),
      selectedDocentes: s.selectedDocentes.filter((id) => id !== userId),
      selectedInstructores: s.selectedInstructores.filter((id) => id !== userId),
      selectedEstudiantes: s.selectedEstudiantes.filter((id) => id !== userId),
    }));
  },

  changeParticipantRole: async (userId, newRole, courseId) => {
    try {
      await invoke("api_remove_student", { courseId, userId });
      await invoke("api_enroll_student", { courseId, userId, role: newRole });
    } catch {
      return;
    }
    set((s) => {
      const cleaned = {
        selectedDocentes: s.selectedDocentes.filter((id) => id !== userId),
        selectedInstructores: s.selectedInstructores.filter((id) => id !== userId),
        selectedEstudiantes: s.selectedEstudiantes.filter((id) => id !== userId),
      };
      const key = newRole === "docente" ? "selectedDocentes" : newRole === "instructor" ? "selectedInstructores" : "selectedEstudiantes";
      cleaned[key] = [...cleaned[key], userId];
      return {
        ...cleaned,
        courseMembers: s.courseMembers.map((m) => (m.id === userId ? { ...m, role: newRole } : m)),
      };
    });
  },

  // ─── Config ────────────────────────────────────────

  updateDraft: (fields) => set((s) => ({ sessionDraft: { ...s.sessionDraft, ...fields } })),

  loadSessionForEdit: (session) =>
    set({
      sessionDraft: {
        title: session.title ?? "",
        description: session.description ?? "",
        startDate: session.scheduled_date ?? "",
        endDate: session.end_date ?? "",
        scheduledTime: session.scheduled_time ?? "08:30",
        durationMinutes: session.duration_minutes ?? 90,
        location: session.location ?? "",
        instructions: session.instructions ?? "",
        sessionType: (session.session_type as "conjunto" | "grupal") ?? "conjunto",
        centroEnabled: !!session.centro_enabled,
      },
    }),

  resetDraft: () => set({ sessionDraft: { ...emptyDraft }, groups: [], sessionDetail: null }),

  createSession: async (courseId) => {
    const { sessionDraft } = get();
    if (!sessionDraft.title.trim()) throw new Error("El título es obligatorio");
    set({ saving: true, error: null });
    try {
      const result = await invoke<{ session: { id: string } }>("api_create_session", {
        data: {
          title: sessionDraft.title,
          description: sessionDraft.description || undefined,
          scheduledDate: sessionDraft.startDate || undefined,
          endDate: sessionDraft.endDate || undefined,
          scheduledTime: sessionDraft.scheduledTime || undefined,
          durationMinutes: sessionDraft.durationMinutes,
          location: sessionDraft.location || undefined,
          instructions: sessionDraft.instructions || undefined,
          sessionType: sessionDraft.sessionType,
          courseId,
          centroEnabled: sessionDraft.centroEnabled ? 1 : 0,
        },
      });
      return result?.session?.id ?? "";
    } finally {
      set({ saving: false });
    }
  },

  updateSession: async (sessionId) => {
    const { sessionDraft } = get();
    set({ saving: true, error: null });
    try {
      await invoke("api_update_session", {
        sessionId,
        data: {
          title: sessionDraft.title,
          description: sessionDraft.description || undefined,
          scheduledDate: sessionDraft.startDate || undefined,
          endDate: sessionDraft.endDate || undefined,
          scheduledTime: sessionDraft.scheduledTime || undefined,
          durationMinutes: sessionDraft.durationMinutes,
          location: sessionDraft.location || undefined,
          instructions: sessionDraft.instructions || undefined,
          sessionType: sessionDraft.sessionType,
          centroEnabled: sessionDraft.centroEnabled ? 1 : 0,
        },
      });
    } finally {
      set({ saving: false });
    }
  },

  // ─── Grupos ────────────────────────────────────────

  addGroup: () =>
    set((s) => ({ groups: [...s.groups, { name: `Grupo ${s.groups.length + 1}`, studentIds: [], instructorId: null }] })),

  removeGroup: (index) => set((s) => ({ groups: s.groups.filter((_, i) => i !== index) })),

  renameGroup: (index, name) => set((s) => ({ groups: s.groups.map((g, i) => (i === index ? { ...g, name } : g)) })),

  assignStudentToGroup: (studentId, groupIndex) =>
    set((s) => ({
      groups: s.groups.map((g, i) => {
        const without = { ...g, studentIds: g.studentIds.filter((id) => id !== studentId) };
        return i === groupIndex ? { ...without, studentIds: [...without.studentIds, studentId] } : without;
      }),
    })),

  removeStudentFromGroup: (studentId, groupIndex) =>
    set((s) => ({ groups: s.groups.map((g, i) => (i === groupIndex ? { ...g, studentIds: g.studentIds.filter((id) => id !== studentId) } : g)) })),

  assignInstructorToGroup: (instructorId, groupIndex) =>
    set((s) => ({ groups: s.groups.map((g, i) => (i === groupIndex ? { ...g, instructorId } : g)) })),

  distributeGroups: (count) =>
    set((s) => {
      if (count < 1) return {};
      const students = [...s.selectedEstudiantes];
      const newGroups: GroupDraft[] = Array.from({ length: count }, (_, i) => ({
        name: `Grupo ${i + 1}`,
        studentIds: [],
        instructorId: null,
      }));
      students.forEach((sid, idx) => newGroups[idx % count].studentIds.push(sid));
      return { groups: newGroups };
    }),

  saveGroups: async (sessionId) => {
    const { groups } = get();
    set({ saving: true, error: null });
    try {
      for (const group of groups) {
        const result = await invoke<{ group: { id: string } }>("api_create_group", {
          data: { name: group.name, description: `Sesión: ${sessionId}` },
        });
        const groupId = result?.group?.id;
        if (!groupId) continue;
        for (const studentId of group.studentIds) {
          await invoke("api_add_group_member", { groupId, data: { userId: studentId, role: "student" } });
        }
        if (group.instructorId) {
          await invoke("api_add_group_member", { groupId, data: { userId: group.instructorId, role: "instructor" } });
        }
      }
    } finally {
      set({ saving: false });
    }
  },

  // ─── Planificación ─────────────────────────────────

  fetchProcedures: async () => {
    try {
      const result = await invoke<{ items: Procedure[] }>("api_get_procedures", {});
      set({ procedures: result?.items ?? [] });
    } catch {
      set({ procedures: [] });
    }
  },

  loadScheduleBlocks: async (sessionId) => {
    try {
      // Cargar agenda items de esta sesión (bloques existentes)
      const today = "2020-01-01";
      const future = "2099-12-31";
      const result = await invoke<{ items: Array<{
        scheduled_date: string;
        scheduled_time: string;
        duration_minutes: number;
        procedure_id: string | null;
        procedure_name: string | null;
        patient_name: string | null;
        patient_notes: string | null;
        session_id: string | null;
      }> }>("api_get_agenda", { from: today, to: future });

      const items = (result?.items ?? []).filter((a) => a.session_id === sessionId);
      const blocks: ScheduleBlock[] = items.map((a) => ({
        date: a.scheduled_date,
        time: a.scheduled_time,
        durationMinutes: a.duration_minutes,
        procedureId: a.procedure_id,
        procedureName: a.patient_notes || a.patient_name || a.procedure_name || "Bloque",
      }));
      set({ scheduleBlocks: blocks });
    } catch {
      set({ scheduleBlocks: [] });
    }
  },

  addBlock: (block) => set((s) => ({ scheduleBlocks: [...s.scheduleBlocks, block] })),

  removeBlock: (index) => set((s) => ({ scheduleBlocks: s.scheduleBlocks.filter((_, i) => i !== index) })),

  repeatWeek: () =>
    set((s) => {
      const { startDate, endDate } = s.sessionDraft;
      if (!startDate || !endDate || s.scheduleBlocks.length === 0) return {};

      const start = new Date(startDate + "T00:00:00");
      const end = new Date(endDate + "T00:00:00");

      // Encontrar los bloques de la primera semana (primeros 7 días desde startDate)
      const firstWeekEnd = new Date(start);
      firstWeekEnd.setDate(firstWeekEnd.getDate() + 6);
      const firstWeekBlocks = s.scheduleBlocks.filter((b) => {
        const d = new Date(b.date + "T00:00:00");
        return d >= start && d <= firstWeekEnd;
      });

      if (firstWeekBlocks.length === 0) return {};

      // Generar bloques para las semanas restantes
      const newBlocks = [...s.scheduleBlocks];
      let weekOffset = 7;

      while (true) {
        const weekStart = new Date(start);
        weekStart.setDate(weekStart.getDate() + weekOffset);
        if (weekStart > end) break;

        for (const block of firstWeekBlocks) {
          const origDate = new Date(block.date + "T00:00:00");
          const dayOffset = Math.floor((origDate.getTime() - start.getTime()) / 86400000);
          const newDate = new Date(start);
          newDate.setDate(newDate.getDate() + weekOffset + dayOffset);
          if (newDate > end) continue;

          newBlocks.push({
            ...block,
            date: newDate.toISOString().split("T")[0],
          });
        }
        weekOffset += 7;
      }

      return { scheduleBlocks: newBlocks };
    }),

  saveSchedule: async (sessionId) => {
    const { scheduleBlocks } = get();
    if (scheduleBlocks.length === 0) return;

    set({ saving: true, error: null });
    try {
      for (const block of scheduleBlocks) {
        await invoke("api_create_agenda_item", {
          item: {
            patientName: block.procedureName,
            scheduledDate: block.date,
            scheduledTime: block.time,
            durationMinutes: block.durationMinutes,
            sessionId,
            patientNotes: block.procedureName,
          },
        });
      }
    } finally {
      set({ saving: false });
    }
  },
}));
