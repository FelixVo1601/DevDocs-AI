import { ApiError, apiGet, getApiBase } from '$lib/api';

export type GitHubConnection = {
	connected: boolean;
	github_user_id?: number | null;
	github_login?: string | null;
	scope?: string | null;
};

class GitHubState {
	connection = $state<GitHubConnection | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	async refresh(): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.connection = await apiGet<GitHubConnection>('/auth/github/connection');
		} catch (err) {
			this.connection = { connected: false };
			if (err instanceof ApiError && err.status === 503) {
				this.error = 'GitHub OAuth is not configured on the API.';
			} else if (err instanceof ApiError) {
				this.error = err.message;
			} else {
				this.error = 'Could not load GitHub connection status.';
			}
		} finally {
			this.loading = false;
		}
	}

	/** Top-level navigation so the session cookie is sent to the API host. */
	startConnect(): void {
		window.location.assign(`${getApiBase()}/auth/github/start`);
	}
}

export const github = new GitHubState();
