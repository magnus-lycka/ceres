/**
 * The import contract: what an author may propose, and what installing it
 * recorded.
 *
 * A proposal arrives from outside the application — an assistant, a
 * collaborator, anyone who can open an issue on the data repository — and its
 * author has neither the app nor its token. So this schema is a boundary, not
 * a convenience: it is deliberately **not** the persistence schema with the
 * awkward parts made optional, because that would turn every stored field into
 * an import interface by accident.
 *
 * What that buys is a proposal which cannot name an id and overwrite something
 * that already exists, cannot smuggle in injuries from a fight it was never
 * in, and cannot lose a misspelled field in silence.
 *
 * See `docs/plan-library-import.md`.
 */
import { z } from 'zod';
import { actorIdSchema, importActorSchema, partyIdSchema } from './actor';
import { tagsSchema } from './tags';

/**
 * One party and the actors in it, with no ids anywhere.
 *
 * Strict at both levels. The actor array is the party's member order, so it is
 * data rather than presentation, and an empty one is refused: a bundle exists
 * to create a party with somebody in it.
 *
 * `name` is required rather than defaulted — a party nobody named cannot be
 * found again in the library, and its absence is far more likely to be a
 * mistake than an intention.
 */
export const libraryBundleSchema = z.strictObject({
  name: z.string(),
  tags: tagsSchema,
  note: z.string().default(''),
  actors: z.array(importActorSchema).min(1),
});

export type LibraryBundle = z.infer<typeof libraryBundleSchema>;

/**
 * What installing a bundle allocated.
 *
 * The receipt is written *before* the entities, and is what makes installation
 * resumable: a crash halfway leaves ids already recorded, so the retry
 * finishes the same installation rather than creating a second set of actors.
 * A completed receipt also answers the question an author will eventually ask
 * — which actors did my issue actually create?
 *
 * Kept after installation. Its other job is to stop a re-appearing inbox file
 * from being installed twice.
 */
export const importReceiptSchema = z.object({
  schemaVersion: z.literal(1),
  /** The inbox entry this receipt is for, e.g. `issue-123`. */
  bundle: z.string(),
  issue: z.number().int().positive(),
  /** `installing` until every entity is written; `complete` afterwards. */
  status: z.enum(['installing', 'complete']),
  /** The actor ids allocated, in the bundle's own order. */
  actors: z.array(actorIdSchema),
  party: partyIdSchema,
});

export type ImportReceipt = z.infer<typeof importReceiptSchema>;

/** The JSON Schema published for assistants and editor tooling. */
export function libraryBundleJSONSchema() {
  return z.toJSONSchema(libraryBundleSchema, { io: 'input' });
}
