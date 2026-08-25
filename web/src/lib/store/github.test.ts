/**
 * The GitHub backend, against a stubbed `fetch`.
 *
 * What is worth testing here is the part that is easy to get wrong and
 * invisible when it is: the sha handshake that makes a stale write fail rather
 * than clobber, and the UTF-8 round trip through base64. The library tests
 * cover everything above this layer without a network.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ConflictError, GitHubFileStore, type Repository } from './github';

const repository: Repository = { owner: 'magnus-lycka', repo: 'ceres-data', branch: 'main', token: 't' };

function respond(status: number, body: unknown) {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), { status });
}

function base64(text: string): string {
  return btoa(String.fromCharCode(...new TextEncoder().encode(text)));
}

afterEach(() => vi.unstubAllGlobals());

/** Queue one response per call, in order. */
function stubFetch(...responses: Response[]) {
  const fetch = vi.fn();
  for (const response of responses) fetch.mockResolvedValueOnce(response);
  vi.stubGlobal('fetch', fetch);
  return fetch;
}

describe('reading', () => {
  it('lists only the files under the directory asked for', async () => {
    stubFetch(
      respond(200, {
        tree: [
          { path: 'actors/1.json', sha: 'a', type: 'blob' },
          { path: 'parties/1.json', sha: 'b', type: 'blob' },
          { path: 'actors', sha: 'c', type: 'tree' },
        ],
      }),
    );
    const store = new GitHubFileStore(repository);
    expect(await store.list('actors')).toEqual(['actors/1.json']);
  });

  // A repository with nothing committed yet has no tree, which is the state
  // ceres-data starts in rather than an error.
  it('treats a repository with no tree as empty', async () => {
    stubFetch(respond(409, 'Git Repository is empty.'));
    expect(await new GitHubFileStore(repository).list('actors')).toEqual([]);
  });

  it('reports a missing file as nothing rather than raising', async () => {
    stubFetch(respond(404, { message: 'Not Found' }));
    expect(await new GitHubFileStore(repository).read('actors/9.json')).toBeNull();
  });

  it('carries text through base64 unharmed, accents and all', async () => {
    const text = '{"name":"Ürsël","note":"Protection −1D"}';
    stubFetch(respond(200, { content: base64(text), sha: 'a' }));
    expect(await new GitHubFileStore(repository).read('actors/1.json')).toBe(text);
  });
});

describe('writing', () => {
  it('sends the sha it read, so GitHub can refuse a stale write', async () => {
    const fetch = stubFetch(
      respond(200, { content: base64('{}'), sha: 'old-sha' }),
      respond(200, { content: { sha: 'new-sha' } }),
    );
    const store = new GitHubFileStore(repository);
    await store.read('actors/1.json');
    await store.write('actors/1.json', '{"id":1}', 'Save actor 1');

    const body = JSON.parse(fetch.mock.calls[1][1].body);
    expect(body).toMatchObject({ sha: 'old-sha', branch: 'main', message: 'Save actor 1' });
  });

  it('sends no sha for a file that does not exist yet', async () => {
    const fetch = stubFetch(respond(200, { content: { sha: 'new-sha' } }));
    await new GitHubFileStore(repository).write('actors/1.json', '{}', 'Save actor 1');
    expect(JSON.parse(fetch.mock.calls[0][1].body).sha).toBeUndefined();
  });

  // Another machine got there first. Failing loudly is the point: the
  // alternative is silently overwriting someone else's session.
  it('raises a conflict rather than clobbering a file that moved on', async () => {
    stubFetch(respond(409, { message: 'is at abc but expected def' }));
    const store = new GitHubFileStore(repository);
    await expect(store.write('actors/1.json', '{}', 'Save')).rejects.toThrow(ConflictError);
  });

  it('remembers the new sha, so a second save in a row works', async () => {
    const fetch = stubFetch(
      respond(200, { content: { sha: 'first' } }),
      respond(200, { content: { sha: 'second' } }),
    );
    const store = new GitHubFileStore(repository);
    await store.write('actors/1.json', '{"n":1}', 'Save');
    await store.write('actors/1.json', '{"n":2}', 'Save');
    expect(JSON.parse(fetch.mock.calls[1][1].body).sha).toBe('first');
  });
});

describe('deleting', () => {
  it('is silent about a file that is already gone', async () => {
    stubFetch(respond(200, { tree: [] }));
    await expect(new GitHubFileStore(repository).remove('actors/9.json', 'Delete')).resolves.toBeUndefined();
  });

  it('sends the sha of the file it is removing', async () => {
    const fetch = stubFetch(
      respond(200, { tree: [{ path: 'actors/1.json', sha: 'a', type: 'blob' }] }),
      respond(200, {}),
    );
    await new GitHubFileStore(repository).remove('actors/1.json', 'Delete actor 1');
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toMatchObject({ sha: 'a', message: 'Delete actor 1' });
  });
});

describe('failures', () => {
  it('says what GitHub said when it refuses', async () => {
    stubFetch(respond(401, { message: 'Bad credentials' }));
    await expect(new GitHubFileStore(repository).read('actors/1.json')).rejects.toThrow(
      /401.*Bad credentials/,
    );
  });
});
