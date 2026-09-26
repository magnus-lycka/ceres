/**
 * Running a situation round by round.
 *
 * These assertions come from `docs/plan-rounds.md` ("The round and tracked
 * combat actions", "Initiative", "Round flow") and from `refs/core/03_combat.md`
 * as cited there — not from what the code happens to do.
 *
 * The rule being encoded: highest initiative acts first, ties break on DEX, and
 * a still-tied pair acts simultaneously. Within a round the turn passes down
 * the initiative steps; an actor who has acted is done for the round, and an
 * actor who delays keeps the right to act after the turn has moved past them.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import {
  act,
  addActors,
  attack,
  clearCondition,
  dive,
  delay,
  emptySituation,
  incapacitate,
  memberState,
  newRound,
  react,
  removeActor,
  roundComplete,
  setInitiative,
  setParty,
  setPartyInitiative,
  turnOrder,
  type Situation,
} from './situation';

function actor(id: number, name: string, dexterity = 8): Actor {
  return {
    id: actorId(id),
    name,
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
    protection: 0,
    movement: null,
    speed: null,
    enduranceHours: null,
    int: null,
  };
}

const rin = actor(1, 'Rin', 9);
const sana = actor(2, 'Sana', 7);
const bo = actor(3, 'Bo', 8);
const roster = [rin, sana, bo];

/** One party brought in, as the page does it. */
const raiders = (...actors: Actor[]) => addActors(emptySituation(), actors, 'Raiders');

/** A situation with initiative already typed in, as the referee would. */
function ready(...pairs: [Actor, number][]): Situation {
  return pairs.reduce(
    (situation, [who, initiative]) => setInitiative(situation, who.id, initiative),
    raiders(...pairs.map(([who]) => who)),
  );
}

const find = (situation: Situation, who: Actor) =>
  situation.members.find((member) => member.actor === who.id)!;

describe('building a situation', () => {
  it('starts empty, planned, in round one', () => {
    expect(emptySituation()).toMatchObject({ round: 1, members: [], state: 'planned' });
  });

  it('takes one row per actor', () => {
    expect(raiders(...roster).members.map((member) => member.actor)).toEqual([rin.id, sana.id, bo.id]);
  });

  // A Situation copies a party rather than pointing at it, so the party is a
  // plain editable name on the row and not a reference.
  it('writes the party name onto every row', () => {
    expect(raiders(...roster).members.every((member) => member.party === 'Raiders')).toBe(true);
  });

  it('brings each actor in with no initiative and a turn still to take', () => {
    const situation = raiders(...roster);
    expect(situation.members.every((member) => member.initiative === null)).toBe(true);
    expect(situation.members.every((member) => !member.acted && !member.waiting)).toBe(true);
  });
});

/**
 * A fight has at least two sides, and the referee also drops in individuals —
 * a bystander, a guard who wanders in. So membership is built up rather than
 * created once.
 */
describe('adding to a situation', () => {
  it('keeps the rows already there when another party arrives', () => {
    const both = addActors(raiders(rin, sana), [bo], 'Guards');
    expect(both.members.map((member) => member.actor)).toEqual([rin.id, sana.id, bo.id]);
  });

  it('gives each side its own name', () => {
    const both = addActors(raiders(rin, sana), [bo], 'Guards');
    expect(both.members.map((member) => member.party)).toEqual(['Raiders', 'Raiders', 'Guards']);
  });

  // An actor who belongs to no side — a bystander — is a row with no party.
  it('takes an actor with no party at all', () => {
    const situation = addActors(emptySituation(), [rin], '');
    expect(situation.members[0].party).toBe('');
  });

  /**
   * "Within one Situation an Actor has at most one membership row." Two
   * parties may both list the same actor, and adding the second must not seat
   * them twice — one actor is one row that gets hurt once.
   */
  it('refuses to seat the same actor twice', () => {
    const twice = addActors(raiders(rin, sana), [sana, bo], 'Guards');
    expect(twice.members.map((member) => member.actor)).toEqual([rin.id, sana.id, bo.id]);
  });

  it('leaves an actor already seated on the side they were seated with', () => {
    const twice = addActors(raiders(rin), [rin], 'Guards');
    expect(twice.members[0].party).toBe('Raiders');
  });

  // Reinforcements arrive mid-fight, and must not be able to act in a round
  // whose turn has already passed their step.
  it('brings a latecomer in with their turn still unspent', () => {
    const started = act(ready([rin, 12]), rin.id);
    const joined = addActors(started, [bo], 'Guards');
    expect(joined.members[1]).toMatchObject({ acted: false, waiting: false, initiative: null });
  });
});

