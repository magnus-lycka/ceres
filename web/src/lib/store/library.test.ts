/**
 * The library's persistence, tested against a file store in memory.
 *
 * These mirror `tests/unit/rounds/test_library.py`: the same store lives on
 * the Python side, and the two must agree about layout and id allocation or a
 * repo written by one will confuse the other.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import type { Actor } from '$lib/schema/actor';
import { Library } from './library';
import { MemoryFileStore } from './memory';

function actor(name: string, id = 0): Actor {
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
    const edited = { ...actor('Rin', 1), note: 'medic' };
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
    await files.write('actors/10.json', JSON.stringify(actor('Ten', 10)), 'x');
    await files.write('actors/2.json', JSON.stringify(actor('Two', 2)), 'x');
    expect((await library.actors()).map((a) => a.name)).toEqual(['Two', 'Ten']);
  });

  // Deletion is unguarded, so every reference is potentially stale. Resolving
  // to nothing is the bargain — the same as ON DELETE SET NULL.
  it('resolves a stale id to nothing rather than raising', async () => {
    expect(await library.actor(99)).toBeNull();
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
    await expect(library.deleteActor(99)).resolves.toBeUndefined();
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
    await library.deleteActor(1);
    const reopened = new Library(files);
    expect((await reopened.saveActor(actor('B'))).id).toBe(2);
  });

  // A file placed by hand, or by an import, may sit above the counter.
  it('does not collide with an id the counter has never seen', async () => {
    await files.write('actors/7.json', JSON.stringify(actor('Seven', 7)), 'x');
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
