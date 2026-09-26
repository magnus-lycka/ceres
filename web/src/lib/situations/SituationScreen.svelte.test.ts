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
import { beginRound, newSituation, start } from '$lib/rules/rounds/lifecycle';
import { addActors, setInitiative } from '$lib/rules/rounds/situation';
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
    protection: 0,
    movement: null,
    speed: null,
    enduranceHours: null,
    int: null,
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

/**
 * Put the cursor in a row by its Ini cell, which is the one that cannot read the
 * same as another: a Target cell names someone, and the Name column would then
 * offer two cells with the same text.
 */
async function pickRowByInitiative(container: HTMLElement, name: string) {
  const row = [...container.querySelectorAll<HTMLElement>('td[data-col-id="name"]')]
    .find((td) => td.textContent?.trim() === name)
    ?.closest('tr');
  await userEvent.click(row!.querySelector<HTMLElement>('td[data-col-id="initiative"]')!);
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

    await expect.element(screen.getByLabelText('Name')).toHaveValue('Warehouse');
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

    // The first field of the injury row, which is STR for a sophont.
    await userEvent.fill(screen.container.querySelector<HTMLInputElement>('tr.add input')!, '2');
    await screen.getByRole('button', { name: 'Add injury' }).click();

    await vi.waitFor(async () => {
      const [rin] = await library.actors();
      expect(rin.injuries).toEqual([{ when: null, kind: 'lethal', reductions: { strength: 2 } }]);
    });
  });

  it('stores a corrected Protection', async () => {
    const screen = await open('round');
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    await pickRow(screen.container, 'Rin');

    await screen.getByLabelText('Protection').fill('3');
    await userEvent.tab();

    await vi.waitFor(async () => expect((await library.actors())[0].protection).toBe(3));
  });
});

/** A fight already in its first round, the actors acting in the order given. */
async function fight(...specs: [Actor, number][]) {
  const actors: Actor[] = [];
  for (const [who] of specs) actors.push(await library.saveActor(who));
  let situation = addActors(newSituation('Fight'), actors, 'Everyone', new Set());
  specs.forEach(([, initiative], index) => {
    situation = setInitiative(situation, actors[index].id, initiative);
  });
  const started = start(situation, []);
  if (!started.ok) throw new Error('could not start the fight');
  const stored = await library.saveSituation(beginRound(started.situation));
  const screen = await render(SituationScreen, { id: stored.id });
  await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
  return { screen, actors, situation: stored };
}

/**
 * The attack is entered from the Target cell of whoever may act: the dialog
 * takes what the referee rolled, and the screen does the arithmetic.
 */
