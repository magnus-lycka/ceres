/**
 * Installing a proposal into the library.
 *
 * The behaviour worth most of these assertions is replay safety. A bundle
 * arrives by sync, and sync can bring the same file back after it was
 * consumed, retry after a crash, or run twice over a slow network — none of
 * which may produce a second copy of a party. From
 * `docs/plan-library-import.md`, "Application-side installation".
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { actorSchema } from '$lib/schema/actor';
import { Library } from './library';
import { MemoryFileStore } from './memory';

/** An unsaved actor, as the Actors page would hand one over. */
const rat = () => actorSchema.parse({ kind: 'animal', hits: 4, name: 'Rat' });

const bundle = {
  name: 'Starport security',
  tags: ['security'],
  note: 'The night shift.',
  actors: [
    {
      name: 'Sergeant Vela',
      kind: 'sophont',
      strength: 9,
      dexterity: 8,
      endurance: 10,
      tags: ['security'],
    },
    { name: 'Guard beast', kind: 'animal', hits: 20 },
  ],
};

let files: MemoryFileStore;
let library: Library;

/** Put a proposal in the inbox, as a sync would have done. */
async function propose(name: string, content: unknown = bundle) {
  await files.write(`inbox/${name}.json`, JSON.stringify(content, null, 2), 'inbox');
}

beforeEach(() => {
  files = new MemoryFileStore();
  library = new Library(files);
});

describe('installing a bundle', () => {
  it('creates the actors it describes', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    expect((await library.actors()).map((actor) => actor.name)).toEqual(['Sergeant Vela', 'Guard beast']);
  });

  it('creates one party holding them, in the submitted order', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    const [party] = await library.parties();
    expect(party.name).toBe('Starport security');
    const members = await library.partyMembers(party.id);
    expect(members.map((actor) => actor?.name)).toEqual(['Sergeant Vela', 'Guard beast']);
  });

  it('brings them in healthy, whatever the party is for', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    expect((await library.actors()).every((actor) => actor.injuries.length === 0)).toBe(true);
  });

  it('keeps the party note and tags', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    const [party] = await library.parties();
    expect(party.note).toBe('The night shift.');
    expect(party.tags).toEqual(['security']);
  });

  it('takes the proposal out of the inbox once it is in', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    expect(await library.inbox()).toEqual([]);
  });

  it('records what it allocated', async () => {
    await propose('issue-1');
    const receipt = await library.importBundle('issue-1');
    expect(receipt).toMatchObject({ bundle: 'issue-1', issue: 1, status: 'complete' });
    expect(receipt.actors).toHaveLength(2);
  });
});

describe('ids', () => {
  it('does not reuse an id already taken by a stored actor', async () => {
    const existing = await library.saveActor(rat());
    await propose('issue-1');
    const receipt = await library.importBundle('issue-1');
    expect(receipt.actors).not.toContain(existing.id);
  });

  it('leaves the counter above everything it handed out', async () => {
    await propose('issue-1');
    const receipt = await library.importBundle('issue-1');
    const later = await library.saveActor(rat());
    expect(later.id).toBeGreaterThan(Math.max(...receipt.actors));
  });
});

/**
 * Replay safety. Sync may bring a consumed file back, and a crash may stop an
 * installation anywhere in the middle; neither may produce a second party.
 */
