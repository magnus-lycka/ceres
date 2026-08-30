/**
 * The round table, rendered in a real browser.
 *
 * This is the in-round screen: the order is the turn order, the colours say
 * whose turn it is, and nothing is typed. Setting initiative belongs to the
 * before-round screen and has its own grid and its own test.
 *
 * The colour assertions are here rather than in the rules tests because "green
 * means can act" is a claim about the screen, and the whole reason that channel
 * was reserved was to be able to see whose turn it is at a glance.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { describe, expect, it, vi } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import { act, addActors, emptySituation, setInitiative } from '$lib/rules/rounds/situation';
import SituationGrid from './SituationGrid.svelte';

function actor(id: number, name: string, dexterity = 8): Actor {
  return {
    id: actorId(id),
    name,
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity,
    endurance: 8,
    hits: null,
    injuries: [],
    criticals: {},
  };
}

const rin = actor(1, 'Rin', 9);
const sana = actor(2, 'Sana', 7);
const roster = [rin, sana];

/** Rin on 12, Sana on 4, in a round being played, so the order is settled. */
function fight() {
  const started = {
    ...addActors(emptySituation(), roster, 'Raiders'),
    state: 'current' as const,
    phase: 'round' as const,
  };
  return setInitiative(setInitiative(started, rin.id, 12), sana.id, 4);
}

function show(situation = fight()) {
  return render(SituationGrid, { situation, roster, ondone: vi.fn(), onwait: vi.fn() });
}

/** The rendered rows, top to bottom, by the name in each. */
function names(container: HTMLElement): string[] {
  return [...container.querySelectorAll('tbody tr')].map(
    (row) => row.querySelector('td')?.textContent?.trim() ?? '',
  );
}

const rowFor = (container: HTMLElement, name: string) =>
  [...container.querySelectorAll('tbody tr')].find((row) => row.textContent?.includes(name))!;

describe('SituationGrid', () => {
  it('shows the actors in the fight', async () => {
    const screen = await show();
    await expect.element(screen.getByText('Rin')).toBeVisible();
    await expect.element(screen.getByText('Sana')).toBeVisible();
  });

  it('lists them highest initiative first', async () => {
    const { container } = await show();
    expect(names(container)).toEqual(['Rin', 'Sana']);
  });

  it('shows the party each row belongs to', async () => {
    const screen = await show();
    await expect.element(screen.getByText('Raiders').first()).toBeVisible();
  });

  /**
   * The channel reserved for this. Green is "may act now" and grey is
   * "finished"; the actor the turn has not reached keeps the plain background,
   * because colouring all three states says less than colouring two.
   */
  it('paints the actor whose turn it is green', async () => {
    const { container } = await show();
    expect(rowFor(container, 'Rin').className).toContain('turn-ready');
    expect(rowFor(container, 'Sana').className).toContain('turn-pending');
  });

  it('paints an actor who has acted grey, and passes the turn on', async () => {
    const { container } = await show(act(fight(), rin.id));
    expect(rowFor(container, 'Rin').className).toContain('turn-acted');
    expect(rowFor(container, 'Sana').className).toContain('turn-ready');
  });

  it('reports the actor whose turn was finished', async () => {
    const ondone = vi.fn();
    const screen = await render(SituationGrid, {
      situation: fight(),
      roster,
      ondone,
      onwait: vi.fn(),
    });
    await userEvent.click(screen.getByRole('button', { name: 'Done' }).first());
    expect(ondone).toHaveBeenCalledWith(rin.id);
  });

  it('reports the actor who let the turn pass', async () => {
    const onwait = vi.fn();
    const screen = await render(SituationGrid, {
      situation: fight(),
      roster,
      ondone: vi.fn(),
      onwait,
    });
    await userEvent.click(screen.getByRole('button', { name: 'Wait' }).first());
    expect(onwait).toHaveBeenCalledWith(rin.id);
  });

  // A finished actor should not be offered a turn they no longer have.
  it('stops offering a turn to an actor who has taken theirs', async () => {
    const { container } = await show(act(fight(), rin.id));
    expect(rowFor(container, 'Rin').textContent).not.toContain('Done');
    expect(rowFor(container, 'Sana').textContent).toContain('Done');
  });
});

