import { describe, expect, it } from 'vitest';
import { actorJSONSchema, actorSchema } from './actor';

const sophont = { name: 'Rin', kind: 'sophont', strength: 8, dexterity: 8, endurance: 8 };
const animal = { name: 'Wolf', kind: 'animal', hits: 12 };
const robot = { name: 'Warbot', kind: 'robot', hits: 20 };

describe('actor schema', () => {
  it('accepts a sophont with all three physical characteristics', () => {
    const actor = actorSchema.parse(sophont);
    expect(actor).toMatchObject({ name: 'Rin', strength: 8, hits: null });
    expect(actor.tags).toEqual([]);
  });

  // Add puts an unnamed row in the grid and you type the name into it, so an
  // actor without one has to survive the round trip to storage.
  it('accepts an actor that has not been named yet', () => {
    expect(actorSchema.parse({ ...sophont, name: '' }).name).toBe('');
  });

  it('accepts an animal with hits', () => {
    expect(actorSchema.parse(animal).hits).toBe(12);
  });

  it('rejects a sophont missing a characteristic', () => {
    const result = actorSchema.safeParse({ ...sophont, endurance: null });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain('endurance');
  });

  it('rejects an animal that was given characteristics', () => {
    expect(actorSchema.safeParse({ ...animal, strength: 4 }).success).toBe(false);
  });

  it('rejects an animal with no hits', () => {
    expect(actorSchema.safeParse({ name: 'Wolf', kind: 'animal' }).success).toBe(false);
  });

  // System criticals are a robot rule. Nothing else on the table has a power
  // supply to lose or a brain to disable.
  it('accepts criticals on a robot', () => {
    const hurt = actorSchema.parse({
      ...robot,
      criticals: { brain: { severity: 2, note: 'DM−2 to all skills' } },
    });
    expect(hurt.criticals.brain).toEqual({ severity: 2, note: 'DM−2 to all skills' });
  });

  it('defaults a critical to undamaged and unannotated', () => {
    expect(actorSchema.parse({ ...robot, criticals: { brain: {} } }).criticals.brain).toEqual({
      severity: 0,
      note: '',
    });
  });

  it('rejects criticals on anything that is not a robot', () => {
    const result = actorSchema.safeParse({ ...animal, criticals: { brain: { severity: 2 } } });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain('critical');
  });

  it('rejects a severity outside 0–6', () => {
    expect(actorSchema.safeParse({ ...robot, criticals: { brain: { severity: 7 } } }).success).toBe(false);
    expect(actorSchema.safeParse({ ...robot, criticals: { brain: { severity: -1 } } }).success).toBe(false);
  });

  it('defaults an unsaved actor to id zero, so the service allocates it', () => {
    expect(actorSchema.parse(sophont).id).toBe(0);
  });

  it('publishes a JSON Schema for CI to validate proposed bundles with', () => {
    const schema = actorJSONSchema() as { properties: Record<string, unknown> };
    expect(Object.keys(schema.properties)).toContain('tags');
  });
});
