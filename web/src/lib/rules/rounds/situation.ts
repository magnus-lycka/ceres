/**
 * A situation: who is in the fight, in what order they act, and how far the
 * round has got.
 *
 * Plain functions over plain data, like the rest of `$lib/rules`. Nothing here
 * imports Svelte or touches the DOM, and nothing here stores anything — the
 * page holds the situation and hands it back for each change.
 *
 * Two things this module deliberately does not hold. Initiative belongs to the
 * situation and to nothing else: it is rolled for this fight and has no meaning
 * outside it, so it lives on the membership row rather than on the Actor. And
 * the party is a **name copied onto the row**, not a reference — importing a
 * party forgets its origin, so editing either afterwards leaves the other
 * alone.
 *
 * See `docs/plan-rounds.md`, "Actors, Parties and Situation membership".
 */
import type { Actor, ActorId } from '$lib/schema/actor';
import { situationSchema, type Member, type Situation } from '$lib/schema/situation';

export type { Member, Situation };

/** Whether an actor may act now, has yet to be reached, or is finished. */
export type MemberState = 'pending' | 'ready' | 'acted';

/**
 * A fight with nobody in it yet.
 *
 * Built from the schema's own defaults rather than written out again here, so
 * there is one answer to what an empty situation is.
 */
export function emptySituation(): Situation {
  return situationSchema.parse({});
}

/**
 * Seat actors, on a side or on none.
 *
 * Membership is built up rather than created once: a fight has at least two
 * sides, and individuals are dropped in as well — a bystander, a guard who
 * wanders in. Bringing in a party copies its members as they are *now* and
 * forgets the party, so editing either afterwards leaves the other alone.
 *
 * An actor already seated is left exactly as they are. Within one situation an
 * actor has at most one membership row: two parties may both list the same
 * person, and one actor is one row that gets hurt once. Leaving the existing
 * row alone also means a latecomer never disturbs a fight in progress.
 *
 * Newcomers arrive with no initiative and a turn unspent, whatever round it
 * is — reinforcements have not rolled yet and have not acted.
 *
 * `engaged` is who is already committed to another *current* situation, from
 * `lifecycle.engagedElsewhere`. It is only consulted when this situation is
 * itself current; see the note below.
 */
export function addActors(
  situation: Situation,
  actors: readonly Actor[],
  party: string,
  engaged: ReadonlySet<ActorId> = new Set(),
): Situation {
  const seated = new Set(situation.members.map((member) => member.actor));
  // An actor may be in at most one *current* situation, so reinforcements
  // already fighting elsewhere are turned away. A plan may include them
  // freely — it commits nobody, and the rule bites again when it starts.
  const busy = situation.state === 'current' ? engaged : new Set<ActorId>();
  const arriving = actors.filter((actor) => !seated.has(actor.id) && !busy.has(actor.id));
  return {
    ...situation,
    members: [
      ...situation.members,
      ...arriving.map((actor) => ({
        actor: actor.id,
        party,
        initiative: null,
        acted: false,
        waiting: false,
      })),
    ],
  };
}

function update(
  situation: Situation,
  matches: (member: Member) => boolean,
  change: (member: Member) => Member,
): Situation {
  return {
    ...situation,
    members: situation.members.map((member) => (matches(member) ? change(member) : member)),
  };
}

/**
 * Take an actor out of the fight.
 *
 * The other half of `addActors`: a fight is not a fixed cast, and someone may
 * withdraw, be removed from a plan that changed, or have been added by
 * mistake. Only the membership row goes — the Actor and its injuries are
 * untouched, because what happened to it happened.
 */
export function removeActor(situation: Situation, actor: ActorId): Situation {
  return {
    ...situation,
    members: situation.members.filter((member) => member.actor !== actor),
  };
}

/** Move one row to another side, or to none. */
export function setParty(situation: Situation, actor: ActorId, party: string): Situation {
  return update(
    situation,
    (member) => member.actor === actor,
    (member) => ({ ...member, party }),
  );
}

