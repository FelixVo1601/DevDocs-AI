<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { auth } from '$lib/auth.svelte';

	let { children } = $props();

	$effect(() => {
		if (!auth.ready || auth.loading) return;
		if (!auth.user) {
			const next = encodeURIComponent(page.url.pathname + page.url.search);
			void goto(`/login?next=${next}`);
		}
	});
</script>

{#if !auth.ready || auth.loading}
	<main class="gate">
		<p>Checking session…</p>
	</main>
{:else if auth.user}
	{@render children()}
{:else}
	<main class="gate">
		<p>Redirecting to login…</p>
	</main>
{/if}

<style>
	.gate {
		max-width: 36rem;
		margin: 0 auto;
		padding: 4rem 1.5rem;
		text-align: center;
		color: #556;
	}
</style>
