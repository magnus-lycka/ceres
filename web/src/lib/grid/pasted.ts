/**
 * Working out what a paste changed.
 *
 * SvGrid's paste writes straight into its own row data and, unlike every other
 * way of changing a cell, never fires `onCellValueChange` — so pasted values
 * appear on screen and are never stored, reverting on the next reload. Nor
 * does it run `valueParser`, so a tags cell arrives as raw text.
 *
 * The grid's own rows are the truth about what a paste produced, so this
 * compares them against what the grid was handed and reports the difference.
 */
import { parseTags } from '$lib/schema/tags';

/**
 * Rows that differ, taken from the grid's copy.
 *
 * Matched by id rather than by position: a paste changes values in place, but
 * row order is the grid's business once sorting or filtering is involved.
 */
export function pastedChanges<T extends { id: number; tags?: unknown }>(
  before: readonly T[],
  after: readonly T[],
): T[] {
  const original = new Map(before.map((row) => [row.id, row]));
  return after
    .filter((row) => {
      const was = original.get(row.id);
      return was !== undefined && JSON.stringify(was) !== JSON.stringify(row);
    })
    .map((row) => ('tags' in row ? { ...row, tags: parseTags(row.tags) } : row));
}

/**
 * Report what a paste changed, once it has actually landed.
 *
 * Hooking the `paste` event is not enough. When the async Clipboard API is
 * available — which it is on localhost and over HTTPS — SvGrid reads the
 * clipboard from its **keydown** handler and preventDefaults, so no native
 * paste event is dispatched at all. The native event only fires in insecure
 * contexts, where the async API is missing.
 *
 * So this is driven by the keystroke instead, and because the clipboard read
 * is asynchronous there is nothing to compare yet when it returns. It looks
 * again a few times, briefly, and stops at the first difference.
 */
export function afterPaste<T extends { id: number; tags?: unknown }>(
  before: () => readonly T[],
  after: () => readonly T[],
  emit: (row: T) => void,
  { attempts = 20, every = 25 } = {},
): void {
  let tries = 0;
  const look = () => {
    const changed = pastedChanges(before(), after());
    if (changed.length > 0) return changed.forEach(emit);
    if ((tries += 1) < attempts) setTimeout(look, every);
  };
  setTimeout(look, 0);
}

/** True for the keystroke that starts a paste, whichever platform. */
export function isPasteKey(event: KeyboardEvent): boolean {
  return Boolean(event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'v';
}
