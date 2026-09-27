/**
 * The round table's compact indicator of a robot's damaged systems: whether it
 * is worth opening the record, not the record itself.
 */
import { render } from 'vitest-browser-svelte';
import { describe, expect, it } from 'vitest';
import { actorId, type Actor } from '$lib/schema/actor';
import CriticalsCell from './CriticalsCell.svelte';

const at = (severity: number) => ({ severity, note: '', taken: {} });

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

describe('CriticalsCell', () => {
  it('says nothing for an undamaged robot, or for anything that has no systems', async () => {
    const undamaged = await render(CriticalsCell, { actor: warbot() });
    expect(undamaged.container.textContent?.trim()).toBe('');

    const sophont = await render(CriticalsCell, { actor: { ...warbot(), kind: 'sophont' } });
    expect(sophont.container.textContent?.trim()).toBe('');
  });

  it('says how many locations are hit and the worst of them', async () => {
    const hurt = warbot({ armour: at(4), weapon: at(2) });

    const screen = await render(CriticalsCell, { actor: hurt });

    expect(screen.container.textContent?.trim()).toBe('2 hit, worst S4');
  });

  it('is red in proportion to the score, and pins the heat to the DOM for the theme rule to use', async () => {
    const hurt = warbot({ armour: at(4) });

    const screen = await render(CriticalsCell, { actor: hurt });
    const span = screen.container.querySelector<HTMLElement>('.crit-heat')!;

    // Score 16, heat = 16 * 8 = 128.
    await expect.poll(() => span.style.getPropertyValue('--crit-heat')).toBe('128');
  });
});
