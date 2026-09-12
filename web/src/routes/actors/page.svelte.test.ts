/**
 * The actors page against the local library.
 *
 * The layer that kept slipping: the store is well covered and the grid is well
 * covered, but whether a button on this page actually reaches storage was only
 * ever verified by hand — and it once did not.
 *
 * Nothing here touches GitHub. The page writes to IndexedDB and a sync pushes
 * that later, so what this has to prove is that the button reaches the library
 * and that the change is recorded as waiting to go up.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { actorId } from '$lib/schema/actor';
import { library, status } from '$lib/store/session.svelte';
import ActorsPage from './+page.svelte';

const rin = {
  id: actorId(1),
  name: 'Rin',
  kind: 'sophont' as const,
  note: '',
  tags: [],
  strength: 8,
  dexterity: 8,
  endurance: 8,
  hits: null,
  injuries: [],
  criticals: {},
};

const warbot = {
  ...rin,
  id: actorId(2),
  name: 'Warbot',
  kind: 'robot' as const,
  strength: null,
  dexterity: null,
  endurance: null,
  hits: 20,
};

/** The grid cell, not the health panel heading that also carries the name. */
function names(container: HTMLElement): string[] {
  return [...container.querySelectorAll("td[data-col-id='name']")].map((cell) =>
    (cell.textContent ?? '').trim(),
  );
}

beforeEach(async () => {
  for (const actor of await library.actors()) await library.deleteActor(actor.id);
  await library.saveActor(rin);
});

describe('the actors page', () => {
  it('shows what the library holds', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toContain('Rin'));
  });

  // The bug this guards: Delete removed the row from the grid and never told
  // storage, so it came back on reload.
  it('deletes from the library, not just from the screen', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toContain('Rin'));

    (screen.container.querySelector("td[data-col-id='name']") as HTMLElement).click();
    await screen.getByRole('button', { name: 'Delete' }).click();

    await vi.waitFor(async () => expect(await library.actors()).toHaveLength(0));
  });

  it('adds to the library', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toContain('Rin'));

    await screen.getByRole('button', { name: 'Add animal' }).click();

    await vi.waitFor(async () => expect(await library.actors()).toHaveLength(2));
  });

  it('duplicates the selected entity when filtering changes its row index', async () => {
    await library.saveActor(warbot);
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toEqual(['Rin', 'Warbot']));

    screen.container
      .querySelector<HTMLButtonElement>('th[data-svgrid-header-col="name"] .sv-grid-col-filter-btn')
      ?.click();
    await userEvent.fill(screen.getByPlaceholder('Filter value...'), 'War');
    screen.container.querySelector<HTMLElement>('.sv-grid-menu-backdrop')?.click();
    await vi.waitFor(() => expect(names(screen.container)).toEqual(['Warbot']));
    await userEvent.click(screen.getByRole('gridcell', { name: 'Warbot' }));

    await userEvent.click(screen.getByRole('button', { name: 'Duplicate' }));

    await vi.waitFor(async () =>
      expect((await library.actors()).map((actor) => actor.name)).toEqual(['Rin', 'Warbot', 'Warbot 1']),
    );
  });

  it('deletes the selected entity when filtering changes its row index', async () => {
    await library.saveActor(warbot);
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toEqual(['Rin', 'Warbot']));

    screen.container
      .querySelector<HTMLButtonElement>('th[data-svgrid-header-col="name"] .sv-grid-col-filter-btn')
      ?.click();
    await userEvent.fill(screen.getByPlaceholder('Filter value...'), 'War');
    screen.container.querySelector<HTMLElement>('.sv-grid-menu-backdrop')?.click();
    await vi.waitFor(() => expect(names(screen.container)).toEqual(['Warbot']));
    await userEvent.click(screen.getByRole('gridcell', { name: 'Warbot' }));

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await vi.waitFor(async () =>
      expect((await library.actors()).map((actor) => actor.name)).toEqual(['Rin']),
    );
  });

  // The nav indicator is driven by this count, so an edit that does not raise
  // it is an edit that can be lost without warning.
  it('marks the change as waiting to be synced', async () => {
    const screen = await render(ActorsPage);
    await vi.waitFor(() => expect(names(screen.container)).toContain('Rin'));

    await screen.getByRole('button', { name: 'Add robot' }).click();

    await vi.waitFor(() => expect(status.changes).toBeGreaterThan(0));
  });
});
