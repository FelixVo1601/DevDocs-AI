<script lang="ts">
	import { ApiError, apiPost } from '$lib/api';
	import AppNav from '$lib/AppNav.svelte';
	import { auth } from '$lib/auth.svelte';
	import { github } from '$lib/github.svelte';

	type AskResponse = {
		full_name: string;
		question: string;
		answer: string;
		model: string;
		citations: { path: string; chunk_id: string }[];
	};

	let question = $state('');
	let asking = $state(false);
	let error = $state<string | null>(null);
	let result = $state<AskResponse | null>(null);

	$effect(() => {
		if (!auth.user) return;
		void github.loadSelected();
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		const text = question.trim();
		if (!text) {
			error = 'Enter a question.';
			return;
		}
		asking = true;
		error = null;
		try {
			result = await apiPost<AskResponse>('/ask', { question: text });
		} catch (err) {
			result = null;
			error = err instanceof ApiError ? err.message : 'Could not get an answer.';
		} finally {
			asking = false;
		}
	}
</script>

<main>
	<AppNav />
	<h1>Ask</h1>
	<p class="muted">
		{#if github.selected}
			Questions use <strong>{github.selected.full_name}</strong>. Index it first if you have not already.
		{:else if github.selectedLoading}
			Loading selected repository…
		{:else}
			Select a repository on <a href="/app">Repositories</a> before asking.
		{/if}
	</p>

	<form onsubmit={submit}>
		<label>
			Question
			<textarea
				name="question"
				rows="4"
				bind:value={question}
				placeholder="How does login work?"
				disabled={asking}
				required
			></textarea>
		</label>
		<button type="submit" disabled={asking || !github.selected}>
			{asking ? 'Asking…' : 'Ask'}
		</button>
	</form>

	{#if error}
		<p class="error" role="alert">{error}</p>
	{/if}

	{#if result}
		<section class="answer" aria-live="polite" aria-labelledby="answer-heading">
			<h2 id="answer-heading">Answer</h2>
			<p class="asked">Asked: {result.question}</p>
			<div class="answer-text">{result.answer}</div>
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

	.muted {
		color: #667;
		line-height: 1.5;
	}

	form {
		margin-top: 1.25rem;
	}

	label {
		display: grid;
		gap: 0.35rem;
		font-size: 0.95rem;
	}

	textarea {
		font: inherit;
		padding: 0.65rem 0.75rem;
		border: 1px solid #c9d0d8;
		border-radius: 0.4rem;
		resize: vertical;
		min-height: 6rem;
	}

	button {
		font: inherit;
		margin-top: 0.75rem;
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

	.error {
		color: #9b1c1c;
		background: #fde8e8;
		border-radius: 0.4rem;
		padding: 0.55rem 0.7rem;
		margin-top: 1rem;
	}

	.answer {
		margin-top: 1.5rem;
		padding: 1.25rem 1.35rem;
		border: 1px solid #dde1e6;
		border-radius: 0.5rem;
		background: #fff;
	}

	.asked {
		margin: 0 0 0.75rem;
		color: #667;
		font-size: 0.95rem;
	}

	.answer-text {
		white-space: pre-wrap;
		line-height: 1.55;
		color: #1c2430;
	}

	a {
		color: #17324d;
		font-weight: 600;
	}
</style>
