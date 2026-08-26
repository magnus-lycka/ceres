/**
 * The local store, against a real IndexedDB rather than a mock of one.
 *
 * This is the source of truth during a session, so its behaviour under the
 * actual browser database is what matters — quota, key ordering and
 * transaction semantics are exactly the things a fake would get wrong.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { IdbFileStore } from './idb';

let store: IdbFileStore;
let database = 0;

beforeEach(() => {
  // A fresh database per test, so nothing leaks between them.
  database += 1;
  store = new IdbFileStore(`ceres-test-${database}`);
});

describe('files', () => {
  it('reads back what was written', async () => {
    await store.write('actors/1.json', '{"id":1}', 'Save actor 1');
    expect(await store.read('actors/1.json')).toBe('{"id":1}');
  });

  it('reports a path that was never written as nothing', async () => {
    expect(await store.read('actors/9.json')).toBeNull();
  });

  it('lists only what is under the directory asked for', async () => {
    await store.write('actors/1.json', '{}', 'x');
    await store.write('parties/1.json', '{}', 'x');
    expect(await store.list('actors')).toEqual(['actors/1.json']);
  });

  it('forgets a removed path', async () => {
    await store.write('actors/1.json', '{}', 'x');
    await store.remove('actors/1.json', 'Delete actor 1');
    expect(await store.read('actors/1.json')).toBeNull();
    expect(await store.list('actors')).toEqual([]);
  });

  it('survives a new handle on the same database, as a reload gives', async () => {
    await store.write('actors/1.json', '{"id":1}', 'x');
    const reopened = new IdbFileStore(`ceres-test-${database}`);
    expect(await reopened.read('actors/1.json')).toBe('{"id":1}');
  });
});

describe('what has changed since the last sync', () => {
  it('has nothing to say about an untouched store', async () => {
    expect(await store.changes()).toEqual(new Map());
  });

  it('records a write, with the reason it happened', async () => {
    await store.write('actors/1.json', '{}', 'Save actor 1: Rin');
    expect(await store.changes()).toEqual(
      new Map([['actors/1.json', { op: 'write', message: 'Save actor 1: Rin' }]]),
    );
  });

  it('records a removal', async () => {
    await store.remove('actors/1.json', 'Delete actor 1');
    expect((await store.changes()).get('actors/1.json')?.op).toBe('remove');
  });

  // The sync pushes the current state of a path, not a replay of what
  // happened to it, so only the latest change matters.
  it('keeps only the latest change to a path', async () => {
    await store.write('actors/1.json', '{}', 'Save');
    await store.remove('actors/1.json', 'Delete actor 1');
    expect((await store.changes()).size).toBe(1);
    expect((await store.changes()).get('actors/1.json')?.op).toBe('remove');
  });

  it('is clean again once a sync says so', async () => {
    await store.write('actors/1.json', '{}', 'x');
    await store.clearChanges();
    expect(await store.changes()).toEqual(new Map());
  });
});

describe('the commit this copy matches', () => {
  it('is nothing before the first sync', async () => {
    expect(await store.head()).toBeNull();
  });

  it('is remembered across handles', async () => {
    await store.setHead('abc123');
    expect(await new IdbFileStore(`ceres-test-${database}`).head()).toBe('abc123');
  });
});

describe('taking a pull wholesale', () => {
  it('replaces what was there and comes back clean', async () => {
    await store.write('actors/1.json', '{"old":true}', 'x');
    await store.replaceAll(new Map([['actors/2.json', '{"new":true}']]));

    expect(await store.read('actors/1.json')).toBeNull();
    expect(await store.read('actors/2.json')).toBe('{"new":true}');
    expect(await store.changes()).toEqual(new Map());
  });
});
