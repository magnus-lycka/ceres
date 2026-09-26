/**
 * Working one hit through a robot's criticals, from refs/robot/50_other_considerations.md
 * (Critical Hits Location, and the Critical Hit Effects table) and the combat
 * cards, not from the code.
 *
 * Nothing here rolls. Wherever the rules call for a roll, the flow asks the
 * referee for it and carries on with the answer.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { answer, locationFor, prompt, startFlow } from './robotCriticals';
import { currentAttribute } from './robotState';

describe('the location a 2D roll gives', () => {
  // refs/robot/50_other_considerations.md:100-109
  it.each([
    [2, 'power'],
    [4, 'power'],
    [5, 'weapon'],
    [6, 'armour'],
    [7, 'chassis'],
    [8, 'locomotion'],
    [9, 'locomotion'],
    [10, 'options'],
    [11, 'options'],
    [12, 'brain'],
  ])('for %i is %s', (roll, location) => {
    expect(locationFor(roll)).toBe(location);
  });

  it('is nothing for a roll 2D cannot give', () => {
    expect(locationFor(1)).toBeNull();
    expect(locationFor(13)).toBeNull();
  });
});

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

describe('an attack critical', () => {
  it('asks for the location, and then applies a flat effect without asking anything more', () => {
    const begun = startFlow(warbot, { round: 2, severity: 1 });
    expect(prompt(begun)).toEqual({ kind: 'location', why: 'Attack critical, Severity 1' });

    // 6 on 2D is Armour; Armour Severity 1 is "Protection -1".
    const done = answer(begun, 6);

    expect(prompt(done)).toBeNull();
    expect(done.actor.criticals.armour).toMatchObject({ severity: 1, taken: { protection: 1 } });
    expect(done.log).toEqual(['Armour, Severity 1: Protection -1']);
  });

  // "Protection -1D" is a roll, and the app rolls nothing: it asks.
  it('asks for the dice an effect costs, and takes that much off', () => {
    const begun = answer(startFlow(warbot, { round: 2, severity: 2 }), 6);

    expect(prompt(begun)).toEqual({ kind: 'dice', dice: 1, why: 'Armour, Severity 2: Protection -1D' });
    const done = answer(begun, 3);

    expect(prompt(done)).toBeNull();
    expect(done.actor.criticals.armour).toMatchObject({ severity: 2, taken: { protection: 3 } });
  });

  // Nothing can go below nothing: Protection 2 hit for 2D that came to 9 loses 2.
  it('takes no more than is left', () => {
    const thin = { ...warbot, protection: 2 };
    const done = answer(answer(startFlow(thin, { round: 2, severity: 4 }), 6), 9);

    expect(done.actor.criticals.armour?.taken.protection).toBe(2);
    expect(currentAttribute(done.actor, 'protection')).toBe(0);
  });

  it('asks again if the answer is not a roll those dice can make', () => {
    const begun = answer(startFlow(warbot, { round: 2, severity: 2 }), 6);

    expect(prompt(answer(begun, 7))).toEqual(prompt(begun));
    expect(prompt(answer(begun, 0))).toEqual(prompt(begun));
    expect(prompt(answer(startFlow(warbot, { round: 2, severity: 2 }), 13))).toEqual({
      kind: 'location',
      why: 'Attack critical, Severity 2',
    });
  });
});

// "use the Severity of the new critical hit or the original +1, whichever is
// higher, and immediately apply any new effects" (:118): the effect is the one
// at the severity reached, not the one rolled.
describe('a location that has already been hit', () => {
  const dented: Actor = {
    ...warbot,
    criticals: { armour: { severity: 2, note: '', taken: { protection: 3 } } },
  };

  it('reaches the higher of the roll and one more than it was, and applies that severity', () => {
    const begun = answer(startFlow(dented, { round: 2, severity: 1 }), 6);

    // Rolled 1, but it was 2: now 3, which is "Protection -1D".
    expect(prompt(begun)).toEqual({ kind: 'dice', dice: 1, why: 'Armour, Severity 3: Protection -1D' });
    const done = answer(begun, 4);
    expect(done.actor.criticals.armour).toMatchObject({ severity: 3, taken: { protection: 7 } });
  });

  it('reaches the roll when it is higher', () => {
    const begun = answer(startFlow(dented, { round: 2, severity: 4 }), 6);

    expect(prompt(begun)).toEqual({ kind: 'dice', dice: 2, why: 'Armour, Severity 4: Protection -2D' });
  });
});

/**
 * "Speed reduced by 1m or one Speed Band". Movement is metres and Speed is a
 * band, and a robot has both. A failing power supply slows the whole robot, so
 * it costs both; a failing locomotion costs Movement, and asks which only when
 * Speed is above Idle, since that is the only case where there is a choice
 * (docs/RULE_INTERPRETATIONS.md, RIC-020).
 */
