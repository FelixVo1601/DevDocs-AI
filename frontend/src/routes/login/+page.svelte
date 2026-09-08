<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import { safeNextPath } from '$lib/navigation';

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let submitting = $state(false);

	$effect(() => {
		if (auth.ready && !auth.loading && auth.user) {
			void goto(safeNextPath(page.url.searchParams.get('next')));
		}
	});

	async function onSubmit(event: Event) {
		event.preventDefault();
		error = null;
		submitting = true;
		try {
			await auth.login(email.trim(), password);
			await goto(safeNextPath(page.url.searchParams.get('next')));
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Login failed.';
		} finally {
			submitting = false;
		}
	}
</script>

<main>
	<h1>Log in</h1>
	<p class="lede">Sign in with your DevDocs AI account.</p>

	<form onsubmit={onSubmit}>
		<label>
			Email
			<input type="email" bind:value={email} autocomplete="email" required />
		</label>
		<label>
			Password
			<input
				type="password"
				bind:value={password}
				autocomplete="current-password"
				minlength="8"
				required
			/>
		</label>

		{#if error}
			<p class="error" role="alert">{error}</p>
		{/if}

		<button type="submit" disabled={submitting}>
			{submitting ? 'Signing in…' : 'Log in'}
		</button>
	</form>

	<p class="footer">
		Need an account?
		<a href="/register">Register</a>
	</p>
</main>

<style>
	main {
		max-width: 24rem;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}

	h1 {
		margin: 0 0 0.5rem;
	}

	.lede,
	.footer {
		color: #556;
	}

	form {
		display: grid;
		gap: 1rem;
		margin-top: 1.5rem;
	}

	label {
		display: grid;
		gap: 0.35rem;
		font-size: 0.95rem;
	}

	input {
		font: inherit;
		padding: 0.55rem 0.7rem;
		border: 1px solid #c9d0d8;
		border-radius: 0.4rem;
	}

	button {
		font: inherit;
		padding: 0.65rem 0.9rem;
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

	.error {
		margin: 0;
		color: #9b1c1c;
		background: #fde8e8;
		border-radius: 0.4rem;
		padding: 0.6rem 0.75rem;
	}

	a {
		color: #17324d;
		font-weight: 600;
	}
</style>
