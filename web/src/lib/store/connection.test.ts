/**
 * Where the data lives, and the credential to reach it.
 *
 * The repository is configuration, never a constant in the source: this is a
 * public code repo and the data repo is private, so the two must not know each
 * other's names at rest.
 */
import { describe, expect, it } from 'vitest';
import { clearConnection, loadConnection, parseRepository, saveConnection } from './connection';

/** localStorage does not exist in Node, and the tests should not need it to. */
function fakeStorage(): Storage {
  const entries = new Map<string, string>();
  return {
    getItem: (key) => entries.get(key) ?? null,
    setItem: (key, value) => void entries.set(key, value),
    removeItem: (key) => void entries.delete(key),
    clear: () => entries.clear(),
    key: (index) => [...entries.keys()][index] ?? null,
    get length() {
      return entries.size;
    },
  };
}

describe('reading a repository out of what was pasted', () => {
  it('accepts the URL from the browser address bar', () => {
    expect(parseRepository('https://github.com/magnus-lycka/ceres-data')).toEqual({
      owner: 'magnus-lycka',
      repo: 'ceres-data',
    });
  });

  it('accepts a trailing slash, as copying a URL often leaves', () => {
    expect(parseRepository('https://github.com/magnus-lycka/ceres-data/')?.repo).toBe('ceres-data');
  });

  it('accepts the clone URL, .git and all', () => {
    expect(parseRepository('https://github.com/magnus-lycka/ceres-data.git')?.repo).toBe('ceres-data');
  });

  it('accepts the SSH remote, which is what a clone usually shows', () => {
    expect(parseRepository('git@github.com:magnus-lycka/ceres-data.git')).toEqual({
      owner: 'magnus-lycka',
      repo: 'ceres-data',
    });
  });

  it('accepts owner/repo on its own, which is how people say it', () => {
    expect(parseRepository('magnus-lycka/ceres-data')?.owner).toBe('magnus-lycka');
  });

  it('ignores surrounding whitespace from a sloppy paste', () => {
    expect(parseRepository('  magnus-lycka/ceres-data \n')?.repo).toBe('ceres-data');
  });

  it('refuses what is not a repository at all', () => {
    expect(parseRepository('')).toBeNull();
    expect(parseRepository('ceres-data')).toBeNull();
    expect(parseRepository('https://github.com/magnus-lycka')).toBeNull();
  });
});

describe('keeping the connection between visits', () => {
  it('reads back what was saved', () => {
    const storage = fakeStorage();
    saveConnection({ owner: 'magnus-lycka', repo: 'ceres-data', branch: 'main', token: 'x' }, storage);
    expect(loadConnection(storage)).toEqual({
      owner: 'magnus-lycka',
      repo: 'ceres-data',
      branch: 'main',
      token: 'x',
    });
  });

  it('has nothing to offer before anything is configured', () => {
    expect(loadConnection(fakeStorage())).toBeNull();
  });

  it('forgets on request, which is how a borrowed machine is left', () => {
    const storage = fakeStorage();
    saveConnection({ owner: 'a', repo: 'b', branch: 'main', token: 'x' }, storage);
    clearConnection(storage);
    expect(loadConnection(storage)).toBeNull();
  });

  it('treats damaged stored settings as none, rather than failing to start', () => {
    const storage = fakeStorage();
    storage.setItem('ceres.connection', '{ this is not json');
    expect(loadConnection(storage)).toBeNull();
  });

  it('rejects stored settings that are missing a field', () => {
    const storage = fakeStorage();
    storage.setItem('ceres.connection', JSON.stringify({ owner: 'a', repo: 'b' }));
    expect(loadConnection(storage)).toBeNull();
  });
});
