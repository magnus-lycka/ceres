/**
 * Reactions, and the DMs they put on an attacker's roll.
 *
 * The referee rolls the attack and types in the Effect, which already includes
 * whatever a reaction cost the attacker. What this offers is the reminder
 * before the roll: which reactions the attack allows, and the DMs the app knows
 * of. It never adjusts a number the referee types.
 */
import type { Actor } from '../../schema/actor';
import { characteristicDm } from '../characteristics';
import { current } from './health';

export type AttackKind = 'melee' | 'ranged';
export type Reaction = 'dodge' | 'dive' | 'parry';

/**
 * What a target may do about an attack (refs/core/03_combat.md:190-214).
 *
 * Both kinds may be dodged. Diving for cover is only from ranged attacks, and a
 * parry is a close-combat response to a melee one.
 */
export function reactionsAgainst(attack: AttackKind): Reaction[] {
  return attack === 'ranged' ? ['dodge', 'dive'] : ['dodge', 'parry'];
}

/** One line of the reminder: what it is, and its DM on the attacker's roll, or null when the app cannot know it. */
export type Modifier = { label: string; dm: number | null };

type Situation = {
  /** Who the attack is against. */
  defender: Actor;
  reaction: Reaction | null;
  attack: AttackKind;
  /** A Shotgun with pellet ammunition ignores Dodge modifiers (refs/core/04_equipment.md:827). */
  shotgun?: boolean;
  /** Reactions the attacker has taken that count against the roll they are about to make. */
  attackerReactions?: number;
};

/**
 * The Dodge: a penalty equal to the defender's DEX DM. That is the floor of what
 * the rule says, since Athletics (dexterity) may be higher and the app holds no
 * skills; and a DEX so poor its DM is negative gives the attacker nothing, as a
 * penalty cannot be a bonus.
 */
function dodge(defender: Actor): Modifier {
  const dexterity = current(defender, 'dexterity');
  if (dexterity === null) return { label: 'Dodge', dm: null };
  const dm = characteristicDm(dexterity);
  return { label: 'Dodge (DEX DM)', dm: dm > 0 ? -dm : 0 };
}

/** What the defender's reaction, if any, costs the attacker. */
function defendersReaction({ defender, reaction, attack, shotgun }: Situation): Modifier[] {
  // A reaction the attack does not allow is no reaction at all.
  if (reaction === null || !reactionsAgainst(attack).includes(reaction)) return [];
  if (reaction === 'dive') return [{ label: 'Dive for cover', dm: -2 }];
  if (reaction === 'parry') return [{ label: 'Parry (Melee skill)', dm: null }];
  if (shotgun) return [{ label: 'Dodge (ignored by a Shotgun)', dm: 0 }];
  return [dodge(defender)];
}

/**
 * The DMs the app knows of: what the defender's reaction costs the attacker, and
 * DM-1 for each reaction the attacker has taken themselves (:192). Nothing here
 * is ever applied to a roll.
 */
export function knownModifiers(situation: Situation): Modifier[] {
  const rows = defendersReaction(situation);
  const own = situation.attackerReactions ?? 0;
  return own > 0 ? [...rows, { label: 'Your reactions', dm: -own }] : rows;
}

/**
 * The known DMs added up. `complete` is false when one of them could not be
 * known, so a total that leaves it out is not mistaken for the whole of it.
 */
export function totalOf(modifiers: Modifier[]): { dm: number; complete: boolean } {
  return {
    dm: modifiers.reduce((sum, modifier) => sum + (modifier.dm ?? 0), 0),
    complete: modifiers.every((modifier) => modifier.dm !== null),
  };
}
