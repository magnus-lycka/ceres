/**
 * Robot critical hits, derived from handouts/robot_combat_cards.typ (Card 2,
 * "Robot Damage") and the Robot Handbook pages it cites — not from the
 * implementation.
 *
 * Criticals matter to this app because they are the only thing that takes a
 * robot out of action or limits what it can do on its turn; a robot's Hits
 * total carries no penalty of its own. Nothing here rolls dice: the two
 * mechanisms that produce a critical are both derived from numbers the referee
 * already has — the attack's Effect, and the damage total. The record itself
 * is the card's: seven locations, each with a severity and a note.
 */
import { describe, expect, it } from 'vitest';
import type { Actor } from '../../schema/actor';
import {
  applyCritical,
  attackCriticalSeverity,
  criticalAt,
  criticalRows,
  setCritical,
  severityAfter,
  sustainedCriticalCount,
} from './criticals';

function warbot(criticals: Actor['criticals'] = {}, hits = 20): Actor {
  return {
    id: 6,
    name: 'Warbot',
    kind: 'robot',
    note: '',
    tags: [],
    strength: null,
    dexterity: null,
    endurance: null,
    hits,
    injuries: [],
    criticals,
  };
}

const at = (severity: number, note = '') => ({ severity, note });

describe('the combat record', () => {
  // The card prints seven rows whether or not anything has been hit, in the
  // order the 2D location table rolls them.
  it('has a row for every location, damaged or not', () => {
    const rows = criticalRows(warbot({ brain: at(2, 'DM−2 to all skills') }));
    expect(rows.map((row) => row.location)).toEqual([
      'power',
      'weapon',
      'armour',
      'chassis',
      'locomotion',
      'options',
      'brain',
    ]);
    expect(rows.at(-1)).toEqual({ location: 'brain', severity: 2, note: 'DM−2 to all skills' });
    expect(rows[0]).toEqual({ location: 'power', severity: 0, note: '' });
  });

  it('reads an undamaged location as severity 0 with no note', () => {
    expect(criticalAt(warbot(), 'options')).toEqual({ severity: 0, note: '' });
  });
});

describe('editing a row directly', () => {
  it('records a severity and the note the referee looked up', () => {
    const edited = setCritical(warbot(), 'armour', 2, 'Protection −1D');
    expect(edited.criticals.armour).toEqual({ severity: 2, note: 'Protection −1D' });
  });

  it('keeps a note on an otherwise undamaged location', () => {
    const edited = setCritical(warbot(), 'options', 0, 'no options fitted');
    expect(edited.criticals.options).toEqual({ severity: 0, note: 'no options fitted' });
  });

  it('drops the row entirely when there is nothing left to say', () => {
    const repaired = setCritical(warbot({ power: at(3, 'Speed −1') }), 'power', 0, '');
    expect(repaired.criticals.power).toBeUndefined();
  });

  it('leaves the other locations alone', () => {
    const edited = setCritical(warbot({ power: at(3, 'Speed −1') }), 'brain', 1, '');
    expect(criticalAt(edited, 'power')).toEqual({ severity: 3, note: 'Speed −1' });
  });
});

describe('repeat hits to one location', () => {
  it('takes the rolled severity when the location is undamaged', () => {
    expect(severityAfter(0, 3)).toBe(3);
  });

  it('takes the higher of the rolled severity and one more than the old', () => {
    expect(severityAfter(2, 5)).toBe(5);
  });

  it('always worsens by at least one, however low the roll', () => {
    expect(severityAfter(4, 1)).toBe(5);
  });

  it('stops at severity 6', () => {
    expect(severityAfter(6, 4)).toBe(6);
  });
});

describe('applying a critical', () => {
  it('records the severity on the robot', () => {
    expect(criticalAt(applyCritical(warbot(), 'brain', 2).actor, 'brain').severity).toBe(2);
  });

  it('keeps the note already written against the location', () => {
    const hurt = applyCritical(warbot({ weapon: at(1, 'left autocannon') }), 'weapon', 3).actor;
    expect(hurt.criticals.weapon).toEqual({ severity: 3, note: 'left autocannon' });
  });

  // "Chassis: S1 Suffer 1D ... S6 Suffer 6D" — the one location whose effect
  // is plain damage, so the only one this module can resolve in full.
  it('inflicts the reached severity in dice when the location is the chassis', () => {
    expect(applyCritical(warbot(), 'chassis', 3).damageDice).toBe(3);
  });

  it('inflicts nothing extra for any other location', () => {
    expect(applyCritical(warbot(), 'power', 3).damageDice).toBe(0);
  });

  // "Once a location is already Severity 6, every further hit there instead
  // inflicts 6D Hits."
  it('inflicts 6D instead once the location is already at severity 6', () => {
    const { actor, damageDice } = applyCritical(warbot({ locomotion: at(6) }), 'locomotion', 2);
    expect(damageDice).toBe(6);
    expect(criticalAt(actor, 'locomotion').severity).toBe(6);
  });
});

/**
 * First mechanism: "If the attack has Effect 6+ and inflicts damage after
 * Protection: Severity = attack Effect − 5."
 */
describe('a critical from the attack roll', () => {
  it('is nothing below Effect 6', () => {
    expect([0, 1, 5].map(attackCriticalSeverity)).toEqual([0, 0, 0]);
  });

  it('is Effect less five', () => {
    expect([6, 7, 11].map(attackCriticalSeverity)).toEqual([1, 2, 6]);
  });

  it('cannot exceed severity 6, however good the roll', () => {
    expect(attackCriticalSeverity(15)).toBe(6);
  });
});

/**
 * Second mechanism: "Every time cumulative damage crosses another 10% of
 * starting Hits, roll a location and inflict a Severity 1 critical. For a
 * 20-Hit robot, mark one at 2, 4, 6, 8 … cumulative damage."
 */
describe('criticals from sustained damage', () => {
  it('counts nothing until the first tenth is crossed', () => {
    expect(sustainedCriticalCount(20, 0, 1)).toBe(0);
  });

  it('counts one as each tenth is reached', () => {
    expect(sustainedCriticalCount(20, 0, 2)).toBe(1);
    expect(sustainedCriticalCount(20, 2, 4)).toBe(1);
  });

  it('counts every threshold a single large hit crosses', () => {
    expect(sustainedCriticalCount(20, 0, 8)).toBe(4);
  });

  it('counts nothing for damage that stays inside one step', () => {
    expect(sustainedCriticalCount(20, 5, 5)).toBe(0);
    expect(sustainedCriticalCount(20, 4, 5)).toBe(0);
  });

  // A tenth of 25 is 2.5, so the thresholds fall at 3, 5, 8, 10 …
  it('handles a starting total that does not divide by ten', () => {
    expect(sustainedCriticalCount(25, 0, 2)).toBe(0);
    expect(sustainedCriticalCount(25, 2, 3)).toBe(1);
  });
});
