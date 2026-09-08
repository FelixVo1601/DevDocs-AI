import { ApiError, apiRequest, type User } from '$lib/api';

class AuthState {
	user = $state<User | null>(null);
	loading = $state(true);
	error = $state<string | null>(null);

	async refresh(): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.user = await apiRequest<User>('/auth/me');
		} catch (err) {
			this.user = null;
			if (err instanceof ApiError && err.status !== 401) {
				this.error = err.message;
			}
		} finally {
			this.loading = false;
		}
	}

	async register(email: string, password: string): Promise<void> {
		this.error = null;
		await apiRequest<User>('/auth/register', {
			method: 'POST',
			body: JSON.stringify({ email, password })
		});
		await this.login(email, password);
	}

	async login(email: string, password: string): Promise<void> {
		this.error = null;
		this.user = await apiRequest<User>('/auth/login', {
			method: 'POST',
			body: JSON.stringify({ email, password })
		});
	}

	async logout(): Promise<void> {
		this.error = null;
		await apiRequest<{ message: string }>('/auth/logout', { method: 'POST' });
		this.user = null;
	}
}

export const auth = new AuthState();
