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

  // Sophonts wear armour and animals have the Armour trait, so every kind
  // takes damage after Protection. Unarmoured is zero, not unknown.
  it('gives every kind a Protection, unarmoured unless said otherwise', () => {
    expect(actorSchema.parse(sophont).protection).toBe(0);
    expect(actorSchema.parse({ ...animal, protection: 12 }).protection).toBe(12);
    expect(actorSchema.parse({ ...robot, protection: 4 }).protection).toBe(4);
  });

  // Movement is metres per Minor Action; Speed is a Speed Band. Two quantities,
  // and every kind has both. Neither is invented: an actor with none set has
  // none, rather than a sophont's 6 m or a robot's Idle.
  it('gives every kind a Movement and a Speed, unset until given', () => {
    expect(actorSchema.parse(sophont)).toMatchObject({ movement: null, speed: null });
    expect(actorSchema.parse({ ...sophont, movement: 6, speed: 1 })).toMatchObject({ movement: 6, speed: 1 });
    expect(actorSchema.parse({ ...animal, movement: 9, speed: 3 })).toMatchObject({ movement: 9, speed: 3 });
    expect(actorSchema.parse({ ...robot, movement: 5, speed: 4 })).toMatchObject({ movement: 5, speed: 4 });
  });

  it('rejects a Speed that is not on the band ladder', () => {
    expect(actorSchema.safeParse({ ...sophont, speed: 12 }).success).toBe(false);
    expect(actorSchema.safeParse({ ...sophont, speed: -1 }).success).toBe(false);
    expect(actorSchema.safeParse({ ...sophont, speed: 0 }).success).toBe(true);
    expect(actorSchema.safeParse({ ...sophont, speed: 11 }).success).toBe(true);
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

  // A robot's Endurance is hours of operation and its INT is a system that a
  // Brain critical erodes. Neither is the sophont's END characteristic.
  it('accepts hours of endurance and INT on a robot', () => {
    const actor = actorSchema.parse({ ...robot, enduranceHours: 40, int: 5 });
    expect(actor).toMatchObject({ enduranceHours: 40, int: 5 });
  });

  it('rejects hours of endurance and INT on anything that is not a robot', () => {
    expect(actorSchema.safeParse({ ...sophont, enduranceHours: 40 }).success).toBe(false);
    expect(actorSchema.safeParse({ ...animal, int: 3 }).success).toBe(false);
  });

  it('rejects recoverable stun on a robot, because a stunner causes physical Hits', () => {
    const result = actorSchema.safeParse({
      ...robot,
      injuries: [{ kind: 'stun', reductions: { hits: 3 } }],
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain('physical Hits');
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
