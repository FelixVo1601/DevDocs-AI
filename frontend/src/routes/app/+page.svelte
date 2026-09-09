<script lang="ts">
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import { auth } from '$lib/auth.svelte';
	import { github } from '$lib/github.svelte';

	const flashMessages: Record<string, string> = {
		connected: 'GitHub connected successfully.',
		denied: 'GitHub authorization was cancelled.',
		missing_params: 'GitHub callback was missing parameters.',
		invalid_state: 'GitHub OAuth state was invalid or expired. Try again.',
		user_mismatch: 'GitHub OAuth user did not match your session.',
		user_not_found: 'Your account was not found during GitHub connect.',
		exchange_failed: 'GitHub token exchange failed. Check API configuration.',
		conflict: 'That GitHub account is already linked to another user.',
		not_configured: 'GitHub OAuth is not configured on the server.'
	};

	let flash = $state<string | null>(null);
	let flashTone = $state<'ok' | 'err'>('ok');
	let filter = $state('');

	const filteredRepos = $derived(
		github.repos.filter((repo) => {
			const q = filter.trim().toLowerCase();
			if (!q) return true;
			return (
				repo.full_name.toLowerCase().includes(q) ||
				(repo.description ?? '').toLowerCase().includes(q)
			);
		})
	);

	$effect(() => {
		if (!auth.user) return;
		void github.refresh();
	});

	$effect(() => {
		const result = page.url.searchParams.get('github');
		if (!result) return;
		flash = flashMessages[result] ?? `GitHub connect result: ${result}`;
		flashTone = result === 'connected' ? 'ok' : 'err';
		void github.refresh();
		const url = new URL(page.url);
		url.searchParams.delete('github');
		replaceState(url.pathname + url.search, {});
	});
</script>

