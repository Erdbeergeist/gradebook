import { useEffect, useState } from "react";
import { listClasses, type ClassRead } from "../api/classes";

type ClassListPageProps = {
    teacherId: string;
};

export default function ClassListPage({ teacherId }: ClassListPageProps) {
    const [classes, setClasses] = useState<ClassRead[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadClasses() {
            try {
                setIsLoading(true);
                setError(null);

                const data = await listClasses(teacherId);
                setClasses(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Unknown error");
            } finally {
                setIsLoading(false);
            }
        }

        void loadClasses();
    }, [teacherId]);

    return (
        <main style={{ padding: "2rem" }}>
            <h2>Classes</h2>

            {isLoading && <p>Loading classes...</p>}

            {!isLoading && error && <p>Error: {error}</p>}

            {!isLoading && !error && classes.length === 0 && (
                <p>No classes found for this teacher.</p>
            )}

            {!isLoading && !error && classes.length > 0 && (
                <ul>
                    {classes.map((classItem) => (
                        <li key={classItem.id}>{classItem.name}</li>
                    ))}
                </ul>
            )}
        </main>
    );
}