describe('losing pace', () => {
  it('costs both Movement and Speed, from the power supply', () => {
    // 3 on 2D is the power supply; Severity 1 is "Speed reduced by 1m or band".
    const done = answer(startFlow(warbot, { round: 2, severity: 1 }), 3);

    expect(prompt(done)).toBeNull();
    expect(currentAttribute(done.actor, 'movement')).toBe(5);
    expect(currentAttribute(done.actor, 'speed')).toBe(3);
  });

  it('costs only what the robot has: a Speed that was never set has none to lose', () => {
    const done = answer(startFlow({ ...warbot, speed: null }, { round: 2, severity: 1 }), 3);

    expect(currentAttribute(done.actor, 'movement')).toBe(5);
    expect(currentAttribute(done.actor, 'speed')).toBeNull();
  });

  it('costs Movement from the locomotion, without asking, when Speed is Idle or unset', () => {
    for (const speed of [null, 0, 1]) {
      const done = answer(startFlow({ ...warbot, speed }, { round: 2, severity: 1 }), 8);

      expect(prompt(done)).toBeNull();
      expect(currentAttribute(done.actor, 'movement')).toBe(5);
      expect(currentAttribute(done.actor, 'speed')).toBe(speed);
    }
  });

  it('asks which the locomotion costs when Speed is above Idle, and takes it from the one chosen', () => {
    const begun = answer(startFlow(warbot, { round: 2, severity: 2 }), 9);
    expect(prompt(begun)).toEqual({
      kind: 'pace',
      why: 'Locomotion, Severity 2: Speed reduced by 1m or one Speed Band',
    });

    const byMovement = answer(begun, 'movement');
    expect(currentAttribute(byMovement.actor, 'movement')).toBe(5);
    expect(currentAttribute(byMovement.actor, 'speed')).toBe(4);

    const bySpeed = answer(begun, 'speed');
    expect(currentAttribute(bySpeed.actor, 'movement')).toBe(6);
    expect(currentAttribute(bySpeed.actor, 'speed')).toBe(3);
  });

  it('does not take the answer to a choice for a roll, or a roll for a choice', () => {
    const begun = answer(startFlow(warbot, { round: 2, severity: 2 }), 9);

    expect(prompt(answer(begun, 5))).toEqual(prompt(begun));
    expect(prompt(answer(startFlow(warbot, { round: 2, severity: 1 }), 'speed'))).toEqual({
      kind: 'location',
      why: 'Attack critical, Severity 1',
    });
  });
});

/**
 * "Remaining Endurance halved", then "halved again", and "Robot INT halved". The
 * critical records what went, so a halving is stored as the amount taken, and
 * each further halving is of what is left. Endurance is hours and may come out
 * fractional; INT is a characteristic and rounds down (RIC-020).
 */
describe('halving', () => {
  const power = (severity: number, from: Actor = warbot) =>
    answer(startFlow(from, { round: 2, severity }), 3);

  it('takes half the remaining Endurance, and half of what is left again on a later hit', () => {
    const once = power(2);
    expect(prompt(once)).toBeNull();
    expect(currentAttribute(once.actor, 'enduranceHours')).toBe(20);

    // Hit again: at least one more severity, so Severity 3, "halved again".
    const twice = power(1, once.actor);
    expect(currentAttribute(twice.actor, 'enduranceHours')).toBe(10);
    expect(twice.actor.criticals.power?.taken.enduranceHours).toBe(30);
  });

  it('keeps a fraction of an hour', () => {
    const odd = power(2, { ...warbot, enduranceHours: 25 });

    expect(currentAttribute(odd.actor, 'enduranceHours')).toBe(12.5);
  });

  it('halves INT and rounds it down', () => {
    const brain = (int: number) => answer(startFlow({ ...warbot, int }, { round: 2, severity: 4 }), 12);

    expect(currentAttribute(brain(6).actor, 'int')).toBe(3);
    expect(currentAttribute(brain(5).actor, 'int')).toBe(2);
    expect(currentAttribute(brain(1).actor, 'int')).toBe(0);
  });

  it('halves nothing that was never set', () => {
    const done = power(2, { ...warbot, enduranceHours: null });

    expect(currentAttribute(done.actor, 'enduranceHours')).toBeNull();
    expect(done.actor.criticals.power?.taken).toEqual({});
  });
});

/**
 * The Chassis row is plain damage: "Robot suffers nD damage". It ignores
 * Protection ("Any extra damage caused by the effects of critical hits ignores
 * the robot's Protection"), and it is Hits like any other, stamped with the round.
 * Other rows say "Chassis Severity +1" or "+1D": a flat step, or a rolled one, up
 * the Chassis, capped at 6, with the Chassis row's effect at the severity reached
 * (docs/RULE_INTERPRETATIONS.md, RIC-016).
 */