<main>
	<h1>App</h1>
	<p>Signed in as <strong>{auth.user?.email}</strong>.</p>

	<section class="card" aria-labelledby="github-heading">
		<h2 id="github-heading">GitHub</h2>

		{#if flash}
			<p class="flash" class:ok={flashTone === 'ok'} class:err={flashTone === 'err'} role="status">
				{flash}
			</p>
		{/if}

		{#if github.loading && !github.connection}
			<p class="muted">Checking GitHub connection…</p>
		{:else if github.connection?.connected}
			<p class="status connected">
				<span class="dot" aria-hidden="true"></span>
				Connected as <strong>{github.connection.github_login}</strong>
			</p>
			{#if github.connection.scope}
				<p class="muted">Scopes: {github.connection.scope}</p>
			{/if}
			<button type="button" class="secondary" onclick={() => void github.refresh()}>
				Refresh
			</button>
		{:else}
			<p class="status disconnected">
				<span class="dot" aria-hidden="true"></span>
				Not connected
			</p>
			{#if github.error}
				<p class="error" role="alert">{github.error}</p>
			{/if}
			<button type="button" onclick={() => github.startConnect()}>Connect GitHub</button>
		{/if}
	</section>

	{#if github.connection?.connected}
		<section class="card" aria-labelledby="selection-heading">
			<h2 id="selection-heading">Selected repository</h2>
			{#if github.selectedLoading && !github.selected}
				<p class="muted">Loading selection…</p>
			{:else if github.selected}
				<p class="selection">
					<strong>{github.selected.full_name}</strong>
					{#if github.selected.private}
						<span class="badge">private</span>
					{:else}
						<span class="badge public">public</span>
					{/if}
				</p>
				<p class="muted">
					Branch <code>{github.selected.default_branch}</code>
					·
					<a href={github.selected.html_url} target="_blank" rel="noreferrer">Open on GitHub</a>
				</p>
			{:else}
				<p class="muted">No repository selected yet. Pick one below.</p>
			{/if}
			{#if github.selectError}
				<p class="error" role="alert">{github.selectError}</p>
			{/if}
		</section>

		<section class="card wide" aria-labelledby="repos-heading">
			<h2 id="repos-heading">Your repositories</h2>
			<label class="filter">
				Filter
				<input type="search" bind:value={filter} placeholder="owner/name" />
			</label>

			{#if github.reposLoading}
				<p class="muted">Loading repositories…</p>
			{:else if github.reposError}
				<p class="error" role="alert">{github.reposError}</p>
			{:else if filteredRepos.length === 0}
				<p class="muted">No repositories match.</p>
			{:else}
				<ul class="repo-list">
					{#each filteredRepos as repo (repo.id)}
						<li class:active={github.selected?.github_repo_id === repo.id}>
							<div>
								<div class="repo-name">
									{repo.full_name}
									{#if repo.private}
										<span class="badge">private</span>
									{/if}
								</div>
								{#if repo.description}
									<p class="repo-desc">{repo.description}</p>
								{/if}
							</div>
							<button
								type="button"
								class="secondary"
								disabled={github.selectingId === repo.id}
								onclick={() => void github.selectRepo(repo.id)}
							>
								{#if github.selected?.github_repo_id === repo.id}
									Selected
								{:else if github.selectingId === repo.id}
									Saving…
								{:else}
									Select
								{/if}
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	{/if}
</main>

<style>
	main {
		max-width: 44rem;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}

	h1 {
		margin: 0 0 0.5rem;
	}

	h2 {
		margin: 0 0 0.75rem;
		font-size: 1.15rem;
	}

	p {
		color: #445;
		line-height: 1.5;
	}

	.card {
		margin-top: 1.5rem;
		padding: 1.25rem 1.35rem;
		border: 1px solid #dde1e6;
		border-radius: 0.5rem;
		background: #fff;
	}

	.status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 0 0 0.75rem;
		font-weight: 500;
	}

	.dot {
		width: 0.55rem;
		height: 0.55rem;
		border-radius: 50%;
		background: #9aa3ad;
	}

	.connected .dot {
		background: #1f7a3f;
	}

	.disconnected .dot {
		background: #9aa3ad;
	}

	.muted {
		color: #667;
		font-size: 0.95rem;
	}

	.error {
		color: #9b1c1c;
		background: #fde8e8;
		border-radius: 0.4rem;
		padding: 0.55rem 0.7rem;
	}

	.flash {
		border-radius: 0.4rem;
		padding: 0.55rem 0.7rem;
		margin: 0 0 0.85rem;
	}

	.flash.ok {
		color: #14532d;
		background: #e8f8ee;
	}

	.flash.err {
		color: #9b1c1c;
		background: #fde8e8;
	}

	button {
		font: inherit;
		margin-top: 0.5rem;
		padding: 0.55rem 0.85rem;
		border: 0;
		border-radius: 0.4rem;
		background: #17324d;
		color: #fff;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.7;
		cursor: wait;
	}

	button.secondary {
		background: #fff;
		color: #17324d;
		border: 1px solid #c9d0d8;
		margin-top: 0;
	}

	.selection {
		margin: 0 0 0.35rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.badge {
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.15rem 0.4rem;
		border-radius: 999px;
		background: #eef1f4;
		color: #445;
	}

	.badge.public {
		background: #e8f8ee;
		color: #14532d;
	}

	.filter {
		display: grid;
		gap: 0.35rem;
		margin-bottom: 1rem;
		font-size: 0.95rem;
	}

	input {
		font: inherit;
		padding: 0.5rem 0.65rem;
		border: 1px solid #c9d0d8;
		border-radius: 0.4rem;
	}

	.repo-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 0.65rem;
	}

	.repo-list li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 0.85rem;
		border: 1px solid #e4e8ec;
		border-radius: 0.45rem;
	}

	.repo-list li.active {
		border-color: #17324d;
		background: #f3f6f9;
	}

	.repo-name {
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
	}

	.repo-desc {
		margin: 0.25rem 0 0;
		font-size: 0.9rem;
		color: #667;
	}

	code {
		font-size: 0.9em;
	}

	a {
		color: #17324d;
		font-weight: 600;
	}
</style>
