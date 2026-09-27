/**
 * What each critical hit does: the Critical Hit Effects table of the Robot
 * Handbook (refs/robot/50_other_considerations.md:132-143), as data.
 *
 * `text` is the table's own wording, for the referee to read. The other fields
 * are what the app acts on, and are there only where it can: a weapon or an
 * option is "random", and the app knows neither, so those rows are text and the
 * referee records which one (docs/plan-rounds.md, "Explicitly deferred").
 *
 * Nothing here rolls. A cell that costs dice says how many, and the referee
 * rolls them.
 */
import type { CriticalLocation } from '../../schema/actor';

/** A loss that is a fixed number, or so many dice of it. */
export type Amount = { flat: number } | { dice: number };

export type CriticalEffect = {
  /** As the table words it. */
  text: string;
  /**
   * "Speed reduced by 1m or one Speed Band." Worded here as Movement and Speed
   * (CONTEXT.md), the two attributes the table's one word conflates: Locomotion
   * takes it from either, Power supply from both (RIC-020).
   */
  pace?: number;
  /** Protection lost. */
  protection?: Amount;
  /** "Remaining Endurance halved". */
  enduranceHalved?: boolean;
  /** "Robot INT halved". */
  intHalved?: boolean;
  /** "Chassis Severity +1", or "+1D": the Chassis critical steps up by this. */
  chassis?: Amount;
  /** Hits the critical itself inflicts, in dice: the Chassis row. It ignores Protection. */
  damageDice?: number;
  /** The robot can do nothing: shut down, or its brain gone. */
  inoperable?: boolean;
  /** "Robot immobilised". Only movement is lost: usable weapons may still fire. */
  immobilised?: boolean;
};

const CHASSIS_ONE = { chassis: { flat: 1 } } as const;
const PACE = 'Movement reduced by 1 m or Speed by one Band';
const PACE_BOTH = 'Movement reduced by 1 m and Speed by one Band';

/** Severities 1 to 6, in order, for each location. */
const effects: Record<CriticalLocation, CriticalEffect[]> = {
  power: [
    { text: PACE_BOTH, pace: 1 },
    { text: 'Remaining Endurance halved', enduranceHalved: true },
    { text: 'Remaining Endurance halved again', enduranceHalved: true },
    { text: 'Remaining Endurance halved again', enduranceHalved: true },
    {
      text: 'Power supply explodes. Robot shuts down. Chassis Severity +1',
      inoperable: true,
      ...CHASSIS_ONE,
    },
    {
      text: 'Power supply explodes. Robot shuts down. Chassis Severity +1D',
      inoperable: true,
      chassis: { dice: 1 },
    },
  ],
  weapon: [
    { text: 'Random weapon suffers DM-2 to attack rolls' },
    { text: 'Random weapon disabled' },
    { text: 'Random weapon destroyed' },
    { text: 'Random weapon explodes. Chassis Severity +1', ...CHASSIS_ONE },
    { text: 'Random weapon explodes. Chassis Severity +1', ...CHASSIS_ONE },
    { text: 'Random weapon explodes. Chassis Severity +1', ...CHASSIS_ONE },
  ],
  armour: [
    { text: 'Protection -1', protection: { flat: 1 } },
    { text: 'Protection -1D', protection: { dice: 1 } },
    { text: 'Protection -1D', protection: { dice: 1 } },
    { text: 'Protection -2D', protection: { dice: 2 } },
    { text: 'Protection -2D, Chassis Severity +1', protection: { dice: 2 }, ...CHASSIS_ONE },
    { text: 'Protection -2D. Chassis Severity +1', protection: { dice: 2 }, ...CHASSIS_ONE },
  ],
  chassis: [1, 2, 3, 4, 5, 6].map((dice) => ({ text: `Robot suffers ${dice}D damage`, damageDice: dice })),
  locomotion: [
    { text: PACE, pace: 1 },
    { text: PACE, pace: 1 },
    { text: PACE, pace: 1 },
    { text: PACE, pace: 1 },
    { text: 'Robot immobilised', immobilised: true },
    { text: 'Robot immobilised. Chassis Severity +1', immobilised: true, ...CHASSIS_ONE },
  ],
  options: [
    { text: 'Random option suffers DM-2' },
    { text: 'Random option disabled' },
    { text: 'Random option destroyed' },
    { text: 'Two random options destroyed' },
    { text: 'Random option destroyed. Chassis Severity +1', ...CHASSIS_ONE },
    { text: 'Random option destroyed. Chassis Severity +1', ...CHASSIS_ONE },
  ],
  brain: [
    { text: 'DM-2 to one skill' },
    { text: 'DM-2 to all skills' },
    { text: 'Robot unable to perform any skills' },
    { text: 'Robot INT halved', intHalved: true },
    { text: 'Robot brain disabled', inoperable: true },
    { text: 'Robot brain destroyed. Chassis Severity +1', inoperable: true, ...CHASSIS_ONE },
  ],
};

/** What a location does at a severity, or null for undamaged (0) or past the worst (7 and up). */
export function criticalEffect(location: CriticalLocation, severity: number): CriticalEffect | null {
  return effects[location][severity - 1] ?? null;
}