/**
 * Inside a round nothing is typed. Initiative was settled before it began, and
 * the round table is for acting and reading — which is exactly the difference
 * the separate screen exists to make visible.
 */
describe('nothing is typed in a round', () => {
  it('refuses to edit initiative', async () => {
    const screen = await show();
    const cell = rowFor(screen.container, 'Sana').querySelector<HTMLElement>('td[data-col-id="initiative"]');
    await userEvent.dblClick(cell!);
    expect(cell!.querySelector('input')).toBeNull();
  });

  it('refuses to edit the party', async () => {
    const screen = await show();
    const cell = rowFor(screen.container, 'Sana').querySelector<HTMLElement>('td[data-col-id="party"]');
    await userEvent.dblClick(cell!);
    expect(cell!.querySelector('input')).toBeNull();
  });

  /**
   * The order *is* the turn order. Clicking a header must not reorder it —
   * that would break the one thing this table exists to show, and the
   * before-round screen is where sorting belongs.
   */
  it('does not re-sort when a header is clicked', async () => {
    const screen = await show();
    const header = screen.container.querySelector<HTMLElement>('th[data-svgrid-header-col="name"]');
    await userEvent.click(header!);
    await userEvent.click(header!);
    expect(names(screen.container)).toEqual(['Rin', 'Sana']);
  });
});

/**
 * What the state allows: a plan has not reached its turns, a record is past
 * them.
 */
describe('what the state allows', () => {
  it('offers no turns before the round has begun', async () => {
    const { container } = await show({ ...fight(), phase: 'setup' as const });
    expect(rowFor(container, 'Rin').textContent).not.toContain('Done');
    expect(rowFor(container, 'Rin').textContent).not.toContain('Wait');
  });

  it('offers no turns once the fight is over', async () => {
    const { container } = await show({ ...fight(), state: 'past' as const });
    expect(rowFor(container, 'Rin').textContent).not.toContain('Done');
  });
});

/**
 * Health on the round table, which is most of what makes it worth reading:
 * what each actor is, what is left, and how much of the difference is stun.
 */
describe('health', () => {
  const cell = (container: HTMLElement, name: string, column: string) =>
    rowFor(container, name).querySelector(`td[data-col-id="${column}"]`)?.textContent?.trim();

  const hurt = (injuries: Actor['injuries']) => {
    const wounded = { ...rin, injuries };
    return render(SituationGrid, {
      situation: fight(),
      roster: [wounded, sana],
      ondone: vi.fn(),
      onwait: vi.fn(),
    });
  };

  it('writes a sophont as half a UCP', async () => {
    const { container } = await show();
    expect(cell(container, 'Rin', 'max')).toBe('898');
  });

  it('shows what is left beside it', async () => {
    const { container } = await hurt([{ when: null, kind: 'lethal', reductions: { strength: 4 } }]);
    expect(cell(container, 'Rin', 'max')).toBe('898');
    expect(cell(container, 'Rin', 'now')).toBe('498');
  });

  // Stun and lethal reduce one shared score, so Now alone cannot say how much
  // will come back after an hour's rest.
  it('says how much of the loss is stun', async () => {
    const { container } = await hurt([{ when: null, kind: 'stun', reductions: { endurance: 5 } }]);
    expect(cell(container, 'Rin', 'now')).toBe('893');
    expect(cell(container, 'Rin', 'stun')).toBe('5');
  });

  it('leaves the stun cell empty when there is none', async () => {
    const { container } = await show();
    expect(cell(container, 'Rin', 'stun')).toBe('');
  });

  // Hits is one score with a wide range; writing 12 as `C` would hide it.
  it('writes an actor hurt through Hits as a plain number', async () => {
    const beast: Actor = {
      ...actor(3, 'Wolf', 8),
      kind: 'animal',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      injuries: [{ when: null, kind: 'lethal', reductions: { hits: 6 } }],
    };
    const screen = await render(SituationGrid, {
      situation: addActors(fight(), [beast], 'Beasts'),
      roster: [...roster, beast],
      ondone: vi.fn(),
      onwait: vi.fn(),
    });
    expect(cell(screen.container, 'Wolf', 'max')).toBe('20');
    expect(cell(screen.container, 'Wolf', 'now')).toBe('14');
  });
});
