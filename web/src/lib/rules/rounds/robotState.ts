/**
 * What a robot is now, given what its criticals have taken off it.
 *
 * A current value is the base less the sum of what every location took, so
 * nothing is replayed to answer a question and repairing a location gives back
 * exactly what it took. The base is what the actor is; it is never edited here.
 */
import {
  criticalLocations,
  type Actor,
  type CriticalLocation,
  type RobotAttribute,
} from '../../schema/actor';
import { criticalEffect } from './criticalEffects';

/** The attribute as it stands: unset stays unset, and nothing goes below nothing. */
export function currentAttribute(actor: Actor, attribute: RobotAttribute): number | null {
  const base = actor[attribute];
  if (base === null) return null;
  const taken = criticalLocations.reduce(
    (sum, location) => sum + (actor.criticals[location]?.taken[attribute] ?? 0),
    0,
  );
  return Math.max(base - taken, 0);
}

/** The effect a location's critical has at the severity it has reached, if any. */
function effectAt(actor: Actor, location: CriticalLocation) {
  return criticalEffect(location, actor.criticals[location]?.severity ?? 0);
}

/**
 * Shut down or brainless: it can do nothing at all. That is the power supply at
 * Severity 5 or 6 ("shuts down") and the brain at 5 ("disabled") or 6
 * ("destroyed"), read off the effects table so that there is one definition.
 */
export function isInoperable(actor: Actor): boolean {
  return criticalLocations.some((location) => effectAt(actor, location)?.inoperable === true);
}

/**
 * Immobilised: it cannot move. That is all it cannot do, and "usable weapons may
 * still fire", so it does not stop the robot taking its turn.
 */
export function isImmobilised(actor: Actor): boolean {
  return effectAt(actor, 'locomotion')?.immobilised === true;
}
