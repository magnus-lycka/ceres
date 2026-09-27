/**
 * How badly damaged a robot reads at a glance, from its criticals.
 *
 * Nothing here is a rule from the source: this is how the app shows what its
 * own record already holds, decided at the table (docs/plan-rounds.md).
 */
import type { Actor } from '../../schema/actor';
import { criticalRows } from './criticals';

/**
 * Sum of squared severities across all seven locations. Squaring means one
 * Severity 6 (36) outweighs six Severity 1s (6): a single wrecked system reads
 * as worse than several scratches, not the same. Null for anything that has no
 * systems to damage.
 */
export function criticalScore(actor: Actor): number | null {
  if (actor.kind !== 'robot') return null;
  return criticalRows(actor).reduce((sum, row) => sum + row.severity * row.severity, 0);
}

/**
 * The red channel value (0-255) for a foreground colour ramp: 8 per point of
 * score, reaching full red at a score of 32 — which one Severity 6 alone (36)
 * already exceeds. Never applied to a row's background, which already carries
 * dead, unconscious and acted.
 */
export function criticalHeat(score: number): number {
  return Math.min(Math.max(score, 0) * 8, 255);
}
