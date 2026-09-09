import { ApiError, apiGet, apiRequest, getApiBase } from '$lib/api';

export type GitHubConnection = {
	connected: boolean;
	github_user_id?: number | null;
	github_login?: string | null;
	scope?: string | null;
};

export type GitHubRepo = {
	id: number;
	name: string;
	full_name: string;
	private: boolean;
	html_url: string;
	description?: string | null;
	default_branch: string;
	language?: string | null;
	updated_at?: string | null;
};

export type SelectedRepository = {
	github_repo_id: number;
	name: string;
	full_name: string;
	private: boolean;
	html_url: string;
	default_branch: string;
	description?: string | null;
};

class GitHubState {
	connection = $state<GitHubConnection | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	repos = $state<GitHubRepo[]>([]);
	reposLoading = $state(false);
	reposError = $state<string | null>(null);

	selected = $state<SelectedRepository | null>(null);
	selectedLoading = $state(false);
	selectError = $state<string | null>(null);
	selectingId = $state<number | null>(null);

	async refresh(): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.connection = await apiGet<GitHubConnection>('/auth/github/connection');
			if (this.connection.connected) {
				await Promise.all([this.loadRepos(), this.loadSelected()]);
			} else {
				this.repos = [];
				this.selected = null;
			}
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

	async loadRepos(): Promise<void> {
		this.reposLoading = true;
		this.reposError = null;
		try {
			const data = await apiGet<{ repos: GitHubRepo[]; count: number }>('/github/repos');
			this.repos = data.repos;
		} catch (err) {
			this.repos = [];
			this.reposError = err instanceof ApiError ? err.message : 'Could not load repositories.';
		} finally {
			this.reposLoading = false;
		}
	}

	async loadSelected(): Promise<void> {
		this.selectedLoading = true;
		try {
			const data = await apiGet<{ selected: SelectedRepository | null }>('/github/selected-repo');
			this.selected = data.selected;
		} catch (err) {
			this.selected = null;
			this.selectError =
				err instanceof ApiError ? err.message : 'Could not load selected repository.';
		} finally {
			this.selectedLoading = false;
		}
	}

	async selectRepo(githubRepoId: number): Promise<void> {
		this.selectError = null;
		this.selectingId = githubRepoId;
		try {
			const data = await apiRequest<{ selected: SelectedRepository | null }>(
				'/github/selected-repo',
				{
					method: 'PUT',
					body: JSON.stringify({ github_repo_id: githubRepoId })
				}
			);
			this.selected = data.selected;
		} catch (err) {
			this.selectError =
				err instanceof ApiError ? err.message : 'Could not save repository selection.';
		} finally {
			this.selectingId = null;
		}
	}

	/** Top-level navigation so the session cookie is sent to the API host. */
	startConnect(): void {
		window.location.assign(`${getApiBase()}/auth/github/start`);
	}
}

export const github = new GitHubState();
