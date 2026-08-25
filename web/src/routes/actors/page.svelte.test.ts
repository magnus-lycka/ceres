/**
 * The actors page against a stubbed GitHub.
 *
 * The layer that kept slipping: the store is well covered and the grid is well
 * covered, but whether a button on this page actually reaches the repository
 * was only ever verified by hand.
 */
import { render } from 'vitest-browser-svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ActorsPage from './+page.svelte';

const rin = {
  id: 1,
  name: 'Rin',
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

function b64(text: string) {
  return btoa(String.fromCharCode(...new TextEncoder().encode(text)));
}
function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

let fetched: ReturnType<typeof vi.fn>;

beforeEach(() => {
  localStorage.setItem(
    'ceres.connection',
    JSON.stringify({ owner: 'o', repo: 'r', branch: 'main', token: 't' }),
  );
  fetched = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    if (method === 'GET' && url.includes('/git/trees/')) {
      return respond(200, { tree: [{ path: 'actors/1.json', sha: 'a', type: 'blob' }] });
    }
    if (method === 'GET') return respond(200, { content: b64(JSON.stringify(rin)), sha: 'a' });
    return respond(200, { content: { sha: 'b' } });
  });
  vi.stubGlobal('fetch', fetched);
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

function requests() {
  return fetched.mock.calls.map(([url, init]) => `${init?.method ?? 'GET'} ${url}`);
}

describe('the actors page', () => {
  /** The grid cell, not the health panel heading that also says the name. */
  function cell(screen: Awaited<ReturnType<typeof render>>, text: string) {
    return screen.container.querySelector(`td[data-col-id='name']`)?.textContent?.trim() === text;
  }

  it('loads the roster from the repository', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(cell(screen, 'Rin')).toBe(true));
  });

  // The bug this guards: Delete removed the row from the grid and never told
  // the repository, so a refresh brought the actor back.
  it('deletes from the repository, not just from the screen', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(cell(screen, 'Rin')).toBe(true));

    (screen.container.querySelector(`td[data-col-id='name']`) as HTMLElement).click();
    await screen.getByRole('button', { name: 'Delete' }).click();

    await vi.waitFor(() => expect(requests().some((call) => call.startsWith('DELETE'))).toBe(true));
  });
});