describe('the chassis', () => {
  const hit = (severity: number, roll: number, from: Actor = warbot) =>
    answer(startFlow(from, { round: 2, severity }), roll);

  it('suffers the dice of its severity as Hits, past Protection, in this round', () => {
    const begun = hit(2, 7);
    expect(prompt(begun)).toEqual({
      kind: 'dice',
      dice: 2,
      why: 'Chassis, Severity 2: Robot suffers 2D damage',
    });

    const done = answer(begun, 7);

    expect(prompt(done)).toBeNull();
    expect(done.actor.injuries).toEqual([{ when: 2, kind: 'lethal', reductions: { hits: 7 } }]);
    expect(done.actor.criticals.chassis?.severity).toBe(2);
  });

  it('is stepped up by one from a power supply that explodes, and suffers the row it reaches', () => {
    // Power Severity 5: "Power supply explodes. Robot shuts down. Chassis Severity +1".
    const begun = hit(5, 3);

    expect(begun.actor.criticals.power?.severity).toBe(5);
    expect(begun.actor.criticals.chassis?.severity).toBe(1);
    expect(prompt(begun)).toEqual({
      kind: 'dice',
      dice: 1,
      why: 'Chassis, Severity 1: Robot suffers 1D damage',
    });
  });

  it('is stepped up by a die roll from Power Severity 6, and capped at 6', () => {
    const begun = hit(6, 3);
    expect(prompt(begun)).toEqual({
      kind: 'dice',
      dice: 1,
      why: 'Power supply, Severity 6: Chassis Severity +1D',
    });

    const stepped = answer(begun, 3);
    expect(stepped.actor.criticals.chassis?.severity).toBe(3);
    expect(prompt(stepped)).toMatchObject({ kind: 'dice', dice: 3 });

    // From Severity 4 a roll of 5 would be 9: it stops at 6.
    const high = answer(
      hit(6, 3, { ...warbot, criticals: { chassis: { severity: 4, note: '', taken: {} } } }),
      5,
    );
    expect(high.actor.criticals.chassis?.severity).toBe(6);
    expect(prompt(high)).toMatchObject({ kind: 'dice', dice: 6 });
  });

  it('suffers 6D again when it is already at 6 and is stepped up', () => {
    const done = hit(5, 3, { ...warbot, criticals: { chassis: { severity: 6, note: '', taken: {} } } });

    expect(done.actor.criticals.chassis?.severity).toBe(6);
    expect(prompt(done)).toMatchObject({ kind: 'dice', dice: 6 });
  });

  // Armour Severity 5 is "Protection -2D, Chassis Severity +1": what the armour
  // costs is asked first, and then what the chassis suffers.
  it('is dealt with after the rest of the effect that stepped it up', () => {
    const armour = answer(hit(5, 6), 7);

    expect(currentAttribute(armour.actor, 'protection')).toBe(1);
    expect(prompt(armour)).toEqual({
      kind: 'dice',
      dice: 1,
      why: 'Chassis, Severity 1: Robot suffers 1D damage',
    });
  });
});

// "Once a location is already Severity 6, the robot sustains 6D damage every
// time the location suffers another critical hit": no new effect, only damage.
describe('a location that is already at the worst', () => {
  const ruined: Actor = {
    ...warbot,
    criticals: { armour: { severity: 6, note: '', taken: { protection: 8 } } },
  };

  it('suffers 6D Hits, and does not get worse or take anything more', () => {
    const begun = answer(startFlow(ruined, { round: 4, severity: 1 }), 6);

    expect(prompt(begun)).toEqual({
      kind: 'dice',
      dice: 6,
      why: 'Armour is already at Severity 6: 6D damage',
    });
    const done = answer(begun, 21);

    expect(done.actor.criticals.armour).toMatchObject({ severity: 6, taken: { protection: 8 } });
    // Hits has no floor: it goes below zero, and how far is what says destroyed.
    expect(done.actor.injuries).toEqual([{ when: 4, kind: 'lethal', reductions: { hits: 21 } }]);
  });
});

// Weapon and Options rows say "random weapon" and "random option": the app knows
// neither, so it changes nothing about the robot and leaves the record to say it.
describe('the rows that name a component', () => {
  it('change nothing on the robot, and are on the record for the referee to read', () => {
    const done = answer(startFlow(warbot, { round: 2, severity: 2 }), 5);

    expect(prompt(done)).toBeNull();
    expect(done.actor.criticals.weapon).toMatchObject({ severity: 2, taken: {} });
    expect(done.actor.protection).toBe(8);
    expect(done.log).toEqual(['Weapon, Severity 2: Random weapon disabled']);
  });
});
