import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface Course {
  id: string;
  institution_id: string;
  name: string;
  code: string | null;
  description: string | null;
  created_by: string;
  creator_name: string | null;
  creator_username: string | null;
  period: string | null;
  student_count: number;
  is_active: number;
  created_at: string;
}

export interface CourseMember {
  id: string;
  username: string;
  full_name: string | null;
  email: string | null;
  student_id_number: string | null;
  role: string;
  enrolled_at: string;
}

export interface ImportSummary {
  created: number;
  found: number;
  enrolled: number;
  errors: string[];
  total: number;
}

interface CoursesState {
  courses: Course[];
  loading: boolean;
  error: string | null;

  // Curso seleccionado
  selectedCourseId: string | null;
  selectedCourse: Course | null;
  members: CourseMember[];
  membersLoading: boolean;

  // Acciones
  setSelectedCourseId: (id: string | null) => void;
  fetchCourses: () => Promise<void>;
  fetchCourseDetail: (id: string) => Promise<void>;
  createCourse: (data: { name: string; code?: string; description?: string; period?: string }) => Promise<void>;
  enrollStudent: (courseId: string, userId: string) => Promise<void>;
  removeStudent: (courseId: string, userId: string) => Promise<void>;
  importStudents: (courseId: string, students: Array<Record<string, string>>) => Promise<ImportSummary>;
}

export const useCoursesStore = create<CoursesState>()((set, get) => ({
  courses: [],
  loading: false,
  error: null,
  selectedCourseId: null,
  selectedCourse: null,
  members: [],
  membersLoading: false,

  setSelectedCourseId: (id) => {
    set({ selectedCourseId: id });
    if (id) get().fetchCourseDetail(id);
    else set({ selectedCourse: null, members: [] });
  },

  fetchCourses: async () => {
    set({ loading: true, error: null });
    try {
      const result = await invoke<{ data: Course[] }>("api_list_courses", {});
      set({ courses: result?.data ?? [] });
    } catch (err) {
      set({ courses: [], error: String(err) });
    } finally {
      set({ loading: false });
    }
  },

  fetchCourseDetail: async (id) => {
    set({ membersLoading: true });
    try {
      const result = await invoke<{ course: Course; members: CourseMember[] }>("api_get_course", { courseId: id });
      set({
        selectedCourse: result.course,
        members: result.members ?? [],
      });
    } catch {
      set({ selectedCourse: null, members: [] });
    } finally {
      set({ membersLoading: false });
    }
  },

  createCourse: async (data) => {
    await invoke("api_create_course", { data });
    await get().fetchCourses();
  },

  enrollStudent: async (courseId, userId) => {
    await invoke("api_enroll_student", { courseId, userId });
    await get().fetchCourseDetail(courseId);
  },

  removeStudent: async (courseId, userId) => {
    await invoke("api_remove_student", { courseId, userId });
    await get().fetchCourseDetail(courseId);
  },

  importStudents: async (courseId, students) => {
    const result = await invoke<{ summary: ImportSummary }>("api_import_students", {
      courseId,
      students,
    });
    await get().fetchCourseDetail(courseId);
    await get().fetchCourses();
    return result.summary;
  },
}));
