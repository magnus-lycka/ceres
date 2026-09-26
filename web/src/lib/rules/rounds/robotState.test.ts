/**
 * What a robot is now, given what its criticals have taken off it.
 *
 * Each location's critical records what it took (docs/plan-rounds.md, "Actor
 * attributes"), so nothing is replayed: a current value is the base less the sum
 * over every location. The base is what the actor is, and never changes here.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { currentAttribute, isImmobilised, isInoperable } from './robotState';

const warbot: Actor = {
  id: actorId(6),
  name: 'Warbot',
  kind: 'robot',
  note: '',
  tags: [],
  strength: null,
  dexterity: null,
  endurance: null,
  hits: 20,
  injuries: [],
  criticals: {},
  protection: 8,
  movement: 6,
  speed: 4,
  enduranceHours: 40,
  int: 6,
};

describe('a robot’s current attributes', () => {
  it('are what it is, when nothing has been taken', () => {
    expect(currentAttribute(warbot, 'protection')).toBe(8);
    expect(currentAttribute(warbot, 'enduranceHours')).toBe(40);
  });

  it('are the base less what every location took, added up', () => {
    const hurt: Actor = {
      ...warbot,
      criticals: {
        power: { severity: 1, note: '', taken: { movement: 1, speed: 1 } },
        locomotion: { severity: 2, note: '', taken: { movement: 2 } },
        armour: { severity: 2, note: '', taken: { protection: 5 } },
      },
    };

    expect(currentAttribute(hurt, 'movement')).toBe(3);
    expect(currentAttribute(hurt, 'speed')).toBe(3);
    expect(currentAttribute(hurt, 'protection')).toBe(3);
    expect(currentAttribute(hurt, 'int')).toBe(6);
  });

  // Nothing can be reduced below nothing, however much has been taken.
  it('never go below zero', () => {
    const wrecked: Actor = {
      ...warbot,
      criticals: { armour: { severity: 6, note: '', taken: { protection: 20 } } },
    };

    expect(currentAttribute(wrecked, 'protection')).toBe(0);
  });

  // A robot with no Speed set has none to lose: unset stays unset.
  it('stay unset when there was no base to take from', () => {
    const unset: Actor = {
      ...warbot,
      speed: null,
      criticals: { power: { severity: 1, note: '', taken: { speed: 1 } } },
    };

    expect(currentAttribute(unset, 'speed')).toBeNull();
  });
});

/**
 * Two things a critical can do to what a robot may do at all. Shut down or
 * brainless, it can do nothing (Power 5 and 6 "shuts down", Brain 5 "disabled"
 * and 6 "destroyed"). Immobilised, "only prevents movement; usable weapons may
 * still fire" (docs/plan-rounds.md), so it does not take its turn.
 */
describe('what a robot can do at all', () => {
  const hit = (
    location: 'power' | 'brain' | 'locomotion' | 'weapon' | 'armour',
    severity: number,
  ): Actor => ({
    ...warbot,
    criticals: { [location]: { severity, note: '', taken: {} } },
  });

  it('is nothing once the power supply has gone, or the brain', () => {
    expect(isInoperable(hit('power', 5))).toBe(true);
    expect(isInoperable(hit('power', 6))).toBe(true);
    expect(isInoperable(hit('brain', 5))).toBe(true);
    expect(isInoperable(hit('brain', 6))).toBe(true);
  });

  it('is still something below that, and for any other location', () => {
    expect(isInoperable(hit('power', 4))).toBe(false);
    expect(isInoperable(hit('brain', 4))).toBe(false);
    expect(isInoperable(hit('weapon', 6))).toBe(false);
    expect(isInoperable(hit('locomotion', 6))).toBe(false);
    expect(isInoperable(warbot)).toBe(false);
  });

  it('is immobilised by the locomotion at 5 and 6, and still operable', () => {
    expect(isImmobilised(hit('locomotion', 4))).toBe(false);
    expect(isImmobilised(hit('locomotion', 5))).toBe(true);
    expect(isImmobilised(hit('locomotion', 6))).toBe(true);
    expect(isInoperable(hit('locomotion', 5))).toBe(false);
  });

  it('is never either, for something that has no systems', () => {
    const wolf: Actor = { ...warbot, kind: 'animal', criticals: {} };

    expect(isInoperable(wolf)).toBe(false);
    expect(isImmobilised(wolf)).toBe(false);
  });
});
