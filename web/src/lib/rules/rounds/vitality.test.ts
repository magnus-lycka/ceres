/**
 * How an actor's health reads on the round table.
 *
 * Two cells say the same thing at two moments: what this actor started with and
 * what is left. A sophont's is half a UCP — STR, DEX and END as three extended
 * hex digits — and an actor hurt through Hits shows a plain number, because
 * Hits is one score and writing it as a digit would hide a wound of 12 behind
 * the letter C.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import { maxVitality, nowVitality, stunCell } from './vitality';

function sophont(extra: Partial<Actor> = {}): Actor {
  return {
    id: actorId(1),
    name: 'Rin',
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 7,
    dexterity: 7,
    endurance: 14,
    hits: null,
    injuries: [],
    criticals: {},
    ...extra,
  };
}

const beast = (extra: Partial<Actor> = {}): Actor =>
  sophont({
    kind: 'animal',
    strength: null,
    dexterity: null,
    endurance: null,
    hits: 42,
    ...extra,
  });

const lethal = (reductions: Partial<Record<string, number>>) => ({
  when: null,
  kind: 'lethal' as const,
  reductions,
});
const stun = (reductions: Partial<Record<string, number>>) => ({
  when: null,
  kind: 'stun' as const,
  reductions,
});

describe('a sophont', () => {
  it('shows its characteristics as three extended hex digits', () => {
    expect(maxVitality(sophont())).toBe('77E');
  });

  it('shows what is left the same way', () => {
    const hurt = sophont({ injuries: [lethal({ strength: 3, endurance: 5 })] });
    expect(nowVitality(hurt)).toBe('479');
  });

  it('reads the same in both cells while unhurt', () => {
    expect(nowVitality(sophont())).toBe(maxVitality(sophont()));
  });

  // A characteristic at zero is a fact worth reading, not a blank.
  it('shows a spent characteristic as zero', () => {
    const spent = sophont({ injuries: [lethal({ strength: 7 })] });
    expect(nowVitality(spent)).toBe('07E');
  });
});

describe('an actor hurt through Hits', () => {
  it('shows a plain number rather than a digit', () => {
    expect(maxVitality(beast())).toBe('42');
  });

  it('counts damage off it', () => {
    expect(nowVitality(beast({ injuries: [lethal({ hits: 10 })] }))).toBe('32');
  });

  // Destruction is measured below zero, so the minus sign carries meaning.
  it('goes below zero rather than stopping there', () => {
    expect(nowVitality(beast({ injuries: [lethal({ hits: 50 })] }))).toBe('-8');
  });
});

/**
 * Stun sits on the same score as lethal damage (RIC-011), so the Now cell
 * cannot say how much of a loss will come back after an hour's rest. That is
 * what this column is for: an END of 9 down from 14 means one thing to a medic
 * and another to someone waiting for the stun to wear off.
 */
describe('the stun cell', () => {
  it('says how many points are stun', () => {
    expect(stunCell(sophont({ injuries: [stun({ endurance: 5 })] }))).toBe('5');
  });

  it('counts only the stun, not the wound beside it', () => {
    const both = sophont({ injuries: [lethal({ endurance: 4 }), stun({ endurance: 5 })] });
    expect(stunCell(both)).toBe('5');
    expect(nowVitality(both)).toBe('775');
  });

  // An empty cell reads as "nothing to know here", which is the common case.
  it('is blank when there is none', () => {
    expect(stunCell(sophont())).toBe('');
  });

  it('reports stun on an actor hurt through Hits too', () => {
    expect(stunCell(beast({ injuries: [stun({ hits: 6 })] }))).toBe('6');
  });
});
