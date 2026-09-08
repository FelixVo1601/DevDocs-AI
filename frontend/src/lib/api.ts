export type User = {
	id: string;
	email: string;
	created_at: string;
};

export class ApiError extends Error {
	status: number;

	constructor(message: string, status: number) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
	}
}

/** Shared API base URL (FastAPI). */
export function getApiBase(): string {
	const base = import.meta.env.PUBLIC_API_URL as string | undefined;
	return base?.replace(/\/$/, '') || 'http://localhost:8001';
}

async function parseError(response: Response): Promise<string> {
	try {
		const data = await response.json();
		if (typeof data?.detail === 'string') return data.detail;
		if (Array.isArray(data?.detail)) {
			return data.detail
				.map((item: { msg?: string }) => item.msg ?? 'Invalid input')
				.join(', ');
		}
		return response.statusText || 'Request failed';
	} catch {
		return response.statusText || 'Request failed';
	}
}

/**
 * Shared API client: JSON fetch with credentials (session cookie).
 * Use this for all backend calls from the frontend.
 */
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
	const headers = new Headers(init.headers);
	if (init.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}

	const response = await fetch(`${getApiBase()}${path}`, {
		...init,
		headers,
		credentials: 'include'
	});

	if (!response.ok) {
		throw new ApiError(await parseError(response), response.status);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
	return apiRequest<T>(path, { method: 'GET' });
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
	return apiRequest<T>(path, {
		method: 'POST',
		body: body === undefined ? undefined : JSON.stringify(body)
	});
}
