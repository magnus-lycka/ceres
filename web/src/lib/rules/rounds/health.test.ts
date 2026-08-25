/**
 * Health rules, derived from refs/core/03_combat.md and the interpretations in
 * docs/RULE_INTERPRETATIONS.md — not from the Python implementation. These
 * mirror the assertions in tests/unit/rounds/test_tracks.py so a divergence
 * between the two ports shows up as a failure rather than as a surprise at the
 * table.
 */
import { describe, expect, it } from 'vitest';
import type { Actor, Injury, Stat } from '../../schema/actor';
import {
  current,
  currentHits,
  healthSummary,
  isDead,
  isUnconscious,
  recordInjury,
  removeInjury,
  stunPoints,
  stunStat,
} from './health';

function hurt(kind: Injury['kind'], reductions: Partial<Record<Stat, number>>): Injury {
  return { when: null, kind, reductions };
}

function sophont(injuries: Injury[] = []): Actor {
  return {
    id: 1,
    name: 'Rin',
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
    injuries,
    criticals: {},
  };
}

function beast(hits = 20, injuries: Injury[] = []): Actor {
  return {
    id: 2,
    name: 'Wolf',
    kind: 'animal',
    note: '',
    tags: [],
    strength: null,
    dexterity: null,
    endurance: null,
    hits,
    injuries,
    criticals: {},
  };
}

function warbot(hits = 20, injuries: Injury[] = []): Actor {
  return {
    id: 6,
    name: 'Warbot',
    kind: 'robot',
    note: '',
    tags: [],
    strength: null,
    dexterity: null,
    endurance: null,
    hits,
    injuries,
    criticals: {},
  };
}

describe('current characteristics', () => {
  it('is the maximum less what the injuries took', () => {
    expect(current(sophont([hurt('lethal', { endurance: 5 })]), 'endurance')).toBe(3);
  });

  it('never goes below zero', () => {
    expect(current(sophont([hurt('lethal', { endurance: 99 })]), 'endurance')).toBe(0);
  });

  it('is null for a stat this kind of actor does not have', () => {
    expect(current(beast(), 'strength')).toBeNull();
  });
});

describe('stun and lethal share one END score (RIC-011)', () => {
  it('both kinds reduce the same END', () => {
    const rin = sophont([hurt('lethal', { endurance: 4 }), hurt('stun', { endurance: 3 })]);
    expect(current(rin, 'endurance')).toBe(1);
    expect(stunPoints(rin)).toBe(3);
  });

  it('stun alone leaves STR and DEX untouched and cannot kill', () => {
    const rin = sophont([hurt('stun', { endurance: 8 })]);
    expect([current(rin, 'strength'), current(rin, 'dexterity')]).toEqual([8, 8]);
    expect(isDead(rin)).toBe(false);
  });
});

describe('unconsciousness and death', () => {
  it('zero END alone does not cause unconsciousness', () => {
    expect(isUnconscious(sophont([hurt('lethal', { endurance: 8 })]))).toBe(false);
  });

  it('unconscious once DEX is exhausted', () => {
    expect(isUnconscious(sophont([hurt('lethal', { endurance: 8, dexterity: 8 })]))).toBe(true);
  });

  it('dead when all three are exhausted by lethal damage', () => {
    const rin = sophont([hurt('lethal', { strength: 8, dexterity: 8, endurance: 8 })]);
    expect(isDead(rin)).toBe(true);
  });

  it('stun cannot complete a kill (RIC-012)', () => {
    // Everything reads zero, but two of the END points are stun.
    const rin = sophont([
      hurt('lethal', { strength: 8, dexterity: 8, endurance: 6 }),
      hurt('stun', { endurance: 2 }),
    ]);
    expect(current(rin, 'endurance')).toBe(0);
    expect(isUnconscious(rin)).toBe(true);
    expect(isDead(rin)).toBe(false);
  });
});

describe('actors hurt through Hits', () => {
  it('subtracts damage from Hits', () => {
    expect(currentHits(beast(20, [hurt('lethal', { hits: 5 })]))).toBe(15);
  });

  it('is unconscious at a tenth of starting Hits', () => {
    expect(isUnconscious(beast(20, [hurt('lethal', { hits: 18 })]))).toBe(true);
  });

  it('is dead at zero Hits', () => {
    expect(isDead(beast(20, [hurt('lethal', { hits: 20 })]))).toBe(true);
  });

  it('stun suppresses Hits without killing', () => {
    const wolf = beast(20, [hurt('stun', { hits: 20 })]);
    expect(isDead(wolf)).toBe(false);
    expect(stunPoints(wolf)).toBe(20);
  });
});

/**
 * "Do not treat it like a sophont or animal... There is no animal-style
 * driven-off, half-Hits or 10%-Hits unconscious state. A robot also takes no
 * automatic general penalty merely for having few Hits left."
 * — handouts/robot_combat_cards.typ, Card 2
 *
 * Hits work as they do for an animal; capacity falls only when a critical
 * damages a system, which `criticals.ts` records.
 */
describe('a robot loses Hits like an animal, but not the states that go with them', () => {
  it('has no unconscious state, however few Hits are left', () => {
    expect(isUnconscious(warbot(20, [hurt('lethal', { hits: 19 })]))).toBe(false);
  });

  it('is out of action at zero Hits', () => {
    expect(isDead(warbot(20, [hurt('lethal', { hits: 20 })]))).toBe(true);
  });

  it('is still operational above zero Hits', () => {
    expect(isDead(warbot(20, [hurt('lethal', { hits: 19 })]))).toBe(false);
  });
});

describe('recording an injury outside a fight', () => {
  it('carries no round, because there is no round in the library', () => {
    const rin = recordInjury(sophont(), 'lethal', { endurance: 3 });
    expect(rin.injuries[0].when).toBeNull();
    expect(current(rin, 'endurance')).toBe(5);
  });

  it('can be taken back off again', () => {
    const rin = recordInjury(sophont(), 'lethal', { endurance: 3 });
    expect(removeInjury(rin, 0).injuries).toEqual([]);
  });
});

describe('stun only ever reduces one stat', () => {
  it('is END for a sophont and Hits for anything else', () => {
    expect(stunStat(sophont())).toBe('endurance');
    expect(stunStat(beast())).toBe('hits');
  });

  it('refuses stun on STR or DEX, which would let it kill', () => {
    expect(() => recordInjury(sophont(), 'stun', { dexterity: 3 })).toThrow(/endurance/);
    expect(() => recordInjury(sophont(), 'stun', { strength: 3 })).toThrow();
  });

  it('accepts stun on END', () => {
    expect(recordInjury(sophont(), 'stun', { endurance: 3 }).injuries).toHaveLength(1);
  });

  it('accepts lethal in any combination, since healing leaves any shape', () => {
    const rin = recordInjury(sophont(), 'lethal', { strength: 2, dexterity: 1, endurance: 4 });
    expect(rin.injuries[0].reductions).toEqual({ strength: 2, dexterity: 1, endurance: 4 });
  });
});

describe('healthSummary', () => {
  it('says nothing about an unhurt actor', () => {
    expect(healthSummary(sophont())).toBe('');
  });

  it('reports stun points', () => {
    expect(healthSummary(sophont([hurt('stun', { endurance: 3 })]))).toBe('stunned 3');
  });

  it('reports death rather than listing the lesser states', () => {
    const rin = sophont([hurt('lethal', { strength: 8, dexterity: 8, endurance: 8 })]);
    expect(healthSummary(rin)).toBe('dead');
  });
});
