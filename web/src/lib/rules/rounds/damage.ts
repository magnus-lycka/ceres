/**
 * Where a hit lands, and what it is recorded as.
 *
 * An injury is stored as the reduction it caused, settled at the moment it
 * lands, so nothing is replayed later. Deciding where damage goes is the rule
 * this module owns (refs/core/03_combat.md:262-266); reading what is left is
 * `health`'s.
 */
import type { Actor, Injury, Stat } from '../../schema/actor';
import { current, hurtByCharacteristics } from './health';

export type Damage = {
  lethal: number;
  /** The round of the situation it landed in. */
  at: number;
  /** Which of STR or DEX takes the excess once END is gone: the target's choice. */
  excessTo?: 'strength' | 'dexterity';
};

/**
 * END first, then the target's choice of STR or DEX, then the other one
 * (:264-265): once either is gone the target is unconscious, and further
 * damage goes to what is left.
 */
function drainOrder(excessTo: 'strength' | 'dexterity'): ('endurance' | 'strength' | 'dexterity')[] {
  return ['endurance', excessTo, excessTo === 'strength' ? 'dexterity' : 'strength'];
}

/** What a hit takes off a sophont's characteristics, in the order it does. */
function drainCharacteristics(actor: Actor, lethal: number, excessTo: 'strength' | 'dexterity') {
  const reductions: Partial<Record<Stat, number>> = {};
  let remaining = lethal;
  for (const stat of drainOrder(excessTo)) {
    const absorbed = Math.min(remaining, current(actor, stat) ?? 0);
    if (absorbed > 0) reductions[stat] = absorbed;
    remaining -= absorbed;
  }
  return reductions;
}

/**
 * The actor after taking the hit, with the injury it caused recorded.
 *
 * Hits has no floor: how far below zero it goes is what says destroyed.
 */
export function takeDamage(actor: Actor, { lethal, at, excessTo = 'dexterity' }: Damage): Actor {
  const reductions: Partial<Record<Stat, number>> = hurtByCharacteristics(actor)
    ? drainCharacteristics(actor, lethal, excessTo)
    : lethal > 0
      ? { hits: lethal }
      : {};
  // A hit that took nothing off is not an injury.
  if (Object.keys(reductions).length === 0) return actor;
  const injury: Injury = { when: at, kind: 'lethal', reductions };
  return { ...actor, injuries: [...actor.injuries, injury] };
}
