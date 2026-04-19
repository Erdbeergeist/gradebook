import { apiFetch } from "./client";

export type TeacherRead = {
    id: string;
    school_id: string;
    name: string;
};

export async function listTeachers(): Promise<TeacherRead[]> {
    return apiFetch<TeacherRead[]>("/teachers");
}
