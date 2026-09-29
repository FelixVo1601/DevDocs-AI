<script lang="ts">
	import {
		displayedIndexStatus,
		indexErrorToShow,
		indexStatusHint
	} from '$lib/indexStatus';
	import { github } from '$lib/github.svelte';

	const status = $derived(
		displayedIndexStatus({
			indexing: github.indexing,
			jobStatus: github.indexStatus?.job?.status
		})
	);

	const errorText = $derived(
		indexErrorToShow(github.indexStatus?.job?.error_message, github.indexError)
	);

	const counts = $derived(github.indexStatus);
</script>

<div class="index-block">
	<h3>Indexing</h3>

	{#if github.indexLoading && !github.indexStatus && !github.indexing}
		<p class="muted">Loading index status…</p>
	{:else}
		<p class="index-status" data-status={status}>
			Status:
			<strong>{status === 'none' ? 'not indexed' : status}</strong>
			{#if status !== 'none' && github.indexStatus?.job?.commit_sha}
				<span class="muted">
					· commit <code>{github.indexStatus.job.commit_sha.slice(0, 7)}</code>
				</span>
			{/if}
		</p>
		<p class="muted">{indexStatusHint(status)}</p>
		{#if counts?.job}
			<p class="muted">
				{counts.file_count} files · {counts.chunk_count} chunks · {counts.embedded_count} embedded
			</p>
		{/if}
	{/if}

	{#if errorText && (status === 'failed' || github.indexError)}
		<p class="error" role="alert">{errorText}</p>
	{/if}

	<div class="actions">
		<button type="button" disabled={github.indexing} onclick={() => void github.indexSelected()}>
			{#if github.indexing || status === 'running'}
				Indexing…
			{:else if status === 'ready'}
				Re-index repository
			{:else}
				Index repository
			{/if}
		</button>
		<button
			type="button"
			class="secondary"
			disabled={github.indexing || github.indexLoading}
			onclick={() => void github.loadIndexStatus()}
		>
			Refresh status
		</button>
	</div>
</div>

<style>
	.index-block {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e4e8ec;
	}

	h3 {
		margin: 0 0 0.5rem;
		font-size: 1rem;
	}

	.index-status {
		margin: 0 0 0.35rem;
	}

	.index-status[data-status='ready'] strong {
		color: #14532d;
	}

	.index-status[data-status='failed'] strong {
		color: #9b1c1c;
	}

	.index-status[data-status='running'] strong,
	.index-status[data-status='pending'] strong {
		color: #9a6700;
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

	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
		margin-top: 0.65rem;
	}

	button {
		font: inherit;
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
	}

	code {
		font-size: 0.9em;
	}
</style>
