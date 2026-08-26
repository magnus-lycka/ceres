/**
 * Reconciling local and remote, against a real IndexedDB and a stubbed
 * repository.
 *
 * The cases that matter are the three the design turns on: the happy path
 * where nothing else has written, being merely behind, and both sides having
 * moved — which must stop rather than guess.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { GitHubRepository } from './github';
import { IdbFileStore } from './idb';
import { Sync } from './sync';

let local: IdbFileStore;
let database = 0;

function repository(head: string | null, files = new Map<string, string>()) {
  return {
    head: vi.fn(async () => head),
    files: vi.fn(async () => files),
    commit: vi.fn(async () => 'new-head'),
  } as unknown as GitHubRepository & { commit: ReturnType<typeof vi.fn> };
}

beforeEach(() => {
  database += 1;
  local = new IdbFileStore(`ceres-sync-${database}`);
});

describe('nothing has changed anywhere', () => {
  it('does nothing at all', async () => {
    await local.setHead('abc');
    const remote = repository('abc');
    expect((await new Sync(local, remote).run()).state).toBe('synced');
    expect(remote.commit).not.toHaveBeenCalled();
  });
});

describe('local changes, remote where we left it', () => {
  it('pushes them as one commit', async () => {
    await local.setHead('abc');
    await local.write('actors/1.json', '{"id":1}', 'Save actor 1: Rin');
    await local.write('actors/2.json', '{"id":2}', 'Save actor 2: Sana');
    const remote = repository('abc');

    const outcome = await new Sync(local, remote).run();

    expect(outcome).toMatchObject({ state: 'synced', changes: 2 });
    expect(remote.commit).toHaveBeenCalledTimes(1);
    const [changes, message, parent] = remote.commit.mock.calls[0];
    expect(changes).toHaveLength(2);
    expect(parent).toBe('abc');
    expect(message).toContain('2 written');
    // The reasons recorded as each change happened, kept in the commit body.
    expect(message).toContain('Save actor 1: Rin');
  });

  it('sends a deletion as a null content, which is how a tree drops a path', async () => {
    await local.setHead('abc');
    await local.write('actors/1.json', '{"id":1}', 'Save');
    await local.clearChanges();
    await local.remove('actors/1.json', 'Delete actor 1');
    const remote = repository('abc');

    await new Sync(local, remote).run();

    expect(remote.commit.mock.calls[0][0]).toEqual([{ path: 'actors/1.json', content: null }]);
  });

  it('comes back clean, so the next sync has nothing to do', async () => {
    await local.setHead('abc');
    await local.write('actors/1.json', '{}', 'Save');
    await new Sync(local, repository('abc')).run();

    expect(await local.changes()).toEqual(new Map());
    expect(await local.head()).toBe('new-head');
  });
});

describe('behind, with nothing of our own', () => {
  // Laptop Y opening a campaign laptop X has been playing. Not a conflict.
  it('takes the repository wholesale and says nothing', async () => {
    await local.setHead('old');
    await local.write('actors/1.json', '{"stale":true}', 'Save');
    await local.clearChanges();
    const remote = repository('newer', new Map([['actors/2.json', '{"id":2}']]));

    const outcome = await new Sync(local, remote).run();

    expect(outcome.state).toBe('synced');
    expect(await local.read('actors/1.json')).toBeNull();
    expect(await local.read('actors/2.json')).toBe('{"id":2}');
    expect(await local.head()).toBe('newer');
  });
});

describe('both sides have moved', () => {
  // Deliberately stops. Merging two weeks of play automatically is a worse
  // outcome than being told to sort it out with git.
  it('refuses to push, and says what happened', async () => {
    await local.setHead('old');
    await local.write('actors/1.json', '{}', 'Save actor 1');
    const remote = repository('newer');

    const outcome = await new Sync(local, remote).run();

    expect(outcome.state).toBe('blocked');
    expect(outcome.detail).toContain('newer'.slice(0, 7));
    expect(remote.commit).not.toHaveBeenCalled();
  });

  it('leaves the local changes alone, so nothing is lost', async () => {
    await local.setHead('old');
    await local.write('actors/1.json', '{"mine":true}', 'Save');

    await new Sync(local, repository('newer')).run();

    expect(await local.read('actors/1.json')).toBe('{"mine":true}');
    expect((await local.changes()).size).toBe(1);
  });
});

describe('a repository with no commits yet', () => {
  it('pushes without a parent, creating the branch', async () => {
    await local.write('actors/1.json', '{}', 'Save actor 1');
    const remote = repository(null);

    expect((await new Sync(local, remote).run()).state).toBe('synced');
    expect(remote.commit.mock.calls[0][2]).toBeNull();
  });
});

describe('status without doing anything', () => {
  it('is pending while changes wait', async () => {
    await local.write('actors/1.json', '{}', 'Save');
    expect(await new Sync(local, repository('abc')).status()).toMatchObject({
      state: 'pending',
      changes: 1,
    });
  });

  it('is synced when nothing waits', async () => {
    expect((await new Sync(local, repository('abc')).status()).state).toBe('synced');
  });

  it('asks the network nothing', async () => {
    const remote = repository('abc');
    await new Sync(local, remote).status();
    expect(remote.head).not.toHaveBeenCalled();
  });
});
