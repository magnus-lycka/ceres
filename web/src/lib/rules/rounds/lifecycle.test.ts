/**
 * A situation's life: planned, current, past.
 *
 *     [New] → planned → (Start) → current → (End) → past
 *              ↓ Delete                              ↓ Delete
 *
 * The rule these assertions exist for is the one that is not obvious from the
 * diagram: **an actor may be in at most one *current* situation.** Planning is
 * free — the same actor may appear in any number of planned fights, because a
 * plan is not a commitment — and the constraint bites when a fight actually
 * starts, and again when someone is added to one already running.
 *
 * Un-starting and un-ending are deliberately not modelled.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import { situationId, type Situation } from '$lib/schema/situation';
import { act, addActors, emptySituation, setInitiative } from './situation';
import { beginRound, end, engagedElsewhere, newSituation, nextRound, start } from './lifecycle';

function actor(id: number, name: string): Actor {
  return {
    id: actorId(id),
    name,
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
  };
}

const rin = actor(1, 'Rin');
const sana = actor(2, 'Sana');
const bo = actor(3, 'Bo');

/** A planned situation with an id, as the store would have given it. */
function planned(id: number, ...actors: Actor[]): Situation {
  return {
    ...addActors(emptySituation(), actors, 'Raiders'),
    id: situationId(id),
    name: `Fight ${id}`,
    note: '',
    state: 'planned',
  };
}

const running = (id: number, ...actors: Actor[]): Situation => ({
  ...planned(id, ...actors),
  state: 'current',
});

describe('a new situation', () => {
  it('starts out planned, so nothing is under way by accident', () => {
    expect(newSituation('Ambush').state).toBe('planned');
  });

  it('is named, empty and at round one', () => {
    const fresh = newSituation('Ambush');
    expect(fresh.name).toBe('Ambush');
    expect(fresh.members).toEqual([]);
    expect(fresh.round).toBe(1);
  });
});

describe('starting a situation', () => {
  it('makes a planned situation current', () => {
    const result = start(planned(1, rin), []);
    expect(result.ok && result.situation.state).toBe('current');
  });

  it('leaves the members and the round alone', () => {
    const result = start(planned(1, rin, sana), []);
    expect(result.ok && result.situation.members).toHaveLength(2);
    expect(result.ok && result.situation.round).toBe(1);
  });

  /**
   * The invariant. One actor cannot be swinging a sword in two fights at once,
   * so a plan that overlaps a fight already happening cannot start.
   */
  it('refuses when one of its actors is already fighting', () => {
    const result = start(planned(2, sana, bo), [running(1, rin, sana)]);
    expect(result.ok).toBe(false);
    expect(!result.ok && result.blocked).toEqual([sana.id]);
  });

  it('names every actor that blocks it, not just the first', () => {
    const result = start(planned(2, rin, sana), [running(1, rin, sana)]);
    expect(!result.ok && result.blocked).toEqual([rin.id, sana.id]);
  });

  // Planning is free: the constraint is about fights happening, not intentions.
  it('ignores an actor who is only in another *plan*', () => {
    expect(start(planned(2, rin), [planned(1, rin)]).ok).toBe(true);
  });

  it('ignores an actor whose other fight is already over', () => {
    const over = { ...running(1, rin), state: 'past' as const };
    expect(start(planned(2, rin), [over]).ok).toBe(true);
  });

  // Concurrent fights are rare but allowed, so long as nobody is in both.
  it('allows a second fight between different actors', () => {
    expect(start(planned(2, bo), [running(1, rin, sana)]).ok).toBe(true);
  });

  it('does not count the situation against itself', () => {
    const already = running(1, rin);
    expect(start({ ...already, state: 'planned' }, [already]).ok).toBe(true);
  });
});

describe('ending a situation', () => {
  it('makes a current situation past', () => {
    expect(end(running(1, rin)).state).toBe('past');
  });

  it('keeps who was in it and how far it got', () => {
    const over = end({ ...running(1, rin, sana), round: 4 });
    expect(over.members).toHaveLength(2);
    expect(over.round).toBe(4);
  });
});

describe('who is already committed', () => {
  it('lists the actors in every other current situation', () => {
    const engaged = engagedElsewhere([running(1, rin, sana), planned(2, bo)], situationId(3));
    expect([...engaged]).toEqual([rin.id, sana.id]);
  });

  /**
   * Adding to a fight already running is the invariant's other enforcement
   * point: reinforcements are welcome, but not ones already fighting elsewhere.
   */
  it('keeps an actor already fighting out of another current situation', () => {
    const here = running(2, bo);
    const engaged = engagedElsewhere([running(1, rin), here], here.id);
    const tried = addActors(here, [rin, sana], 'Guards', engaged);
    expect(tried.members.map((member) => member.actor)).toEqual([bo.id, sana.id]);
  });

  // A plan may freely include someone who is busy right now; they simply
  // cannot start until that fight ends.
  it('lets a plan include an actor who is fighting elsewhere', () => {
    const here = planned(2, bo);
    const engaged = engagedElsewhere([running(1, rin), here], here.id);
    const tried = addActors(here, [rin], 'Guards', engaged);
    expect(tried.members.map((member) => member.actor)).toEqual([bo.id, rin.id]);
  });
});

/**
 * Inside `current`, a fight alternates between deciding initiative and working
 * through the turn order:
 *
 *     before round 1 → in round 1 → before round 2 → in round 2 → …
 *
 * The two are different jobs, and which one you are in decides what may be
 * changed — initiative is typed before a round and settled inside it.
 */
describe('the rounds of a running situation', () => {
  it('starts before round one rather than inside it', () => {
    const result = start(planned(1, rin), []);
    expect(result.ok && result.situation.phase).toBe('setup');
    expect(result.ok && result.situation.round).toBe(1);
  });

  it('goes into the round when the referee begins it', () => {
    expect(beginRound(running(1, rin)).phase).toBe('round');
  });

  it('comes back out to set up the next one', () => {
    const playing = beginRound({ ...running(1, rin), round: 1 });
    const between = nextRound(playing);
    expect(between.phase).toBe('setup');
    expect(between.round).toBe(2);
  });

  // Leaving a round is what gives everyone their turn back — the setup for the
  // next round is where a fresh turn is waiting to be spent.
  it('gives everyone their turn back on the way out of a round', () => {
    const spent = act(beginRound(running(1, rin)), rin.id);
    expect(nextRound(spent).members.every((member) => !member.acted && !member.waiting)).toBe(true);
  });

  it('keeps the initiative typed in before the round', () => {
    const ready = setInitiative(beginRound(running(1, rin)), rin.id, 9);
    expect(nextRound(ready).members[0].initiative).toBe(9);
  });
});
