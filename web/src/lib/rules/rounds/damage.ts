/**
 * Where a hit lands, and what it is recorded as.
 *
 * An injury is stored as the reduction it caused, settled at the moment it
 * lands, so nothing is replayed later. Deciding where damage goes is the rule
 * this module owns (refs/core/03_combat.md:262-266); reading what is left is
 * `health`'s.
 */
import type { Actor, Injury, Stat } from '../../schema/actor';
import { current, hurtByCharacteristics, stunPoints } from './health';

export type Damage = {
  lethal?: number;
  /** Stun points: END only, and never lethal (:366). */
  stun?: number;
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

/** How much of a characteristic lethal damage has taken, whatever stun is holding. */
function lethalOn(actor: Actor, stat: Stat): number {
  return actor.injuries
    .filter((injury) => injury.kind === 'lethal')
    .reduce((sum, injury) => sum + (injury.reductions[stat] ?? 0), 0);
}

/**
 * What a hit takes off a sophont's characteristics, in the order it does.
 *
 * Damage with nowhere left to go claims the END that stun is holding: END is
 * one score (RIC-011), and stun must never be what stands between an actor and
 * death (RIC-012).
 */
function drainCharacteristics(actor: Actor, lethal: number, excessTo: 'strength' | 'dexterity') {
  const reductions: Partial<Record<Stat, number>> = {};
  let remaining = lethal;
  for (const stat of drainOrder(excessTo)) {
    const absorbed = Math.min(remaining, current(actor, stat) ?? 0);
    if (absorbed > 0) reductions[stat] = absorbed;
    remaining -= absorbed;
  }
  const heldByStun = (actor.endurance ?? 0) - lethalOn(actor, 'endurance') - (reductions.endurance ?? 0);
  const claimed = Math.min(remaining, Math.max(heldByStun, 0));
  if (claimed > 0) reductions.endurance = (reductions.endurance ?? 0) + claimed;
  return reductions;
}

/**
 * How much stun this actor's damage-bearing stat can hold, given what lethal
 * damage has already taken: what is left of END, or of Hits above the half
 * that stun may not go below (RIC-015).
 */
function stunCapacity(actor: Actor): { stat: Stat; capacity: number } {
  if (hurtByCharacteristics(actor)) {
    return {
      stat: 'endurance',
      capacity: Math.max((actor.endurance ?? 0) - lethalOn(actor, 'endurance'), 0),
    };
  }
  const start = actor.hits ?? 0;
  return { stat: 'hits', capacity: Math.max(start - lethalOn(actor, 'hits') - Math.floor(start / 2), 0) };
}

/** Give up stun that lethal damage has claimed, oldest hit first, down to what can still be held. */
function displaceStun(actor: Actor): Actor {
  const { stat, capacity } = stunCapacity(actor);
  let excess = stunPoints(actor) - capacity;
  if (excess <= 0) return actor;
  const injuries: Injury[] = [];
  for (const injury of actor.injuries) {
    const held = injury.kind === 'stun' ? (injury.reductions[stat] ?? 0) : 0;
    if (held === 0 || excess <= 0) {
      injuries.push(injury);
      continue;
    }
    const removed = Math.min(excess, held);
    excess -= removed;
    if (held - removed > 0) injuries.push({ ...injury, reductions: { [stat]: held - removed } });
  }
  return { ...actor, injuries };
}

/** What a hit did: the actor afterwards, and for how many rounds it put them out. */
export type Hurt = { actor: Actor; incapacitatedFor: number };

/** Lethal damage, and the injury it caused recorded. Hits has no floor: how far below zero it goes is what says destroyed. */
function landLethal(actor: Actor, lethal: number, at: number, excessTo: 'strength' | 'dexterity'): Actor {
  const reductions: Partial<Record<Stat, number>> = hurtByCharacteristics(actor)
    ? drainCharacteristics(actor, lethal, excessTo)
    : lethal > 0
      ? { hits: lethal }
      : {};
  // A hit that took nothing off is not an injury.
  if (Object.keys(reductions).length === 0) return actor;
  const injury: Injury = { when: at, kind: 'lethal', reductions };
  const landed = { ...actor, injuries: [...actor.injuries, injury] };
  return displaceStun(landed);
}

/**
 * How much stun an animal's Hits can still hold: they may be suppressed to half
 * the starting value and no lower (RIC-015), measured from what lethal damage
 * has left.
 */
function stunRoomOnHits(actor: Actor): number {
  const start = actor.hits ?? 0;
  const lethalNow = start - lethalOn(actor, 'hits');
  return Math.max(lethalNow - Math.floor(start / 2), 0) - stunPoints(actor);
}

/**
 * Stun damage. A sophont's comes off END only, an animal's suppresses Hits to
 * half; whatever they cannot take is how many rounds the hit puts them out for
 * (:366, RIC-015).
 */
function landStun(actor: Actor, stun: number, at: number): Hurt {
  if (stun <= 0) return { actor, incapacitatedFor: 0 };
  const stat: Stat = hurtByCharacteristics(actor) ? 'endurance' : 'hits';
  const room = hurtByCharacteristics(actor) ? (current(actor, 'endurance') ?? 0) : stunRoomOnHits(actor);
  const absorbed = Math.min(stun, Math.max(room, 0));
  const injuries: Injury[] =
    absorbed > 0 ? [{ when: at, kind: 'stun', reductions: { [stat]: absorbed } }] : [];
  return {
    actor: { ...actor, injuries: [...actor.injuries, ...injuries] },
    incapacitatedFor: stun - absorbed,
  };
}

/** The actor after taking the hit, with what it caused recorded. */
export function takeDamage(actor: Actor, { lethal = 0, stun = 0, at, excessTo = 'dexterity' }: Damage): Hurt {
  // A stunner causes a robot physical Hits, not stun it could recover from
  // (Robot Handbook, p.106): it is lethal damage by the time it lands.
  if (actor.kind === 'robot')
    return { actor: landLethal(actor, lethal + stun, at, excessTo), incapacitatedFor: 0 };
  return landStun(landLethal(actor, lethal, at, excessTo), stun, at);
}
