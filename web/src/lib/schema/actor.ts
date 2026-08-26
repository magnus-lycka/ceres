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

/**
 * Typed references to stored entities.
 *
 * Integers in JSON, distinct types here, so a `PartyId` can never be passed
 * where an `ActorId` belongs — which is exactly the mistake available now that
 * a party holds a list of actor ids. Mirrors `ceres.rounds.library.ids`.
 *
 * A reference may be stale: what it points at can be deleted at any time, and
 * every reader has to cope with resolving to nothing.
 */
const id = z.number().int().nonnegative();
export const actorIdSchema = id.brand<'ActorId'>();
export const partyIdSchema = id.brand<'PartyId'>();
export type ActorId = z.infer<typeof actorIdSchema>;
export type PartyId = z.infer<typeof partyIdSchema>;

/** Integers arrive from JSON and from the grid; this is where they become ids. */
export const actorId = (value: number) => actorIdSchema.parse(value);
export const partyId = (value: number) => partyIdSchema.parse(value);

/**
 * The id of an entity the store has not seen yet.
 *
 * Allocated ids start at 1, so this is unambiguous, and it keeps `id` a plain
 * id everywhere rather than an optional one every caller has to narrow.
 */
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

/**
 * Where a robot critical landed, in the order the 2D location table rolls
 * them (handouts/robot_combat_cards.typ, Card 2).
 */
export const criticalLocations = [
  'power',
  'weapon',
  'armour',
  'chassis',
  'locomotion',
  'options',
  'brain',
] as const;
export type CriticalLocation = (typeof criticalLocations)[number];

/**
 * How badly one location is damaged: 0 for undamaged, up to 6.
 *
 * Severity comes from the attack's Effect (Effect − 5) or from a
 * sustained-damage threshold (always 1). The note is the "Component / effect"
 * column of the card's combat record — which weapon was hit, what the severity
 * row said to reduce. Ceres does not encode the effects table, so the note is
 * where its answer is kept.
 */
export const criticalSchema = z.object({
  severity: z.number().int().min(0).max(6).default(0),
  note: z.string().default(''),
});
export type Critical = z.infer<typeof criticalSchema>;
export const WORST_SEVERITY = 6;

const base = z.object({
  id: actorIdSchema.default(UNSAVED as ActorId),
  /**
   * Empty until it is typed. An actor is added to the roster and named in the
   * grid afterwards, so the unnamed moment is a normal state to be stored, not
   * an error — requiring a name here meant Add wrote a row that could never be
   * read back.
   */
  name: z.string().default(''),
  kind: z.enum(actorKinds),
  note: z.string().default(''),
  tags: z.array(z.string()).default([]),
  strength: z.number().int().nullable().default(null),
  dexterity: z.number().int().nullable().default(null),
  endurance: z.number().int().nullable().default(null),
  hits: z.number().int().nullable().default(null),
  /** Persistent health: what has been done to this actor, oldest first. */
  injuries: z.array(injurySchema).default([]),
  /**
   * Robot system damage, as the card's combat record keeps it: the worst
   * severity each location has reached, and a note.
   *
   * One entry per location is the whole of it. Severity only ever climbs
   * (`max(rolled, old + 1)`), so a location has no history worth keeping.
   * Undamaged locations are simply absent; `criticalRows` presents all seven.
   */
  criticals: z.partialRecord(z.enum(criticalLocations), criticalSchema).default({}),
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
  if (actor.kind !== 'robot' && Object.values(actor.criticals).some((row) => row.severity > 0 || row.note)) {
    ctx.addIssue({ code: 'custom', message: `a ${actor.kind} has no systems to take a critical` });
  }
});

export type Actor = z.infer<typeof actorSchema>;

/** The JSON Schema CI validates proposed bundles against. */
export function actorJSONSchema() {
  return z.toJSONSchema(base);
}
