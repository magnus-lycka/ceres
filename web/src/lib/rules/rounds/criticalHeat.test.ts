/**
 * How badly damaged a robot reads at a glance: a score from its criticals, and
 * the colour that score is shown in.
 *
 * The score is the sum of squared severities, so one Severity 6 (36) outweighs
 * six Severity 1s (6) rather than counting the same — a single wrecked system
 * is worse than several scratches. The colour is a foreground-only ramp, so it
 * never competes with the row's own dead/unconscious/acted background; full red
 * is reached at a score of 32, on the step the referee settled on (8 per point
 * of score), which one Severity 6 alone already exceeds.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { criticalHeat, criticalScore } from './criticalHeat';

function warbot(criticals: Actor['criticals'] = {}): Actor {
  return {
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
    criticals,
    protection: 0,
    movement: null,
    speed: null,
    enduranceHours: null,
    int: null,
  };
}

const at = (severity: number) => ({ severity, note: '', taken: {} });

describe('criticalScore', () => {
  it('is nothing for an undamaged robot', () => {
    expect(criticalScore(warbot())).toBe(0);
  });

  it('is the sum of each damaged location’s severity squared', () => {
    // One Severity 5, one Severity 2, one Severity 1: 25 + 4 + 1.
    const hurt = warbot({ armour: at(5), weapon: at(2), options: at(1) });

    expect(criticalScore(hurt)).toBe(30);
  });

  it('weighs one bad location above several small ones', () => {
    const oneWorst = warbot({ armour: at(6) });
    const sixSmall = warbot({
      power: at(1),
      weapon: at(1),
      armour: at(1),
      chassis: at(1),
      locomotion: at(1),
      options: at(1),
    });

    expect(criticalScore(oneWorst)).toBeGreaterThan(criticalScore(sixSmall)!);
  });

  it('is null for anything that has no systems to damage', () => {
    const wolf: Actor = { ...warbot(), kind: 'animal' };

    expect(criticalScore(wolf)).toBeNull();
  });
});

describe('criticalHeat', () => {
  it('is nothing at a score of zero', () => {
    expect(criticalHeat(0)).toBe(0);
  });

  it('is the step the referee settled on: 8 per point of score', () => {
    expect(criticalHeat(1)).toBe(8);
    expect(criticalHeat(4)).toBe(32);
  });

  it('reaches full red at a score of 32, and goes no further past it', () => {
    expect(criticalHeat(32)).toBe(255);
    expect(criticalHeat(40)).toBe(255);
  });

  // One Severity 6 alone (36) is past the cap: fully red on its own.
  it('is already full red from a single Severity 6', () => {
    expect(criticalHeat(36)).toBe(255);
  });
});
