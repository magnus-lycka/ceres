/**
 * Robot critical hits.
 *
 * A robot loses Hits like an animal, but its Hits total carries no penalty of
 * its own. Criticals are the only thing that limits what a robot can do on its
 * turn or takes it out of action, which is why this app tracks them at all.
 * The state behind the combat record on `handouts/robot_combat_cards.typ`
 * (Card 2, "Robot Damage").
 *
 * **Nothing here is random.** The two mechanisms that produce a critical are
 * both derived from numbers the referee already has:
 *
 *  - the attack roll's Effect, when it is 6 or better — `attackCriticalSeverity`
 *  - each 10% of starting Hits that cumulative damage crosses, at Severity 1
 *    each — `sustainedCriticalCount`
 *
 * The location is the one thing the rules roll for, and the referee rolls it:
 * 2D on the table printed on the card. It arrives here as a location.
 *
 * What this module deliberately does **not** encode is the severity effects
 * table — Protection −1D, Speed −1 m/band, DM−2 to all skills, and the
 * "Chassis S+1" knock-ons. Most of it needs component identity the actor model
 * does not carry (which weapon, which option), and the knock-on rows do not
 * state plainly what severity the follow-on chassis critical takes. The record
 * names the row, the handout says what it does, and the note records the
 * answer.
 */
import {
  criticalLocations,
  WORST_SEVERITY,
  type Actor,
  type Critical,
  type CriticalLocation,
} from '../../schema/actor';

const UNDAMAGED: Critical = { severity: 0, note: '' };

/** What the record says about one location, whether or not it has been hit. */
export function criticalAt(actor: Actor, location: CriticalLocation): Critical {
  return actor.criticals[location] ?? UNDAMAGED;
}

export type CriticalRow = { location: CriticalLocation } & Critical;

/**
 * The whole combat record: all seven locations in table order, undamaged ones
 * included. The card prints seven rows whether or not anything has been hit,
 * and so does the screen.
 */
export function criticalRows(actor: Actor): CriticalRow[] {
  return criticalLocations.map((location) => ({ location, ...criticalAt(actor, location) }));
}

/**
 * Write one row of the record.
 *
 * A row with nothing to say — undamaged and unannotated — is dropped rather
 * than stored as an empty entry, so an undamaged robot carries no criticals at
 * all. Severity is free to go down as well as up here: this is the referee
 * editing the record, including repairing between situations.
 */
export function setCritical(actor: Actor, location: CriticalLocation, severity: number, note: string): Actor {
  const { [location]: _replaced, ...rest } = actor.criticals;
  const criticals = severity > 0 || note ? { ...rest, [location]: { severity, note } } : rest;
  return { ...actor, criticals };
}

/**
 * The severity a location reaches when it is hit again.
 *
 * "new Severity = max(rolled Severity, old Severity + 1)" — a repeat hit
 * always worsens the location by at least one step, however low the roll, and
 * severity stops climbing at 6.
 */
export function severityAfter(previous: number, rolled: number): number {
  if (previous <= 0) return rolled;
  return Math.min(Math.max(rolled, previous + 1), WORST_SEVERITY);
}

/**
 * Hits inflicted by the critical itself, over and above the attack's own
 * damage. Both cases below bypass Protection.
 *
 * The chassis row is the one whose effect is plain damage — Severity n means
 * suffer nD. And once a location is already at Severity 6 it cannot worsen, so
 * every further hit there inflicts 6D instead.
 */
function diceFor(location: CriticalLocation, previous: number, reached: number): number {
  if (previous >= WORST_SEVERITY) return WORST_SEVERITY;
  return location === 'chassis' ? reached : 0;
}

/**
 * Record a hit to a location, returning the damaged robot and any dice of Hits
 * the critical itself inflicts. The caller rolls them: this module does not
 * roll, and dice belong to the situation rather than to the record of what has
 * been hit.
 */
export function applyCritical(
  actor: Actor,
  location: CriticalLocation,
  severity: number,
): { actor: Actor; damageDice: number } {
  const previous = criticalAt(actor, location);
  const reached = severityAfter(previous.severity, severity);
  return {
    actor: setCritical(actor, location, reached, previous.note),
    damageDice: diceFor(location, previous.severity, reached),
  };
}

/**
 * The severity an attack's Effect inflicts, or 0 for no critical.
 *
 * "If the attack has Effect 6+ and inflicts damage after Protection:
 * Severity = attack Effect − 5." Whether damage got through Protection is the
 * caller's question; this answers only what the Effect is worth.
 */
export function attackCriticalSeverity(effect: number): number {
  if (effect < 6) return 0;
  return Math.min(effect - 5, WORST_SEVERITY);
}

/**
 * How many Severity 1 criticals a damage total has newly earned.
 *
 * "Every time cumulative damage crosses another 10% of starting Hits, roll a
 * location and inflict a Severity 1 critical." Both arguments are cumulative
 * damage, before and after the hit; a hit large enough to cross several
 * thresholds earns one for each.
 *
 * The extra damage a critical itself inflicts can cross further thresholds, so
 * the caller keeps resolving until this returns 0.
 */
export function sustainedCriticalCount(startingHits: number, before: number, after: number): number {
  if (startingHits <= 0) return 0;
  const step = startingHits / 10;
  return Math.max(Math.floor(after / step) - Math.floor(Math.max(before, 0) / step), 0);
}
