/**
 * Tags arrive as a list, as pasted text, or as whatever an older file holds.
 * All three have to end up as the same list.
 */
import { describe, expect, it } from 'vitest';
import { formatTags, parseTags, tagsSchema } from './tags';

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
});

describe('formatTags', () => {
  it('writes a tag list out as one clipboard cell', () => {
    expect(formatTags(['pc', 'marduk'])).toBe('pc marduk');
  });

  it('round-trips through a paste', () => {
    expect(parseTags(formatTags(['pc', 'marduk']))).toEqual(['pc', 'marduk']);
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
