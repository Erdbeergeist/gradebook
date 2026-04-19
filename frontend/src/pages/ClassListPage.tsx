import { useEffect, useState } from "react";
import { listClasses, type ClassRead } from "../api/classes";

export default function ClassListPage() {
    const [classes, setClasses] = useState<ClassRead[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                setIsLoading(true);
                setError(null);
                const data = await listClasses();
                setClasses(data);
            } catch (err) {
                const message =
                    err instanceof Error ? err.message : "Unknown error";
                setError(message);
            } finally {
                setIsLoading(false);
            }
        }

        void load();
    }, []);

    if (isLoading) {
        return <p>Loading classes...</p>;
    }

    if (error) {
        return <p>Error: {error}</p>;
    }

    return (
        <div style={{ padding: "2rem" }}>
            <h2>Classes</h2>

            {classes.length === 0 ? (
                <p>No classes found.</p>
            ) : (
                <ul>
                    {classes.map((classItem) => (
                        <li key={classItem.id}>
                            {classItem.name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
