const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

console.log("VITE_API_BASE_URL =", API_BASE_URL);

export async function apiFetch<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const url = `${API_BASE_URL}${path}`;
    console.log("Fetching URL:", url);

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options?.headers ?? {}),
        },
        ...options,
    });

    const contentType = response.headers.get("content-type") ?? "";
    const responseText = await response.text();

    if (!response.ok) {
        throw new Error(`API error ${response.status}: ${responseText}`);
    }

    if (!contentType.includes("application/json")) {
        throw new Error(
            `Expected JSON but got content-type "${contentType}". Body: ${responseText}`,
        );
    }

    return JSON.parse(responseText) as T;
}
