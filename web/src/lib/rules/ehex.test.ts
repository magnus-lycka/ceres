/**
 * Traveller extended hex.
 *
 * Mirrors `ceres.shared` — one alphabet, defined the same way on both sides.
 * The assertions come from the notation itself, not from the implementation:
 * digits 0-9 then letters, with **I and O left out** so they cannot be misread
 * as 1 and 0.
 */
import { describe, expect, it } from 'vitest';
import { toEhex } from './ehex';

describe('toEhex', () => {
  it('leaves the single digits alone', () => {
    expect(toEhex(0)).toBe('0');
    expect(toEhex(9)).toBe('9');
  });

  it('carries on into letters', () => {
    expect(toEhex(10)).toBe('A');
    expect(toEhex(15)).toBe('F');
  });

  // The whole point of the notation: I and O are skipped, so H is followed by
  // J and N by P. Getting this wrong shifts every value above 17.
  it('skips I, so 17 is H and 18 is J', () => {
    expect(toEhex(17)).toBe('H');
    expect(toEhex(18)).toBe('J');
  });

  it('skips O, so 22 is N and 23 is P', () => {
    expect(toEhex(22)).toBe('N');
    expect(toEhex(23)).toBe('P');
  });

  it('runs out at Z', () => {
    expect(toEhex(33)).toBe('Z');
  });

  it('never produces the two letters the notation excludes', () => {
    const all = Array.from({ length: 34 }, (_, value) => toEhex(value)).join('');
    expect(all).not.toContain('I');
    expect(all).not.toContain('O');
  });

  // A value with no digit has no honest representation, and a silently wrong
  // one is worse than a loud failure.
  it('refuses a value the notation cannot express', () => {
    expect(() => toEhex(34)).toThrow();
    expect(() => toEhex(-1)).toThrow();
  });
});
