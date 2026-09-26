/**
 * One situation on a screen of its own.
 *
 * Reached by a link from the list, so it can be opened in a tab, and showing
 * nothing but that situation: mid-fight the other situations are noise.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { actorId, UNSAVED, type Actor } from '$lib/schema/actor';
import { newSituation } from '$lib/rules/rounds/lifecycle';
import { library } from '$lib/store/session.svelte';
import SituationScreen from './SituationScreen.svelte';

function sophont(name: string): Actor {
  return {
    id: actorId(UNSAVED),
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

beforeEach(async () => {
  for (const situation of await library.situations()) await library.deleteSituation(situation.id);
  for (const actor of await library.actors()) await library.deleteActor(actor.id);
  await library.saveActor(sophont('Rin'));
});

/** A fight with one actor in it, opened, and taken as far as `phase`. */
async function open(phase: 'setup' | 'round') {
  const fight = await library.saveSituation(newSituation('Fight'));
  const screen = await render(SituationScreen, { id: fight.id });
  await screen.getByRole('combobox').last().selectOptions('Rin');
  await screen.getByRole('button', { name: 'Add actor' }).click();
  await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(1));
  await screen.getByRole('button', { name: 'Start' }).click();
  await vi.waitFor(async () => expect((await library.situations())[0].state).toBe('current'));
  if (phase === 'round') {
    await screen.getByRole('button', { name: 'Begin round 1' }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].phase).toBe('round'));
  }
  return screen;
}

/** Put the cursor in a row, the way clicking a name cell does. */
async function pickRow(container: HTMLElement, name: string) {
  const cell = [...container.querySelectorAll<HTMLElement>('td[data-col-id="name"]')].find(
    (td) => td.textContent?.trim() === name,
  );
  await userEvent.click(cell!);
}

const hasTurnButtons = (container: HTMLElement) =>
  [...container.querySelectorAll('tbody button')].some((b) => b.textContent?.trim() === 'Done');

describe('running a situation', () => {
  it('sets up before the first round rather than starting in it', async () => {
    const screen = await open('setup');
    await expect.element(screen.getByText(/Before round 1/)).toBeVisible();
    expect(hasTurnButtons(screen.container)).toBe(false);
  });

  it('shows the round table once the round is begun', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
  });

  /**
   * The point of the explicit press. When the last actor finishes, the table
   * has to stay exactly where it is: it is the record of the round that just
   * happened, and reading it is half of what it is for.
   */
  it('keeps the round table up after everyone has acted', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await screen.getByRole('button', { name: 'Done' }).first().click();

    await vi.waitFor(async () => expect((await library.situations())[0].members[0].acted).toBe(true));
    // Still the round table: the actor's row is there, marked as finished.
    await expect.element(screen.getByText('Rin', { exact: true })).toBeVisible();
    await expect.element(screen.getByText(/Everyone has acted/)).toBeVisible();
    await expect.element(screen.getByRole('button', { name: 'Finish round' })).toBeVisible();
  });

  it('only leaves the round when the referee says so', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await screen.getByRole('button', { name: 'Done' }).first().click();
    await vi.waitFor(async () => expect((await library.situations())[0].members[0].acted).toBe(true));
    expect((await library.situations())[0].phase).toBe('round');

    await screen.getByRole('button', { name: 'Finish round' }).click();
    await vi.waitFor(async () => {
      const stored = (await library.situations())[0];
      expect(stored.phase).toBe('setup');
      expect(stored.round).toBe(2);
    });
    await expect.element(screen.getByText(/Before round 2/)).toBeVisible();
  });
});

/**
 * Adding actors and taking them out again are two halves of the same job, so
 * both belong to the before/between-round table.
 */
