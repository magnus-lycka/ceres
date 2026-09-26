/**
 * Where damage lands, derived from refs/core/03_combat.md:262-266 and the
 * interpretations in docs/RULE_INTERPRETATIONS.md (RIC-011, RIC-012) — not from
 * the Python `DamageTrack` this ports.
 *
 * A hit is stored as the reduction it caused, so what these check is the
 * injury recorded and what the actor is left with.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { current, currentHits, isDead, isDestroyed } from './health';
import { takeDamage } from './damage';

const base = {
  note: '',
  tags: [],
  injuries: [],
  criticals: {},
  protection: 0,
  movement: null,
  speed: null,
  enduranceHours: null,
  int: null,
};

function sophont(): Actor {
  return {
    ...base,
    id: actorId(1),
    name: 'Rin',
    kind: 'sophont',
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
  };
}

describe('lethal damage to a sophont', () => {
  // "Damage is initially applied to a target's END." (:264)
  it('comes off END first, and records the round it landed in', () => {
    const hit = takeDamage(sophont(), { lethal: 3, at: 2 });

    expect(hit.injuries).toEqual([{ when: 2, kind: 'lethal', reductions: { endurance: 3 } }]);
    expect(current(hit, 'endurance')).toBe(5);
    expect(current(hit, 'strength')).toBe(8);
  });

  // "any excess damage is deducted from either the target's STR or DEX
  // (target's choice of which)" (:264)
  it('spills to the characteristic the target chooses, once END is gone', () => {
    const toStrength = takeDamage(sophont(), { lethal: 11, at: 1, excessTo: 'strength' });
    expect(toStrength.injuries[0].reductions).toEqual({ endurance: 8, strength: 3 });

    const toDexterity = takeDamage(sophont(), { lethal: 11, at: 1, excessTo: 'dexterity' });
    expect(toDexterity.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 3 });
  });

  // "If either STR or DEX are reduced to 0 ... any further damage is deducted
  // from the remaining physical characteristic." (:265)
  it('goes on to the other one when the chosen one is gone', () => {
    const hit = takeDamage(sophont(), { lethal: 19, at: 1, excessTo: 'strength' });

    expect(hit.injuries[0].reductions).toEqual({ endurance: 8, strength: 8, dexterity: 3 });
    expect(current(hit, 'strength')).toBe(0);
  });

  // "If all three ... are reduced to 0, the Traveller has been killed." (:266)
  // Damage past that has nowhere to go and is not recorded.
  it('kills at the last point, and records no more than there was to take', () => {
    const hit = takeDamage(sophont(), { lethal: 40, at: 1 });

    expect(hit.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 8, strength: 8 });
    expect(isDead(hit)).toBe(true);
  });

  it('records nothing for a hit that took nothing off', () => {
    expect(takeDamage(sophont(), { lethal: 0, at: 1 }).injuries).toEqual([]);
  });

  it('starts from what earlier hits left, not from the maximum', () => {
    const twice = takeDamage(takeDamage(sophont(), { lethal: 6, at: 1 }), { lethal: 5, at: 2 });

    expect(twice.injuries[1].reductions).toEqual({ endurance: 2, dexterity: 3 });
  });
});

function beast(hits = 20): Actor {
  return {
    ...base,
    id: actorId(2),
    name: 'Wolf',
    kind: 'animal',
    strength: null,
    dexterity: null,
    endurance: null,
    hits,
  };
}

describe('lethal damage to something hurt through Hits', () => {
  // "All damage is applied to Hits, rather than STR, DEX and END" — and Hits
  // may go negative, because destruction is measured below zero.
  it('comes straight off Hits, past zero if it must', () => {
    const hit = takeDamage(beast(20), { lethal: 25, at: 3 });

    expect(hit.injuries).toEqual([{ when: 3, kind: 'lethal', reductions: { hits: 25 } }]);
    expect(currentHits(hit)).toBe(-5);
    expect(isDestroyed(takeDamage(beast(20), { lethal: 40, at: 3 }))).toBe(true);
  });
});