describe('changing sides', () => {
  // The party is a plain editable name, so a row can be reassigned and a side
  // can be split by editing names.
  it('reassigns one row without touching the others', () => {
    const moved = setParty(raiders(rin, sana), sana.id, 'Guards');
    expect(moved.members.map((member) => member.party)).toEqual(['Raiders', 'Guards']);
  });
});

describe('turn order', () => {
  it('puts the highest initiative first', () => {
    const situation = ready([rin, 4], [sana, 12], [bo, 8]);
    expect(turnOrder(situation, roster).map((member) => member.actor)).toEqual([sana.id, bo.id, rin.id]);
  });

  // 03_combat.md:28-48 — ties break on the higher DEX.
  it('breaks a tie on the higher DEX', () => {
    const situation = ready([sana, 8], [rin, 8]);
    expect(turnOrder(situation, roster).map((member) => member.actor)).toEqual([rin.id, sana.id]);
  });

  // Still tied means the actors act simultaneously. Nothing invents an order
  // for them; they simply share a step.
  it('leaves an equal-DEX tie as one step rather than ordering it', () => {
    const twin = actor(4, 'Twin', 9);
    const situation = ready([rin, 8], [twin, 8]);
    const order = turnOrder(situation, [...roster, twin]);
    expect(order).toHaveLength(2);
    expect(order[0].initiative).toBe(order[1].initiative);
  });

  /**
   * Once the rules run out of tie-breaks the order still has to be stable and
   * readable, or rows appear to shuffle at random — which is what a table full
   * of not-yet-typed initiative looks like when DEX alone decides.
   */
  it('settles a remaining tie by party, then by name', () => {
    const ann = actor(5, 'Ann', 8);
    const zoe = actor(6, 'Zoe', 8);
    const cat = actor(7, 'Cat', 8);
    const everyone = [ann, zoe, cat];
    const situation = setPartyInitiative(
      setParty(addActors(emptySituation(), everyone, 'Raiders'), cat.id, 'Guards'),
      'Raiders',
      8,
    );
    const withGuards = setInitiative(situation, cat.id, 8);
    expect(turnOrder(withGuards, everyone).map((member) => member.actor)).toEqual([cat.id, ann.id, zoe.id]);
  });

  it('keeps rows with no initiative in a settled order rather than a shuffled one', () => {
    const zoe = actor(6, 'Zoe', 8);
    const ann = actor(5, 'Ann', 8);
    const everyone = [zoe, ann];
    const situation = addActors(emptySituation(), everyone, 'Raiders');
    expect(turnOrder(situation, everyone).map((member) => member.actor)).toEqual([ann.id, zoe.id]);
  });

  // Initiative is typed in by the referee, so a row may not have one yet.
  it('sorts a row with no initiative yet to the end', () => {
    const situation = ready([rin, 5], [sana, 0]);
    const waiting = setInitiative(situation, rin.id, null);
    expect(turnOrder(waiting, roster).map((member) => member.actor)).toEqual([sana.id, rin.id]);
  });
});

describe('shared initiative', () => {
  // 03_combat.md:36 — a side may share one initiative. That is an input
  // convenience: it writes the value into each matching row, after which any
  // row may be edited on its own.
  it('writes one value into every row of that party', () => {
    const split = setParty(raiders(...roster), bo.id, 'Guards');
    const set = setPartyInitiative(split, 'Raiders', 9);
    expect(set.members.map((member) => member.initiative)).toEqual([9, 9, null]);
  });

  it('leaves the shared value editable row by row afterwards', () => {
    const shared = setPartyInitiative(raiders(...roster), 'Raiders', 9);
    const tweaked = setInitiative(shared, sana.id, 3);
    expect(tweaked.members.map((member) => member.initiative)).toEqual([9, 3, 9]);
  });
});

