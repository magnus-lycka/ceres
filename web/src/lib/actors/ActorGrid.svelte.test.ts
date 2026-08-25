/**
 * The actor grid, rendered in a real browser.
 *
 * SvGrid is a third-party black box, and every defect it has produced here has
 * been one a type checker cannot see: a grid that renders its row count and no
 * cells, a shell reserving a screen of empty space, a footer summing the id
 * column. These are the assertions that catch that class.
 *
 * They are written in the component's own terms — actors in, selected actor
 * out — so they survive a change of grid library rather than pinning the
 * current one.
 */
import { render } from 'vitest-browser-svelte';
import { describe, expect, it, vi } from 'vitest';
import type { Actor } from '$lib/schema/actor';
import ActorGrid from './ActorGrid.svelte';

function actor(id: number, name: string, extra: Partial<Actor> = {}): Actor {
  return {
    id,
    name,
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity: 8,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
    ...extra,
  };
}

const actors = [
  actor(1, 'Rin', { tags: ['pc', 'marduk'] }),
  actor(2, 'Warbot', { kind: 'robot', strength: null, dexterity: null, endurance: null, hits: 20 }),
];

describe('ActorGrid', () => {
  // The `field` / `accessorKey` mix-up renders headers and the right row count
  // with every cell blank, which reads as "the data did not arrive".
  it('shows the actors it was given', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await expect.element(screen.getByText('Warbot')).toBeVisible();
    await expect.element(screen.getByText('Rin')).toBeVisible();
  });

  it('shows each tag as its own chip rather than one run of text', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await expect.element(screen.getByText('pc', { exact: true })).toBeVisible();
    await expect.element(screen.getByText('marduk', { exact: true })).toBeVisible();
  });

  // SvGrid reserves a flat 520px whatever it holds, burying whatever the page
  // puts below the grid under a screen of blank.
  it('fits its shell to the rows rather than reserving a fixed height', async () => {
    const { container } = await render(ActorGrid, { actors, onselect: vi.fn() });
    const shell = container.querySelector('.sv-grid-root') as HTMLElement;
    expect(shell.getBoundingClientRect().height).toBeLessThan(300);
  });

  // The default summary row totals every numeric column: the sum of a set of
  // ids is a number that means nothing.
  it('shows no summary row, because summing ids means nothing', async () => {
    const { container } = await render(ActorGrid, { actors, onselect: vi.fn() });
    expect(container.querySelector('.sv-grid-summary-row')).toBeNull();
  });

  // The page drives Duplicate, Delete and the health panel off this, and must
  // receive an actor rather than a row index.
  it('reports the actor whose row was clicked', async () => {
    const onselect = vi.fn();
    const screen = await render(ActorGrid, { actors, onselect });

    await screen.getByText('Warbot').click();

    expect(onselect).toHaveBeenCalled();
    expect(onselect.mock.calls.at(-1)![0]).toMatchObject({ id: 2, name: 'Warbot' });
  });
});
