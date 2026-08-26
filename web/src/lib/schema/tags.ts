/**
 * Tags, and getting a list of them out of whatever arrived.
 *
 * A tag list is a schema concern rather than a grid one: it is written by
 * editing a cell, by pasting a block from a spreadsheet, and by an import, and
 * all three can present it as text. Keeping the conversion here means stored
 * data is repaired on the way in, wherever it came from.
 */
import { z } from 'zod';

/**
 * A tag list from whatever a cell edit, a paste, or an older file produced.
 *
 * Separators are spaces or commas, so a block pasted from a spreadsheet works
 * whichever the other tool used.
 */
export function parseTags(input: unknown): string[] {
  if (Array.isArray(input))
    return input
      .map(String)
      .map((tag) => tag.trim())
      .filter(Boolean);
  if (input === null || input === undefined) return [];
  return String(input)
    .split(/[\s,]+/)
    .filter(Boolean);
}

/** Tags as one cell of text, for the clipboard and for spreadsheets. */
export function formatTags(tags: unknown): string {
  return parseTags(tags).join(' ');
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
