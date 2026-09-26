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
import { current, currentHits, isDead, isDestroyed, stunPoints } from './health';
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
    const hit = takeDamage(sophont(), { lethal: 3, at: 2 }).actor;

    expect(hit.injuries).toEqual([{ when: 2, kind: 'lethal', reductions: { endurance: 3 } }]);
    expect(current(hit, 'endurance')).toBe(5);
    expect(current(hit, 'strength')).toBe(8);
  });

  // "any excess damage is deducted from either the target's STR or DEX
  // (target's choice of which)" (:264)
  it('spills to the characteristic the target chooses, once END is gone', () => {
    const toStrength = takeDamage(sophont(), { lethal: 11, at: 1, excessTo: 'strength' }).actor;
    expect(toStrength.injuries[0].reductions).toEqual({ endurance: 8, strength: 3 });

    const toDexterity = takeDamage(sophont(), { lethal: 11, at: 1, excessTo: 'dexterity' }).actor;
    expect(toDexterity.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 3 });
  });

  // "If either STR or DEX are reduced to 0 ... any further damage is deducted
  // from the remaining physical characteristic." (:265)
  it('goes on to the other one when the chosen one is gone', () => {
    const hit = takeDamage(sophont(), { lethal: 19, at: 1, excessTo: 'strength' }).actor;

    expect(hit.injuries[0].reductions).toEqual({ endurance: 8, strength: 8, dexterity: 3 });
    expect(current(hit, 'strength')).toBe(0);
  });

  // "If all three ... are reduced to 0, the Traveller has been killed." (:266)
  // Damage past that has nowhere to go and is not recorded.
  it('kills at the last point, and records no more than there was to take', () => {
    const hit = takeDamage(sophont(), { lethal: 40, at: 1 }).actor;

    expect(hit.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 8, strength: 8 });
    expect(isDead(hit)).toBe(true);
  });

  it('records nothing for a hit that took nothing off', () => {
    expect(takeDamage(sophont(), { lethal: 0, at: 1 }).actor.injuries).toEqual([]);
  });

  it('starts from what earlier hits left, not from the maximum', () => {
    const twice = takeDamage(takeDamage(sophont(), { lethal: 6, at: 1 }).actor, { lethal: 5, at: 2 }).actor;

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
    const hit = takeDamage(beast(20), { lethal: 25, at: 3 }).actor;

    expect(hit.injuries).toEqual([{ when: 3, kind: 'lethal', reductions: { hits: 25 } }]);
    expect(currentHits(hit)).toBe(-5);
    expect(isDestroyed(takeDamage(beast(20), { lethal: 40, at: 3 }).actor)).toBe(true);
  });
});

/**
 * Stun (refs/core/03_combat.md:366): "Damage is only deducted from END ... If
 * the target's END is reduced to 0, the target will be incapacitated and
 * unable to perform any actions for a number of rounds by which the damage
 * exceeded their END."
 */
describe('stun damage to a sophont', () => {
  it('comes off END only, and what does not fit is the rounds they are out for', () => {
    const { actor, incapacitatedFor } = takeDamage(sophont(), { stun: 10, at: 1 });

    expect(actor.injuries).toEqual([{ when: 1, kind: 'stun', reductions: { endurance: 8 } }]);
    expect(current(actor, 'endurance')).toBe(0);
    expect(current(actor, 'strength')).toBe(8);
    expect(stunPoints(actor)).toBe(8);
    expect(incapacitatedFor).toBe(2);
  });

  it('costs nothing while END lasts, and a hit that lands exactly on zero costs no rounds', () => {
    const some = takeDamage(sophont(), { stun: 3, at: 1 });
    expect(current(some.actor, 'endurance')).toBe(5);
    expect(some.incapacitatedFor).toBe(0);

    expect(takeDamage(sophont(), { stun: 8, at: 1 }).incapacitatedFor).toBe(0);
  });

  // RIC-011: one END score, reduced by both kinds. Stun is measured against
  // what lethal damage has left, not against a fresh maximum.
  it('is measured against the END that lethal damage has left', () => {
    const wounded = takeDamage(sophont(), { lethal: 5, at: 1 }).actor;

    const { actor, incapacitatedFor } = takeDamage(wounded, { stun: 5, at: 2 });

    expect(actor.injuries[1]).toEqual({ when: 2, kind: 'stun', reductions: { endurance: 3 } });
    expect(incapacitatedFor).toBe(2);
  });

  it('is all excess once END is already gone', () => {
    const flat = takeDamage(sophont(), { stun: 8, at: 1 }).actor;

    const { actor, incapacitatedFor } = takeDamage(flat, { stun: 4, at: 2 });

    expect(actor.injuries).toHaveLength(1);
    expect(incapacitatedFor).toBe(4);
  });

  // RIC-012: stun changes when someone falls unconscious, never how much lethal
  // damage it takes to kill them. STR 8, DEX 8, END 8 dies to 24 lethal
  // however much stun was on END first.
  it('can never make the kill: lethal damage claims the END that stun holds', () => {
    const stunned = takeDamage(sophont(), { stun: 8, at: 1 }).actor;

    const dead = takeDamage(stunned, { lethal: 23, at: 2 }).actor;
    expect(isDead(dead)).toBe(false);

    const gone = takeDamage(stunned, { lethal: 24, at: 2 }).actor;
    expect(isDead(gone)).toBe(true);
    expect(stunPoints(gone)).toBe(0);
  });

  // "displacing the stun points one for one" (RIC-012)
  it('gives up stun one point for each point of END that lethal damage claims', () => {
    const stunned = takeDamage(sophont(), { stun: 5, at: 1 }).actor;

    // 3 END left, 8 DEX and 8 STR take 19, the 20th point finds END held by stun.
    const hit = takeDamage(stunned, { lethal: 20, at: 2 }).actor;

    expect(stunPoints(hit)).toBe(4);
    expect(current(hit, 'endurance')).toBe(0);
    expect(isDead(hit)).toBe(false);
  });
});

