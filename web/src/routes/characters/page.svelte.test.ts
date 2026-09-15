import { render } from 'vitest-browser-svelte';
import { afterEach, expect, it, vi } from 'vitest';
import CharactersPage from './+page.svelte';

const ada = {
  id: 1,
  name: 'Ada',
  age: 18,
  age_display: '18',
  term_status: 'Starting term 1',
  rank_display: null,
  sophont: 'Humaniti',
  homeworld: 'Regina',
  ucp: '777777',
  characteristics: { STR: 7, DEX: 7, END: 7 },
  skills: 'Medic 0',
  cash: 0,
  benefits: [],
  history: ['Grew up on Regina'],
  connections: [],
  problems: [],
  finished: false,
  changes: [],
  pending: {
    id: '3.0',
    instruction: 'Choose a skill',
    inputs: [
      {
        kind: 'Select',
        name: 'skill',
        label: 'Skill',
        options: [['Pilot', 'pilot']],
        min_select: 1,
        max_select: 1,
        default: null,
      },
    ],
  },
};
afterEach(() => {
  vi.unstubAllGlobals();
  history.replaceState(null, '', location.pathname);
});
it('shows lifetime term progress above the decision and the age range in the summary', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) =>
      Response.json(
        url.endsWith('/characters')
          ? [{ id: 1, name: 'Ada', player: 'NPC', sophont: 'Humaniti' }]
          : { ...ada, age: 30, age_display: '30–34', term_status: 'In term 4' },
      ),
    ),
  );
  const screen = await render(CharactersPage);
  await screen.getByRole('button', { name: 'Ada', exact: true }).click();
  await expect.element(screen.getByText('In term 4', { exact: true })).toBeVisible();
  await expect.element(screen.getByText(/Humaniti · Age 30–34/)).toBeVisible();
});
it('shows actual rank separately from a name containing Captain', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) =>
      Response.json(
        url.endsWith('/characters')
          ? [{ id: 1, name: 'Captain Darling', player: 'NPC', sophont: 'Humaniti' }]
          : { ...ada, name: 'Captain Darling', rank_display: 'Rank 1 · Senior Crewman' },
      ),
    ),
  );
  const screen = await render(CharactersPage);
  await screen.getByRole('button', { name: 'Captain Darling', exact: true }).click();
  await expect.element(screen.getByRole('heading', { name: 'Captain Darling', exact: true })).toBeVisible();
  await expect.element(screen.getByText('Rank 1 · Senior Crewman', { exact: true })).toBeVisible();
});

it('continues a saved character and shows the outcome beside its summary', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'POST')
        return Response.json({
          ...ada,
          finished: true,
          pending: null,
          changes: ['Gained Pilot 0'],
          skills: 'Medic 0, Pilot 0',
        });
      return Response.json(
        _url.endsWith('/characters') ? [{ id: 1, name: 'Ada', player: 'Magnus', sophont: 'Humaniti' }] : ada,
      );
    }),
  );
  const screen = await render(CharactersPage);
  await screen.getByRole('button', { name: 'Ada', exact: true }).click();
  await expect.element(screen.getByText('Choose a skill', { exact: true })).toBeVisible();
  await screen.getByRole('button', { name: 'Confirm', exact: true }).click();
  await expect.element(screen.getByText('Gained Pilot 0')).toBeVisible();
  await expect.element(screen.getByText('Medic 0, Pilot 0', { exact: true })).toBeVisible();
  await expect.element(screen.getByRole('button', { name: 'Add to actors' })).toBeVisible();
});
it('explains an unavailable character server and offers retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
  const screen = await render(CharactersPage);
  await expect.element(screen.getByRole('alert')).toHaveTextContent('Character server unavailable');
  await expect.element(screen.getByRole('button', { name: 'Retry' })).toBeVisible();
});

it('automatically lists relocation worlds using the previous location and supplied base filters', async () => {
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/characters'))
      return Response.json([{ id: 1, name: 'Ada', player: 'NPC', sophont: 'Humaniti' }]);
    if (url.includes('/worlds/'))
      return Response.json({
        name: 'Spinward Marches',
        options: { bases: ['S', 'W'] },
        worlds: [
          {
            sector: 'Spinward Marches',
            sector_abbreviation: 'Spin',
            name: 'Regina',
            hex: '1910',
            uwp: 'A788899-C',
            remarks: '',
            distance: 0,
          },
        ],
      });
    if (init?.method === 'POST') return Response.json({ ...ada, homeworld: 'Regina' });
    return Response.json({
      ...ada,
      pending: {
        id: '3.0',
        instruction: 'Select your new homeworld.',
        inputs: [
          { kind: 'InfoText', text: 'Your homeworld must have a Scout base.' },
          {
            kind: 'SelectWorld',
            name: 'homeworld',
            label: 'New homeworld',
            sector_abbreviation: 'Spin',
            reference_world: { sector_abbreviation: 'Spin', hex: '0905' },
            filters: { bases: ['S', 'W'] },
          },
        ],
      },
    });
  });
  vi.stubGlobal('fetch', fetcher);
  const screen = await render(CharactersPage);
  await screen.getByRole('button', { name: 'Ada', exact: true }).click();
  await expect.element(screen.getByText('Your homeworld must have a Scout base.')).toBeVisible();
  await screen.getByRole('button', { name: 'Regina', exact: true }).click();
  const worldRequest = fetcher.mock.calls.find(([url]) => url.includes('/worlds/'));
  expect(worldRequest?.[0]).toBe('/api/worlds/Spin?q=&reference_hex=0905&bases=S&bases=W');
  expect(fetcher).toHaveBeenCalledWith(
    expect.stringContaining('/choices'),
    expect.objectContaining({
      body: JSON.stringify({ fulfills: '3.0', values: { sector: 'Spin', hex_code: '1910' } }),
    }),
  );
});
