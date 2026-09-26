/**
 * What an attack does once the referee has rolled it.
 *
 * Nothing here rolls. The referee rolls the check and the damage at the table
 * and types the results in; this is the arithmetic that follows, which is the
 * same for a sophont, an animal and a robot (refs/core/03_combat.md:263-280).
 */
import type { Actor, ActorId } from '../../schema/actor';
import { attackCriticalSeverity } from './criticals';
import { takeDamage } from './damage';
import { attack, dive, incapacitate, react, type Situation } from './situation';
import type { Reaction } from './reaction';

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
  /** What the target did about it. Recorded whether the attack hit or missed. */
  reaction?: Reaction | null;
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
  { attacker, target, effect, roll, ap, protection, excessTo, stun, shotgun, reaction }: Strike,
): { situation: Situation; target: Actor; criticalSeverity: number } {
  const victim = roster.find((actor) => actor.id === target);
  if (!victim) throw new Error(`there is no actor ${target} to attack`);
  const met = protection ?? protectionAgainst(victim, { shotgun, stun });
  const landed = resolveAttack({ effect, roll, ap, protection: met });
  const hurt = takeDamage(victim, {
    ...(stun ? { stun: landed } : { lethal: landed }),
    at: situation.round,
    excessTo,
  });
  const struck = incapacitate(attack(situation, attacker, target), target, hurt.incapacitatedFor);
  return {
    situation: withReaction(struck, target, reaction),
    target: hurt.actor,
    // Only a robot has systems to take one. "Effect 6+ and inflicts damage after Protection": an
    // Effect of 6 or more always inflicts at least 1 (:278), so the second condition always holds.
    criticalSeverity: victim.kind === 'robot' ? attackCriticalSeverity(effect) : 0,
  };
}

/**
 * What the target's reaction costs them. A Dodge or a Parry is DM-1 on their next
 * actions; diving for cover costs those actions themselves, and leaves them prone.
 */
function withReaction(
  situation: Situation,
  target: ActorId,
  reaction: Reaction | null | undefined,
): Situation {
  if (reaction === 'dodge' || reaction === 'parry') return react(situation, target);
  if (reaction === 'dive') return dive(situation, target);
  return situation;
}

export type Harm = {
  target: ActorId;
  /** The damage as it lands: no Effect, no AP and no Protection, as armour does not stop a fall. */
  damage: number;
  /** Stun rather than lethal: END only, and never lethal (:366). */
  stun?: boolean;
  /** Which of STR or DEX takes the excess once END is gone: the target's choice. */
  excessTo?: 'strength' | 'dexterity';
};

/**
 * Injury with nobody to blame: a fall, a fire, a hull breach. The referee enters
 * the damage as it lands (refs/core/03_combat.md:400: armour does not protect
 * against a fall). No one's turn is spent and no target recorded, because no one
 * acted; a stun that puts the target out is counted as for any other hit.
 */
export function harm(
  situation: Situation,
  roster: readonly Actor[],
  { target, damage, stun, excessTo }: Harm,
): { situation: Situation; target: Actor } {
  const victim = roster.find((actor) => actor.id === target);
  if (!victim) throw new Error(`there is no actor ${target} to hurt`);
  const hurt = takeDamage(victim, {
    ...(stun ? { stun: damage } : { lethal: damage }),
    at: situation.round,
    excessTo,
  });
  return { situation: incapacitate(situation, target, hurt.incapacitatedFor), target: hurt.actor };
}
