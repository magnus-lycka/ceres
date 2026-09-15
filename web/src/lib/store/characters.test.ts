import { expect, it } from 'vitest';
import { Library } from './library';
import { MemoryFileStore } from './memory';
import { actorId } from '$lib/schema/actor';
import { duplicate } from '$lib/rules/rounds/library';
import { situationSchema } from '$lib/schema/situation';

const source = {
  url: 'http://ceres.test/api/characters/1',
  name: 'Guard',
  strength: 8,
  dexterity: 9,
  endurance: 7,
};
it('adds once, refreshes explicitly, and detaches copies', async () => {
  const library = new Library(new MemoryFileStore());
  const actor = await library.addCharacter(source);
  expect((await library.addCharacter({ ...source, name: 'Changed' })).name).toBe('Guard');
  expect(await library.actors()).toHaveLength(1);
  await library.saveActor({
    ...actor,
    note: 'on duty',
    tags: ['guard'],
    injuries: [{ when: null, kind: 'lethal', reductions: { strength: 2 } }],
  });
  const updated = await library.refreshCharacter(actor.id, { ...source, name: 'Officer', strength: 10 });
  expect(updated).toMatchObject({
    name: 'Officer',
    strength: 10,
    note: 'on duty',
    tags: ['guard'],
    injuries: [{ when: null, kind: 'lethal', reductions: { strength: 2 } }],
  });
  const copy = await library.saveActor(duplicate(updated, actorId(0), [updated]));
  expect(copy.character).toBeUndefined();
  expect(await library.actors()).toHaveLength(2);
});
it('refuses refresh in a current situation without changing the actor', async () => {
  const library = new Library(new MemoryFileStore());
  const actor = await library.addCharacter(source);
  await library.saveSituation(
    situationSchema.parse({ name: 'Fight', state: 'current', members: [{ actor: actor.id }] }),
  );
  await expect(library.refreshCharacter(actor.id, { ...source, strength: 12 })).rejects.toThrow(
    'active situation',
  );
  expect(await library.actor(actor.id)).toEqual(actor);
});
