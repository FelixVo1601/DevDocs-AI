export type Citation = {
	chunk_id: string;
	path: string;
	chunk_index: number;
	start_line: number | null;
	end_line: number | null;
	distance: number;
	content: string;
};

export type AnswerPart = { kind: 'text'; text: string } | { kind: 'cite'; index: number };

/** Split answer text on [n] markers that match a returned citation (1-based). */
export function splitAnswerCitations(answer: string, citationCount: number): AnswerPart[] {
	const pattern = /\[(\d+)\]/g;
	const parts: AnswerPart[] = [];
	let last = 0;
	for (const match of answer.matchAll(pattern)) {
		const start = match.index ?? 0;
		const n = Number(match[1]);
		if (start > last) {
			parts.push({ kind: 'text', text: answer.slice(last, start) });
		}
		if (Number.isInteger(n) && n >= 1 && n <= citationCount) {
			parts.push({ kind: 'cite', index: n });
		} else {
			parts.push({ kind: 'text', text: match[0] });
		}
		last = start + match[0].length;
	}
	if (last < answer.length) {
		parts.push({ kind: 'text', text: answer.slice(last) });
	}
	return parts;
}

export function citationLineLabel(citation: Pick<Citation, 'start_line' | 'end_line'>): string {
	if (citation.start_line != null && citation.end_line != null) {
		return `lines ${citation.start_line}–${citation.end_line}`;
	}
	return 'line range unavailable';
}