describe('installing twice', () => {
  it('does nothing the second time', async () => {
    await propose('issue-1');
    const first = await library.importBundle('issue-1');
    await propose('issue-1');
    const again = await library.importBundle('issue-1');
    expect(again).toEqual(first);
    expect(await library.actors()).toHaveLength(2);
    expect(await library.parties()).toHaveLength(1);
  });

  it('removes the stale file rather than leaving it to try again forever', async () => {
    await propose('issue-1');
    await library.importBundle('issue-1');
    await propose('issue-1');
    await library.importBundle('issue-1');
    expect(await library.inbox()).toEqual([]);
  });

  /**
   * Interrupted after the receipt was written but before the entities: the
   * retry must reuse the recorded ids and finish the same installation, not
   * reserve a second set and create everybody twice.
   */
  it('resumes an installation that stopped partway', async () => {
    await propose('issue-1');
    await files.write(
      'imports/issue-1.json',
      JSON.stringify({
        schemaVersion: 1,
        bundle: 'issue-1',
        issue: 1,
        status: 'installing',
        actors: [41, 42],
        party: 9,
      }),
      'interrupted',
    );

    const receipt = await library.importBundle('issue-1');
    expect(receipt.status).toBe('complete');
    expect(receipt.actors).toEqual([41, 42]);
    expect((await library.actors()).map((actor) => actor.id)).toEqual([41, 42]);
    expect((await library.parties())[0].id).toBe(9);
  });

  it('finishes a half-written installation without duplicating what was there', async () => {
    await propose('issue-1');
    await files.write(
      'imports/issue-1.json',
      JSON.stringify({
        schemaVersion: 1,
        bundle: 'issue-1',
        issue: 1,
        status: 'installing',
        actors: [41, 42],
        party: 9,
      }),
      'interrupted',
    );
    // The first actor had already been written before the interruption.
    await files.write(
      'actors/41.json',
      JSON.stringify({
        id: 41,
        name: 'Sergeant Vela',
        kind: 'sophont',
        strength: 9,
        dexterity: 8,
        endurance: 10,
      }),
      'half',
    );

    await library.importBundle('issue-1');
    expect(await library.actors()).toHaveLength(2);
    expect(await library.parties()).toHaveLength(1);
  });
});

describe('a proposal that cannot be installed', () => {
  it('refuses one the schema rejects', async () => {
    await propose('issue-1', { name: 'Nobody', actors: [] });
    await expect(library.importBundle('issue-1')).rejects.toThrow(/not a valid library bundle/);
  });

  it('says which field was wrong, for an author who cannot run the validator', async () => {
    await propose('issue-1', {
      name: 'Guards',
      actors: [{ name: 'Vela', kind: 'sophont', hits: 9 }],
    });
    await expect(library.importBundle('issue-1')).rejects.toThrow(/actors\.0/);
  });

  it('leaves it in the inbox, so it stays visible', async () => {
    await propose('issue-1', { name: 'Nobody', actors: [] });
    await library.importBundle('issue-1').catch(() => undefined);
    expect(await library.inbox()).toEqual(['issue-1']);
  });

  it('creates nothing at all', async () => {
    await propose('issue-1', { name: 'Nobody', actors: [] });
    await library.importBundle('issue-1').catch(() => undefined);
    expect(await library.actors()).toEqual([]);
    expect(await library.parties()).toEqual([]);
  });
});

describe('installing everything waiting', () => {
  it('takes each proposal in turn', async () => {
    await propose('issue-1');
    await propose('issue-2', { ...bundle, name: 'Pirates' });
    const outcome = await library.importInbox();
    expect(outcome.installed).toHaveLength(2);
    expect((await library.parties()).map((party) => party.name)).toEqual(['Starport security', 'Pirates']);
  });

  // One author's mistake must not hold up somebody else's party.
  it('installs the good ones even when one is bad', async () => {
    await propose('issue-1', { name: 'Broken', actors: [] });
    await propose('issue-2', { ...bundle, name: 'Pirates' });
    const outcome = await library.importInbox();
    expect(outcome.installed).toHaveLength(1);
    expect(outcome.problems).toHaveLength(1);
    expect((await library.parties()).map((party) => party.name)).toEqual(['Pirates']);
    expect(await library.inbox()).toEqual(['issue-1']);
  });

  it('has nothing to say when the inbox is empty', async () => {
    expect(await library.importInbox()).toEqual({ installed: [], problems: [] });
  });
});
