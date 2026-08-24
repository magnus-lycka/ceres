/**
 * What an actor's injuries add up to.
 *
 * Ported from `ceres.rounds.domain.tracks`. Current values are the maximum
 * less what the injury history records, so nothing is replayed to answer a
 * question and the first-aid view reads the same history.
 *
 * The rule interpretations are recorded in `docs/RULE_INTERPRETATIONS.md`:
 * RIC-011 (stun and lethal reduce one shared END score) and RIC-012 (stun can
 * never complete a kill) are the two that shape this file.
 */
import type { Actor, Injury, Stat } from '../../schema/actor';

const CHARACTERISTICS = ['strength', 'dexterity', 'endurance'] as const;
export type Characteristic = (typeof CHARACTERISTICS)[number];

/** Whether this actor is hurt through characteristics or through Hits. */
export function hurtByCharacteristics(actor: Actor): boolean {
  return actor.kind === 'sophont';
}

function reduction(injury: Injury, stat: Stat): number {
  return injury.reductions[stat] ?? 0;
}

function total(actor: Actor, stat: Stat, kind?: Injury['kind']): number {
  return actor.injuries
    .filter((injury) => kind === undefined || injury.kind === kind)
    .reduce((sum, injury) => sum + reduction(injury, stat), 0);
}

/**
 * The one stat stun can touch.
 *
 * Stun damage is deducted from END only — it never spills into STR or DEX, and
 * so can never kill. For an actor hurt through Hits it suppresses Hits.
 */
export function stunStat(actor: Actor): Stat {
  return hurtByCharacteristics(actor) ? 'endurance' : 'hits';
}

/** Stun currently suppressing the damage-bearing stat. */
export function stunPoints(actor: Actor): number {
  return total(actor, stunStat(actor), 'stun');
}

/**
 * Current value of a characteristic: maximum less lethal, less the stun
 * sitting on END. Stun and lethal reduce one shared END score (RIC-011), so
 * nothing here branches on which kind a point came from.
 */
export function current(actor: Actor, stat: Characteristic): number | null {
  const maximum = actor[stat];
  if (maximum === null) return null;
  const stun = stat === 'endurance' ? total(actor, 'endurance', 'stun') : 0;
  return Math.max(maximum - total(actor, stat, 'lethal') - stun, 0);
}

/** Current Hits. Allowed to go negative: destruction is measured below zero. */
export function currentHits(actor: Actor): number | null {
  if (actor.hits === null) return null;
  return actor.hits - total(actor, 'hits', 'lethal') - total(actor, 'hits', 'stun');
}

/**
 * Unconscious once STR or DEX is exhausted; END alone does not do it. For an
 * actor hurt through Hits, at a tenth of starting Hits or less.
 */
export function isUnconscious(actor: Actor): boolean {
  if (hurtByCharacteristics(actor)) {
    return current(actor, 'strength') === 0 || current(actor, 'dexterity') === 0;
  }
  const hits = lethalHits(actor);
  return hits !== null && hits > 0 && hits * 10 <= (actor.hits ?? 0);
}

/** Hits after lethal damage only — stun can never complete a kill (RIC-012). */
function lethalHits(actor: Actor): number | null {
  if (actor.hits === null) return null;
  return actor.hits - total(actor, 'hits', 'lethal');
}

/**
 * Dead when every physical characteristic is exhausted **by lethal damage
 * alone** — END suppressed by a stunner cannot be the point that finishes
 * someone off (RIC-012). For Hits, at zero or below by lethal damage.
 */
export function isDead(actor: Actor): boolean {
  if (hurtByCharacteristics(actor)) {
    return CHARACTERISTICS.every((stat) => (actor[stat] ?? 0) - total(actor, stat, 'lethal') <= 0);
  }
  const hits = lethalHits(actor);
  return hits !== null && hits <= 0;
}

/** Body destroyed at negative starting Hits or worse. */
export function isDestroyed(actor: Actor): boolean {
  const hits = lethalHits(actor);
  return hits !== null && hits <= -(actor.hits ?? 0);
}

/**
 * Record an injury that happened outside any fight — last session, offscreen,
 * or a correction. It carries no round, because there is no round here.
 *
 * Lethal damage may be any combination of stats: the cascade decides where it
 * lands at the moment it happens, but a partly healed actor can be any shape,
 * so there is nothing to check. Stun is different — it only ever touches one
 * stat, and allowing it anywhere else would let it kill.
 */
export function recordInjury(actor: Actor, kind: Injury['kind'], reductions: Partial<Record<Stat, number>>): Actor {
  if (kind === 'stun') {
    const allowed = stunStat(actor);
    const illegal = Object.entries(reductions).filter(([stat, points]) => stat !== allowed && points);
    if (illegal.length > 0) {
      throw new Error(`stun only reduces ${allowed}, not ${illegal.map(([stat]) => stat).join(', ')}`);
    }
  }
  return { ...actor, injuries: [...actor.injuries, { when: null, kind, reductions }] };
}

export function removeInjury(actor: Actor, index: number): Actor {
  return { ...actor, injuries: actor.injuries.filter((_, position) => position !== index) };
}

/** A short description of what is wrong with an actor, or '' when nothing is. */
export function healthSummary(actor: Actor): string {
  if (isDead(actor)) return isDestroyed(actor) ? 'destroyed' : 'dead';
  const states: string[] = [];
  if (isUnconscious(actor)) states.push('unconscious');
  if (stunPoints(actor) > 0) states.push(`stunned ${stunPoints(actor)}`);
  return states.join(', ');
}
