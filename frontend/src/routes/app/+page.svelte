<script lang="ts">
	import { auth } from '$lib/auth.svelte';
</script>

<main>
	<h1>App</h1>
	<p>Signed in as <strong>{auth.user?.email}</strong>.</p>
	<p class="hint">This area is protected. Unauthenticated visitors are sent to login.</p>
</main>

<style>
	main {
		max-width: 36rem;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}

	h1 {
		margin: 0 0 1rem;
	}

	p {
		color: #445;
		line-height: 1.5;
	}

	.hint {
		color: #667;
		font-size: 0.95rem;
	}
</style>
