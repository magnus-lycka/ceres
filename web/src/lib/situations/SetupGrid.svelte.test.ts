/**
 * The before-round table, rendered in a real browser.
 *
 * A different job from the round table and deliberately a different grid: here
 * you sort, type down a column and paste a block in from a spreadsheet, which
 * is how initiative has always been set. There, the order is the turn order and
 * nothing is typed at all.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { describe, expect, it, vi } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import { addActors, emptySituation, setInitiative } from '$lib/rules/rounds/situation';
import SetupGrid from './SetupGrid.svelte';

function actor(id: number, name: string): Actor {
  return {
    id: actorId(id),
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
  };
}

const rin = actor(1, 'Rin');
const sana = actor(2, 'Sana');
const roster = [rin, sana];

/** A fight being set up, before its first round. */
const setup = () => ({
  ...addActors(emptySituation(), roster, 'Raiders'),
  state: 'current' as const,
  phase: 'setup' as const,
});

function show(props: Record<string, unknown> = {}) {
  return render(SetupGrid, {
    situation: setup(),
    roster,
    oninitiative: vi.fn(),
    onparty: vi.fn(),
    ...props,
  });
}

const rowFor = (container: HTMLElement, name: string) =>
  [...container.querySelectorAll('tbody tr')].find((row) => row.textContent?.includes(name))!;

describe('SetupGrid', () => {
  it('shows who is in the fight', async () => {
    const screen = await show();
    await expect.element(screen.getByText('Rin')).toBeVisible();
    await expect.element(screen.getByText('Sana')).toBeVisible();
  });

  /**
   * Actor names are not unique — ten chickens may all be called Chicken — so a
   * row has to be tellable from its twin.
   */
  it('shows the id, since two actors may share a name', async () => {
    const { container } = await show();
    expect(rowFor(container, 'Rin').querySelector('td[data-col-id="id"]')?.textContent).toContain('1');
  });

  it('takes an initiative typed into a row', async () => {
    const oninitiative = vi.fn();
    const screen = await show({ oninitiative });
    const cell = rowFor(screen.container, 'Sana').querySelector<HTMLElement>('td[data-col-id="initiative"]');
    await userEvent.dblClick(cell!);
    await userEvent.fill(screen.getByRole('spinbutton'), '15');
    await userEvent.keyboard('{Enter}');
    expect(oninitiative).toHaveBeenCalledWith(sana.id, 15);
  });

  it('takes a row moved to another side', async () => {
    const onparty = vi.fn();
    const screen = await show({ onparty });
    const cell = rowFor(screen.container, 'Sana').querySelector<HTMLElement>('td[data-col-id="party"]');
    await userEvent.dblClick(cell!);
    await userEvent.fill(screen.getByRole('textbox'), 'Guards');
    await userEvent.keyboard('{Enter}');
    expect(onparty).toHaveBeenCalledWith(sana.id, 'Guards');
  });

  // Sorting is the referee's here — by party to set a side's initiative
  // together, by name to find someone. The round table is where order is fixed.
  it('lets the referee sort it', async () => {
    const { container } = await show();
    expect(container.querySelector('th button')).not.toBeNull();
  });

  /**
   * One initiative for a whole side, by copy and paste — the case that used to
   * have a control of its own, and the reason a spreadsheet was used for this
   * before there was an app.
   *
   * SvGrid's paste never fires `onCellValueChange`, so without the workaround
   * in `$lib/grid/pasted` the values would show and reach the situation never.
   */
  it('reports every row a range paste filled', async () => {
    const oninitiative = vi.fn();
    const screen = await show({ oninitiative });

    const cellIn = (name: string) =>
      rowFor(screen.container, name).querySelector<HTMLElement>('td[data-col-id="initiative"]')!;

    // The clipboard cannot be written to from a test, so stand in for it at
    // the point SvGrid reads: everything after `readText` is the real path.
    vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue('7');

    await userEvent.click(cellIn('Rin'));
    await userEvent.keyboard('{Shift>}{ArrowDown}{/Shift}');
    await userEvent.keyboard('{Meta>}v{/Meta}');

    await vi.waitFor(() => {
      expect(oninitiative).toHaveBeenCalledWith(rin.id, 7);
      expect(oninitiative).toHaveBeenCalledWith(sana.id, 7);
    });
  });

  // Order is the referee's to choose, so it must not be imposed. Initiative
  // typed in does not reshuffle the rows under whoever is typing.
  it('keeps the rows where they are as initiative is typed', async () => {
    const ready = setInitiative(setup(), sana.id, 20);
    const { container } = await show({ situation: ready });
    expect(
      [...container.querySelectorAll('tbody tr')].map((row) =>
        row.querySelector('td[data-col-id="name"]')?.textContent?.trim(),
      ),
    ).toEqual(['Rin', 'Sana']);
  });
});

/**
 * Removing is done from the page, on the row the cursor is in — the same way
 * Delete works on the Actors page. The grid's part is to say which row that is.
 */
describe('saying which row the cursor is in', () => {
  it('reports the actor when a row is clicked', async () => {
    const onselect = vi.fn();
    const screen = await show({ onselect });
    await userEvent.click(
      rowFor(screen.container, 'Sana').querySelector<HTMLElement>('td[data-col-id="name"]')!,
    );
    expect(onselect).toHaveBeenCalledWith(sana.id);
  });

  // Row indices are the grid's currency and stop at this boundary: the page is
  // told which actor, never which row.
  it('reports the actor rather than the row it happens to sit in', async () => {
    const onselect = vi.fn();
    const screen = await show({ onselect });
    await userEvent.click(
      rowFor(screen.container, 'Rin').querySelector<HTMLElement>('td[data-col-id="name"]')!,
    );
    expect(onselect).toHaveBeenCalledWith(rin.id);
    expect(onselect).not.toHaveBeenCalledWith(0);
  });
});
