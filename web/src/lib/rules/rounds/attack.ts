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
  { attacker, target, effect, roll, ap, protection, excessTo, stun }: Strike,
): { situation: Situation; target: Actor } {
  const victim = roster.find((actor) => actor.id === target);
  if (!victim) throw new Error(`there is no actor ${target} to attack`);
  const landed = resolveAttack({ effect, roll, ap, protection: protection ?? victim.protection });
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
