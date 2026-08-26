/**
 * The repository, against a stubbed `fetch`.
 *
 * What is worth pinning here is the shape of the tree we build, because
 * getting it wrong is answered by GitHub with a 422 and a message about object
 * state rather than anything that names the mistake.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { GitHubRepository, type Repository } from './github';

const repository: Repository = {
  owner: 'magnus-lycka',
  repo: 'ceres-data',
  branch: 'main',
  token: 't',
  device: 'thinkpad',
};

function respond(status: number, body: unknown) {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), { status });
}

afterEach(() => vi.unstubAllGlobals());

/**
 * Answer by route rather than in order, so a test says what the repository
 * contains rather than how many calls it takes to find out.
 */
function stubGitHub(paths: string[] = []) {
  const fetched = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    if (method === 'GET' && url.includes('/git/ref/heads/')) {
      return respond(200, { object: { sha: 'head-sha' } });
    }
    if (method === 'GET' && url.includes('/git/commits/')) {
      return respond(200, { tree: { sha: 'base-tree' } });
    }
    if (method === 'GET' && url.includes('/git/trees/')) {
      return respond(200, {
        tree: paths.map((path) => ({ path, sha: `${path}-sha`, type: 'blob' })),
      });
    }
    if (method === 'POST' && url.endsWith('/git/trees')) return respond(200, { sha: 'new-tree' });
    if (method === 'POST' && url.endsWith('/git/commits')) return respond(200, { sha: 'new-commit' });
    return respond(200, {});
  });
  vi.stubGlobal('fetch', fetched);
  return fetched;
}

function treeSent(fetched: ReturnType<typeof stubGitHub>) {
  const call = fetched.mock.calls.find(
    ([url, init]) => init?.method === 'POST' && String(url).endsWith('/git/trees'),
  );
  return call ? JSON.parse(call[1]!.body as string) : null;
}

describe('building a tree', () => {
  it('writes file contents inline, so there is no request per file', async () => {
    const fetched = stubGitHub([]);
    await new GitHubRepository(repository).commit(
      [
        { path: 'actors/1.json', content: '{"id":1}' },
        { path: 'actors/2.json', content: '{"id":2}' },
      ],
      'Sync: 2 written',
      'head-sha',
    );

    expect(treeSent(fetched).tree).toEqual([
      { path: 'actors/1.json', mode: '100644', type: 'blob', content: '{"id":1}' },
      { path: 'actors/2.json', mode: '100644', type: 'blob', content: '{"id":2}' },
    ]);
  });

  it('deletes a path the repository has, with a null sha', async () => {
    const fetched = stubGitHub(['actors/1.json']);
    await new GitHubRepository(repository).commit(
      [{ path: 'actors/1.json', content: null }],
      'Sync: 1 deleted',
      'head-sha',
    );

    expect(treeSent(fetched).tree).toEqual([
      { path: 'actors/1.json', mode: '100644', type: 'blob', sha: null },
    ]);
  });

  /**
   * Created and deleted again between two syncs, so the repository never saw
   * it. Asking a tree to delete a path it does not have is answered with
   * `422 GitRPC::BadObjectState`, which blocks every later sync too.
   */
  it('drops a deletion for a path the repository never had', async () => {
    const fetched = stubGitHub(['actors/1.json']);
    await new GitHubRepository(repository).commit(
      [
        { path: 'actors/1.json', content: null },
        { path: 'parties/9.json', content: null },
      ],
      'Sync: 2 deleted',
      'head-sha',
    );

    expect(treeSent(fetched).tree).toEqual([
      { path: 'actors/1.json', mode: '100644', type: 'blob', sha: null },
    ]);
  });

  it('commits nothing at all when every change was such a deletion', async () => {
    const fetched = stubGitHub([]);
    const head = await new GitHubRepository(repository).commit(
      [{ path: 'parties/9.json', content: null }],
      'Sync: 1 deleted',
      'head-sha',
    );

    expect(head).toBe('head-sha');
    expect(treeSent(fetched)).toBeNull();
  });

  it('names the machine, so the history says which laptop', async () => {
    const fetched = stubGitHub([]);
    await new GitHubRepository(repository).commit(
      [{ path: 'actors/1.json', content: '{}' }],
      'Sync: 1 written',
      'head-sha',
    );

    const call = fetched.mock.calls.find(([url]) => String(url).endsWith('/git/commits'));
    expect(JSON.parse(call![1]!.body as string).author).toMatchObject({ name: 'thinkpad' });
  });

  it('commits without a parent into an empty repository', async () => {
    const fetched = stubGitHub([]);
    await new GitHubRepository(repository).commit(
      [{ path: 'actors/1.json', content: '{}' }],
      'Sync: 1 written',
      null,
    );

    expect(treeSent(fetched).base_tree).toBeUndefined();
    const call = fetched.mock.calls.find(([url]) => String(url).endsWith('/git/commits'));
    expect(JSON.parse(call![1]!.body as string).parents).toEqual([]);
  });
});

describe('reading', () => {
  it('reports an empty repository as having no head', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => respond(404, { message: 'Not Found' })),
    );
    expect(await new GitHubRepository(repository).head()).toBeNull();
  });

  it('never reads through the browser cache', async () => {
    const fetched = stubGitHub([]);
    await new GitHubRepository(repository).head();
    expect(fetched.mock.calls[0][1]!.cache).toBe('no-store');
  });
});
