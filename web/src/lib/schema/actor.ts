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
import { tagsSchema } from './tags';

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

/**
 * The Speed Band ladder, lowest first. A band is stored as its position here,
 * which is the Speed Band Number the rules use: Slow is 3. Mirrors
 * `ceres.make.vehicle.speed.SpeedBand`.
 */
export const speedBands = [
  'Stopped',
  'Idle',
  'Very Slow',
  'Slow',
  'Medium',
  'High',
  'Fast',
  'Very Fast',
  'Subsonic',
  'Supersonic',
  'Hypersonic',
  'Orbital',
] as const;

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
/** What a critical can take something off. */
export const robotAttributes = ['protection', 'movement', 'speed', 'enduranceHours', 'int'] as const;
export type RobotAttribute = (typeof robotAttributes)[number];

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
  /**
   * What this location's criticals took off the robot: Protection, Movement,
   * Speed, Endurance hours, INT. Current values are the base less the sum over
   * every location, so nothing is replayed to answer a question, and repairing a
   * location gives back exactly what it took. A halving is stored as the amount
   * that went, since what it comes to depends on what was left.
   */
  taken: z.partialRecord(z.enum(robotAttributes), z.number().nonnegative()).default({}),
});
export type Critical = z.infer<typeof criticalSchema>;
export const WORST_SEVERITY = 6;

/**
 * What an actor *is*, as opposed to what has happened to it.
 *
 * Named and shared because two schemas need exactly these fields: the stored
 * `actorSchema`, which adds an id and the injury history, and the strict
 * `importActorSchema`, which adds nothing. Writing them twice would let a
 * proposal and a stored actor drift apart one field at a time.
 */
export const actorDefinition = {
  /**
   * Empty until it is typed. An actor is added to the roster and named in the
   * grid afterwards, so the unnamed moment is a normal state to be stored, not
   * an error — requiring a name here meant Add wrote a row that could never be
   * read back.
   */
  name: z.string().default(''),
  kind: z.enum(actorKinds),
  note: z.string().default(''),
  tags: tagsSchema,
  strength: z.number().int().nullable().default(null),
  dexterity: z.number().int().nullable().default(null),
  endurance: z.number().int().nullable().default(null),
  hits: z.number().int().nullable().default(null),
  /**
   * What is taken off each hit before it lands. Every kind has it: sophonts
   * wear armour and animals have the Armour trait. Zero is unarmoured, not
   * unknown.
   */
  protection: z.number().int().nonnegative().default(0),
  /**
   * How far it moves on foot in one Minor Action, in metres. Fractional on
   * purpose: prone quarters it, and 6 m becomes 1.5. Null is unset, not zero.
   */
  movement: z.number().nonnegative().nullable().default(null),
  /**
   * Its Speed Band, as the Speed Band Number the rules use. A different
   * quantity from Movement: a robot with vehicle speed movement has both.
   */
  speed: z
    .number()
    .int()
    .min(0)
    .max(speedBands.length - 1)
    .nullable()
    .default(null),
  /**
   * A robot's Endurance: hours of operation. Not the sophont's END, which is
   * the `endurance` above and is eroded by injury; this is only ever halved
   * by a Power critical, so it may come out fractional (12.5 hours).
   */
  enduranceHours: z.number().nonnegative().nullable().default(null),
  /** A robot's INT, as a system attribute a Brain critical reduces. */
  int: z.number().int().nonnegative().nullable().default(null),
};

const base = z.object({
  id: actorIdSchema.default(UNSAVED as ActorId),
  ...actorDefinition,
  /** Optional origin; duplicated actors deliberately omit it. */
  character: z.object({ url: z.url() }).optional(),
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

/** The shape the kind rule needs, whether or not the schema stores damage. */
type KindChecked = {
  kind: ActorKind;
  strength: number | null;
  dexterity: number | null;
  endurance: number | null;
  hits: number | null;
  enduranceHours: number | null;
  int: number | null;
  injuries?: Injury[];
  criticals?: Partial<Record<CriticalLocation, Critical>>;
};

/**
 * A sophont is hurt through STR/DEX/END; anything else through Hits, and only
 * a robot has hours of endurance and an INT to lose. The check is applied to
 * both the stored and the proposal schema, so a bundle validated by CI is a
 * bundle the application will also accept. (`ceres.rounds.library.models`
 * predates the attributes and does not check them: see docs/plan-rounds.md.)
 *
 * Named and applied to both schemas rather than written inline, because a
 * proposal that CI accepted and the application then refused would be the
 * worst possible outcome for an author with no way to run either.
 */
export function checkKind(actor: KindChecked, ctx: z.RefinementCtx): void {
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
  if (actor.kind === 'robot' && actor.injuries?.some((injury) => injury.kind === 'stun')) {
    ctx.addIssue({
      code: 'custom',
      message: 'a robot cannot retain stun damage; an electromagnetic stunner causes physical Hits',
    });
  }
  if (actor.kind !== 'robot' && (actor.enduranceHours !== null || actor.int !== null)) {
    ctx.addIssue({
      code: 'custom',
      message: `a ${actor.kind} has no hours of endurance or INT; those are a robot's systems`,
    });
  }
  const criticals = Object.values(actor.criticals ?? {});
  if (actor.kind !== 'robot' && criticals.some((row) => row.severity > 0 || row.note)) {
    ctx.addIssue({ code: 'custom', message: `a ${actor.kind} has no systems to take a critical` });
  }
}

export const actorSchema = base.superRefine(checkKind);

/**
 * An actor as a proposal may describe one.
 *
 * Strict on purpose. An ordinary Zod object *strips* unknown keys, which would
 * turn `strenght: 9` into a sophont with no STR and no complaint; rejecting is
 * the only way an author with no application gets told about a typo. It is
 * built from `actorDefinition` rather than by `omit()`ing the stored schema,
 * because `omit()` on a refined schema drops the refinement with it.
 *
 * Ids, injuries and criticals are absent rather than optional: they are the
 * application's to allocate and the fight's to record, and a proposal that
 * could name an id could overwrite an actor that already exists.
 */
export const importActorSchema = z.strictObject(actorDefinition).superRefine(checkKind);

/** An actor as proposed: no id, no history. */
export type ImportActor = z.infer<typeof importActorSchema>;

export type Actor = z.infer<typeof actorSchema>;

/**
 * The JSON Schema CI validates proposed bundles against.
 *
 * The input side, because tags accept either a list or a string and the
 * conversion between them is a transform, which JSON Schema cannot express.
 * Input is also the right side to publish: it describes what a producer may
 * send, not what we store afterwards.
 */
export function actorJSONSchema() {
  return z.toJSONSchema(base, { io: 'input' });
}
