<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/auth.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		void auth.refresh();
	});

	async function onLogout(event: Event) {
		event.preventDefault();
		await auth.logout();
		await goto('/');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>DevDocs AI</title>
</svelte:head>

<div class="shell">
	<header class="nav">
		<a class="brand" href="/">DevDocs AI</a>
		<nav>
			{#if auth.loading}
				<span class="muted">Checking session…</span>
			{:else if auth.user}
				<a href="/app">App</a>
				<span class="email">{auth.user.email}</span>
				<form method="POST" onsubmit={onLogout}>
					<button type="submit">Log out</button>
				</form>
			{:else}
				<a href="/login">Log in</a>
				<a class="primary" href="/register">Register</a>
			{/if}
		</nav>
	</header>

	{@render children()}
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: system-ui, sans-serif;
		color: #122;
		background: #f6f7f8;
	}

	.shell {
		min-height: 100vh;
	}

	.nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #dde1e6;
		background: #fff;
	}

	.brand {
		font-weight: 700;
		color: inherit;
		text-decoration: none;
	}

	nav {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	nav a,
	nav button {
		font: inherit;
		color: #234;
		text-decoration: none;
		background: transparent;
		border: 1px solid #c9d0d8;
		border-radius: 0.4rem;
		padding: 0.4rem 0.75rem;
		cursor: pointer;
	}

	nav a.primary,
	nav button {
		background: #17324d;
		border-color: #17324d;
		color: #fff;
	}

	.email,
	.muted {
		color: #556;
		font-size: 0.95rem;
	}
</style>