/** Type the initiative for one row. */
export function setInitiative(situation: Situation, actor: ActorId, initiative: number | null): Situation {
  return update(
    situation,
    (member) => member.actor === actor,
    (member) => ({ ...member, initiative }),
  );
}

/**
 * Type one initiative for a whole side.
 *
 * An input convenience rather than a shared object: the value is written into
 * every row carrying the name, and each row may be edited on its own after.
 */
export function setPartyInitiative(
  situation: Situation,
  party: string,
  initiative: number | null,
): Situation {
  return update(
    situation,
    (member) => member.party === party,
    (member) => ({ ...member, initiative }),
  );
}

/** Finish an actor's turn. */
export function act(situation: Situation, actor: ActorId): Situation {
  return update(
    situation,
    (member) => member.actor === actor,
    (member) => ({ ...member, acted: true }),
  );
}

/** Let the turn pass without spending it, so the actor may act later. */
export function delay(situation: Situation, actor: ActorId): Situation {
  return update(
    situation,
    (member) => member.actor === actor,
    (member) => ({ ...member, waiting: true }),
  );
}

/** Everyone gets their turn back; the typed initiative stays (RAW: fixed). */
export function newRound(situation: Situation): Situation {
  return {
    ...situation,
    round: situation.round + 1,
    members: situation.members.map((member) => ({ ...member, acted: false, waiting: false })),
  };
}

/**
 * The order actors act in: highest initiative first, ties broken by the higher
 * DEX. Those two are the rule.
 *
 * Past that the rule says the actors act simultaneously, so any further order
 * is presentation rather than precedence — but it still has to be *settled*.
 * Left to chance, a table whose initiative has not been typed in yet appears to
 * shuffle every time it is redrawn, which reads as a bug. Party then name keeps
 * sides together and each side alphabetical.
 *
 * A row with no initiative typed in yet sorts to the end rather than to zero:
 * "not entered" and "rolled nothing" are different facts.
 */
export function turnOrder(situation: Situation, roster: readonly Actor[]): Member[] {
  const actorFor = (member: Member) => roster.find((actor) => actor.id === member.actor);
  const dexterity = (member: Member) => actorFor(member)?.dexterity ?? 0;
  const name = (member: Member) => actorFor(member)?.name ?? '';
  const rank = (member: Member) => member.initiative ?? Number.NEGATIVE_INFINITY;
  return [...situation.members].sort(
    (a, b) =>
      rank(b) - rank(a) ||
      dexterity(b) - dexterity(a) ||
      a.party.localeCompare(b.party) ||
      name(a).localeCompare(name(b)),
  );
}

/**
 * The initiative the turn has reached, or null once the round is over.
 *
 * The turn passes down the steps, leaving one behind when every actor on it
 * has either acted or chosen to wait. Waiting is what lets the turn move past
 * an actor who is still able to act.
 */
function currentStep(situation: Situation, roster: readonly Actor[]): Member | null {
  return turnOrder(situation, roster).find((member) => !member.acted && !member.waiting) ?? null;
}

/**
 * Whether one actor may act now.
 *
 * Ready covers both the actors the turn has reached and those who let it pass
 * and are still owed one — which is why this asks about initiative rather than
 * about position in the order.
 */
export function memberState(situation: Situation, member: Member, roster: readonly Actor[]): MemberState {
  if (member.acted) return 'acted';
  const step = currentStep(situation, roster);
  if (step === null) return 'ready';
  if (member.waiting) return 'ready';
  return member === step || sameStep(member, step, roster) ? 'ready' : 'pending';
}

/** Two rows share a step when neither initiative nor DEX separates them. */
function sameStep(member: Member, step: Member, roster: readonly Actor[]): boolean {
  const dexterity = (of: Member) => roster.find((actor) => actor.id === of.actor)?.dexterity ?? 0;
  return member.initiative === step.initiative && dexterity(member) === dexterity(step);
}

/** True once no one is still owed a turn. */
export function roundComplete(situation: Situation): boolean {
  return situation.members.every((member) => member.acted || member.waiting);
}
