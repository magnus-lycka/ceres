/**
 * The situation list against the local library.
 *
 * The list is a way to get to a situation, and nothing else. What happens on
 * a situation's own screen is covered beside that screen.
 */
import { render } from 'vitest-browser-svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { goto } from '$app/navigation';
import { newSituation } from '$lib/rules/rounds/lifecycle';
import { library } from '$lib/store/session.svelte';
import SituationPage from './+page.svelte';

// The router is the boundary: what matters is where the page sends you.
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

beforeEach(async () => {
  vi.mocked(goto).mockClear();
  for (const situation of await library.situations()) await library.deleteSituation(situation.id);
});

/** Each one is a real link, so it can be opened in its own tab. */
describe('the situation list', () => {
  it('links each situation to its own page', async () => {
    const warehouse = await library.saveSituation(newSituation('Warehouse'));
    const arrest = await library.saveSituation(newSituation('Robot Arrest'));

    const screen = await render(SituationPage);

    await expect
      .element(screen.getByRole('link', { name: /Warehouse/ }))
      .toHaveAttribute('href', `/situation/${warehouse.id}`);
    await expect
      .element(screen.getByRole('link', { name: /Robot Arrest/ }))
      .toHaveAttribute('href', `/situation/${arrest.id}`);
  });
});

describe('starting a new situation', () => {
  it('stores it and leads to its own page rather than opening it in the list', async () => {
    const screen = await render(SituationPage);

    await screen.getByRole('button', { name: 'New situation' }).click();

    await vi.waitFor(async () => expect(await library.situations()).toHaveLength(1));
    const [created] = await library.situations();
    await vi.waitFor(() => expect(goto).toHaveBeenCalledWith(`/situation/${created.id}`));
    await expect.element(screen.getByRole('button', { name: 'Add actor' })).not.toBeInTheDocument();
  });
});