describe('attacking', () => {
  it('opens an attack from the Target cell of the actor whose turn it is', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();

    await expect.element(screen.getByRole('dialog', { name: 'Attack' })).toBeVisible();
  });

  it('stores the damage, spends the turn, and shows who was gone for', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Target').selectOptions('Guard');
    await dialog.getByLabelText('Effect').fill('2');
    await dialog.getByLabelText('Damage roll').fill('7');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
      expect(guard.injuries).toEqual([
        { when: 1, kind: 'lethal', reductions: { endurance: 8, dexterity: 1 } },
      ]);
      const [stored] = await library.situations();
      expect(stored.members.find((member) => member.target !== null)?.acted).toBe(true);
    });
    await expect.element(screen.getByRole('dialog')).not.toBeInTheDocument();
    await expect.element(screen.getByText('Guard', { exact: true }).first()).toBeVisible();
  });

  // Only whoever's turn it is may go for someone; the rest are waiting their step.
  it('offers the attack to the actor whose turn it is and to nobody else', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await expect.element(screen.getByRole('button', { name: 'Rex attacks' })).toBeVisible();
    await expect.element(screen.getByRole('button', { name: 'Guard attacks' })).not.toBeInTheDocument();
  });

  it('records a miss as an attack on the target that hurts no one', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Effect').fill('-1');
    await dialog.getByLabelText('Damage roll').fill('12');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const [stored] = await library.situations();
      expect(stored.members.some((member) => member.target !== null && member.acted)).toBe(true);
    });
    const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
    expect(guard.injuries).toEqual([]);
  });

  // "Your previous target will be preselected", and the referee changes it only
  // when it changes. It has to survive the round turning.
  it('starts the next attack from the last target, even a round later', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8], [sophont('Sana'), 4]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const first = screen.getByRole('dialog', { name: 'Attack' });
    await first.getByLabelText('Target').selectOptions('Sana');
    await first.getByLabelText('Effect').fill('-1');
    await first.getByRole('button', { name: 'Apply' }).click();
    await expect.element(screen.getByRole('dialog')).not.toBeInTheDocument();

    await screen.getByRole('button', { name: 'Finish round' }).click();
    await screen.getByRole('button', { name: 'Begin round 2' }).click();
    await screen.getByRole('button', { name: 'Rex attacks' }).click();

    await expect
      .element(screen.getByRole('dialog', { name: 'Attack' }).getByLabelText('Target'))
      .toHaveDisplayValue('Sana');
  });

  it('takes off the Protection the target wears, and shows it', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), protection: 3 }, 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await expect.element(dialog.getByLabelText('Protection')).toHaveValue(3);
    await dialog.getByLabelText('Effect').fill('0');
    await dialog.getByLabelText('Damage roll').fill('7');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
      expect(guard.injuries[0].reductions).toEqual({ endurance: 4 });
    });
  });

  it('does not offer the attacker as their own target', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();

    const targets = screen.getByRole('dialog', { name: 'Attack' }).getByLabelText('Target').element();
    const options = [...targets.querySelectorAll('option')].map((o) => o.textContent?.trim());
    expect(options).toEqual(['Guard']);
  });

  // Cover, a called shot: one number overtyped, for this attack only.
  it('uses the Protection typed for this attack instead of the one worn', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), protection: 3 }, 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Effect').fill('0');
    await dialog.getByLabelText('Damage roll').fill('7');
    await dialog.getByLabelText('Protection').fill('7');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () =>
      expect((await library.situations())[0].members.some((m) => m.acted)).toBe(true),
    );
    const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
    expect(guard.injuries).toEqual([]);
    expect(guard.protection).toBe(3);
  });

  it('ignores as much of the Protection as the weapon has AP', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), protection: 3 }, 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Effect').fill('0');
    await dialog.getByLabelText('Damage roll').fill('7');
    await dialog.getByLabelText('AP').fill('2');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
      expect(guard.injuries[0].reductions).toEqual({ endurance: 6 });
    });
  });

  // "target's choice of which" (:264): the referee asks, so the dialog does.
  it('puts the excess on the characteristic the target chooses', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Effect').fill('0');
    await dialog.getByLabelText('Damage roll').fill('11');
    await dialog.getByLabelText('Excess to').selectOptions('STR');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
      expect(guard.injuries[0].reductions).toEqual({ endurance: 8, strength: 3 });
    });
  });

  // Something hurt through Hits has no STR or DEX to choose between.
  it('does not ask an animal which characteristic takes the excess', async () => {
    const wolf: Actor = {
      ...sophont('Wolf'),
      kind: 'animal',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 12,
    };
    const { screen } = await fight([sophont('Rex'), 12], [wolf, 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();

    await expect.element(screen.getByRole('dialog', { name: 'Attack' })).toBeVisible();
    await expect.element(screen.getByLabelText('Excess to')).not.toBeInTheDocument();
  });

  it('changes nothing when cancelled', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Damage roll').fill('9');
    await dialog.getByRole('button', { name: 'Cancel' }).click();

    await expect.element(screen.getByRole('dialog')).not.toBeInTheDocument();
    const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
    expect(guard.injuries).toEqual([]);
    expect((await library.situations())[0].members.some((member) => member.acted)).toBe(false);
    await expect.element(screen.getByRole('button', { name: 'Rex attacks' })).toBeVisible();
  });

  // Stun: END only, and what END cannot take is the rounds out (:366).
  it('puts a target out with a Stun weapon, and says for how long', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Effect').fill('0');
    await dialog.getByLabelText('Damage roll').fill('10');
    await dialog.getByLabelText('Stun').click();
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await vi.waitFor(async () => {
      const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
      expect(guard.injuries).toEqual([{ when: 1, kind: 'stun', reductions: { endurance: 8 } }]);
    });
    // Out for this round and the next, and not offered anything to do.
    await expect.element(screen.getByText('out 2')).toBeVisible();
    await expect.element(screen.getByRole('button', { name: 'Guard attacks' })).not.toBeInTheDocument();
    await expect.element(screen.getByText(/Everyone has acted/)).toBeVisible();
  });

  it('counts the stun down as the rounds turn, and gives the turn back', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);
    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Damage roll').fill('10');
    await dialog.getByLabelText('Stun').click();
    await dialog.getByRole('button', { name: 'Apply' }).click();
    await expect.element(screen.getByText('out 2')).toBeVisible();

    await screen.getByRole('button', { name: 'Finish round' }).click();
    await screen.getByRole('button', { name: 'Begin round 2' }).click();
    await expect.element(screen.getByText('out 1')).toBeVisible();

    await screen.getByRole('button', { name: 'Finish round' }).click();
    await screen.getByRole('button', { name: 'Begin round 3' }).click();
    await expect.element(screen.getByText(/^out/)).not.toBeInTheDocument();
    await vi.waitFor(() => expect(hasTurnButtons(screen.container)).toBe(true));
    // Both of them are owed a turn again, Guard included.
    expect(screen.container.querySelectorAll('tbody button').length).toBeGreaterThanOrEqual(4);
  });

  // Nothing about a lethal hit needs stun: an actor knocked out cannot act, and
  // the table says so rather than offering them a turn.
  it('shows an actor who has been knocked out as out of action', async () => {
    const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

    await screen.getByRole('button', { name: 'Rex attacks' }).click();
    const dialog = screen.getByRole('dialog', { name: 'Attack' });
    await dialog.getByLabelText('Damage roll').fill('20');
    await dialog.getByRole('button', { name: 'Apply' }).click();

    await expect.element(screen.getByText('out', { exact: true })).toBeVisible();
    await expect.element(screen.getByRole('button', { name: 'Guard attacks' })).not.toBeInTheDocument();
  });

  describe('weapon traits', () => {
    const warbot: Actor = {
      ...sophont('Warbot'),
      kind: 'robot',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      protection: 8,
    };

    // Doubled by a Shotgun: shown, and said, so it cannot be silently wrong.
    it('doubles the Protection shown for a Shotgun, says why, and uses it', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), protection: 3 }, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = screen.getByRole('dialog', { name: 'Attack' });
      await dialog.getByLabelText('Shotgun').click();
      await expect.element(dialog.getByLabelText('Protection')).toHaveValue(6);
      await expect.element(dialog.getByText(/doubled/)).toBeVisible();
      await dialog.getByLabelText('Damage roll').fill('12');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await vi.waitFor(async () => {
        const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
        expect(guard.injuries[0].reductions).toEqual({ endurance: 6 });
      });
    });

    it('halves a robot’s Protection for a stunner, and says why', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [warbot, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = screen.getByRole('dialog', { name: 'Attack' });
      await expect.element(dialog.getByLabelText('Protection')).toHaveValue(8);
      await dialog.getByLabelText('Stun').click();

      await expect.element(dialog.getByLabelText('Protection')).toHaveValue(4);
      await expect.element(dialog.getByText(/halved/)).toBeVisible();
    });

    it('takes what is typed over any trait', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), protection: 3 }, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = screen.getByRole('dialog', { name: 'Attack' });
      await dialog.getByLabelText('Shotgun').click();
      await dialog.getByLabelText('Protection').fill('1');
      // What was typed stays, and the reason for the computed number goes.
      await expect.element(dialog.getByLabelText('Protection')).toHaveValue(1);
      await expect.element(dialog.getByText(/doubled/)).not.toBeInTheDocument();
      // Changing a trait afterwards must not overwrite what the referee typed.
      await dialog.getByLabelText('Shotgun').click();
      await expect.element(dialog.getByLabelText('Protection')).toHaveValue(1);
      await dialog.getByLabelText('Shotgun').click();
      await dialog.getByLabelText('Damage roll').fill('12');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await vi.waitFor(async () => {
        const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
        expect(guard.injuries[0].reductions).toEqual({ endurance: 8, dexterity: 3 });
      });
    });
  });

  /**
   * The reaction is chosen before the roll, so what it costs the attacker is
   * in front of the referee when they roll. The table is a reminder: the Effect
   * typed afterwards already includes it, and nothing here changes it.
   */
  describe('reactions', () => {
    const options = (dialog: ReturnType<typeof attackDialog>) =>
      [...dialog.getByLabelText('Reaction').element().querySelectorAll('option')].map((o) =>
        o.textContent?.trim(),
      );
    const attackDialog = (screen: Awaited<ReturnType<typeof fight>>['screen']) =>
      screen.getByRole('dialog', { name: 'Attack' });

    it('offers the reactions the attack allows, which depend on whether it is melee or ranged', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      expect(options(dialog)).toEqual(['—', 'Dodge', 'Dive for cover']);

      await dialog.getByLabelText('Melee').click();
      expect(options(dialog)).toEqual(['—', 'Dodge', 'Parry']);
    });

    it('shows what a Dodge costs the attacker, from the target’s DEX', async () => {
      const guard = { ...sophont('Guard'), dexterity: 12 };
      const { screen } = await fight([sophont('Rex'), 12], [guard, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');

      await expect.element(dialog.getByText('Dodge (DEX DM)')).toBeVisible();
      await expect.element(dialog.getByText('−2', { exact: true }).first()).toBeVisible();
    });

    // No DEX in the model for a robot: the reminder says it does not know.
    it('says a DM is unknown for a target with no DEX, and that the total is not the whole of it', async () => {
      const warbot: Actor = {
        ...sophont('Warbot'),
        kind: 'robot',
        strength: null,
        dexterity: null,
        endurance: null,
        hits: 20,
      };
      const { screen } = await fight([sophont('Rex'), 12], [warbot, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');

      await expect.element(dialog.getByText('?', { exact: true }).first()).toBeVisible();
      await expect.element(dialog.getByText(/Not every DM is known/)).toBeVisible();
    });

    it('says a Shotgun ignores a Dodge', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), dexterity: 12 }, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');
      await dialog.getByLabelText('Shotgun').click();

      await expect.element(dialog.getByText('Dodge (ignored by a Shotgun)')).toBeVisible();
    });

    it('drops a reaction the attack no longer allows when it turns melee', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dive for cover');
      await expect.element(dialog.getByText('Dive for cover', { exact: true }).nth(1)).toBeVisible();

      await dialog.getByLabelText('Melee').click();

      await expect.element(dialog.getByLabelText('Reaction')).toHaveValue('');
      await expect.element(dialog.getByRole('table')).not.toBeInTheDocument();
    });

    // The point of it being a reminder: the Effect typed already has it in.
    it('never changes the damage: the Effect typed is the Effect used', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), dexterity: 12 }, 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');
      await dialog.getByLabelText('Effect').fill('0');
      await dialog.getByLabelText('Damage roll').fill('7');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await vi.waitFor(async () => {
        const guard = (await library.actors()).find((actor) => actor.name === 'Guard')!;
        expect(guard.injuries[0].reductions).toEqual({ endurance: 7 });
      });
    });

    // The cost lands on the defender, and it shows where they take their turn.
    it('puts the penalty on the defender’s row when a Dodge is applied', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await vi.waitFor(async () => {
        const [stored] = await library.situations();
        expect(stored.members.map((member) => member.reactions)).toContain(1);
      });
      await expect.element(screen.getByText('DM−1')).toBeVisible();
    });

    it('is spent when the defender acts', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);
      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();
      await expect.element(screen.getByText('DM−1')).toBeVisible();

      await screen.getByRole('button', { name: 'Done' }).click();

      await expect.element(screen.getByText('DM−1')).not.toBeInTheDocument();
    });

    // Already acted: the reaction costs next round's actions, and says so.
    it('is carried to next round for a defender who has already acted', async () => {
      const { screen } = await fight([sophont('Guard'), 12], [sophont('Rex'), 8]);
      await screen.getByRole('button', { name: 'Done' }).first().click();
      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Target').selectOptions('Guard');
      await dialog.getByLabelText('Reaction').selectOptions('Dodge');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await expect.element(screen.getByText(/next DM−1/)).toBeVisible();
    });

    // The other half of the same rule: what a reaction cost the defender is a DM
    // on their own roll, and it is in front of them when they make it.
    it('reminds someone who has reacted that it costs them on their own roll', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);
      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const first = attackDialog(screen);
      await first.getByLabelText('Reaction').selectOptions('Dodge');
      await first.getByLabelText('Effect').fill('-1');
      await first.getByRole('button', { name: 'Apply' }).click();

      await screen.getByRole('button', { name: 'Guard attacks' }).click();

      const second = attackDialog(screen);
      await expect.element(second.getByText('Your reactions')).toBeVisible();
      await expect.element(second.getByText('−1', { exact: true }).first()).toBeVisible();
    });

    // Diving for cover is not a penalty but a change of state: down, and out of
    // the round they had not yet used.
    it('puts a target who dives for cover on the ground and takes their turn', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dive for cover');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await expect.element(screen.getByRole('button', { name: 'Clear prone for Guard' })).toBeVisible();
      await vi.waitFor(async () => {
        const [stored] = await library.situations();
        expect(stored.members.flatMap((member) => member.conditions)).toEqual(['prone']);
        expect(stored.members.every((member) => member.acted)).toBe(true);
      });
      await expect.element(screen.getByText(/Everyone has acted/)).toBeVisible();
    });

    // Getting up is a Minor Action nobody tracks: it is the referee who says so.
    it('clears prone when the referee says the actor has got up', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [sophont('Guard'), 8]);
      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dive for cover');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await screen.getByRole('button', { name: 'Clear prone for Guard' }).click();

      await vi.waitFor(async () => {
        const [stored] = await library.situations();
        expect(stored.members.flatMap((member) => member.conditions)).toEqual([]);
      });
      await expect
        .element(screen.getByRole('button', { name: 'Clear prone for Guard' }))
        .not.toBeInTheDocument();
    });

    // "Prone Target -1": every attack on someone on the ground, not only the one
    // they dived from.
    it('reminds the next attacker that a prone target costs them DM-1', async () => {
      const { screen } = await fight([sophont('Guard'), 12], [sophont('Rex'), 8], [sophont('Sana'), 4]);
      await screen.getByRole('button', { name: 'Guard attacks' }).click();
      const first = attackDialog(screen);
      await first.getByLabelText('Target').selectOptions('Sana');
      await first.getByLabelText('Reaction').selectOptions('Dive for cover');
      await first.getByLabelText('Effect').fill('-1');
      await first.getByRole('button', { name: 'Apply' }).click();

      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const second = attackDialog(screen);
      await second.getByLabelText('Target').selectOptions('Sana');

      await expect.element(second.getByText('Prone target')).toBeVisible();
    });

    it('shows a prone actor’s Movement as it is on the ground in the detail panel', async () => {
      const { screen } = await fight([sophont('Rex'), 12], [{ ...sophont('Guard'), movement: 6 }, 8]);
      await screen.getByRole('button', { name: 'Rex attacks' }).click();
      const dialog = attackDialog(screen);
      await dialog.getByLabelText('Reaction').selectOptions('Dive for cover');
      await dialog.getByLabelText('Effect').fill('-1');
      await dialog.getByRole('button', { name: 'Apply' }).click();

      await pickRowByInitiative(screen.container, 'Guard');

      await expect.element(screen.getByText('prone: 1.5 m')).toBeVisible();
    });
  });
});
