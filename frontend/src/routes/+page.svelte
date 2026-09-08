<script lang="ts">
	import { auth } from '$lib/auth.svelte';
</script>

<main>
	<h1>DevDocs AI</h1>
	{#if auth.loading}
		<p>Checking session…</p>
	{:else if auth.user}
		<p>Signed in as <strong>{auth.user.email}</strong>.</p>
		<p class="hint">Refresh the page — your session should stay.</p>
	{:else}
		<p>Ask natural-language questions about a GitHub repository.</p>
		<p class="actions">
			<a href="/register">Create an account</a>
			or
			<a href="/login">log in</a>
		</p>
	{/if}
</main>

<style>
	main {
		max-width: 36rem;
		margin: 0 auto;
		padding: 4rem 1.5rem;
		text-align: center;
	}

	h1 {
		margin: 0 0 1rem;
		font-size: 2.5rem;
		font-weight: 600;
	}

	p {
		margin: 0.5rem 0;
		color: #445;
		line-height: 1.5;
	}

	.hint {
		font-size: 0.95rem;
		color: #667;
	}

	.actions a {
		color: #17324d;
		font-weight: 600;
	}
</style>
