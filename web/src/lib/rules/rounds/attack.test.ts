/**
 * What an attack does, derived from refs/core/03_combat.md — the damage
 * paragraph (:263), Armour (:278) and the AP trait (:280) — and not from the
 * implementation.
 *
 * The referee rolls; these take what was rolled. Nothing here is random.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { current, isDead } from './health';
import { addActors, emptySituation, memberState } from './situation';
import { carryOutAttack, resolveAttack } from './attack';

describe('the damage an attack lands', () => {
  // "damage is rolled for, with the Effect of the attack roll added" (:263),
  // then "Armour reduces the damage sustained by its Protection" (:278).
  it('is the damage roll plus the Effect, less Protection', () => {
    expect(resolveAttack({ effect: 2, roll: 7, protection: 3 })).toBe(6);
  });

  it('is never less than nothing, however good the armour', () => {
    expect(resolveAttack({ effect: 0, roll: 2, protection: 5 })).toBe(0);
  });

  // "An attack with Effect 6+ always inflicts at least one point of damage,
  // regardless of the actual damage rolled or the Protection score." (:278)
  it('is at least 1 at Effect 6 or better, whatever the armour', () => {
    expect(resolveAttack({ effect: 6, roll: 2, protection: 20 })).toBe(1);
    expect(resolveAttack({ effect: 9, roll: 2, protection: 20 })).toBe(1);
  });

  it('gets no such minimum at Effect 5', () => {
    expect(resolveAttack({ effect: 5, roll: 2, protection: 20 })).toBe(0);
  });

  // The check succeeds at 8+, which is Effect 0 or more; below that the attack
  // missed, and any damage dice rolled from habit are not damage.
  it('is nothing on a miss, however hard the dice were thrown', () => {
    expect(resolveAttack({ effect: -1, roll: 12 })).toBe(0);
    expect(resolveAttack({ effect: 0, roll: 12 })).toBe(12);
  });

  // "ignore an amount of Protection equal to the AP score" (:280): it takes
  // Protection down, and no further.
  it('ignores as much Protection as the weapon has AP', () => {
    expect(resolveAttack({ effect: 0, roll: 7, protection: 5, ap: 3 })).toBe(5);
    expect(resolveAttack({ effect: 0, roll: 7, protection: 2, ap: 5 })).toBe(7);
  });
});

function sophont(id: number, name: string): Actor {
  return {
    id: actorId(id),
    name,
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
    protection: 0,
    movement: null,
    speed: null,
    enduranceHours: null,
    int: null,
  };
}

const rex = sophont(1, 'Rex');
const guard = sophont(2, 'Guard');
const roster = [rex, guard];
const brawl = { ...addActors(emptySituation(), roster, 'Everyone'), round: 3 };

/** One attack, end to end: the arithmetic, where it lands, whose turn it spends. */
describe('carrying out an attack', () => {
  it('lands the damage on the target in this round, and spends the attacker turn', () => {
    const { situation, target } = carryOutAttack(brawl, roster, {
      attacker: rex.id,
      target: guard.id,
      effect: 2,
      roll: 7,
    });

    expect(target.injuries).toEqual([
      { when: 3, kind: 'lethal', reductions: { endurance: 8, dexterity: 1 } },
    ]);
    expect(memberState(situation, situation.members[0], roster)).toBe('acted');
    expect(situation.members[0].target).toBe(guard.id);
  });

  it('hurts no one on a miss, but still spends the turn and remembers the target', () => {
    const { situation, target } = carryOutAttack(brawl, roster, {
      attacker: rex.id,
      target: guard.id,
      effect: -2,
      roll: 12,
    });

    expect(target.injuries).toEqual([]);
    expect(current(target, 'endurance')).toBe(8);
    expect(memberState(situation, situation.members[0], roster)).toBe('acted');
    expect(situation.members[0].target).toBe(guard.id);
  });

  it('takes off the target’s own Protection unless told otherwise', () => {
    const armoured = { ...guard, protection: 5 };
    const { target } = carryOutAttack(brawl, [rex, armoured], {
      attacker: rex.id,
      target: armoured.id,
      effect: 0,
      roll: 9,
    });

    expect(target.injuries[0].reductions).toEqual({ endurance: 4 });
  });

  // Cover, a called shot, anything unusual: one number overtyped for this attack.
  it('takes off the Protection typed for this attack instead, when there is one', () => {
    const armoured = { ...guard, protection: 5 };
    const { target } = carryOutAttack(brawl, [rex, armoured], {
      attacker: rex.id,
      target: armoured.id,
      effect: 0,
      roll: 9,
      protection: 2,
    });

    expect(target.injuries[0].reductions).toEqual({ endurance: 7 });
  });

  it('puts the excess on the characteristic the target chose', () => {
    const { target } = carryOutAttack(brawl, roster, {
      attacker: rex.id,
      target: guard.id,
      effect: 0,
      roll: 10,
      excessTo: 'strength',
    });

    expect(target.injuries[0].reductions).toEqual({ endurance: 8, strength: 2 });
  });

  it('can kill, and does not refuse the last point', () => {
    const { target } = carryOutAttack(brawl, roster, {
      attacker: rex.id,
      target: guard.id,
      effect: 6,
      roll: 30,
    });

    expect(isDead(target)).toBe(true);
  });

  it('refuses an attack on someone who is not there', () => {
    expect(() =>
      carryOutAttack(brawl, roster, { attacker: rex.id, target: actorId(99), effect: 0, roll: 5 }),
    ).toThrow(/no actor 99/);
  });
});