describe('whose turn it is', () => {
  it('lets the highest initiative act while the rest wait their step', () => {
    const situation = ready([rin, 4], [sana, 12], [bo, 8]);
    expect(memberState(situation, find(situation, sana), roster)).toBe('ready');
    expect(memberState(situation, find(situation, bo), roster)).toBe('pending');
    expect(memberState(situation, find(situation, rin), roster)).toBe('pending');
  });

  it('passes the turn down a step once everyone on it has acted', () => {
    const situation = act(ready([rin, 4], [sana, 12], [bo, 8]), sana.id);
    expect(memberState(situation, find(situation, sana), roster)).toBe('acted');
    expect(memberState(situation, find(situation, bo), roster)).toBe('ready');
  });

  it('holds the turn until every actor on the step has acted', () => {
    const situation = act(ready([rin, 8], [sana, 8], [bo, 4]), rin.id);
    expect(memberState(situation, find(situation, sana), roster)).toBe('ready');
    expect(memberState(situation, find(situation, bo), roster)).toBe('pending');
  });

  /**
   * Delaying: an actor may act later in the turn (03_combat.md:32). The turn
   * moves past them and they stay able to act — which is the whole point, and
   * what distinguishes delaying from being done.
   */
  it('moves the turn past an actor who delays, leaving them able to act', () => {
    const situation = delay(ready([rin, 12], [sana, 8]), rin.id);
    expect(memberState(situation, find(situation, rin), roster)).toBe('ready');
    expect(memberState(situation, find(situation, sana), roster)).toBe('ready');
  });

  it('lets a delayed actor act after the step has passed them', () => {
    const situation = act(delay(ready([rin, 12], [sana, 8]), rin.id), rin.id);
    expect(memberState(situation, find(situation, rin), roster)).toBe('acted');
  });

  it('is over once everyone has acted or delayed', () => {
    const situation = ready([rin, 12], [sana, 8]);
    expect(roundComplete(situation, roster)).toBe(false);
    expect(roundComplete(act(delay(situation, rin.id), sana.id), roster)).toBe(true);
  });
});

/**
 * An attack is the one action the tracker records. It spends the turn, and it
 * remembers who was gone for: a hit, a miss and a dodge all leave the attacker
 * having attacked that person, and "who did they go for" is worth reading off
 * the table.
 */
describe('an attack', () => {
  it('spends the attacker turn and records who they went for', () => {
    const situation = attack(ready([rin, 12], [sana, 8]), rin.id, sana.id);

    expect(memberState(situation, find(situation, rin), roster)).toBe('acted');
    expect(find(situation, rin).target).toBe(sana.id);
    expect(find(situation, sana).target).toBeNull();
  });

  // Unlike the turn beside it, who they went for stays: the next attack starts
  // from the last target, and the referee changes it only when it changes.
  it('is remembered when the round turns, though the turn is not', () => {
    const after = newRound(attack(ready([rin, 12], [sana, 8]), rin.id, sana.id));

    expect(find(after, rin).target).toBe(sana.id);
    expect(memberState(after, find(after, rin), roster)).not.toBe('acted');
  });
});

/**
 * Whoever cannot act does not hold the table up. Stunned, unconscious, dead or
 * destroyed, they are out for the round, and the turn passes on without them.
 */
describe('who is out of action', () => {
  const round3 = () => ({ ...ready([rin, 12], [sana, 8], [bo, 4]), round: 3 });
  const felled = (who: Actor, reductions: Record<string, number>): Actor => ({
    ...who,
    injuries: [{ when: 1, kind: 'lethal', reductions }],
  });

  it('includes someone stunned, until the round they may act again', () => {
    const stunned = incapacitate(round3(), sana.id, 2);

    expect(memberState(stunned, find(stunned, sana), roster)).toBe('out');
    expect(memberState({ ...stunned, round: 4 }, find(stunned, sana), roster)).toBe('out');
    expect(memberState({ ...stunned, round: 5 }, find(stunned, sana), roster)).not.toBe('out');
  });

  it('includes someone unconscious, dead or destroyed', () => {
    const down = round3();
    const asleep = [rin, felled(sana, { strength: 8 }), bo];
    expect(memberState(down, find(down, sana), asleep)).toBe('out');

    const dead = [rin, felled(sana, { strength: 8, dexterity: 8, endurance: 8 }), bo];
    expect(memberState(down, find(down, sana), dead)).toBe('out');
  });

  // Hits has no "unconscious" at zero: a dead animal or a wrecked robot is out
  // for a different reason than someone who has fallen asleep.
  it('includes an animal at zero Hits and a robot that is wrecked', () => {
    const wolf: Actor = { ...bo, kind: 'animal', strength: null, dexterity: null, endurance: null, hits: 10 };
    const down = round3();

    const dead = { ...wolf, injuries: [{ when: 1, kind: 'lethal' as const, reductions: { hits: 10 } }] };
    expect(memberState(down, find(down, bo), [rin, sana, dead])).toBe('out');

    const wrecked = { ...dead, kind: 'robot' as const };
    expect(memberState(down, find(down, bo), [rin, sana, wrecked])).toBe('out');
  });

  it('lets the turn pass on without them', () => {
    const stunned = act(incapacitate(round3(), sana.id, 2), rin.id);

    // Rin has acted and Sana is out, so it is Bo's turn.
    expect(memberState(stunned, find(stunned, bo), roster)).toBe('ready');
  });

  it('does not keep the round open', () => {
    const stunned = incapacitate(round3(), sana.id, 2);
    const everyoneElse = act(act(stunned, rin.id), bo.id);

    expect(roundComplete(everyoneElse, roster)).toBe(true);
    expect(roundComplete(stunned, roster)).toBe(false);
  });
});

