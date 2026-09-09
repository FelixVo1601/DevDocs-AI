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
				Refresh status
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
</main>

<style>
	main {
		max-width: 36rem;
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
		margin-top: 2rem;
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
		padding: 0.6rem 0.9rem;
		border: 0;
		border-radius: 0.4rem;
		background: #17324d;
		color: #fff;
		cursor: pointer;
	}

	button.secondary {
		background: #fff;
		color: #17324d;
		border: 1px solid #c9d0d8;
	}
</style>
