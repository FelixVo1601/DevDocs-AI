import { ApiError, apiGet, apiPost, type User } from '$lib/api';

class AuthState {
	user = $state<User | null>(null);
	loading = $state(true);
	error = $state<string | null>(null);
	/** True after the first /auth/me attempt finishes. */
	ready = $state(false);

	async refresh(): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.user = await apiGet<User>('/auth/me');
		} catch (err) {
			this.user = null;
			if (err instanceof ApiError && err.status !== 401) {
				this.error = err.message;
			}
		} finally {
			this.loading = false;
			this.ready = true;
		}
	}

	async register(email: string, password: string): Promise<void> {
		this.error = null;
		await apiPost<User>('/auth/register', { email, password });
		await this.login(email, password);
	}

	async login(email: string, password: string): Promise<void> {
		this.error = null;
		this.user = await apiPost<User>('/auth/login', { email, password });
	}

	async logout(): Promise<void> {
		this.error = null;
		await apiPost<{ message: string }>('/auth/logout');
		this.user = null;
	}
}

export const auth = new AuthState();
