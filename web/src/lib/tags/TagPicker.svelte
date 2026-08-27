<script lang="ts">
  /**
   * Choosing the tags on one thing.
   *
   * A form rather than a cell editor, because a tag list is not the shape a
   * spreadsheet cell has: it needs room for the tags already chosen, room for
   * the ones in use elsewhere, and an input that is not three characters wide.
   * Squeezing that into a cell is what made every in-cell attempt unpleasant.
   *
   * The rule this form exists to keep: what is typed becomes **one** tag,
   * whatever is inside it. Nothing here splits on anything. Text is only a
   * transport at the clipboard boundary — see `$lib/schema/tags` — and this is
   * not that boundary.
   *
   * The vocabulary is offered, never enforced. A tag that has never been used
   * before is typed the same way as one that has, which is precisely what
   * SvGrid's chips editor cannot do: supplying it options turns off free entry.
   */
  let {
    subject,
    tags,
    vocabulary,
    onapply,
    oncancel,
  }: {
    /** What is being tagged, named — the row itself is hidden behind this. */
    subject: string;
    tags: string[];
    /** Tags already in use, offered as suggestions. Never a restriction. */
    vocabulary: string[];
    onapply: (tags: string[]) => void;
    oncancel: () => void;
  } = $props();

  // A working copy: nothing reaches the caller until Apply, so abandoning the
  // form leaves the thing exactly as it was. Deliberately the value `tags` had
  // when the form opened — the form is mounted fresh for each thing tagged,
  // and must not follow the row while it is being edited.
  // svelte-ignore state_referenced_locally
  let chosen = $state<string[]>([...tags]);
  let draft = $state('');

  const suggestions = $derived(
    vocabulary
      .filter((tag) => !chosen.includes(tag))
      .filter((tag) => tag.toLowerCase().includes(draft.trim().toLowerCase())),
  );

  /** Whole, trimmed, and only once. Trimming is padding, not separating. */
  function add(tag: string) {
    const wanted = tag.trim();
    if (wanted && !chosen.includes(wanted)) chosen = [...chosen, wanted];
    draft = '';
  }

  function remove(tag: string) {
    chosen = chosen.filter((each) => each !== tag);
  }
</script>

<div
  class="picker"
  role="dialog"
  tabindex={-1}
  aria-label="Tags for {subject}"
  onkeydown={(event) => {
    if (event.key === 'Escape') oncancel();
  }}
>
  <h2>Tags — {subject}</h2>

  <div class="chosen">
    {#each chosen as tag (tag)}
      <span class="pill">
        <!-- The label is its own element so that it is the tag and nothing
             else — the remove button's text would otherwise be part of it. -->
        <span>{tag}</span>
        <button type="button" aria-label="Remove tag {tag}" onclick={() => remove(tag)}>×</button>
      </span>
    {:else}
      <p class="none">No tags yet.</p>
    {/each}
  </div>

  <div class="entry">
    <input
      type="text"
      placeholder="New or existing tag"
      bind:value={draft}
      onkeydown={(event) => {
        if (event.key !== 'Enter') return;
        // The form's own default action would submit and close it.
        event.preventDefault();
        add(draft);
      }}
    />
    <button type="button" onclick={() => add(draft)} disabled={!draft.trim()}>Add</button>
  </div>

  {#if suggestions.length > 0}
    <div class="suggestions">
      {#each suggestions as tag (tag)}
        <button type="button" class="pill suggestion" aria-label="Add tag {tag}" onclick={() => add(tag)}
          >{tag}</button
        >
      {/each}
    </div>
  {/if}

  <div class="actions">
    <button type="button" onclick={() => oncancel()}>Cancel</button>
    <button type="button" class="primary" onclick={() => onapply(chosen)}>Apply</button>
  </div>
</div>

<style>
  .picker {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 320px;
    max-width: 480px;
    padding: 16px;
    background: #fff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
  }

  h2 {
    margin: 0;
    font-size: 1rem;
  }

  .chosen,
  .suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  /* Enough room to read the vocabulary without the form growing without
     bound — the list is every tag in the library. */
  .suggestions {
    max-height: 8rem;
    overflow-y: auto;
    padding-top: 8px;
    border-top: 1px solid #e2e8f0;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e2e8f0;
    border: 0;
    border-radius: 9999px;
    padding: 2px 8px;
    font: inherit;
  }

  .suggestion {
    cursor: pointer;
  }

  .pill button {
    background: none;
    border: 0;
    cursor: pointer;
    padding: 0 2px;
    line-height: 1;
  }

  .none {
    margin: 0;
    color: #64748b;
  }

  .entry {
    display: flex;
    gap: 8px;
  }

  .entry input {
    flex: 1;
    padding: 4px 8px;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .primary {
    font-weight: 600;
  }
</style>
