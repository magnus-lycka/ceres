/**
 * What a proposal may say, and what the application refuses.
 *
 * This schema is the boundary between an author with no access to the store
 * and the store itself, so what it rejects matters more than what it accepts.
 * The author may be an assistant, and may never see the application; a
 * proposal that CI waves through and the application then refuses would leave
 * them with no way to find out why.
 *
 * From `docs/plan-library-import.md`, "Bundle contract".
 */
import { describe, expect, it } from 'vitest';
import { importReceiptSchema, libraryBundleSchema } from './import';

const sergeant = {
  name: 'Sergeant Vela',
  kind: 'sophont',
  strength: 9,
  dexterity: 8,
  endurance: 10,
  tags: ['security', 'starport'],
  note: 'Carries a laser carbine.',
};

const beast = { name: 'Guard beast', kind: 'animal', hits: 20, tags: ['security'] };

const bundle = (extra: Record<string, unknown> = {}, ...actors: unknown[]) => ({
  name: 'Starport security',
  tags: ['security'],
  note: 'The night shift at the downport.',
  actors: actors.length > 0 ? actors : [sergeant, beast],
  ...extra,
});

describe('a library bundle', () => {
  it('takes one party with its actors embedded', () => {
    const parsed = libraryBundleSchema.parse(bundle());
    expect(parsed.name).toBe('Starport security');
    expect(parsed.actors.map((actor) => actor.name)).toEqual(['Sergeant Vela', 'Guard beast']);
  });

  // The array order becomes party member order, so it is data, not decoration.
  it('keeps the actors in the order they were submitted', () => {
    const parsed = libraryBundleSchema.parse(bundle({}, beast, sergeant));
    expect(parsed.actors.map((actor) => actor.name)).toEqual(['Guard beast', 'Sergeant Vela']);
  });

  it('takes a mixture of kinds', () => {
    const robot = { name: 'Loader', kind: 'robot', hits: 12 };
    const parsed = libraryBundleSchema.parse(bundle({}, sergeant, beast, robot));
    expect(parsed.actors.map((actor) => actor.kind)).toEqual(['sophont', 'animal', 'robot']);
  });

  it('fills in what an author left out', () => {
    const parsed = libraryBundleSchema.parse({
      name: 'Two guards',
      actors: [{ name: 'Guard', kind: 'animal', hits: 8 }],
    });
    expect(parsed.note).toBe('');
    expect(parsed.tags).toEqual([]);
    expect(parsed.actors[0].note).toBe('');
  });

  it('refuses a bundle with nobody in it', () => {
    expect(libraryBundleSchema.safeParse(bundle({ actors: [] })).success).toBe(false);
  });

  it('refuses a bundle that does not name its party', () => {
    const { name: _dropped, ...unnamed } = bundle();
    expect(libraryBundleSchema.safeParse(unnamed).success).toBe(false);
  });
});

/**
 * Strictness is the whole point. An ordinary Zod object strips unknown keys,
 * which would accept `strenght: 9` and quietly produce a sophont with no STR.
 */
describe('what a proposal may not say', () => {
  const refused = (extra: Record<string, unknown>) =>
    libraryBundleSchema.safeParse(bundle({}, { ...sergeant, ...extra })).success;

  it('refuses an actor id, which is the application’s to allocate', () => {
    expect(refused({ id: 7 })).toBe(false);
  });

  // Temporal state belongs to a fight, and a proposal is not in one.
  it('refuses injuries', () => {
    expect(refused({ injuries: [{ kind: 'lethal', reductions: { strength: 2 } }] })).toBe(false);
  });

  it('refuses robot criticals', () => {
    expect(refused({ criticals: { power: { severity: 3, note: '' } } })).toBe(false);
  });

  it('refuses a misspelled field rather than dropping it', () => {
    expect(refused({ strenght: 9 })).toBe(false);
  });

  it('refuses an unknown field on the party too', () => {
    expect(libraryBundleSchema.safeParse(bundle({ initiative: 8 })).success).toBe(false);
  });

  it('refuses a party id', () => {
    expect(libraryBundleSchema.safeParse(bundle({ id: 3 })).success).toBe(false);
  });
});

/**
 * The kind rule is the same function the stored schema uses, so a proposal CI
 * accepted cannot be one the application refuses.
 */
describe('the kind rule reaches proposals', () => {
  const check = (actor: Record<string, unknown>) => libraryBundleSchema.safeParse(bundle({}, actor)).success;

  it('wants characteristics for a sophont', () => {
    expect(check({ name: 'Vela', kind: 'sophont', hits: 10 })).toBe(false);
  });

  it('wants hits for an animal', () => {
    expect(check({ name: 'Wolf', kind: 'animal' })).toBe(false);
  });

  it('refuses characteristics on an animal', () => {
    expect(check({ name: 'Wolf', kind: 'animal', hits: 8, strength: 5 })).toBe(false);
  });

  it('accepts a robot with hits', () => {
    expect(check({ name: 'Loader', kind: 'robot', hits: 12 })).toBe(true);
  });
});

/**
 * A receipt is what makes installing a bundle replay-safe: it records the ids
 * allocated, so a retry finishes the same installation instead of starting a
 * second one.
 */
describe('an import receipt', () => {
  const receipt = {
    schemaVersion: 1,
    bundle: 'issue-123',
    issue: 123,
    status: 'complete',
    actors: [41, 42],
    party: 9,
  };

  it('records which entities a bundle produced', () => {
    const parsed = importReceiptSchema.parse(receipt);
    expect(parsed.actors).toEqual([41, 42]);
    expect(parsed.party).toBe(9);
  });

  it('knows an installation that has not finished', () => {
    expect(importReceiptSchema.parse({ ...receipt, status: 'installing' }).status).toBe('installing');
  });

  it('refuses a status it does not know', () => {
    expect(importReceiptSchema.safeParse({ ...receipt, status: 'done' }).success).toBe(false);
  });
});
