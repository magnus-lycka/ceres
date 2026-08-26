/**
 * The health panel, rendered in a real browser.
 *
 * These test what the panel does, not how it is built: which records it offers
 * for which kind of actor, and that an edit reaches the caller as a changed
 * actor. The rules behind the numbers are covered in `rules/rounds`.
 */
import { render } from 'vitest-browser-svelte';
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
    expect(onchange.mock.calls[0][0].criticals.brain).toEqual({ severity: 3, note: '' });
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
