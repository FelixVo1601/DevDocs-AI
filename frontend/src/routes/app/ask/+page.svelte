<script lang="ts">
	import { ApiError, apiPost } from '$lib/api';
	import AppNav from '$lib/AppNav.svelte';
	import { auth } from '$lib/auth.svelte';
	import {
		citationLineLabel,
		splitAnswerCitations,
		type Citation
	} from '$lib/citations';
	import { github } from '$lib/github.svelte';

	type AskResponse = {
		full_name: string;
		question: string;
		answer: string;
		model: string;
		citations: Citation[];
	};

	let question = $state('');
	let asking = $state(false);
	let error = $state<string | null>(null);
	let result = $state<AskResponse | null>(null);
	let focusedId = $state<string | null>(null);

	const answerParts = $derived(
		result ? splitAnswerCitations(result.answer, result.citations.length) : []
	);

	$effect(() => {
		if (!auth.user) return;
		void github.loadSelected();
	});

	const focused = $derived(
		result?.citations.find((citation) => citation.chunk_id === focusedId) ?? null
	);

	function focusCitation(chunkId: string) {
		focusedId = chunkId;
		queueMicrotask(() => {
			const preview = document.getElementById('source-preview');
			preview?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
			if (preview instanceof HTMLElement) preview.focus();
		});
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		const text = question.trim();
		if (!text) {
			error = 'Enter a question.';
			return;
		}
		asking = true;
		error = null;
		focusedId = null;
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
			<div class="answer-text">
				{#each answerParts as part, i (i)}
					{#if part.kind === 'text'}
						{part.text}
					{:else}
						<button
							type="button"
							class="cite-mark"
							onclick={() => focusCitation(result!.citations[part.index - 1].chunk_id)}
						>
							[{part.index}]
						</button>
					{/if}
				{/each}
			</div>
		</section>

		<section class="citations" aria-labelledby="citations-heading">
			<h2 id="citations-heading">Sources</h2>
			{#if result.citations.length === 0}
				<p class="muted">No files were cited for this answer.</p>
			{:else}
				<ol>
					{#each result.citations as citation, i (citation.chunk_id)}
						<li>
							<article
								id="citation-{citation.chunk_id}"
								class:focused={focusedId === citation.chunk_id}
								tabindex="-1"
							>
								<button type="button" class="cite-title" onclick={() => focusCitation(citation.chunk_id)}>
									[{i + 1}] {citation.path}
								</button>
								<p class="meta">
									{citationLineLabel(citation)}
									· chunk <code>{citation.chunk_id}</code>
								</p>
							</article>
						</li>
					{/each}
				</ol>
			{/if}
		</section>

		<section class="preview" id="source-preview" tabindex="-1" aria-labelledby="preview-heading">
			<h2 id="preview-heading">Source preview</h2>
			{#if focused}
				<p class="meta">
					{focused.path} · {citationLineLabel(focused)}
				</p>
				<pre><code>{focused.content}</code></pre>
			{:else}
				<p class="muted">Click a citation to inspect the cited source.</p>
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

	.answer,
	.citations,
	.preview {
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

	.cite-mark {
		margin: 0 0.1rem;
		padding: 0 0.28rem;
		border: 0;
		border-radius: 0.25rem;
		background: #e7eef6;
		color: #17324d;
		font: inherit;
		font-weight: 700;
		cursor: pointer;
		vertical-align: baseline;
	}

	ol {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 0.65rem;
	}

	article {
		padding: 0.7rem 0.8rem;
		border: 1px solid #e4e8ec;
		border-radius: 0.45rem;
	}

	article:focus {
		outline: 2px solid #17324d;
		outline-offset: 2px;
	}

	article.focused {
		border-color: #17324d;
		background: #f3f6f9;
	}

	.cite-title {
		margin: 0;
		padding: 0;
		border: 0;
		background: transparent;
		color: #17324d;
		font: inherit;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}

	.meta {
		margin: 0.35rem 0 0;
		color: #667;
		font-size: 0.9rem;
		word-break: break-all;
	}

	code {
		font-size: 0.85em;
	}

	.preview pre {
		margin: 0.75rem 0 0;
		padding: 0.85rem 1rem;
		overflow: auto;
		border-radius: 0.4rem;
		background: #f6f8fa;
		border: 1px solid #e4e8ec;
		white-space: pre;
		line-height: 1.45;
	}

	.preview:focus {
		outline: 2px solid #17324d;
		outline-offset: 2px;
	}

	a {
		color: #17324d;
		font-weight: 600;
	}
</style>