/**
 * Stun (:366) takes an actor out for a number of rounds. The count starts with
 * the round of the hit, but only if their turn in it is still to come: someone
 * who has already acted has nothing left in this round to lose, so their rounds
 * out are the ones after it (docs/RULE_INTERPRETATIONS.md, RIC-022).
 */
describe('being incapacitated', () => {
  const round3 = () => ({ ...ready([rin, 12], [sana, 8]), round: 3 });

  it('loses the current round too, for someone who has not acted yet', () => {
    const situation = incapacitate(round3(), sana.id, 2);

    // Out for rounds 3 and 4; able to act again in round 5.
    expect(find(situation, sana).incapacitatedUntil).toBe(5);
  });

  it('starts with the next round, for someone who has already acted', () => {
    const situation = incapacitate(act(round3(), sana.id), sana.id, 2);

    // Nothing left to lose in round 3; out for rounds 4 and 5.
    expect(find(situation, sana).incapacitatedUntil).toBe(6);
  });

  it('counts someone who is waiting as not having acted', () => {
    const situation = incapacitate(delay(round3(), sana.id), sana.id, 1);

    expect(find(situation, sana).incapacitatedUntil).toBe(4);
  });

  // "durations do not add together" (RIC-011): a later hit only matters if it
  // reaches further than the wait already running.
  it('is extended by a later hit only when that reaches further', () => {
    const first = incapacitate(round3(), sana.id, 3);
    expect(find(first, sana).incapacitatedUntil).toBe(6);

    const shorter = incapacitate({ ...first, round: 4 }, sana.id, 1);
    expect(find(shorter, sana).incapacitatedUntil).toBe(6);

    const longer = incapacitate({ ...first, round: 4 }, sana.id, 4);
    expect(find(longer, sana).incapacitatedUntil).toBe(8);
  });

  it('does nothing for a hit that overflowed nothing', () => {
    expect(find(incapacitate(round3(), sana.id, 0), sana).incapacitatedUntil).toBeNull();
  });
});

/**
 * "every time a Traveller performs a Reaction, they will suffer DM-1 on their
 * next set of actions" (refs/core/03_combat.md:192). RIC-013 reads "next" as the
 * next set not yet spent: a reaction before they have acted this round costs this
 * round's actions, one after they have acted costs next round's.
 */
describe('a reaction', () => {
  const round2 = () => ({ ...ready([rin, 12], [sana, 8]), round: 2 });

  it('costs the actions still to come this round, for someone who has not acted', () => {
    const situation = react(round2(), sana.id);

    expect(find(situation, sana)).toMatchObject({ reactions: 1, nextReactions: 0 });
  });

  it('costs next round’s actions instead, for someone who has already acted', () => {
    const situation = react(act(round2(), sana.id), sana.id);

    expect(find(situation, sana)).toMatchObject({ reactions: 0, nextReactions: 1 });
  });

  // "Dodge two shots, take DM-2." (handouts/combat_cards.typ)
  it('adds up: every reaction is a further DM-1', () => {
    const situation = react(react(round2(), sana.id), sana.id);

    expect(find(situation, sana).reactions).toBe(2);
  });

  it('is spent by acting, and by attacking', () => {
    expect(find(act(react(round2(), sana.id), sana.id), sana).reactions).toBe(0);
    expect(find(attack(react(round2(), sana.id), sana.id, rin.id), sana).reactions).toBe(0);
  });

  it('does not spend what was carried to next round by acting now', () => {
    const after = act(react(act(round2(), sana.id), sana.id), sana.id);

    expect(find(after, sana).nextReactions).toBe(1);
  });

  it('turns the carried penalty into this round’s when the round turns', () => {
    const next = newRound(react(act(round2(), sana.id), sana.id));

    expect(find(next, sana)).toMatchObject({ reactions: 1, nextReactions: 0 });
  });

  // RIC-013: the penalty attaches to the next set not yet spent. Someone who
  // never got a turn this round (out, say) still has it for their next.
  it('stays until it is spent, if the actor never acted this round', () => {
    const next = newRound(react(round2(), sana.id));

    expect(find(next, sana).reactions).toBe(1);
  });
});

