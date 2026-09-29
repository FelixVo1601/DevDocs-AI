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

export type IndexJob = {
	id: string;
	status: 'pending' | 'running' | 'ready' | 'failed' | string;
	error_message?: string | null;
	commit_sha?: string | null;
	started_at?: string | null;
	finished_at?: string | null;
	created_at?: string | null;
};

export type IndexStatus = {
	selected: { full_name: string; default_branch: string } | null;
	job: IndexJob | null;
	file_count: number;
	chunk_count: number;
	embedded_count: number;
	embedded?: number | null;
	skipped_empty?: number | null;
	truncated?: number | null;
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

	indexStatus = $state<IndexStatus | null>(null);
	indexLoading = $state(false);
	indexError = $state<string | null>(null);
	indexing = $state(false);

	async refresh(): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.connection = await apiGet<GitHubConnection>('/auth/github/connection');
			if (this.connection.connected) {
				await Promise.all([this.loadRepos(), this.loadSelected()]);
				await this.loadIndexStatus();
			} else {
				this.repos = [];
				this.selected = null;
				this.indexStatus = null;
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
			await this.loadIndexStatus();
		} catch (err) {
			this.selectError =
				err instanceof ApiError ? err.message : 'Could not save repository selection.';
		} finally {
			this.selectingId = null;
		}
	}

	async loadIndexStatus(options?: { keepError?: boolean }): Promise<void> {
		if (!this.selected) {
			this.indexStatus = null;
			return;
		}
		this.indexLoading = true;
		if (!options?.keepError) this.indexError = null;
		try {
			this.indexStatus = await apiGet<IndexStatus>('/github/selected-repo/index-status');
		} catch (err) {
			this.indexError =
				err instanceof ApiError ? err.message : 'Could not load index status.';
		} finally {
			this.indexLoading = false;
		}
	}

	async indexSelected(): Promise<void> {
		this.indexError = null;
		this.indexing = true;
		try {
			this.indexStatus = await apiRequest<IndexStatus>('/github/selected-repo/index', {
				method: 'POST'
			});
		} catch (err) {
			this.indexError = err instanceof ApiError ? err.message : 'Indexing failed.';
			await this.loadIndexStatus({ keepError: true });
		} finally {
			this.indexing = false;
		}
	}

	/** Top-level navigation so the session cookie is sent to the API host. */
	startConnect(): void {
		window.location.assign(`${getApiBase()}/auth/github/start`);
	}
}

export const github = new GitHubState();