/**
 * RIC-015: an animal's stun is the same points-and-overflow model as a
 * sophont's, with Hits in place of END. "A Stun weapon will incapacitate an
 * animal if it inflicts a cumulative amount of damage equal to half of its
 * Hits" (:604), so stun suppresses Hits down to half the starting Hits and no
 * further; the rest is how long it is out.
 */
describe('stun damage to an animal', () => {
  it('suppresses Hits down to half their starting value, and the rest is rounds out', () => {
    const { actor, incapacitatedFor } = takeDamage(beast(20), { stun: 12, at: 1 });

    expect(actor.injuries).toEqual([{ when: 1, kind: 'stun', reductions: { hits: 10 } }]);
    expect(currentHits(actor)).toBe(10);
    expect(incapacitatedFor).toBe(2);
  });

  it('is measured from the Hits lethal damage has left', () => {
    const wounded = takeDamage(beast(20), { lethal: 6, at: 1 }).actor;

    const { incapacitatedFor, actor } = takeDamage(wounded, { stun: 6, at: 2 });

    // 14 Hits left, half of 20 is the floor: only 4 more can be suppressed.
    expect(actor.injuries[1]).toEqual({ when: 2, kind: 'stun', reductions: { hits: 4 } });
    expect(incapacitatedFor).toBe(2);
  });

  it('is cumulative, and all excess once the floor is reached', () => {
    const half = takeDamage(beast(20), { stun: 10, at: 1 });
    expect(half.incapacitatedFor).toBe(0);

    const more = takeDamage(half.actor, { stun: 3, at: 2 });
    expect(more.actor.injuries).toHaveLength(1);
    expect(more.incapacitatedFor).toBe(3);
  });

  // RIC-015: lethal damage displaces stun one for one, so stun never lowers the
  // damage it takes to kill, or to knock out, or to destroy.
  it('gives up stun as lethal damage claims the Hits it was holding', () => {
    const stunned = takeDamage(beast(20), { stun: 10, at: 1 }).actor;

    const hit = takeDamage(stunned, { lethal: 6, at: 2 }).actor;

    // 14 Hits left, 10 is the floor: room for 4 stun, so 6 points go.
    expect(stunPoints(hit)).toBe(4);
    expect(currentHits(hit)).toBe(10);
  });
});

function warbot(hits = 20): Actor {
  return { ...beast(hits), id: actorId(3), name: 'Warbot', kind: 'robot' };
}

/**
 * "A stunner causes physical Hits, not temporary damage to robots"
 * (refs/robot/50_other_considerations.md:29). There is nothing to recover from
 * and nothing to be out for: it is Hits, and it stays.
 */
describe('stun damage to a robot', () => {
  it('is lasting Hits damage, with no stun held and no rounds out', () => {
    const { actor, incapacitatedFor } = takeDamage(warbot(20), { stun: 12, at: 2 });

    expect(actor.injuries).toEqual([{ when: 2, kind: 'lethal', reductions: { hits: 12 } }]);
    expect(stunPoints(actor)).toBe(0);
    expect(currentHits(actor)).toBe(8);
    expect(incapacitatedFor).toBe(0);
  });
});
