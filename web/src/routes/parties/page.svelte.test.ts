/**
 * The parties page against the local library.
 *
 * What matters here is the reference model: a party points at actors, those
 * actors can be deleted underneath it, and the screen has to say so rather
 * than quietly closing the gap.
 */
import { render } from 'vitest-browser-svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { actorId, partyId, UNSAVED, type Actor } from '$lib/schema/actor';
import { library } from '$lib/store/session.svelte';
import PartiesPage from './+page.svelte';

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

function rows(container: HTMLElement): string[] {
  return [...container.querySelectorAll('section tbody tr')].map((row) =>
    (row.textContent ?? '').replace(/\s+/g, ' ').trim(),
  );
}

let rin: Actor;
let sana: Actor;

beforeEach(async () => {
  for (const party of await library.parties()) await library.deleteParty(party.id);
  for (const actor of await library.actors()) await library.deleteActor(actor.id);
  rin = await library.saveActor(sophont('Rin'));
  sana = await library.saveActor(sophont('Sana'));
});

describe('the parties page', () => {
  it('shows what the library holds', async () => {
    await library.saveParty({
      id: partyId(UNSAVED),
      name: 'The crew',
      note: '',
      tags: [],
      actors: [rin.id],
    });
    const screen = await render(PartiesPage);
    await vi.waitFor(() =>
      expect(
        [...screen.container.querySelectorAll("td[data-col-id='name']")].map((c) => c.textContent?.trim()),
      ).toContain('The crew'),
    );
  });

  it('adds a party to the library', async () => {
    const screen = await render(PartiesPage);
    await screen.getByRole('button', { name: 'Add party' }).click();
    await vi.waitFor(async () => expect(await library.parties()).toHaveLength(1));
  });

  it('adds a member, and stores the reference', async () => {
    const crew = await library.saveParty({
      id: partyId(UNSAVED),
      name: 'The crew',
      note: '',
      tags: [],
      actors: [],
    });
    const screen = await render(PartiesPage);
    // A real click: SvGrid moves the cursor on pointer events, and a plain
    // DOM click does not reach them.
    await screen.getByText('The crew').click();

    const picker = screen.getByLabelText('Actor to add');
    await vi.waitFor(() => expect(screen.container.querySelectorAll('option').length).toBeGreaterThan(1));
    await picker.selectOptions('Rin — sophont');
    await screen.getByRole('button', { name: 'Add', exact: true }).click();

    await vi.waitFor(async () => expect((await library.party(crew.id))?.actors).toEqual([rin.id]));
  });

  /**
   * The reference model, made visible. Deleting an actor is unguarded and
   * nothing goes back to tidy the parties that named it, so the party still
   * has a member there — it just cannot be resolved.
   */
  it('shows a hole where a member has been deleted, keeping the others in order', async () => {
    await library.saveParty({
      id: partyId(UNSAVED),
      name: 'The crew',
      note: '',
      tags: [],
      actors: [rin.id, sana.id],
    });
    await library.deleteActor(rin.id);

    const screen = await render(PartiesPage);
    await screen.getByText('The crew').click();

    await vi.waitFor(() => {
      const listed = rows(screen.container);
      expect(listed[0]).toContain('deleted actor');
      expect(listed[1]).toContain('Sana');
    });
  });
});
