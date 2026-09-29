/** Backend index job statuses. The UI must display these values as returned. */
export const INDEX_STATUSES = ['pending', 'running', 'ready', 'failed'] as const;

export type IndexStatusValue = (typeof INDEX_STATUSES)[number];

const STATUS_HINT: Record<IndexStatusValue, string> = {
	pending: 'Queued. The index job has been created.',
	running: 'Fetching files, chunking, and writing embeddings.',
	ready: 'This repository is indexed and ready to search.',
	failed: 'Indexing stopped. See the error below.'
};

export function isIndexStatus(value: string | null | undefined): value is IndexStatusValue {
	return INDEX_STATUSES.includes(value as IndexStatusValue);
}

/**
 * Status the UI should show.
 * While a sync index request is in flight, the backend job is `running`.
 */
export function displayedIndexStatus(options: {
	indexing: boolean;
	jobStatus?: string | null;
}): IndexStatusValue | 'none' {
	if (options.indexing) return 'running';
	if (isIndexStatus(options.jobStatus)) return options.jobStatus;
	return 'none';
}

export function indexStatusHint(status: IndexStatusValue | 'none'): string {
	if (status === 'none') return 'This repository has not been indexed yet.';
	return STATUS_HINT[status];
}

/** Prefer the stored job error; fall back to the request error when they differ. */
export function indexErrorToShow(
	jobError: string | null | undefined,
	requestError: string | null | undefined
): string | null {
	const job = jobError?.trim() || null;
	const request = requestError?.trim() || null;
	if (job && request && job === request) return job;
	if (job && request) return `${job} (${request})`;
	return job ?? request;
}
