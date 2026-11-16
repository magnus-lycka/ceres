/**
 * Initiative's own cell editor, in a real browser.
 *
 * SvGrid's built-in "number" editor is deliberately a text input (so a typed
 * "-" or "12." on the way to a finished value survives), which trades away the
 * native increment/decrement spinner — a loss that matters here, since
 * initiative is the one field in the app that is commonly negative (the
 * Effect of a failed DEX or INT check), and the spinner is a way to get there
 * without typing a minus sign at all.
 */
import { render } from 'vitest-browser-svelte';
import { userEvent } from 'vitest/browser';
import { describe, expect, it, vi } from 'vitest';
import IniEditor from './IniEditor.svelte';

describe('IniEditor', () => {
  it('is a native number input, with the spinner that comes with one', async () => {
    const screen = await render(IniEditor, { value: 8, onChange: vi.fn(), onCommit: vi.fn() });
    const input = screen.getByRole('spinbutton');
    await expect.element(input).toBeVisible();
    await expect.element(input).toHaveValue(8);
  });

  it('commits a typed negative value on Enter', async () => {
    const onCommit = vi.fn();
    const screen = await render(IniEditor, { value: null, onChange: vi.fn(), onCommit });
    await userEvent.fill(screen.getByRole('spinbutton'), '-2');
    await userEvent.keyboard('{Enter}');
    expect(onCommit).toHaveBeenCalledWith(-2);
  });

  // The spinner reaches a negative value without ever typing a minus sign —
  // a keyboard stuck on a layout that swallows "-" (Unicode Hex Input, say)
  // can still get there.
  it('reaches a negative value from the spinner alone, no typing at all', async () => {
    const onChange = vi.fn();
    const screen = await render(IniEditor, { value: 0, onChange, onCommit: vi.fn() });
    const input = screen.getByRole('spinbutton').element() as HTMLInputElement;
    input.stepDown();
    input.dispatchEvent(new Event('input', { bubbles: true }));
    expect(onChange).toHaveBeenCalledWith(-1);
  });

  it('clears to null rather than zero when emptied', async () => {
    const onCommit = vi.fn();
    const screen = await render(IniEditor, { value: 4, onChange: vi.fn(), onCommit });
    await userEvent.fill(screen.getByRole('spinbutton'), '');
    await userEvent.keyboard('{Enter}');
    expect(onCommit).toHaveBeenCalledWith(null);
  });

  it('cancels on Escape without committing', async () => {
    const onCommit = vi.fn();
    const onCancel = vi.fn();
    const screen = await render(IniEditor, { value: 4, onChange: vi.fn(), onCommit, onCancel });
    await userEvent.fill(screen.getByRole('spinbutton'), '9');
    await userEvent.keyboard('{Escape}');
    expect(onCommit).not.toHaveBeenCalled();
    expect(onCancel).toHaveBeenCalled();
  });
});
