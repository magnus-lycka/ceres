/**
 * What a Situation is, defined once.
 *
 * One fight, or any other round-by-round stretch of intense action, in one of
 * three states. A situation is planned, then run, then kept:
 *
 *     [New] → planned → (Start) → current → (End) → past
 *              ↓ Delete                              ↓ Delete
 *
 * The three are the same object at different times rather than three kinds of
 * thing. What changes with the state is what may be done to it: a planned
 * situation is a guest list, a current one is the fight actually happening, and
 * a past one is a record — kept because it may be of interest, and read-only
 * because rewriting history is not a thing the table needs.
 *
 * Initiative and rounds only mean something once the fight is happening, so
 * they are typed while current. Planning is for deciding who is in it.
 *
 * A situation holds members by `ActorId` and party by *name*: it copies a Party
 * rather than pointing at one, so a party may be edited or deleted afterwards
 * without disturbing a fight. See `docs/plan-rounds.md`.
 */
import { z } from 'zod';
import { actorIdSchema, UNSAVED } from './actor';

const id = z.number().int().nonnegative();
export const situationIdSchema = id.brand<'SituationId'>();
export type SituationId = z.infer<typeof situationIdSchema>;

/** Integers arrive from JSON; this is where they become ids. */
export const situationId = (value: number) => situationIdSchema.parse(value);

/**
 * Planned, current, past — in the order they happen.
 *
 * Named for what the situation *is* rather than for what may be done to it, so
 * that adding a rule about read-only-ness later changes one place.
 */
export const situationStates = ['planned', 'current', 'past'] as const;
export type SituationState = (typeof situationStates)[number];

/**
 * Where a running situation is between rounds, or inside one.
 *
 * A fight alternates: before round 1, in round 1, before round 2, in round 2.
 * The two halves are different jobs. Before a round you decide initiative —
 * individually or for a whole side — and who is in the fight. Inside one you
 * work down the turn order, and initiative is settled: what changes is who has
 * acted and who got hurt.
 *
 * The rules make this explicit. RAW keeps initiative fixed, so the before-phase
 * is a formality after round one; under Battlefield Dev each side rolls again
 * every round, and the before-phase is where that happens. A DEX loss that
 * lowers initiative is corrected there too.
 *
 * Meaningless while planned or past, both of which are handled by `state`.
 */
export const roundPhases = ['setup', 'round'] as const;
export type RoundPhase = (typeof roundPhases)[number];

/**
 * One actor's place in one fight.
 *
 * `acted` and `waiting` are the two ways a turn is used up. They are not one
 * three-valued field because they mean opposite things: an actor who has acted
 * is finished for the round, while one who is waiting has deliberately let the
 * turn pass and may still act.
 */
export const memberSchema = z.object({
  actor: actorIdSchema,
  /** A plain editable name. Rows may be reassigned, or left with no side. */
  party: z.string().default(''),
  /** The Effect of the referee's DEX or INT check. Null until typed in. */
  initiative: z.number().int().nullable().default(null),
  acted: z.boolean().default(false),
  waiting: z.boolean().default(false),
});

export type Member = z.infer<typeof memberSchema>;

export const situationSchema = z.object({
  id: situationIdSchema.default(UNSAVED as SituationId),
  name: z.string().default(''),
  note: z.string().default(''),
  state: z.enum(situationStates).default('planned'),
  /** Between rounds, or inside one. Only meaningful while current. */
  phase: z.enum(roundPhases).default('setup'),
  /**
   * Rounds elapsed. Meaningful only once the fight is happening; a planned
   * situation sits at one because that is where it will start, not because a
   * round has passed.
   */
  round: z.number().int().positive().default(1),
  members: z.array(memberSchema).default([]),
});

export type Situation = z.infer<typeof situationSchema>;

/** The JSON Schema CI validates proposed situations against. */
export function situationJSONSchema() {
  return z.toJSONSchema(situationSchema);
}