/**
 * "a Traveller diving for cover will forgo their next actions completely – they
 * are too busy trying to avoid being hurt!" (refs/core/03_combat.md:208), and
 * they are on the ground afterwards. "Next" is the next set not yet spent, as
 * for any reaction (RIC-013).
 */
describe('diving for cover', () => {
  const round2 = () => ({ ...ready([rin, 12], [sana, 8]), round: 2 });

  it('ends the turn now for someone who has not acted, and leaves them prone', () => {
    const situation = dive(round2(), sana.id);

    expect(find(situation, sana)).toMatchObject({ acted: true, forfeitsNext: false, conditions: ['prone'] });
    expect(memberState(situation, find(situation, sana), roster)).toBe('acted');
  });

  it('costs next round’s turn instead for someone who has already acted', () => {
    const situation = dive(act(round2(), sana.id), sana.id);

    expect(find(situation, sana)).toMatchObject({ acted: true, forfeitsNext: true, conditions: ['prone'] });

    const next = newRound(situation);
    expect(find(next, sana)).toMatchObject({ acted: true, forfeitsNext: false });
    expect(memberState(next, find(next, sana), roster)).toBe('acted');
  });

  it('is on the ground once, however often they dive', () => {
    expect(find(dive(dive(round2(), sana.id), sana.id), sana).conditions).toEqual(['prone']);
  });

  // Getting up is the referee's to record: it is a Minor Action nobody tracks.
  it('is undone by clearing the condition, and stays prone until it is', () => {
    const down = newRound(dive(round2(), sana.id));
    expect(find(down, sana).conditions).toEqual(['prone']);

    expect(find(clearCondition(down, sana.id, 'prone'), sana).conditions).toEqual([]);
  });
});

describe('a new round', () => {
  it('counts up', () => {
    expect(newRound(ready([rin, 8])).round).toBe(2);
  });

  // RAW: "Every Traveller retains the same Initiative score for every combat
  // round" (03_combat.md:81). The typed values stay.
  it('keeps the initiative already typed in', () => {
    const situation = newRound(ready([rin, 8], [sana, 4]));
    expect(situation.members.map((member) => member.initiative)).toEqual([8, 4]);
  });

  it('gives everyone their turn back', () => {
    const spent = act(delay(ready([rin, 12], [sana, 8]), rin.id), sana.id);
    const next = newRound(spent);
    expect(memberState(next, find(next, rin), roster)).toBe('ready');
    expect(memberState(next, find(next, sana), roster)).toBe('pending');
  });
});

describe('a new round leaves the situation itself alone', () => {
  // `newRound` rebuilds the situation, and every field it forgets to carry
  // over is silently lost — which is how a fight would come back from a round
  // with no name and planned all over again.
  it('keeps the name, note and state', () => {
    const fight = {
      ...raiders(rin),
      id: 0 as never,
      name: 'Ambush',
      note: 'in the alley',
      state: 'current' as const,
    };
    expect(newRound(fight)).toMatchObject({
      name: 'Ambush',
      note: 'in the alley',
      state: 'current',
    });
  });
});

/**
 * Taking someone out again. The plan calls this withdrawing, and it is the
 * other half of actors joining: a fight is not a fixed cast.
 */
describe('removing from a situation', () => {
  it('takes the row out', () => {
    const left = removeActor(raiders(rin, sana), rin.id);
    expect(left.members.map((member) => member.actor)).toEqual([sana.id]);
  });

  // Removing one row must not disturb what the others rolled or have done.
  it('leaves everyone else exactly as they were', () => {
    const fight = act(setInitiative(raiders(rin, sana, bo), sana.id, 9), sana.id);
    const left = removeActor(fight, rin.id);
    expect(left.members[0]).toMatchObject({ actor: sana.id, initiative: 9, acted: true });
  });

  it('does nothing for an actor who was never in it', () => {
    const fight = raiders(rin);
    expect(removeActor(fight, bo.id)).toEqual(fight);
  });

  // Withdrawing frees the actor for another fight, so the seat must really be
  // vacated rather than merely hidden.
  it('lets the same actor be seated again afterwards', () => {
    const left = removeActor(raiders(rin), rin.id);
    expect(addActors(left, [rin], 'Guards').members).toHaveLength(1);
  });
});
