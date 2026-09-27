/**
 * Working one hit through a robot's criticals.
 *
 * A hit can start a chain: an attack critical needs a location, an effect can ask
 * for dice, and an effect can raise the Chassis, which suffers damage of its
 * own. The app rolls nothing, so the chain is a queue of questions for the
 * referee and this is the step function that answers them one at a time.
 */
import {
  WORST_SEVERITY,
  type Actor,
  type Critical,
  type CriticalLocation,
  type RobotAttribute,
} from '../../schema/actor';
import { criticalEffect, type Amount } from './criticalEffects';
import { takeDamage } from './damage';
import { severityAfter } from './criticals';
import { currentAttribute } from './robotState';
import { cumulativeHitsDamage, isDead } from './health';
import { sustainedCriticalCount } from './criticals';

/**
 * The location a 2D roll gives (refs/robot/50_other_considerations.md:100-109),
 * or null for a total 2D cannot make.
 */
export function locationFor(roll: number): CriticalLocation | null {
  if (roll < 2 || roll > 12) return null;
  if (roll <= 4) return 'power';
  if (roll === 5) return 'weapon';
  if (roll === 6) return 'armour';
  if (roll === 7) return 'chassis';
  if (roll <= 9) return 'locomotion';
  if (roll <= 11) return 'options';
  return 'brain';
}

/** What a roll of dice is for, once the referee has made it. */
type DiceUse = { use: 'protection'; location: CriticalLocation } | { use: 'hits' } | { use: 'chassisSteps' };

/** What the flow is waiting on. */
type Task =
  | { t: 'location'; severity: number; why: string }
  | { t: 'dice'; dice: number; why: string; then: DiceUse }
  | { t: 'pace'; location: CriticalLocation; why: string }
  | { t: 'chassis'; steps: Amount; why: string };

/** A hit's criticals, part way through: the robot as it stands, what is still to ask, and what has been done. */
export type Flow = {
  actor: Actor;
  /** The round of the situation, for stamping any Hits the criticals inflict. */
  round: number;
  tasks: Task[];
  log: string[];
};

/** What the referee is asked for next. */
export type Prompt =
  | { kind: 'location'; why: string }
  | { kind: 'dice'; dice: number; why: string }
  | { kind: 'pace'; why: string };

/** A choice between the two things "1m or one Speed Band" can take. */
export type Choice = 'movement' | 'speed';

/** Begin with one critical of this severity, whose location is still to be rolled. */
export function startFlow(
  actor: Actor,
  { round, severity = 0, sustained = 0 }: { round: number; severity?: number; sustained?: number },
): Flow {
  const tasks: Task[] = [];
  if (severity > 0) tasks.push({ t: 'location', severity, why: `Attack critical, Severity ${severity}` });
  for (let i = 0; i < sustained; i += 1) {
    tasks.push({ t: 'location', severity: 1, why: 'Sustained damage threshold, Severity 1' });
  }
  return { actor, round, tasks, log: [] };
}

/** The question the referee has to answer next, or null when the hit is worked through. */
export function prompt(flow: Flow): Prompt | null {
  const task = flow.tasks[0];
  if (!task || task.t === 'chassis') return null;
  if (task.t === 'dice') return { kind: 'dice', dice: task.dice, why: task.why };
  return { kind: task.t, why: task.why };
}

const NAMES: Record<CriticalLocation, string> = {
  power: 'Power supply',
  weapon: 'Weapon',
  armour: 'Armour',
  chassis: 'Chassis',
  locomotion: 'Locomotion',
  options: 'Options',
  brain: 'Brain',
};

/** Speed Band Number of Idle: at or below it there is no band to lose in place of a metre. */
const IDLE = 1;

const blank = (): Critical => ({ severity: 0, note: '', taken: {} });

/** Take some of an attribute off, as this location's critical: never more than is left. */
function takeOff(actor: Actor, location: CriticalLocation, attribute: RobotAttribute, amount: number): Actor {
  const left = currentAttribute(actor, attribute) ?? 0;
  const taking = Math.min(amount, left);
  if (taking <= 0) return actor;
  const critical = actor.criticals[location] ?? blank();
  const taken = { ...critical.taken, [attribute]: (critical.taken[attribute] ?? 0) + taking };
  return { ...actor, criticals: { ...actor.criticals, [location]: { ...critical, taken } } };
}

