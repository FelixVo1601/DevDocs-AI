import { displayedIndexStatus } from './indexStatus';

export type FlowNotice = {
	tone: 'loading' | 'empty' | 'error';
	title: string;
	detail: string;
	href?: string;
	linkLabel?: string;
};

export function askPageNotice(input: {
	connectionKnown: boolean;
	connected: boolean;
	selectedLoading: boolean;
	fullName: string | null;
	indexing: boolean;
	jobStatus?: string | null;
	indexError?: string | null;
	hasIndexPayload: boolean;
}): FlowNotice | null {
	if (!input.connectionKnown) {
		return {
			tone: 'loading',
			title: 'Checking your setup',
			detail: 'Loading your GitHub connection and selected repository.'
		};
	}
	if (!input.connected) {
		return {
			tone: 'empty',
			title: 'GitHub is not connected',
			detail: 'Connect GitHub, select a repository, and index it before asking a question.',
			href: '/app',
			linkLabel: 'Connect on Repositories'
		};
	}
	if (input.selectedLoading && !input.fullName) {
		return {
			tone: 'loading',
			title: 'Loading repository',
			detail: 'Checking which repository is selected.'
		};
	}
	if (!input.fullName) {
		return {
			tone: 'empty',
			title: 'No repository selected',
			detail: 'Select a repository, then index it until the status is ready.',
			href: '/app',
			linkLabel: 'Choose a repository'
		};
	}
	if (!input.hasIndexPayload && !input.indexing) {
		if (input.indexError) {
			return {
				tone: 'error',
				title: 'Could not load index status',
				detail: input.indexError,
				href: '/app',
				linkLabel: 'Open Repositories'
			};
		}
		return {
			tone: 'loading',
			title: 'Loading index status',
			detail: `Checking whether ${input.fullName} is indexed.`
		};
	}

	const status = displayedIndexStatus({
		indexing: input.indexing,
		jobStatus: input.jobStatus
	});
	if (status === 'ready') return null;
	if (status === 'failed') {
		return {
			tone: 'error',
			title: 'Indexing failed',
			detail: `${input.fullName} is not ready to search. Open Repositories to read the error and index again.`,
			href: '/app',
			linkLabel: 'View the index error'
		};
	}
	if (status === 'running' || status === 'pending') {
		return {
			tone: 'loading',
			title: 'Repository is indexing',
			detail: `${input.fullName} is ${status}. Ask after the status is ready.`,
			href: '/app',
			linkLabel: 'View index status'
		};
	}
	return {
		tone: 'empty',
		title: 'Repository is not indexed',
		detail: `${input.fullName} has no index yet. Index it on Repositories, wait until the status is ready, then come back.`,
		href: '/app',
		linkLabel: 'Index this repository'
	};
}

/** Next step after a failed ask, so the error is not a dead end. */
export function askFailureHelp(message: string): string {
	const lower = message.toLowerCase();
	if (lower.includes('index') || lower.includes('chunk')) {
		return 'Index the selected repository on Repositories until the status is ready, then ask again.';
	}
	return 'Try the question again. If it still fails, confirm you are signed in and the API is running.';
}
