/**
 * Tags arrive as a list, as a pasted clipboard cell, or as whatever an older
 * file holds. All three have to end up as the same list.
 *
 * A tag is one thing, not a run of characters that happens to contain
 * separators. What is written out says so — a JSON list — so a tag survives
 * the round trip whatever it contains. What is read back accepts the looser
 * forms too, because a spreadsheet and an older file cannot be asked to
 * change.
 */
import { describe, expect, it } from 'vitest';
import { distinctTags, formatTags, parseTags, tagsSchema } from './tags';

describe('parseTags', () => {
  it('keeps an array as it is', () => {
    expect(parseTags(['pc', 'marduk'])).toEqual(['pc', 'marduk']);
  });

  it('splits pasted text rather than storing a string that renders per letter', () => {
    expect(parseTags('pc marduk')).toEqual(['pc', 'marduk']);
  });

  it('accepts commas, since another tool may have written them', () => {
    expect(parseTags('pc, marduk')).toEqual(['pc', 'marduk']);
  });

  it('treats an empty or missing cell as no tags', () => {
    expect(parseTags('')).toEqual([]);
    expect(parseTags(null)).toEqual([]);
    expect(parseTags(undefined)).toEqual([]);
  });

  it('drops padding rather than making an empty tag', () => {
    expect(parseTags('  pc   marduk  ')).toEqual(['pc', 'marduk']);
    expect(parseTags([' pc ', ''])).toEqual(['pc']);
  });

  // JSON is only recognised as a *list*. A cell holding a bare number parses
  // as JSON perfectly well, and taking that as structure would turn the tag
  // `2` into something that is not a tag list at all.
  it('treats a cell that is not a JSON list as text', () => {
    expect(parseTags('2')).toEqual(['2']);
    expect(parseTags('null')).toEqual(['null']);
    expect(parseTags('{"tag":"pc"}')).toEqual(['{"tag":"pc"}']);
  });

  it('reads the numbers a spreadsheet column may hold as tags', () => {
    expect(parseTags('[1,2]')).toEqual(['1', '2']);
  });
});

describe('reading a clipboard cell we wrote ourselves', () => {
  it('takes the tags back out of a JSON list', () => {
    expect(parseTags('["pc","marduk"]')).toEqual(['pc', 'marduk']);
  });

  it('reads an empty list as no tags', () => {
    expect(parseTags('[]')).toEqual([]);
  });

  // The whole point of writing JSON: a tag keeps whatever is inside it.
  it('keeps a tag that contains a separator whole', () => {
    expect(parseTags('["player character","ex-navy, retired"]')).toEqual([
      'player character',
      'ex-navy, retired',
    ]);
  });
});

describe('formatTags', () => {
  it('writes a tag list out as one clipboard cell', () => {
    expect(formatTags(['pc', 'marduk'])).toBe('["pc","marduk"]');
  });

  it('round-trips through a paste', () => {
    expect(parseTags(formatTags(['pc', 'marduk']))).toEqual(['pc', 'marduk']);
  });

  // The separators are what a looser format would lose. This is the case the
  // old space-joined format could not represent at all.
  it('round-trips a tag that contains spaces and commas', () => {
    const tags = ['player character', 'ex-navy, retired'];
    expect(parseTags(formatTags(tags))).toEqual(tags);
  });

  // SvGrid copies a range as TSV, so a tab or a newline in a tag would tear
  // the pasted block apart into extra cells and rows. JSON escapes both.
  it('writes a tag list that cannot break a TSV block', () => {
    const cell = formatTags(['two\twords', 'two\nlines']);
    expect(cell).not.toMatch(/[\t\n]/);
    expect(parseTags(cell)).toEqual(['two\twords', 'two\nlines']);
  });
});

describe('reading tags out of stored data', () => {
  it('takes a list as it is', () => {
    expect(tagsSchema.parse(['pc', 'marduk'])).toEqual(['pc', 'marduk']);
  });

  // A mis-typed edit once stored `"tags": "PC Marduk"`, and refusing it made
  // every party in the library unreadable rather than just that one.
  it('repairs a file that stored them as one string', () => {
    expect(tagsSchema.parse('PC Marduk')).toEqual(['PC', 'Marduk']);
  });

  it('treats a missing value as no tags', () => {
    expect(tagsSchema.parse(undefined)).toEqual([]);
  });
});

describe('the tags already in use', () => {
  const tagged = (...tags: string[]) => ({ tags });

  it('offers each tag once, however many things carry it', () => {
    expect(distinctTags([tagged('pc', 'marduk'), tagged('pc', 'npc')])).toEqual(['marduk', 'npc', 'pc']);
  });

  it('sorts them, so the form does not reorder itself as things are tagged', () => {
    expect(distinctTags([tagged('zeta'), tagged('alpha')])).toEqual(['alpha', 'zeta']);
  });

  it('has nothing to offer for things with no tags', () => {
    expect(distinctTags([tagged(), tagged()])).toEqual([]);
  });
});
