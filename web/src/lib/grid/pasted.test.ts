/**
 * What a paste changed, worked out by comparison.
 *
 * The bug behind this: pasted values showed in the grid and were never stored,
 * because SvGrid's paste does not report cell changes the way an edit does.
 */
import { describe, expect, it, vi } from 'vitest';
import { formatTags } from '$lib/schema/tags';
import { afterPaste, isPasteKey, pastedChanges } from './pasted';

const rin = { id: 1, name: 'Rin', tags: ['pc'] };
const sana = { id: 2, name: 'Sana', tags: ['pc'] };

describe('pastedChanges', () => {
  it('finds nothing when nothing moved', () => {
    expect(pastedChanges([rin, sana], [rin, sana])).toEqual([]);
  });

  it('reports every row a range paste touched', () => {
    const after = [
      { ...rin, tags: ['bot', 'marduk'] },
      { ...sana, tags: ['bot', 'marduk'] },
    ];
    expect(pastedChanges([rin, sana], after).map((row) => row.id)).toEqual([1, 2]);
  });

  // The paste path does not run `valueParser`, so a tags cell arrives as the
  // raw clipboard text and would be stored as a string — which is what made a
  // whole party list unreadable.
  it('splits tags that arrived as raw text', () => {
    const after = [{ ...rin, tags: 'bot marduk' as unknown as string[] }];
    expect(pastedChanges([rin], after)[0].tags).toEqual(['bot', 'marduk']);
  });

  // Copying tags out and pasting them back is the round trip that has to be
  // exact, separators and all — this is the pair `formatTags` is written for.
  it('takes back the tags a copy of our own put on the clipboard', () => {
    const copied = formatTags(['player character', 'ex-navy, retired']);
    const after = [{ ...rin, tags: copied as unknown as string[] }];
    expect(pastedChanges([rin], after)[0].tags).toEqual(['player character', 'ex-navy, retired']);
  });

  it('matches by id, not by position', () => {
    const after = [{ ...sana, name: 'Sana II' }, rin];
    expect(pastedChanges([rin, sana], after)).toEqual([{ ...sana, name: 'Sana II' }]);
  });

  it('ignores a row the grid has but we do not', () => {
    expect(pastedChanges([rin], [rin, { id: 9, name: 'Ghost', tags: [] }])).toEqual([]);
  });
});

describe('afterPaste', () => {
  const rows = (tags: string[]) => [{ ...rin, tags }];

  /**
   * The clipboard read is asynchronous, so at the moment the keystroke is seen
   * there is nothing to compare yet. Looking once finds nothing and the paste
   * is silently lost — which is exactly what happened.
   */
  it('waits for the paste to land before reporting it', async () => {
    let current = rows(['pc']);
    const seen: { id: number }[] = [];
    afterPaste(
      () => rows(['pc']),
      () => current,
      (row) => seen.push(row),
      { attempts: 20, every: 5 },
    );

    expect(seen).toEqual([]);
    await new Promise((resolve) => setTimeout(resolve, 30));
    current = rows(['bot']);

    await vi.waitFor(() => expect(seen).toHaveLength(1));
  });

  it('gives up rather than looking for ever', async () => {
    const seen: unknown[] = [];
    afterPaste(
      () => rows(['pc']),
      () => rows(['pc']),
      (row) => seen.push(row),
      { attempts: 3, every: 1 },
    );
    await new Promise((resolve) => setTimeout(resolve, 40));
    expect(seen).toEqual([]);
  });
});

describe('isPasteKey', () => {
  const key = (fields: Partial<KeyboardEvent>) => fields as KeyboardEvent;

  it('recognises the paste keystroke on either platform', () => {
    expect(isPasteKey(key({ key: 'v', metaKey: true }))).toBe(true);
    expect(isPasteKey(key({ key: 'V', ctrlKey: true }))).toBe(true);
  });

  it('is not just any v', () => {
    expect(isPasteKey(key({ key: 'v' }))).toBe(false);
    expect(isPasteKey(key({ key: 'c', metaKey: true }))).toBe(false);
  });
});
