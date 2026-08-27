/**
 * Tags, and getting a list of them out of whatever arrived.
 *
 * A tag is one thing. The list is the stored form and the form every part of
 * the application works in; text is only ever a transport, used where the
 * medium leaves no choice — the clipboard, an import, a file written before
 * this was settled.
 *
 * There is exactly one such crossing in each direction, and they are
 * deliberately not symmetric. What we write is strict, so a tag survives the
 * round trip whatever it contains. What we read is lenient, because a
 * spreadsheet, another tool, or a file already on disk cannot be asked to
 * change.
 */
import { z } from 'zod';

/** Trimmed, with the blanks that padding and empty cells leave dropped. */
function cleaned(values: readonly unknown[]): string[] {
  return values
    .map(String)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

/**
 * The tags in a cell we wrote ourselves, or null if we did not write it.
 *
 * Only a JSON *list* counts. A cell holding `2` is valid JSON, and reading it
 * as structure would take a perfectly good tag and turn it into something
 * that is not a tag list at all.
 */
function jsonTags(text: string): string[] | null {
  if (!text.startsWith('[')) return null;
  try {
    const parsed: unknown = JSON.parse(text);
    return Array.isArray(parsed) ? cleaned(parsed) : null;
  } catch {
    return null;
  }
}

/**
 * A tag list from whatever a cell edit, a paste, or an older file produced.
 *
 * Our own clipboard format is read back exactly. Anything else is text from
 * elsewhere, and is split on spaces and commas — which is a guess, and the
 * reason we do not write that form ourselves.
 */
export function parseTags(input: unknown): string[] {
  if (Array.isArray(input)) return cleaned(input);
  if (input === null || input === undefined) return [];
  const text = String(input).trim();
  if (!text) return [];
  return jsonTags(text) ?? text.split(/[\s,]+/).filter(Boolean);
}

/**
 * Tags as one clipboard cell.
 *
 * A JSON list rather than joined text, so that a tag containing a space or a
 * comma is still one tag when it comes back. It also keeps a range copy
 * intact: SvGrid copies as TSV, and JSON escapes the tabs and newlines that
 * would otherwise tear the pasted block into extra cells and rows.
 */
export function formatTags(tags: unknown): string {
  return JSON.stringify(parseTags(tags));
}

/**
 * Accepts a list, or the plain string a mis-typed edit may have left on disk.
 *
 * Being strict here cost a whole party list once: one file holding
 * `"tags": "PC Marduk"` made every party unreadable. What gets written is
 * always a list; this is about surviving what is already stored.
 */
export const tagsSchema = z
  .union([z.array(z.string()), z.string()])
  .transform(parseTags)
  .default([]);

/**
 * Every tag in use across a set of tagged things, once each, in order.
 *
 * This is the vocabulary a tag form offers. It is derived rather than stored:
 * a tag exists because something carries it, so the list of tags and the
 * things tagged with them cannot drift apart.
 */
export function distinctTags(tagged: readonly { tags: unknown }[]): string[] {
  const seen = new Set(tagged.flatMap((item) => parseTags(item.tags)));
  return [...seen].sort((a, b) => a.localeCompare(b));
}
