<script lang="ts">
  /**
   * The lasting states an actor is in, as tags the referee clears.
   *
   * Prone is the one there is. It clears only by its ×, on purpose: getting up is
   * a Minor Action nobody tracks, so the referee says when it has happened, and a
   * stray click on the row must not lose it.
   */
  import type { Condition } from '$lib/schema/situation';

  let {
    actor,
    conditions,
    onclear,
  }: {
    actor: string;
    conditions: Condition[];
    onclear: (condition: Condition) => void;
  } = $props();
</script>

{#each conditions as condition (condition)}
  <span class="tag">
    {condition}
    <button
      type="button"
      tabindex={-1}
      aria-label="Clear {condition} for {actor}"
      onclick={() => onclear(condition)}
    >
      ×
    </button>
  </span>
{/each}

<style>
  .tag {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    background: var(--warning-bg, #fef3c7);
    border-radius: 4px;
    padding: 0 4px;
  }

  button {
    background: none;
    border: 0;
    cursor: pointer;
    font: inherit;
    line-height: 1;
    padding: 0 2px;
  }
</style>