/** A location's critical has reached a severity: record it, apply what the table says, and queue what it asks for. */
function reach(flow: Flow, rest: Task[], location: CriticalLocation, severity: number): Flow {
  const critical = flow.actor.criticals[location] ?? blank();
  let actor: Actor = {
    ...flow.actor,
    criticals: { ...flow.actor.criticals, [location]: { ...critical, severity } },
  };
  const effect = criticalEffect(location, severity);
  const why = `${NAMES[location]}, Severity ${severity}: ${effect?.text ?? ''}`;
  const asks: Task[] = [];
  if (effect?.protection) {
    if ('flat' in effect.protection) actor = takeOff(actor, location, 'protection', effect.protection.flat);
    else asks.push({ t: 'dice', dice: effect.protection.dice, why, then: { use: 'protection', location } });
  }
  if (effect?.pace) {
    const amount = effect.pace;
    if (location === 'power') {
      // A failing power supply slows the whole robot: both Movement and Speed.
      actor = takeOff(takeOff(actor, location, 'movement', amount), location, 'speed', amount);
    } else if ((currentAttribute(actor, 'speed') ?? 0) > IDLE) {
      // Only here is "1m or one Speed Band" a choice.
      asks.push({ t: 'pace', location, why });
    } else {
      actor = takeOff(actor, location, 'movement', amount);
    }
  }
  if (effect?.enduranceHalved) {
    // Half of what is left goes, and the hours may come out fractional.
    actor = takeOff(actor, location, 'enduranceHours', (currentAttribute(actor, 'enduranceHours') ?? 0) / 2);
  }
  if (effect?.intHalved) {
    // INT is a characteristic: halved, and rounded down.
    const int = currentAttribute(actor, 'int') ?? 0;
    actor = takeOff(actor, location, 'int', int - Math.floor(int / 2));
  }
  if (effect?.damageDice) asks.push({ t: 'dice', dice: effect.damageDice, why, then: { use: 'hits' } });
  if (effect?.chassis) {
    // What is asked is the step and where it comes from, not the whole sentence.
    const step = 'flat' in effect.chassis ? `+${effect.chassis.flat}` : `+${effect.chassis.dice}D`;
    asks.push({
      t: 'chassis',
      steps: effect.chassis,
      why: `${NAMES[location]}, Severity ${severity}: Chassis Severity ${step}`,
    });
  }
  return { ...flow, actor, tasks: [...asks, ...rest], log: [...flow.log, why] };
}

/** The Chassis is stepped up: to the severity reached, or, if it was already at the worst, 6D more. */
function stepChassis(flow: Flow, steps: number): Flow {
  const previous = flow.actor.criticals.chassis?.severity ?? 0;
  if (previous >= WORST_SEVERITY) return worstAgain(flow, 'chassis');
  return reach(flow, flow.tasks, 'chassis', Math.min(WORST_SEVERITY, previous + steps));
}

/** "Once a location is already Severity 6 ... 6D damage every time": another hit there is 6D Hits. */
function worstAgain(flow: Flow, location: CriticalLocation): Flow {
  const why = `${NAMES[location]} is already at Severity 6: 6D damage`;
  return {
    ...flow,
    tasks: [{ t: 'dice', dice: 6, why, then: { use: 'hits' } }, ...flow.tasks],
    log: [...flow.log, why],
  };
}

/** Run whatever needs no answer from the referee, until the next thing that does. */
function settle(flow: Flow): Flow {
  let current = flow;
  for (;;) {
    const [task, ...rest] = current.tasks;
    if (task?.t !== 'chassis') return current;
    current =
      'flat' in task.steps
        ? stepChassis({ ...current, tasks: rest }, task.steps.flat)
        : {
            ...current,
            tasks: [
              { t: 'dice', dice: task.steps.dice, why: task.why, then: { use: 'chassisSteps' } },
              ...rest,
            ],
          };
  }
}

