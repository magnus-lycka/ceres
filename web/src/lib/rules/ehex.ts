/**
 * Traveller extended hex.
 *
 * One character per value, 0 to 33. **I and O are not used**, so that a digit
 * can never be misread as a 1 or a 0 — which is why the letters run
 * `…G H J K…` and `…M N P Q…` rather than straight through the alphabet.
 *
 * Mirrors `ceres.shared` on the Python side, deliberately and character for
 * character: both render the same characteristics for the same reader, so a
 * difference between them would be a bug wherever it appeared.
 */
const EHEX = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ';

/**
 * The digit for a value, or a throw if there is not one.
 *
 * Refusing is deliberate. A value outside the range has no honest digit, and
 * inventing one would put a wrong characteristic in front of a referee who has
 * no way to tell it is wrong. Callers that display untrusted numbers should
 * decide for themselves what to show instead — see `vitality`.
 */
export function toEhex(value: number): string {
  const digit = EHEX[value];
  if (digit === undefined || !Number.isInteger(value)) {
    throw new RangeError(`No extended hex digit for ${value}: the notation runs 0 to 33.`);
  }
  return digit;
}
