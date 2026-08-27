<script lang="ts">
  /**
   * A tag list as a grid cell shows it: the tags, and a way in to the form.
   *
   * The cell displays and invites; it never edits. Everything about choosing
   * tags lives in `TagPicker`, which has room for it. That split is what makes
   * the tags column ordinary — no popup fighting the grid's clipping, no
   * editor squeezed into a column three tags wide.
   */
  let {
    tags,
    onedit,
  }: {
    tags: string[];
    /** Open the form for this row. */
    onedit: () => void;
  } = $props();
</script>

<div class="cell">
  {#each tags as tag (tag)}<span class="pill">{tag}</span>{/each}
  <!--
    Kept out of the tab order: this button exists once per row, and tabbing
    through a library of them to reach anything else would be miserable. The
    grid's own keyboard model — arrow to the cell, Enter — is the keyboard
    route in.
  -->
  <button type="button" tabindex={-1} aria-label="Edit tags" onclick={() => onedit()}>+</button>
</div>

<style>
  .cell {
    display: flex;
    align-items: center;
    gap: 4px;
    overflow: hidden;
  }

  .pill {
    background: #e2e8f0;
    border-radius: 9999px;
    padding: 1px 8px;
    white-space: nowrap;
  }

  /* Sits at the end of the tags rather than in a column of its own, so a row
     with no tags still offers the way in. */
  button {
    flex: none;
    background: none;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    cursor: pointer;
    color: #475569;
    line-height: 1;
    padding: 1px 5px;
  }

  button:hover {
    background: #e8f0fe;
  }
</style>
