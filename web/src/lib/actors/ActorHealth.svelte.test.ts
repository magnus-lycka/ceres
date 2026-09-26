/**
 * The health panel, rendered in a real browser.
 *
 * These test what the panel does, not how it is built: which records it offers
 * for which kind of actor, and that an edit reaches the caller as a changed
 * actor. The rules behind the numbers are covered in `rules/rounds`.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { describe, expect, it, vi } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import ActorHealth from './ActorHealth.svelte';

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
  protection: 0,
  movement: null,
  speed: null,
  enduranceHours: null,
  int: null,
};

const rin: Actor = {
  ...warbot,
  id: actorId(1),
  name: 'Rin',
  kind: 'sophont',
  strength: 8,
  dexterity: 8,
  endurance: 8,
  hits: null,
};

describe('ActorHealth', () => {
  // What decides how a hit lands and how far they get, so it is on the panel
  // for every kind, not only the ones with a critical record.
  it('shows Protection, Movement and Speed, the speed by name', async () => {
    const guard: Actor = { ...rin, protection: 5, movement: 6, speed: 1 };
    const screen = await render(ActorHealth, { actor: guard, onchange: vi.fn() });

    await expect.element(screen.getByLabelText('Protection')).toHaveValue(5);
    await expect.element(screen.getByLabelText('Movement (m)')).toHaveValue(6);
    await expect.element(screen.getByLabelText('Speed')).toHaveDisplayValue('Idle');
  });

  // A robot's Endurance is hours of operation, not the END a sophont's damage
  // erodes; offering it to a sophont would put two Endurances on one panel.
  it('shows hours of endurance and INT for a robot, and only for a robot', async () => {
    const bot: Actor = { ...warbot, enduranceHours: 40, int: 5 };
    const robot = await render(ActorHealth, { actor: bot, onchange: vi.fn() });
    await expect.element(robot.getByLabelText('Endurance (hours)')).toHaveValue(40);
    await expect.element(robot.getByLabelText('INT')).toHaveValue(5);
    robot.unmount();

    const sophont = await render(ActorHealth, { actor: rin, onchange: vi.fn() });
    await expect.element(sophont.getByLabelText('Endurance (hours)')).not.toBeInTheDocument();
    await expect.element(sophont.getByLabelText('INT')).not.toBeInTheDocument();
  });

  it('reports a changed Protection to the caller as a changed actor', async () => {
    const onchange = vi.fn();
    const screen = await render(ActorHealth, { actor: rin, onchange });

    await screen.getByLabelText('Protection').fill('4');
    await userEvent.tab();

    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ id: rin.id, protection: 4 }));
  });

  it('stores a chosen Speed as its band number, and unsets it with the dash', async () => {
    const onchange = vi.fn();
    const screen = await render(ActorHealth, { actor: { ...rin, speed: 1 }, onchange });

    await screen.getByLabelText('Speed').selectOptions('Medium');
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ speed: 4 }));

    await screen.getByLabelText('Speed').selectOptions('—');
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ speed: null }));
  });

  // Blank is unset, not zero: a Movement of 0 says something a blank does not.
  it('commits Movement, hours and INT as numbers, and a blank as unset', async () => {
    const onchange = vi.fn();
    const screen = await render(ActorHealth, {
      actor: { ...warbot, movement: 6, enduranceHours: 40, int: 5 },
      onchange,
    });

    await screen.getByLabelText('Movement (m)').fill('1.5');
    await userEvent.tab();
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ movement: 1.5 }));

    await screen.getByLabelText('Movement (m)').fill('');
    await userEvent.tab();
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ movement: null }));

    await screen.getByLabelText('Endurance (hours)').fill('12.5');
    await userEvent.tab();
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ enduranceHours: 12.5 }));

    await screen.getByLabelText('INT').fill('3');
    await userEvent.tab();
    expect(onchange).toHaveBeenLastCalledWith(expect.objectContaining({ int: 3 }));
  });

  // "Being prone will quarter a Traveller's Movement score" (:162). The stored
  // Movement is what the actor is; the hint is what it comes to on the ground.
  it('says what Movement comes to while prone, and only then', async () => {
    const guard: Actor = { ...rin, movement: 6 };

    const down = await render(ActorHealth, { actor: guard, prone: true, onchange: vi.fn() });
    await expect.element(down.getByText('prone: 1.5 m')).toBeVisible();
    down.unmount();

    const standing = await render(ActorHealth, { actor: guard, onchange: vi.fn() });
    await expect.element(standing.getByText(/prone:/)).not.toBeInTheDocument();
    standing.unmount();

    const unset = await render(ActorHealth, { actor: rin, prone: true, onchange: vi.fn() });
    await expect.element(unset.getByText(/prone:/)).not.toBeInTheDocument();
  });

  // The table's own sentence for the severity the row is at, so the referee does
  // not have to look it up in the handbook to know what the number means.
  it('says what each critical does, in the table’s words', async () => {
    const hurt: Actor = {
      ...warbot,
      criticals: {
        armour: { severity: 2, note: '', taken: { protection: 3 } },
        brain: { severity: 4, note: '', taken: { int: 3 } },
      },
    };
    const screen = await render(ActorHealth, { actor: hurt, onchange: vi.fn() });

    await expect.element(screen.getByText('Protection -1D')).toBeVisible();
    await expect.element(screen.getByText('Robot INT halved')).toBeVisible();
    // Undamaged rows say nothing.
    expect(screen.container.querySelectorAll('.effect:not(:empty)')).toHaveLength(2);
  });

  // The base is what the robot is and stays editable; what is left of it is
  // shown beside it once a critical has taken something off.
  it('shows what is left of an attribute a critical has reduced, and nothing when none has', async () => {
    const hurt: Actor = {
      ...warbot,
      protection: 8,
      movement: 6,
      criticals: { armour: { severity: 2, note: '', taken: { protection: 5 } } },
    };
    const screen = await render(ActorHealth, { actor: hurt, onchange: vi.fn() });

    await expect.element(screen.getByText('now 3')).toBeVisible();
    expect(screen.container.textContent).not.toContain('now 6');
  });

  it('names what is left of Speed as a band, and shows hours and metres with their units', async () => {
    const hurt: Actor = {
      ...warbot,
      movement: 6,
      speed: 4,
      enduranceHours: 40,
      criticals: {
        power: { severity: 3, note: '', taken: { speed: 1, movement: 1, enduranceHours: 30 } },
      },
    };
    const screen = await render(ActorHealth, { actor: hurt, onchange: vi.fn() });

    await expect.element(screen.getByText('now Slow')).toBeVisible();
    await expect.element(screen.getByText('now 5 m')).toBeVisible();
    await expect.element(screen.getByText('now 10 h')).toBeVisible();
  });

  it('keeps a critical record for a robot', async () => {
    const screen = await render(ActorHealth, { actor: warbot, onchange: vi.fn() });
    await expect.element(screen.getByText('Criticals')).toBeVisible();
    await expect.element(screen.getByLabelText('locomotion severity')).toBeVisible();
  });

  // Only a robot has systems to lose; a sophont has no power supply or brain
  // in this sense, and the panel must not offer the record.
  it('offers no critical record to anything else', async () => {
    const screen = await render(ActorHealth, { actor: rin, onchange: vi.fn() });
    expect(screen.container.querySelector('.record')).toBeNull();
  });

  it('reports a severity change to the caller as a changed actor', async () => {
    const onchange = vi.fn();
    const screen = await render(ActorHealth, { actor: warbot, onchange });

    await screen.getByLabelText('brain severity').selectOptions('S3');

    expect(onchange).toHaveBeenCalledTimes(1);
    expect(onchange.mock.calls[0][0].criticals.brain).toEqual({ severity: 3, note: '', taken: {} });
  });

  it('offers robots physical damage rather than recoverable stun', async () => {
    const screen = await render(ActorHealth, { actor: warbot, onchange: vi.fn() });

    await expect.element(screen.getByText('Stunners cause physical Hits to robots.')).toBeVisible();
    expect(screen.container.querySelector('option[value="stun"]')).toBeNull();
    await expect.element(screen.getByLabelText('Injury kind')).toHaveValue('lethal');
  });

  // Stun is deducted from END alone, so the form must not offer STR or DEX —
  // stun that reached them could kill, which it never can.
  it('offers stun on one stat only, where lethal offers three', async () => {
    const screen = await render(ActorHealth, { actor: rin, onchange: vi.fn() });
    const entries = () => screen.container.querySelectorAll('.add input[type=number]');
    expect(entries()).toHaveLength(3);

    await screen.getByLabelText('Injury kind').selectOptions('stun');

    await vi.waitFor(() => expect(entries()).toHaveLength(1));
  });
});
