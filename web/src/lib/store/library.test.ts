/**
 * The library's persistence, tested against a file store in memory.
 *
 * These mirror `tests/unit/rounds/test_library.py`: the same store lives on
 * the Python side, and the two must agree about layout and id allocation or a
 * repo written by one will confuse the other.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { actorId, partyId, type Actor } from '$lib/schema/actor';
import type { Party } from '$lib/schema/party';
import { Library } from './library';
import { MemoryFileStore } from './memory';

function actor(name: string, id = actorId(0)): Actor {
  return {
    id,
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

let files: MemoryFileStore;
let library: Library;

beforeEach(() => {
  files = new MemoryFileStore();
  library = new Library(files);
});

describe('saving', () => {
  it('allocates an id to an actor that has never been saved', async () => {
    expect((await library.saveActor(actor('Rin'))).id).toBe(1);
  });

  it('keeps the id of an actor that already has one', async () => {
    await library.saveActor(actor('Rin'));
    const edited = { ...actor('Rin', actorId(1)), note: 'medic' };
    expect((await library.saveActor(edited)).id).toBe(1);
    expect(await library.actors()).toHaveLength(1);
  });

  it('writes one file per actor, named by id', async () => {
    await library.saveActor(actor('Rin'));
    expect(await files.list('actors')).toEqual(['actors/1.json']);
  });

  it('round-trips everything the actor was carrying', async () => {
    const hurt: Actor = {
      ...actor('Warbot'),
      kind: 'robot',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      injuries: [{ when: null, kind: 'lethal', reductions: { hits: 8 } }],
      criticals: { power: { severity: 3, note: 'Speed −1 m/band' } },
    };
    const saved = await library.saveActor(hurt);
    expect(await library.actor(saved.id)).toEqual(saved);
  });

  it('says what it did, so the history reads as a log', async () => {
    await library.saveActor(actor('Rin'));
    expect(files.messages.at(-1)).toContain('Rin');
  });
});

describe('reading', () => {
  it('has nothing to offer an empty repo', async () => {
    expect(await library.actors()).toEqual([]);
  });

  it('returns actors in id order, however the store lists them', async () => {
    await files.write('actors/10.json', JSON.stringify(actor('Ten', actorId(10))), 'x');
    await files.write('actors/2.json', JSON.stringify(actor('Two', actorId(2))), 'x');
    expect((await library.actors()).map((a) => a.name)).toEqual(['Two', 'Ten']);
  });

  // Deletion is unguarded, so every reference is potentially stale. Resolving
  // to nothing is the bargain — the same as ON DELETE SET NULL.
  it('resolves a stale id to nothing rather than raising', async () => {
    expect(await library.actor(actorId(99))).toBeNull();
  });

  it('names the file when its contents are not a valid actor', async () => {
    await files.write('actors/3.json', '{"name": "broken"}', 'x');
    await expect(library.actors()).rejects.toThrow(/actors\/3\.json/);
  });
});

describe('deleting', () => {
  it('takes the actor out of the library', async () => {
    const rin = await library.saveActor(actor('Rin'));
    await library.deleteActor(rin.id);
    expect(await library.actors()).toEqual([]);
  });

  it('is silent about an actor that is already gone', async () => {
    await expect(library.deleteActor(actorId(99))).resolves.toBeUndefined();
  });
});

describe('id allocation', () => {
  it('climbs, one at a time', async () => {
    const ids = [await library.saveActor(actor('A')), await library.saveActor(actor('B'))];
    expect(ids.map((a) => a.id)).toEqual([1, 2]);
  });

  // The bug this guards: `max(id) + 1` hands a deleted actor's id to the next
  // new one, so a stale reference resolves to a stranger instead of nothing.
  it('never reissues the id of a deleted actor', async () => {
    const first = await library.saveActor(actor('A'));
    await library.deleteActor(first.id);
    expect((await library.saveActor(actor('B'))).id).toBe(2);
  });

  it('survives a reload, because the counter is stored', async () => {
    await library.saveActor(actor('A'));
    await library.deleteActor(actorId(1));
    const reopened = new Library(files);
    expect((await reopened.saveActor(actor('B'))).id).toBe(2);
  });

  // A file placed by hand, or by an import, may sit above the counter.
  it('does not collide with an id the counter has never seen', async () => {
    await files.write('actors/7.json', JSON.stringify(actor('Seven', actorId(7))), 'x');
    expect((await library.saveActor(actor('New'))).id).toBe(8);
  });
});

describe('overlapping work', () => {
  // Clicking Add twice before the first save returns must not hand both
  // actors the same id, nor fail one of them: each save reads the counter,
  // and without serialising, the second reads it before the first writes it.
  it('allocates distinct ids when saves overlap', async () => {
    const [first, second] = await Promise.all([library.saveActor(actor('A')), library.saveActor(actor('B'))]);
    expect([first.id, second.id]).toEqual([1, 2]);
    expect(await library.actors()).toHaveLength(2);
  });

  it('keeps allocating cleanly through a burst', async () => {
    const names = ['A', 'B', 'C', 'D', 'E'];
    const saved = await Promise.all(names.map((name) => library.saveActor(actor(name))));
    expect(saved.map((a) => a.id).sort((x, y) => x - y)).toEqual([1, 2, 3, 4, 5]);
  });
});

function party(name: string, actors: number[] = [], id = partyId(0)): Party {
  return { id, name, note: '', tags: [], actors: actors.map(actorId) };
}

describe('parties', () => {
  it('allocates ids from a counter of their own, not the actors one', async () => {
    await library.saveActor(actor('Rin'));
    await library.saveActor(actor('Sana'));
    expect((await library.saveParty(party('The crew'))).id).toBe(1);
  });

  it('writes one file per party, named by id', async () => {
    await library.saveParty(party('The crew'));
    expect(await files.list('parties')).toEqual(['parties/1.json']);
  });

  it('round-trips its members', async () => {
    const saved = await library.saveParty(party('The crew', [1, 2]));
    expect((await library.party(saved.id))?.actors).toEqual([1, 2]);
  });

  it('resolves a stale party id to nothing rather than raising', async () => {
    expect(await library.party(partyId(99))).toBeNull();
  });

  it('takes a party out of the library', async () => {
    const saved = await library.saveParty(party('The crew'));
    await library.deleteParty(saved.id);
    expect(await library.parties()).toEqual([]);
  });
});

describe('members', () => {
  it('resolves each reference to its actor, in stored order', async () => {
    const rin = await library.saveActor(actor('Rin'));
    const sana = await library.saveActor(actor('Sana'));
    const crew = await library.saveParty(party('The crew', [sana.id, rin.id]));

    expect((await library.partyMembers(crew.id)).map((member) => member?.name)).toEqual(['Sana', 'Rin']);
  });

  // Deleting is unguarded and nothing goes back to tidy the parties that
  // referenced the actor. The hole is the truth: a member was there.
  it('leaves a hole where a member has been deleted', async () => {
    const rin = await library.saveActor(actor('Rin'));
    const sana = await library.saveActor(actor('Sana'));
    const crew = await library.saveParty(party('The crew', [rin.id, sana.id]));
    await library.deleteActor(rin.id);

    expect((await library.partyMembers(crew.id)).map((member) => member?.name ?? null)).toEqual([
      null,
      'Sana',
    ]);
  });

  it('has nothing to offer for a party that is itself gone', async () => {
    expect(await library.partyMembers(partyId(99))).toEqual([]);
  });

  // Ids only ever climb, so a deleted actor's id is never handed to a new one
  // — a stale reference resolves to nothing, never to a stranger.
  it('never resolves a stale reference to a different actor', async () => {
    const rin = await library.saveActor(actor('Rin'));
    const crew = await library.saveParty(party('The crew', [rin.id]));
    await library.deleteActor(rin.id);
    const newcomer = await library.saveActor(actor('Kes'));

    expect(newcomer.id).not.toBe(rin.id);
    expect(await library.partyMembers(crew.id)).toEqual([null]);
  });
});
