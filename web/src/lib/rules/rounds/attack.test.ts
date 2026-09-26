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
import { act, addActors, emptySituation, memberState } from './situation';
import { carryOutAttack, harm, protectionAgainst, resolveAttack } from './attack';

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

/**
 * The Protection an attack meets. Two weapon traits change it before anything
 * is subtracted, and both are named here so that neither is forgotten
 * (docs/RULE_INTERPRETATIONS.md, RIC-017 and RIC-018).
 */
describe('the Protection an attack meets', () => {
  const armoured = { ...sophont(9, 'Guard'), protection: 3 };

  it('is what the target wears, for an ordinary weapon', () => {
    expect(protectionAgainst(armoured, {})).toBe(3);
  });

  // "armour gives double Protection against pellet attacks" (:827)
  it('is doubled against a Shotgun', () => {
    expect(protectionAgainst(armoured, { shotgun: true })).toBe(6);
  });

  // "A normal robot's Protection is only half effective against stunner
  // attacks" (refs/robot/50_other_considerations.md:29). Halved and rounded
  // down, which is RIC-017's reading of a Protection that does not halve evenly.
  it('is halved against a Stun weapon, when the target is a robot, rounding down', () => {
    const plated = { ...armoured, kind: 'robot' as const, protection: 5 };

    expect(protectionAgainst(plated, { stun: true })).toBe(2);
    expect(protectionAgainst({ ...plated, protection: 8 }, { stun: true })).toBe(4);
  });

  it('is not halved for a target that is not a robot, nor against anything but Stun', () => {
    expect(protectionAgainst(armoured, { stun: true })).toBe(3);
    expect(protectionAgainst({ ...armoured, kind: 'robot' as const }, {})).toBe(3);
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

  // Recorded when the attack is applied, hit or miss: the reaction was taken
  // whatever came of the attack.
  describe('with a reaction', () => {
    const strike = { attacker: rex.id, target: guard.id, effect: 0, roll: 5 };

    it('costs the target DM-1 on the actions they have still to take', () => {
      const dodged = carryOutAttack(brawl, roster, { ...strike, reaction: 'dodge' });
      expect(dodged.situation.members[1]).toMatchObject({ reactions: 1, nextReactions: 0 });

      const parried = carryOutAttack(brawl, roster, { ...strike, reaction: 'parry' });
      expect(parried.situation.members[1].reactions).toBe(1);
    });

    it('is recorded on a miss too', () => {
      const { situation } = carryOutAttack(brawl, roster, { ...strike, effect: -1, reaction: 'dodge' });

      expect(situation.members[1].reactions).toBe(1);
    });

    it('costs next round’s actions when the target has already acted', () => {
      const { situation } = carryOutAttack(act(brawl, guard.id), roster, { ...strike, reaction: 'dodge' });

      expect(situation.members[1]).toMatchObject({ reactions: 0, nextReactions: 1 });
    });

    // Diving for cover forfeits their next actions entirely; it is not also a
    // DM-1 on actions they will not take.
    it('is not a DM-1 reaction, when the reaction is diving for cover', () => {
      const { situation } = carryOutAttack(brawl, roster, { ...strike, reaction: 'dive' });

      expect(situation.members[1]).toMatchObject({ reactions: 0, nextReactions: 0 });
    });

    it('puts a target who dives on the ground and takes the turn they had not yet used', () => {
      const { situation } = carryOutAttack(brawl, roster, { ...strike, reaction: 'dive' });

      expect(situation.members[1]).toMatchObject({ acted: true, conditions: ['prone'], forfeitsNext: false });
    });

    it('costs a target who dives after acting their next turn instead', () => {
      const { situation } = carryOutAttack(act(brawl, guard.id), roster, { ...strike, reaction: 'dive' });

      expect(situation.members[1]).toMatchObject({ conditions: ['prone'], forfeitsNext: true });
    });

    it('costs nothing when there is no reaction', () => {
      const { situation } = carryOutAttack(brawl, roster, strike);

      expect(situation.members[1]).toMatchObject({ reactions: 0, nextReactions: 0 });
    });
  });

  describe('with weapon traits', () => {
    const armoured = { ...guard, protection: 3 };
    const plated: Actor = {
      ...guard,
      id: actorId(3),
      name: 'Warbot',
      kind: 'robot',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      protection: 8,
    };
    const strike = { attacker: rex.id, effect: 0, roll: 12 };

    it('meets double the Protection from a Shotgun', () => {
      const { target } = carryOutAttack(brawl, [rex, armoured], {
        ...strike,
        target: armoured.id,
        shotgun: true,
      });

      // 12 less 6, not 12 less 3.
      expect(target.injuries[0].reductions).toEqual({ endurance: 6 });
    });

    it('meets half a robot’s Protection from a stunner, as lasting Hits', () => {
      const fight = { ...addActors(emptySituation(), [rex, plated], 'Everyone'), round: 3 };

      const { target } = carryOutAttack(fight, [rex, plated], { ...strike, target: plated.id, stun: true });

      // 12 less 4, not 12 less 8.
      expect(target.injuries).toEqual([{ when: 3, kind: 'lethal', reductions: { hits: 8 } }]);
    });

    it('still takes the Protection typed for this attack over any trait', () => {
      const { target } = carryOutAttack(brawl, [rex, armoured], {
        ...strike,
        target: armoured.id,
        shotgun: true,
        protection: 1,
      });

      expect(target.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 3 });
    });
  });

  describe('with a Stun weapon', () => {
    it('takes the damage off END as stun, and puts the target out for the overflow', () => {
      const { situation, target } = carryOutAttack(brawl, roster, {
        attacker: rex.id,
        target: guard.id,
        effect: 0,
        roll: 10,
        stun: true,
      });

      expect(target.injuries).toEqual([{ when: 3, kind: 'stun', reductions: { endurance: 8 } }]);
      // Hit in round 3 before acting, two rounds of overflow: out until round 5.
      expect(situation.members[1].incapacitatedUntil).toBe(5);
    });

    it('counts from the next round when the target has already acted', () => {
      const { situation } = carryOutAttack(act(brawl, guard.id), roster, {
        attacker: rex.id,
        target: guard.id,
        effect: 0,
        roll: 10,
        stun: true,
      });

      expect(situation.members[1].incapacitatedUntil).toBe(6);
    });

    it('puts no one out when the stun does not use up their END, or misses', () => {
      const light = carryOutAttack(brawl, roster, {
        attacker: rex.id,
        target: guard.id,
        effect: 0,
        roll: 5,
        stun: true,
      });
      expect(light.situation.members[1].incapacitatedUntil).toBeNull();

      const miss = carryOutAttack(brawl, roster, {
        attacker: rex.id,
        target: guard.id,
        effect: -1,
        roll: 12,
        stun: true,
      });
      expect(miss.situation.members[1].incapacitatedUntil).toBeNull();
      expect(miss.target.injuries).toEqual([]);
    });

    // A stunner causes a robot physical Hits: lasting, and nothing to be out for.
    it('does lasting Hits damage to a robot, and puts it out for no rounds', () => {
      const bot: Actor = {
        ...guard,
        id: actorId(3),
        name: 'Warbot',
        kind: 'robot',
        strength: null,
        dexterity: null,
        endurance: null,
        hits: 20,
      };
      const fight = { ...addActors(emptySituation(), [rex, bot], 'Everyone'), round: 3 };

      const { situation, target } = carryOutAttack(fight, [rex, bot], {
        attacker: rex.id,
        target: bot.id,
        effect: 0,
        roll: 12,
        stun: true,
      });

      expect(target.injuries).toEqual([{ when: 3, kind: 'lethal', reductions: { hits: 12 } }]);
      expect(situation.members[1].incapacitatedUntil).toBeNull();
    });
  });
});

/**
 * Falls, fire, vacuum: injury with nobody to blame. There is no attack check, so
 * no Effect, no AP and no reaction, and "Armour does not protect against damage
 * sustained from falling" (refs/core/03_combat.md:400). The referee enters the
 * damage as it lands; nobody's turn is spent, because nobody acted.
 */
describe('harm from something other than an attacker', () => {
  const armoured = { ...guard, protection: 5 };

  it('lands as given in this round, past any armour, and spends nobody’s turn', () => {
    const { situation, target } = harm(brawl, [rex, armoured], { target: armoured.id, damage: 6 });

    expect(target.injuries).toEqual([{ when: 3, kind: 'lethal', reductions: { endurance: 6 } }]);
    for (const member of situation.members) {
      expect(member).toMatchObject({ acted: false, target: null });
    }
  });

  it('can be stun, which puts the target out for the overflow as any stun does', () => {
    const { situation, target } = harm(brawl, roster, { target: guard.id, damage: 10, stun: true });

    expect(target.injuries).toEqual([{ when: 3, kind: 'stun', reductions: { endurance: 8 } }]);
    expect(situation.members[1].incapacitatedUntil).toBe(5);
  });

  it('puts the excess on the characteristic the target chose', () => {
    const { target } = harm(brawl, roster, { target: guard.id, damage: 10, excessTo: 'strength' });

    expect(target.injuries[0].reductions).toEqual({ endurance: 8, strength: 2 });
  });

  it('hurts no one for no damage', () => {
    const { target } = harm(brawl, roster, { target: guard.id, damage: 0 });

    expect(target.injuries).toEqual([]);
  });

  it('refuses someone who is not there', () => {
    expect(() => harm(brawl, roster, { target: actorId(99), damage: 3 })).toThrow(/no actor 99/);
  });
});
