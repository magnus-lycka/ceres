/**
 * What a characteristic score is worth as a dice modifier.
 *
 * The Characteristic Modifiers table, refs/core/02_traveller_creation.md:81. A
 * score is impaired by damage, and the impaired DM is the one that counts until
 * it is healed (refs/core/03_combat.md:267).
 */

/** The DM for a score: 0 is −3, 1–2 −2, 3–5 −1, 6–8 0, 9–11 +1, 12–14 +2, 15 and up +3. */
export function characteristicDm(score: number): number {
  if (score <= 0) return -3;
  if (score >= 15) return 3;
  return Math.floor(score / 3) - 2;
}
