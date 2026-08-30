/**
 * How a situation moves between planned, current and past.
 *
 *     [New] → planned → (Start) → current → (End) → past
 *              ↓ Delete                              ↓ Delete
 *
 * Separate from `situation.ts`, which is about running one round after another
 * inside a fight. This is about the fight's place in a life that outlasts it:
 * which stage it is at, and the one rule that spans several situations at once.
 *
 * **An actor may be in at most one current situation.** Planning is free — a
 * plan is not a commitment, and the same actor may appear in any number of
 * planned fights — so the rule bites at exactly two moments: when a plan starts,
 * and when someone is added to a fight already running.
 *
 * Un-starting and un-ending are deliberately not here. A situation that went
 * the wrong way is corrected by the referee, not by a reverse transition.
 */
import type { ActorId } from '$lib/schema/actor';
import { UNSAVED } from '$lib/schema/actor';
import type { Situation, SituationId } from '$lib/schema/situation';
import { newRound } from './situation';

/** A fight that has not happened yet, with nobody in it. */
export function newSituation(name: string): Situation {
  return {
    id: UNSAVED as SituationId,
    name,
    note: '',
    state: 'planned',
    phase: 'setup',
    round: 1,
    members: [],
  };
}

/**
 * Every actor committed to a fight that is happening right now, other than
 * this one.
 *
 * The single expression of the invariant, used at both points that enforce it:
 * `start` below, and `addActors` when the situation being added to is current.
 */
export function engagedElsewhere(
  situations: readonly Situation[],
  except: SituationId,
): ReadonlySet<ActorId> {
  return new Set(
    situations
      .filter((situation) => situation.state === 'current' && situation.id !== except)
      .flatMap((situation) => situation.members.map((member) => member.actor)),
  );
}

/**
 * The answer to Start: the situation now running, or who stopped it.
 *
 * A result rather than a thrown error, because the interesting case is not
 * exceptional — it is a plan that has aged badly, and the referee needs to be
 * told *which* actors are busy so they can decide what to do about it.
 */
export type StartResult = { ok: true; situation: Situation } | { ok: false; blocked: ActorId[] };

/** Begin the fight, unless one of its actors is already in another. */
export function start(situation: Situation, situations: readonly Situation[]): StartResult {
  const engaged = engagedElsewhere(situations, situation.id);
  const blocked = situation.members.map((member) => member.actor).filter((actor) => engaged.has(actor));
  if (blocked.length > 0) return { ok: false, blocked };
  // A fight opens *before* its first round: initiative is decided, then the
  // round is played. Dropping straight into round one would skip the only
  // moment the referee is meant to type initiative.
  return { ok: true, situation: { ...situation, state: 'current', phase: 'setup' } };
}

/** Work through the turn order for the round now set up. */
export function beginRound(situation: Situation): Situation {
  return { ...situation, phase: 'round' };
}

/**
 * Leave the round and set up the next one.
 *
 * Coming out of a round is what gives everyone their turn back, because the
 * setup that follows is the setup *for* that fresh turn. Initiative survives:
 * RAW keeps it for the whole fight, and the setup phase is where it would be
 * changed if a house rule or a DEX loss called for it.
 */
export function nextRound(situation: Situation): Situation {
  return { ...newRound(situation), phase: 'setup' };
}

/**
 * Finish the fight.
 *
 * Nothing is discarded: who was in it and how far it got are what makes a past
 * situation worth keeping. What changes is that it becomes read-only.
 */
export function end(situation: Situation): Situation {
  return { ...situation, state: 'past' };
}
