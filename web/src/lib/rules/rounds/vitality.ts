/**
 * An actor's health as two cells: what it started with, and what is left.
 *
 * Presentation of the rules in `health.ts`, kept beside them rather than in a
 * component because how a characteristic is written is a Traveller convention,
 * not a styling choice — the same string belongs in an export, a print sheet
 * and a grid.
 *
 * A sophont reads as half a UCP: STR, DEX and END as three extended hex digits,
 * `77E`. An actor hurt through Hits reads as a plain number, because Hits is
 * one score with a wide range and writing 12 as `C` would hide it.
 */
import { toEhex } from '$lib/rules/ehex';
import type { Actor } from '$lib/schema/actor';
import { CHARACTERISTICS, current, currentHits, hurtByCharacteristics, stunPoints } from './health';

/**
 * A number that has no extended hex digit, shown as itself.
 *
 * `toEhex` refuses rather than inventing a digit, which is right for the
 * notation and wrong for a table: a characteristic outside 0-33 is bad data,
 * and the useful thing to do with bad data on screen is show it, not hide the
 * row behind an exception.
 */
function digit(value: number | null): string {
  if (value === null) return '-';
  try {
    return toEhex(value);
  } catch {
    return String(value);
  }
}

/** What this actor is when unhurt. */
export function maxVitality(actor: Actor): string {
  if (!hurtByCharacteristics(actor)) return actor.hits === null ? '-' : String(actor.hits);
  return CHARACTERISTICS.map((stat) => digit(actor[stat])).join('');
}

/** What is left of it. */
export function nowVitality(actor: Actor): string {
  if (!hurtByCharacteristics(actor)) {
    const left = currentHits(actor);
    return left === null ? '-' : String(left);
  }
  return CHARACTERISTICS.map((stat) => digit(current(actor, stat))).join('');
}

/**
 * How much of the loss is stun, and will therefore come back.
 *
 * Stun and lethal damage reduce one shared score (RIC-011), so `nowVitality`
 * cannot distinguish them — an END of 9 down from 14 means one thing to a
 * medic and another to someone waiting for an hour's rest to undo it. Blank
 * when there is none, which is the common case and the one worth not shouting.
 *
 * The rounds of incapacitation are deliberately absent. RIC-011 makes the
 * countdown separate from the suppression, with a later hit replacing the
 * remaining duration only when it is longer, so it cannot be derived from the
 * injuries: they record the reduction applied, never the damage rolled. It
 * belongs on the membership row, and nothing sets it until attacks are entered.
 */
export function stunCell(actor: Actor): string {
  const points = stunPoints(actor);
  return points === 0 ? '' : String(points);
}
