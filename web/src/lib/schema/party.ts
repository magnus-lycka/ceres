/**
 * What a Party is, defined once.
 *
 * A reusable named set of actors: the PCs, a wolf pack, starport security.
 * It holds no initiative and no combat state — a Situation copies a Party
 * rather than pointing at it, so a party may be edited or deleted freely
 * afterwards without disturbing a fight already under way.
 *
 * Mirrors `ceres.rounds.library.models.Party`.
 */
import { z } from 'zod';
import { actorIdSchema, partyIdSchema, UNSAVED, type PartyId } from './actor';
import { tagsSchema } from './tags';

export const partySchema = z.object({
  id: partyIdSchema.default(UNSAVED as PartyId),
  name: z.string().default(''),
  note: z.string().default(''),
  tags: tagsSchema,
  /**
   * Members, in the order they were added. Held as references, so an actor
   * deleted from the library leaves a hole here rather than an error — the
   * same bargain as ON DELETE SET NULL. Nothing prunes them: a party that
   * looks short is telling you something true.
   */
  actors: z.array(actorIdSchema).default([]),
});

export type Party = z.infer<typeof partySchema>;

/** The JSON Schema CI validates proposed parties against. */
export function partyJSONSchema() {
  return z.toJSONSchema(partySchema);
}