/**
 * A rolled location does not always apply: the robot has no such weapon or
 * option (`:110`, "if the location does not exist, reroll"), or a hardened
 * brain "negates the effects of all critical hits affecting the brain; these
 * critical hits are ignored, not re-rolled" (`refs/robot/50_other_considerations.md:31`).
 * Ceres does not model either fact, so the referee says which applies.
 *
 * A reroll is nothing more than asking the same question again: the app never
 * learns what was rolled, so there is no state to undo. Discard drops it: the
 * critical is abandoned, applying nothing.
 */
export function discard(flow: Flow): Flow {
  const [task, ...rest] = flow.tasks;
  if (!task || task.t !== 'location') return flow;
  return { ...flow, tasks: rest, log: [...flow.log, `${task.why} (discarded: does not apply)`] };
}

/**
 * Extra Hits damage from a critical is damage like any other: it can itself
 * cross a sustained-damage threshold. Once it wrecks the robot, no further
 * location is asked for the rest of this resolution (RIC-019) — the remaining
 * queued ones are dropped, though the damage already applied stands.
 */
function withSustainedFrom(flow: Flow, before: Actor): Flow {
  if (isDead(flow.actor)) {
    return { ...flow, tasks: flow.tasks.filter((task) => task.t !== 'location') };
  }
  const count = sustainedCriticalCount(
    flow.actor.hits ?? 0,
    cumulativeHitsDamage(before),
    cumulativeHitsDamage(flow.actor),
  );
  const queued: Task[] = Array.from({ length: count }, () => ({
    t: 'location',
    severity: 1,
    why: 'Sustained damage threshold, Severity 1',
  }));
  return { ...flow, tasks: [...flow.tasks, ...queued] };
}

/** A roll of dice has been made: carry out what it was for. */
function rolled(flow: Flow, rest: Task[], task: Extract<Task, { t: 'dice' }>, total: number): Flow {
  const next = { ...flow, tasks: rest };
  const use = task.then;
  if (use.use === 'chassisSteps') {
    return stepChassis({ ...next, log: [...next.log, `Rolled ${total}: Chassis Severity +${total}`] }, total);
  }
  if (use.use === 'hits') {
    // Extra damage from a critical ignores Protection, so it is not reduced.
    const actor = takeDamage(next.actor, { lethal: total, at: next.round }).actor;
    return withSustainedFrom(
      { ...next, actor, log: [...next.log, `Rolled ${total}: ${total} Hits`] },
      next.actor,
    );
  }
  const actor = takeOff(next.actor, use.location, 'protection', total);
  return { ...next, actor, log: [...next.log, `Rolled ${total}: Protection -${total}`] };
}

/** The pace lost, from the one chosen. */
function paced(flow: Flow, rest: Task[], task: Extract<Task, { t: 'pace' }>, choice: Choice): Flow {
  const effect = criticalEffect(task.location, flow.actor.criticals[task.location]?.severity ?? 0);
  const actor = takeOff(flow.actor, task.location, choice, effect?.pace ?? 0);
  return { ...flow, actor, tasks: rest, log: [...flow.log, `Taken from ${choice}`] };
}

/**
 * The referee's answer to the question asked: a roll of dice, or a choice.
 * Anything that is not an answer to it leaves the flow as it is.
 */
export function answer(flow: Flow, value: number | Choice): Flow {
  const [task, ...rest] = flow.tasks;
  if (!task || task.t === 'chassis') return flow;
  if (task.t === 'pace')
    return value === 'movement' || value === 'speed' ? settle(paced(flow, rest, task, value)) : flow;
  if (typeof value !== 'number') return flow;
  if (task.t === 'dice') {
    const possible = Number.isInteger(value) && value >= task.dice && value <= task.dice * 6;
    return possible ? settle(rolled(flow, rest, task, value)) : flow;
  }
  const location = locationFor(value);
  if (location === null) return flow;
  const previous = flow.actor.criticals[location]?.severity ?? 0;
  const next = { ...flow, tasks: rest };
  if (previous >= WORST_SEVERITY) return settle(worstAgain(next, location));
  return settle(reach(next, rest, location, severityAfter(previous, task.severity)));
}
