/**
 * What an Actor is, defined once.
 *
 * This one definition produces the TypeScript types the app is written
 * against, the runtime validation an import runs through, and — via
 * `toJSONSchema` — the schema the GitHub Action checks inbox bundles with. A
 * second definition anywhere else is a drift bug waiting to happen.
 *
 * Mirrors `ceres.rounds.library.models`. Kept deliberately close to it: an
 * actor is one individual, five identical dogs are five actors, and the fields
 * that vary are the ones that decide how it absorbs damage.
 */
import { z } from 'zod';

/** Allocated by the service. Zero means "not saved yet"; ids start at 1. */
export const UNSAVED = 0;

export const actorKinds = ['sophont', 'animal', 'robot'] as const;
export type ActorKind = (typeof actorKinds)[number];

/** Which stat an injury took points off. Hits for animals and robots. */
export const stats = ['strength', 'dexterity', 'endurance', 'hits'] as const;
export type Stat = (typeof stats)[number];

/**
 * One hit, stored as the reduction it caused rather than as what was rolled.
 *
 * `when` is the round of the situation it landed in, or null once that
 * situation has ended — injuries carried out of a fight are past the
 * one-minute first-aid window, so their round has no further use. An actor
 * edited in the library carries only `null` entries: there is no round here.
 */
export const injurySchema = z.object({
  when: z.number().int().nullable().default(null),
  kind: z.enum(['lethal', 'stun']),
  reductions: z.partialRecord(z.enum(stats), z.number().int().nonnegative()).default({}),
});
export type Injury = z.infer<typeof injurySchema>;

const base = z.object({
  id: z.number().int().nonnegative().default(UNSAVED),
  name: z.string().min(1),
  kind: z.enum(actorKinds),
  note: z.string().default(''),
  tags: z.array(z.string()).default([]),
  strength: z.number().int().nullable().default(null),
  dexterity: z.number().int().nullable().default(null),
  endurance: z.number().int().nullable().default(null),
  hits: z.number().int().nullable().default(null),
  /** Persistent health: what has been done to this actor, oldest first. */
  injuries: z.array(injurySchema).default([]),
});

const characteristics = ['strength', 'dexterity', 'endurance'] as const;

/**
 * A sophont is hurt through STR/DEX/END; anything else through Hits. The
 * check is the same rule the Python model enforces, so a bundle validated by
 * CI is a bundle the application will also accept.
 */
export const actorSchema = base.superRefine((actor, ctx) => {
  const missing = characteristics.filter((field) => actor[field] === null);
  const wantsCharacteristics = actor.kind === 'sophont';

  if (wantsCharacteristics && missing.length > 0) {
    ctx.addIssue({ code: 'custom', message: `a ${actor.kind} needs ${missing.join(', ')}` });
  }
  if (!wantsCharacteristics && missing.length < characteristics.length) {
    ctx.addIssue({ code: 'custom', message: `a ${actor.kind} has no characteristics, only hits` });
  }
  if (!wantsCharacteristics && actor.hits === null) {
    ctx.addIssue({ code: 'custom', message: `a ${actor.kind} needs hits` });
  }
});

export type Actor = z.infer<typeof actorSchema>;

/** The JSON Schema CI validates proposed bundles against. */
export function actorJSONSchema() {
  return z.toJSONSchema(base);
}
