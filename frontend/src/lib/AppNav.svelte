<script lang="ts">
	import { page } from '$app/state';

	const path = $derived(page.url.pathname);
</script>

<nav aria-label="App">
	<a href="/app" aria-current={path === '/app' ? 'page' : undefined}>Repositories</a>
	<a href="/app/ask" aria-current={path.startsWith('/app/ask') ? 'page' : undefined}>Ask</a>
</nav>

<style>
	nav {
		display: flex;
		gap: 1rem;
		margin: 0 0 1.25rem;
	}

	a {
		color: #17324d;
		font-weight: 600;
		text-decoration: none;
	}

	a[aria-current='page'] {
		text-decoration: underline;
	}
</style>
