<script lang="ts">
  /**
   * Initiative's own cell editor: a native `<input type="number">`, kept
   * uncontrolled while editing.
   *
   * SvGrid's built-in "number" editor is a text input on purpose — committing
   * a native number input's `.value` to the DOM reactively mid-edit loses a
   * lone "-" the moment it is typed (the HTML value sanitization algorithm
   * coerces it to ""), which is exactly the quirk that editor exists to avoid.
   * But that trade also loses the native increment/decrement spinner, and
   * initiative is the one field in the app that is routinely negative (the
   * Effect of a failed DEX or INT check) — worth the spinner back for,
   * especially since clicking it reaches a negative value without typing a
   * minus sign at all, which a keyboard stuck on the wrong input source
   * (Unicode Hex Input, say) can swallow.
   *
   * The DOM value is set once, on mount, and never written back to from this
   * component while editing — only read, on change and commit — so nothing
   * ever stomps on what the browser is already showing mid-keystroke.
   */
  import { onMount } from 'svelte';

  let {
    value = null,
    onChange,
    onCommit,
    onCancel,
  }: {
    value?: number | null;
    onChange?: (value: number | null) => void;
    onCommit?: (value: number | null) => void;
    onCancel?: () => void;
  } = $props();

  let input: HTMLInputElement;

  onMount(() => {
    // A seed from typing directly into a selected cell may be a partial
    // string ("-") that a number input's own value setter cannot hold — it
    // silently becomes "". Leaving the field blank loses nothing further:
    // the alternative is the same keystroke, silently misapplied.
    input.value = value === null ? '' : String(value);
    input.focus();
    input.select();
  });

  function parsed(): number | null {
    const raw = input.value.trim();
    return raw === '' ? null : Number.isFinite(Number(raw)) ? Number(raw) : null;
  }
</script>

<input
  bind:this={input}
  type="number"
  step="1"
  class="sv-grid-cell-editor"
  oninput={() => onChange?.(parsed())}
  onblur={() => onCommit?.(parsed())}
  onkeydown={(event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      onCommit?.(parsed());
    } else if (event.key === 'Escape') {
      event.preventDefault();
      onCancel?.();
    }
  }}
/>
