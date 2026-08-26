import { describe, expect, it } from 'vitest';
import { actorId, type Actor, type ActorId } from '../../schema/actor';
import { createIdSequence, duplicate, highestId } from './library';

function actor(id: ActorId, name: string, tags: string[] = []): Actor {
  return {
    id,
    name,
    kind: 'sophont',
    note: '',
    tags,
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
  };
}

const roster = [
  actor(actorId(1), 'Rin', ['pc', 'marduk']),
  actor(actorId(2), 'Wolf', ['beasts']),
  actor(actorId(3), 'Pirate', ['pirates', 'marduk']),
];

describe('id sequence', () => {
  it('climbs, one at a time', () => {
    const ids = createIdSequence(highestId(roster));
    expect([ids.next(), ids.next()]).toEqual([4, 5]);
  });

  it('starts at one for an empty library', () => {
    expect(createIdSequence(highestId([])).next()).toBe(1);
  });

  it('does not go backwards when the highest actor is deleted', () => {
    const ids = createIdSequence(highestId(roster));
    const issued = ids.next();
    const survivors = roster.slice(0, 1);
    // Re-deriving from what is left would hand out 2 again; the sequence must not.
    expect(highestId(survivors)).toBeLessThan(issued);
    expect(ids.next()).toBe(issued + 1);
  });

  it('never reissues an id, however many actors are deleted', () => {
    const ids = createIdSequence(highestId(roster));
    const issued = [ids.next(), ids.next(), ids.next()];
    expect(new Set(issued).size).toBe(issued.length);
    expect(ids.next()).toBeGreaterThan(Math.max(...issued));
  });
});

describe('duplicate', () => {
  it('numbers the copy so it is distinguishable from its original', () => {
    expect(duplicate(actor(actorId(1), 'Wolf'), actorId(2), [actor(actorId(1), 'Wolf')]).name).toBe('Wolf 1');
  });

  it('continues the series when pressed again', () => {
    const first = duplicate(actor(actorId(1), 'Wolf'), actorId(2), [actor(actorId(1), 'Wolf')]);
    const second = duplicate(actor(actorId(1), 'Wolf'), actorId(3), [actor(actorId(1), 'Wolf'), first]);
    expect([first.name, second.name]).toEqual(['Wolf 1', 'Wolf 2']);
  });

  it('continues the series when duplicating a copy, not starting a new one', () => {
    const roster = [actor(actorId(1), 'Wolf'), actor(actorId(2), 'Wolf 1')];
    expect(duplicate(roster[1], actorId(3), roster).name).toBe('Wolf 2');
  });

  it('takes its id from the sequence rather than from the roster', () => {
    expect(duplicate(actor(actorId(1), 'Wolf'), actorId(9), [actor(actorId(1), 'Wolf')]).id).toBe(9);
  });

  it('does not share the tag list with the original', () => {
    const source = actor(actorId(1), 'Chicken', ['fowl']);
    duplicate(source, actorId(2), [source]).tags.push('extra');
    expect(source.tags).toEqual(['fowl']);
  });

  // Ten chickens in a fight are ten actors precisely because each is hurt
  // separately. A copy of a hurt one starts undamaged.
  it('arrives unhurt, whatever state the original is in', () => {
    const source: Actor = {
      ...actor(actorId(1), 'Warbot'),
      kind: 'robot',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      injuries: [{ when: null, kind: 'lethal', reductions: { hits: 8 } }],
      criticals: { power: { severity: 3, note: 'Speed −1 m/band' } },
    };
    const copy = duplicate(source, actorId(2), [source]);
    expect(copy.injuries).toEqual([]);
    expect(copy.criticals).toEqual({});
  });
});
