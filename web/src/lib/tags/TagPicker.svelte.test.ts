/**
 * Choosing tags, in a form rather than in a cell.
 *
 * The point of this form is atomicity: a tag is one thing, whatever is inside
 * it. These assertions are mostly about that — typing a tag with a space in it
 * must produce one tag, not two — and about the form never limiting what may
 * be entered to what has been entered before.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@vitest/browser/context';
import { describe, expect, it, vi } from 'vitest';
import TagPicker from './TagPicker.svelte';

async function open(props: Partial<Parameters<typeof TagPicker>[1]> = {}) {
  const onapply = vi.fn();
  const oncancel = vi.fn();
  const screen = await render(TagPicker, {
    subject: 'Rin',
    tags: [],
    vocabulary: [],
    onapply,
    oncancel,
    ...props,
  });
  return { screen, onapply, oncancel };
}

describe('TagPicker', () => {
  it('shows the tags the thing already carries', async () => {
    const { screen } = await open({ tags: ['pc', 'marduk'] });
    await expect.element(screen.getByText('pc', { exact: true })).toBeVisible();
    await expect.element(screen.getByText('marduk', { exact: true })).toBeVisible();
  });

  /**
   * The whole reason for the form. In a text cell this input was a delimited
   * string and the user had to do the splitting; here what is typed is one
   * tag, so a tag may contain anything.
   */
  it('makes one tag of what was typed, spaces and all', async () => {
    const { screen, onapply } = await open();
    await userEvent.fill(screen.getByRole('textbox'), 'player character');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['player character']);
  });

  it('adds on Enter as well, since that is what a form invites', async () => {
    const { screen, onapply } = await open();
    await userEvent.fill(screen.getByRole('textbox'), 'marduk');
    await userEvent.keyboard('{Enter}');
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['marduk']);
  });

  it('offers a tag already in use, so the same tag is not spelled two ways', async () => {
    const { screen, onapply } = await open({ vocabulary: ['marduk', 'pc'] });
    await userEvent.click(screen.getByRole('button', { name: 'Add tag marduk' }));
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['marduk']);
  });

  // Suggestions suggest. Anything may be typed whether or not it is offered,
  // which is exactly what SvGrid's chips editor cannot do.
  it('accepts a tag that is not in the vocabulary at all', async () => {
    const { screen, onapply } = await open({ vocabulary: ['pc'] });
    await userEvent.fill(screen.getByRole('textbox'), 'brand-new');
    await userEvent.keyboard('{Enter}');
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['brand-new']);
  });

  it('narrows what it offers as the tag is typed', async () => {
    const { screen } = await open({ vocabulary: ['marduk', 'pc', 'npc'] });
    await userEvent.fill(screen.getByRole('textbox'), 'mar');
    await expect.element(screen.getByRole('button', { name: 'Add tag marduk' })).toBeVisible();
    expect(screen.container.querySelectorAll('.suggestion')).toHaveLength(1);
  });

  it('does not offer a tag the thing already carries', async () => {
    const { screen } = await open({ tags: ['pc'], vocabulary: ['pc', 'marduk'] });
    await expect.element(screen.getByRole('button', { name: 'Add tag marduk' })).toBeVisible();
    expect(screen.container.querySelector('[aria-label="Add tag pc"]')).toBeNull();
  });

  it('removes a tag that was chosen by mistake', async () => {
    const { screen, onapply } = await open({ tags: ['pc', 'marduk'] });
    await userEvent.click(screen.getByRole('button', { name: 'Remove tag pc' }));
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['marduk']);
  });

  it('does not add the same tag twice', async () => {
    const { screen, onapply } = await open({ tags: ['pc'] });
    await userEvent.fill(screen.getByRole('textbox'), 'pc');
    await userEvent.keyboard('{Enter}');
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }));
    expect(onapply).toHaveBeenCalledWith(['pc']);
  });

  it('leaves the tags alone when the form is abandoned', async () => {
    const { screen, onapply, oncancel } = await open({ tags: ['pc'] });
    await userEvent.fill(screen.getByRole('textbox'), 'oops');
    await userEvent.keyboard('{Enter}');
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(oncancel).toHaveBeenCalled();
    expect(onapply).not.toHaveBeenCalled();
  });

  it('abandons on Escape, as a dialog should', async () => {
    const { screen, oncancel } = await open();
    await userEvent.click(screen.getByRole('textbox'));
    await userEvent.keyboard('{Escape}');
    expect(oncancel).toHaveBeenCalled();
  });

  it('says what is being tagged, since the grid row is behind the form', async () => {
    const { screen } = await open({ subject: 'Warbot' });
    await expect.element(screen.getByText(/Warbot/)).toBeVisible();
  });
});
