import { describe, expect, it } from 'vitest';
import { actorJSONSchema, actorSchema } from './actor';

const sophont = { name: 'Rin', kind: 'sophont', strength: 8, dexterity: 8, endurance: 8 };
const animal = { name: 'Wolf', kind: 'animal', hits: 12 };

describe('actor schema', () => {
  it('accepts a sophont with all three physical characteristics', () => {
    const actor = actorSchema.parse(sophont);
    expect(actor).toMatchObject({ name: 'Rin', strength: 8, hits: null });
    expect(actor.tags).toEqual([]);
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

  it('defaults an unsaved actor to id zero, so the service allocates it', () => {
    expect(actorSchema.parse(sophont).id).toBe(0);
  });

  it('publishes a JSON Schema for CI to validate proposed bundles with', () => {
    const schema = actorJSONSchema() as { properties: Record<string, unknown> };
    expect(Object.keys(schema.properties)).toContain('tags');
  });
});
