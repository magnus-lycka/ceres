/**
 * What an attack does once the referee has rolled it.
 *
 * Nothing here rolls. The referee rolls the check and the damage at the table
 * and types the results in; this is the arithmetic that follows, which is the
 * same for a sophont, an animal and a robot (refs/core/03_combat.md:263-280).
 */
import type { Actor, ActorId } from '../../schema/actor';
import { takeDamage } from './damage';
import { attack, incapacitate, type Situation } from './situation';

export type Attack = {
  /** The attack check's Effect: the roll and modifiers, less 8. */
  effect: number;
  /** The damage dice as rolled, before Effect and Protection. */
  roll: number;
  /** Protection the weapon ignores (AP). */
  ap?: number;
  /** The target's Protection for this attack. */
  protection?: number;
};

/** The check succeeds at 8 or more, which is Effect 0; below that it missed. */
export function isMiss(effect: number): boolean {
  return effect < 0;
}

/** The damage that reaches the target, after Protection. */
export function resolveAttack({ effect, roll, ap = 0, protection = 0 }: Attack): number {
  if (isMiss(effect)) return 0;
  const landed = Math.max(roll + effect - Math.max(protection - ap, 0), 0);
  // A precise enough hit always hurts, whatever it hit (:278).
  return effect >= 6 ? Math.max(landed, 1) : landed;
}

/** The weapon traits that change what Protection an attack meets. */
export type Traits = {
  /** Pellet ammunition: armour is doubly effective (refs/core/04_equipment.md:827). */
  shotgun?: boolean;
  /** A stunner: a robot's Protection is only half effective (refs/robot/50_other_considerations.md:29). */
  stun?: boolean;
};

/**
 * What the target's Protection comes to against this weapon.
 *
 * Only a robot's is halved by a stunner: a stunner causes it physical Hits, so
 * the armour that would have stood in the way of a shock is half as much use
 * against it. An android's or a biological robot's stays whole, and so do the
 * hostile-environment and radiation additions; none of those are modelled, and
 * the referee overtypes Protection for them (RIC-017). A halving that comes out
 * fractional rounds down.
 */
export function protectionAgainst(target: Actor, { shotgun, stun }: Traits): number {
  let protection = shotgun ? target.protection * 2 : target.protection;
  if (stun && target.kind === 'robot') protection = Math.floor(protection / 2);
  return protection;
}

export type Strike = {
  attacker: ActorId;
  target: ActorId;
  effect: number;
  roll: number;
  ap?: number;
  /** For this attack. Defaults to the target's own, and is overtyped for cover. */
  protection?: number;
  /** Which of STR or DEX takes the excess once END is gone: the target's choice. */
  excessTo?: 'strength' | 'dexterity';
  /** A Stun weapon: the damage is stun, not lethal (:366). */
  stun?: boolean;
  /** A Shotgun with pellet ammunition: armour is doubly effective. */
  shotgun?: boolean;
};

/**
 * One attack, end to end: what lands, where it lands, and whose turn it spends.
 *
 * Returns the situation, with the attacker's turn spent and their target
 * recorded, and the target as it now stands. A miss still spends the turn and
 * records the target; it just hurts no one.
 */
export function carryOutAttack(
  situation: Situation,
  roster: readonly Actor[],
  { attacker, target, effect, roll, ap, protection, excessTo, stun, shotgun }: Strike,
): { situation: Situation; target: Actor } {
  const victim = roster.find((actor) => actor.id === target);
  if (!victim) throw new Error(`there is no actor ${target} to attack`);
  const met = protection ?? protectionAgainst(victim, { shotgun, stun });
  const landed = resolveAttack({ effect, roll, ap, protection: met });
  const hurt = takeDamage(victim, {
    ...(stun ? { stun: landed } : { lethal: landed }),
    at: situation.round,
    excessTo,
  });
  return {
    situation: incapacitate(attack(situation, attacker, target), target, hurt.incapacitatedFor),
    target: hurt.actor,
  };
}
