/**
 * Reactions, from refs/core/03_combat.md:190-214 (Reactions, Dodging, Diving
 * for cover, Parrying) and the combat cards, not from the Python.
 *
 * The DMs here are the ones the app can know, tabulated as a reminder before
 * the referee rolls. Nothing in this file is ever applied to a roll: the Effect
 * the referee types already includes them.
 */
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '../../schema/actor';
import { knownModifiers, reactionsAgainst, totalOf } from './reaction';

describe('which reactions there are', () => {
  it('lets a ranged attack be dodged or dived from, and a melee attack dodged or parried', () => {
    expect(reactionsAgainst('ranged')).toEqual(['dodge', 'dive']);
    expect(reactionsAgainst('melee')).toEqual(['dodge', 'parry']);
  });
});

function sophont(dexterity: number, injuries: Actor['injuries'] = []): Actor {
  return {
    id: actorId(1),
    name: 'Guard',
    kind: 'sophont',
    note: '',
    tags: [],
    strength: 8,
    dexterity,
    endurance: 8,
    hits: null,
    injuries,
    criticals: {},
    protection: 0,
    movement: null,
    speed: null,
    enduranceHours: null,
    int: null,
  };
}

describe('the DM a Dodge puts on the attack', () => {
  // "a penalty equal to their DEX DM or Athletics (dexterity), whichever is
  // higher" (:196). The app holds DEX, not Athletics, so it can offer the DEX
  // DM and say that is what it is.
  it('is the defender’s DEX DM as a penalty to the attacker', () => {
    expect(knownModifiers({ defender: sophont(12), reaction: 'dodge', attack: 'ranged' })).toEqual([
      { label: 'Dodge (DEX DM)', dm: -2 },
    ]);
    expect(knownModifiers({ defender: sophont(9), reaction: 'dodge', attack: 'melee' })[0].dm).toBe(-1);
  });

  // Damage impairs the characteristic, and the impaired DM is the one that
  // counts until it is healed (:267).
  it('uses the DEX the defender has left, not the one they started with', () => {
    const hurt = sophont(12, [{ when: null, kind: 'lethal', reductions: { dexterity: 4 } }]);

    expect(knownModifiers({ defender: hurt, reaction: 'dodge', attack: 'ranged' })[0].dm).toBe(0);
  });

  it('cannot help the attacker, however poor the DEX', () => {
    const clumsy = sophont(2);

    expect(knownModifiers({ defender: clumsy, reaction: 'dodge', attack: 'melee' })[0].dm).toBe(0);
  });

  // An animal or a robot has no DEX in the model, so what it would dodge with
  // is unknown, and the reminder says so rather than inventing a number.
  it('is unknown for something that has no DEX to look at', () => {
    const wolf: Actor = {
      ...sophont(8),
      kind: 'animal',
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 12,
    };

    expect(knownModifiers({ defender: wolf, reaction: 'dodge', attack: 'melee' })).toEqual([
      { label: 'Dodge', dm: null },
    ]);
  });

  // "A Traveller diving for cover will inflict a DM-2 on the attack roll of
  // every attacker who targets them" (:204).
  it('is −2 for diving for cover, which only a ranged attack allows', () => {
    expect(knownModifiers({ defender: sophont(8), reaction: 'dive', attack: 'ranged' })).toEqual([
      { label: 'Dive for cover', dm: -2 },
    ]);
    expect(knownModifiers({ defender: sophont(8), reaction: 'dive', attack: 'melee' })).toEqual([]);
  });

  // "inflict their Melee skill as a negative DM" (:212). The app holds no skills.
  it('is unknown for a parry, which is the defender’s Melee skill', () => {
    expect(knownModifiers({ defender: sophont(8), reaction: 'parry', attack: 'melee' })).toEqual([
      { label: 'Parry (Melee skill)', dm: null },
    ]);
    expect(knownModifiers({ defender: sophont(8), reaction: 'parry', attack: 'ranged' })).toEqual([]);
  });

  it('is nothing when there is no reaction', () => {
    expect(knownModifiers({ defender: sophont(12), reaction: null, attack: 'ranged' })).toEqual([]);
  });

  // "A shotgun using pellet ammunition ignores Dodge dice modifiers" (:827).
  it('is nothing against a Shotgun, which ignores what a Dodge would cost it', () => {
    expect(
      knownModifiers({ defender: sophont(12), reaction: 'dodge', attack: 'ranged', shotgun: true }),
    ).toEqual([{ label: 'Dodge (ignored by a Shotgun)', dm: 0 }]);
  });
});

describe('adding up what is known', () => {
  it('sums the known DMs', () => {
    expect(
      totalOf([
        { label: 'a', dm: -2 },
        { label: 'b', dm: -1 },
      ]),
    ).toEqual({ dm: -3, complete: true });
    expect(totalOf([])).toEqual({ dm: 0, complete: true });
  });

  // A total that leaves out a DM the app could not know would read as the whole
  // truth, so it says it is not.
  it('says so when a DM could not be known, and adds only the rest', () => {
    expect(
      totalOf([
        { label: 'a', dm: -2 },
        { label: 'b', dm: null },
      ]),
    ).toEqual({ dm: -2, complete: false });
  });
});
