import { useEffect, useState } from "react";
import ClassListPage from "./pages/ClassListPage";
import { listTeachers, type TeacherRead } from "./api/teachers";

export default function App() {
    const [teachers, setTeachers] = useState<TeacherRead[]>([]);
    const [currentTeacher, setCurrentTeacher] = useState<TeacherRead | null>(null);
    const [isLoadingTeachers, setIsLoadingTeachers] = useState(true);
    const [teacherError, setTeacherError] = useState<string | null>(null);

    useEffect(() => {
        async function loadTeachers() {
            try {
                setIsLoadingTeachers(true);
                setTeacherError(null);

                const data = await listTeachers();
                setTeachers(data);

                if (data.length > 0) {
                    setCurrentTeacher(data[0]);
                }
            } catch (err) {
                setTeacherError(
                    err instanceof Error ? err.message : "Unknown error",
                );
            } finally {
                setIsLoadingTeachers(false);
            }
        }

        void loadTeachers();
    }, []);

    return (
        <div style={{ fontFamily: "sans-serif" }}>
            <header
                style={{
                    padding: "1rem 2rem",
                    borderBottom: "1px solid #ddd",
                    background: "#fff",
                }}
            >
                <h1 style={{ margin: 0 }}>Gradebook</h1>

                {isLoadingTeachers && <p>Loading teacher...</p>}

                {!isLoadingTeachers && teacherError && (
                    <p>Error loading teacher: {teacherError}</p>
                )}

                {!isLoadingTeachers && !teacherError && currentTeacher && (
                    <div>
                        <p style={{ margin: "0.5rem 0 0 0" }}>
                            Signed in as: <strong>{currentTeacher.name}</strong>
                        </p>
                        <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.9rem" }}>
                            teacher_id: <code>{currentTeacher.id}</code>
                        </p>
                    </div>
                )}

                {!isLoadingTeachers && !teacherError && !currentTeacher && (
                    <p>No teacher found.</p>
                )}
            </header>

            {currentTeacher && <ClassListPage teacherId={currentTeacher.id} />}
        </div>
    );
}
