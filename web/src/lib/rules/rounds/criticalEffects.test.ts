/**
 * The Critical Hit Effects table, transcribed from the Robot Handbook
 * (refs/robot/50_other_considerations.md:132-143) and not from the code.
 *
 * Every cell is asserted: 7 locations by 6 severities. The wording is the
 * table's own, so a slip in the transcription shows up as a wrong sentence, and
 * the mechanical meaning is what the rest of the app acts on.
 */
import { describe, expect, it } from 'vitest';
import { criticalLocations } from '../../schema/actor';
import { criticalEffect, type CriticalEffect } from './criticalEffects';

const chassisOne = { chassis: { flat: 1 } };
const chassisDie = { chassis: { dice: 1 } };

/**
 * [location, severity, what the table says]
 *
 * Two rows depart from the table's own wording. The table says "Speed reduced
 * by 1m or one Speed Band" for both Power and Locomotion, but Speed and
 * Movement are two different attributes in this model (CONTEXT.md): Locomotion
 * takes it from either, Power from both (RIC-020). Written here as Movement
 * and Speed so the wording does not contradict the fields beside it.
 */
const table: [(typeof criticalLocations)[number], number, CriticalEffect][] = [
  ['power', 1, { text: 'Movement reduced by 1 m and Speed by one Band', pace: 1 }],
  ['power', 2, { text: 'Remaining Endurance halved', enduranceHalved: true }],
  ['power', 3, { text: 'Remaining Endurance halved again', enduranceHalved: true }],
  ['power', 4, { text: 'Remaining Endurance halved again', enduranceHalved: true }],
  [
    'power',
    5,
    { text: 'Power supply explodes. Robot shuts down. Chassis Severity +1', inoperable: true, ...chassisOne },
  ],
  [
    'power',
    6,
    {
      text: 'Power supply explodes. Robot shuts down. Chassis Severity +1D',
      inoperable: true,
      ...chassisDie,
    },
  ],

  ['weapon', 1, { text: 'Random weapon suffers DM-2 to attack rolls' }],
  ['weapon', 2, { text: 'Random weapon disabled' }],
  ['weapon', 3, { text: 'Random weapon destroyed' }],
  ['weapon', 4, { text: 'Random weapon explodes. Chassis Severity +1', ...chassisOne }],
  ['weapon', 5, { text: 'Random weapon explodes. Chassis Severity +1', ...chassisOne }],
  ['weapon', 6, { text: 'Random weapon explodes. Chassis Severity +1', ...chassisOne }],

  ['armour', 1, { text: 'Protection -1', protection: { flat: 1 } }],
  ['armour', 2, { text: 'Protection -1D', protection: { dice: 1 } }],
  ['armour', 3, { text: 'Protection -1D', protection: { dice: 1 } }],
  ['armour', 4, { text: 'Protection -2D', protection: { dice: 2 } }],
  ['armour', 5, { text: 'Protection -2D, Chassis Severity +1', protection: { dice: 2 }, ...chassisOne }],
  ['armour', 6, { text: 'Protection -2D. Chassis Severity +1', protection: { dice: 2 }, ...chassisOne }],

  ['chassis', 1, { text: 'Robot suffers 1D damage', damageDice: 1 }],
  ['chassis', 2, { text: 'Robot suffers 2D damage', damageDice: 2 }],
  ['chassis', 3, { text: 'Robot suffers 3D damage', damageDice: 3 }],
  ['chassis', 4, { text: 'Robot suffers 4D damage', damageDice: 4 }],
  ['chassis', 5, { text: 'Robot suffers 5D damage', damageDice: 5 }],
  ['chassis', 6, { text: 'Robot suffers 6D damage', damageDice: 6 }],

  ['locomotion', 1, { text: 'Movement reduced by 1 m or Speed by one Band', pace: 1 }],
  ['locomotion', 2, { text: 'Movement reduced by 1 m or Speed by one Band', pace: 1 }],
  ['locomotion', 3, { text: 'Movement reduced by 1 m or Speed by one Band', pace: 1 }],
  ['locomotion', 4, { text: 'Movement reduced by 1 m or Speed by one Band', pace: 1 }],
  ['locomotion', 5, { text: 'Robot immobilised', immobilised: true }],
  ['locomotion', 6, { text: 'Robot immobilised. Chassis Severity +1', immobilised: true, ...chassisOne }],

  ['options', 1, { text: 'Random option suffers DM-2' }],
  ['options', 2, { text: 'Random option disabled' }],
  ['options', 3, { text: 'Random option destroyed' }],
  ['options', 4, { text: 'Two random options destroyed' }],
  ['options', 5, { text: 'Random option destroyed. Chassis Severity +1', ...chassisOne }],
  ['options', 6, { text: 'Random option destroyed. Chassis Severity +1', ...chassisOne }],

  ['brain', 1, { text: 'DM-2 to one skill' }],
  ['brain', 2, { text: 'DM-2 to all skills' }],
  ['brain', 3, { text: 'Robot unable to perform any skills' }],
  ['brain', 4, { text: 'Robot INT halved', intHalved: true }],
  ['brain', 5, { text: 'Robot brain disabled', inoperable: true }],
  ['brain', 6, { text: 'Robot brain destroyed. Chassis Severity +1', inoperable: true, ...chassisOne }],
];

describe('the critical hit effects table', () => {
  it.each(table)('%s, severity %i', (location, severity, expected) => {
    expect(criticalEffect(location, severity)).toEqual(expected);
  });

  it('has a cell for every location at every severity, and no others', () => {
    expect(table).toHaveLength(criticalLocations.length * 6);
    expect(new Set(table.map(([location, severity]) => `${location}${severity}`)).size).toBe(42);
  });

  // Severity 0 is undamaged and 6 is the worst there is: nothing lies outside.
  it('says nothing for an undamaged location or a severity past the worst', () => {
    expect(criticalEffect('power', 0)).toBeNull();
    expect(criticalEffect('power', 7)).toBeNull();
  });
});
