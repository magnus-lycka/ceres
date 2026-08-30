/**
 * The situation page against the local library.
 *
 * What matters here is which table is on screen and when it changes. The round
 * table is not only where turns are entered — it is where the referee reads
 * what has happened — so it must never be taken away by anything except an
 * explicit press. A round completing is the moment that reading matters most.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { actorId, UNSAVED, type Actor } from '$lib/schema/actor';
import { library } from '$lib/store/session.svelte';
import SituationPage from './+page.svelte';

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
  const screen = await render(SituationPage);
  await screen.getByRole('button', { name: 'New situation' }).click();
  await vi.waitFor(async () => expect(await library.situations()).toHaveLength(1));
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

describe('the situation page', () => {
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
    await expect.element(screen.getByText('Rin')).toBeVisible();
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
    const screen = await render(SituationPage);
    await screen.getByRole('button', { name: 'New situation' }).click();
    await vi.waitFor(async () => expect(await library.situations()).toHaveLength(1));
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