describe('removing an actor from a situation', () => {
  it('offers nothing to remove until a row is picked', async () => {
    const fight = await library.saveSituation(newSituation('Fight'));
    const screen = await render(SituationScreen, { id: fight.id });
    await expect.element(screen.getByRole('button', { name: 'Remove' })).toBeDisabled();
  });

  it('takes the actor out of the situation, and stores that', async () => {
    const screen = await open('setup');
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(1));
    await pickRow(screen.container, 'Rin');
    await screen.getByRole('button', { name: /Remove Rin/ }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(0));
  });

  // Removing from a fight is not removing from the library: the actor and
  // everything that has happened to it are untouched.
  it('leaves the actor in the library', async () => {
    const screen = await open('setup');
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(1));
    await pickRow(screen.container, 'Rin');
    await screen.getByRole('button', { name: /Remove Rin/ }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(0));
    expect((await library.actors()).map((actor) => actor.name)).toContain('Rin');
  });

  // Withdrawing frees the seat, so the same actor can be brought back.
  it('offers the actor again once they are out', async () => {
    const screen = await open('setup');
    await pickRow(screen.container, 'Rin');
    await screen.getByRole('button', { name: /Remove Rin/ }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(0));
    await screen.getByRole('combobox').last().selectOptions('Rin');
    await screen.getByRole('button', { name: 'Add actor' }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].members).toHaveLength(1));
  });
});

/**
 * Who is in the fight is settled between rounds, never inside one.
 *
 * A round is six seconds; someone arriving can wait for it. The reason this
 * had to go is concrete: a row added mid-round arrived with no party and no
 * initiative, and the round table has no way to give it either.
 */
describe('membership is decided between rounds', () => {
  it('offers no way to add or remove inside a round', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    expect(screen.container.querySelector('select')).toBeNull();
    expect([...screen.container.querySelectorAll('button')].map((b) => b.textContent?.trim())).not.toContain(
      'Add actor',
    );
  });

  it('offers them again once the round is finished', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await screen.getByRole('button', { name: 'Finish round' }).click();
    await vi.waitFor(async () => expect((await library.situations())[0].phase).toBe('setup'));
    await expect.element(screen.getByRole('button', { name: 'Add actor' })).toBeVisible();
  });
});

describe('a situation screen', () => {
  it('shows the situation it was given and none of the others', async () => {
    const warehouse = await library.saveSituation(newSituation('Warehouse'));
    await library.saveSituation(newSituation('Robot Arrest'));

    const screen = await render(SituationScreen, { id: warehouse.id });

    await expect.element(screen.getByRole('heading', { name: 'Warehouse' })).toBeVisible();
    await expect.element(screen.getByText('Robot Arrest')).not.toBeInTheDocument();
  });

  it('leads back to the list', async () => {
    const warehouse = await library.saveSituation(newSituation('Warehouse'));

    const screen = await render(SituationScreen, { id: warehouse.id });

    await expect
      .element(screen.getByRole('link', { name: 'Situations' }))
      .toHaveAttribute('href', '/situation');
  });
});

/**
 * Whoever the cursor is on gets their details beside the table, so what is
 * wrong with them can be read and corrected without leaving the fight.
 */
describe('the detail panel', () => {
  it('shows nothing until a row is picked', async () => {
    const screen = await open('setup');
    await expect.element(screen.getByRole('heading', { name: /Health/ })).not.toBeInTheDocument();
  });

  it('shows the actor whose row is picked, before the round', async () => {
    const screen = await open('setup');
    await pickRow(screen.container, 'Rin');
    await expect.element(screen.getByRole('heading', { name: 'Health — Rin' })).toBeVisible();
  });

  it('shows the actor whose row is picked, during the round', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await pickRow(screen.container, 'Rin');
    await expect.element(screen.getByRole('heading', { name: 'Health — Rin' })).toBeVisible();
  });

  // The point of having it here: the fight is when you notice the wrong number.
  it('stores what is corrected in it', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await pickRow(screen.container, 'Rin');
    await expect.element(screen.getByRole('heading', { name: 'Health — Rin' })).toBeVisible();

    await screen.getByRole('spinbutton').first().fill('2');
    await screen.getByRole('button', { name: 'Add injury' }).click();

    await vi.waitFor(async () => {
      const [rin] = await library.actors();
      expect(rin.injuries).toEqual([{ when: null, kind: 'lethal', reductions: { strength: 2 } }]);
    });
  });
});
