import { apiFetch } from "./client";

export type ClassRead = {
    id: string;
    name: string;
    school_id: string;
    teacher_id: string;
};

export async function listClasses(teacherId?: string): Promise<ClassRead[]> {
    const query = teacherId ? `?teacher_id=${encodeURIComponent(teacherId)}` : "";
    return apiFetch<ClassRead[]>(`/classes${query}`);
}
