/**
 * Safe in-app redirect path (open-redirect guard).
 * Only allows relative paths starting with a single "/".
 */
export function safeNextPath(next: string | null | undefined, fallback = '/app'): string {
	if (!next) return fallback;
	if (!next.startsWith('/') || next.startsWith('//') || next.includes('://')) {
		return fallback;
	}
	return next;
}
