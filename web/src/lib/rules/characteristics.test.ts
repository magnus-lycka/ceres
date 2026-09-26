/**
 * The Characteristic Modifiers table (refs/core/02_traveller_creation.md:81),
 * asserted at the edge of every band rather than at a formula's idea of them.
 */
import { describe, expect, it } from 'vitest';
import { characteristicDm } from './characteristics';

describe('characteristicDm', () => {
  it.each([
    [0, -3],
    [1, -2],
    [2, -2],
    [3, -1],
    [5, -1],
    [6, 0],
    [8, 0],
    [9, 1],
    [11, 1],
    [12, 2],
    [14, 2],
    [15, 3],
  ])('is the table’s value for a score of %i', (score, dm) => {
    expect(characteristicDm(score)).toBe(dm);
  });

  // "15+" is the top row: augmentation can take a score past 15 without the
  // modifier going on climbing.
  it('stays at +3 above 15', () => {
    expect(characteristicDm(18)).toBe(3);
    expect(characteristicDm(33)).toBe(3);
  });
});
