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
import { userEvent } from '@vitest/browser/context';
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

describe('moving around without a mouse', () => {
  // The panel below the grid follows the cursor. Arrow keys move the cursor
  // just as a click does, so they must report the actor too.
  it('reports the actor when the cursor moves by keyboard', async () => {
    const onselect = vi.fn();
    const screen = await render(ActorGrid, { actors, onselect });
    await screen.getByText('Rin').click();
    onselect.mockClear();

    await userEvent.keyboard('{ArrowDown}');

    expect(onselect.mock.calls.at(-1)?.[0]).toMatchObject({ name: 'Warbot' });
  });

  // SvGrid starts editing on F2 or Space. Needing the mouse to edit a
  // spreadsheet is not a spreadsheet.
  it('opens an editor on F2', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await screen.getByText('Rin').click();

    await userEvent.keyboard('{F2}');

    expect(screen.container.querySelector('.sv-grid-cell input, .sv-grid-cell select')).not.toBeNull();
  });
});

describe('showing where the cursor is', () => {
  // Row background belongs to what an actor is — green "can act", grey
  // "spent" in the Situation grid. The cursor must not claim that channel.
  it('marks the row through the Id cell, not the row background', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await screen.getByText('Warbot').click();

    const row = screen.container.querySelector('tr:has(.sv-grid-cell-active)') as HTMLElement;
    const marker = row.querySelector('td[data-col-id="id"]') as HTMLElement;
    expect(getComputedStyle(marker).backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
    expect(getComputedStyle(row).backgroundColor).toBe('rgba(0, 0, 0, 0)');
  });

  // Excel green is what "can act" has to mean, so the cursor frame is blue.
  it('frames the active cell in blue rather than green', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await screen.getByText('Warbot').click();

    const active = screen.container.querySelector('.sv-grid-cell-active') as HTMLElement;
    expect(getComputedStyle(active).boxShadow).toContain('rgb(26, 115, 232)');
  });
});

describe('arriving on the page', () => {
  // Arrow keys are handled by the grid table, which has to hold DOM focus to
  // receive them. Without this the grid looks ready and ignores every key.
  it('takes the keyboard without being clicked first', async () => {
    const onselect = vi.fn();
    const screen = await render(ActorGrid, { actors, onselect });
    await vi.waitFor(() =>
      expect(document.activeElement).toBe(screen.container.querySelector('.sv-grid-table')),
    );

    await userEvent.keyboard('{ArrowDown}');
    expect(onselect.mock.calls.at(-1)?.[0]).toMatchObject({ name: 'Warbot' });
  });
});

describe('the column marker', () => {
  it('fills the header of the column the cursor is in', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await screen.getByText('Warbot').click();

    const head = screen.container.querySelector('th[data-svgrid-header-col="name"]') as HTMLElement;
    await vi.waitFor(() => expect(getComputedStyle(head).backgroundColor).toBe('rgb(232, 240, 254)'));
  });

  // A spreadsheet tints the rest of a dragged range but leaves the anchor
  // cell plain, so the frame is what marks it.
  it('leaves the active cell itself unfilled', async () => {
    const screen = await render(ActorGrid, { actors, onselect: vi.fn() });
    await screen.getByText('Warbot').click();

    const active = screen.container.querySelector('.sv-grid-cell-active') as HTMLElement;
    expect(getComputedStyle(active).backgroundColor).toBe('rgba(0, 0, 0, 0)');
  });
});
