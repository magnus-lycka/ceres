<script lang="ts">
  /**
   * Who this actor last went for, and the way to go for someone.
   *
   * Only the actor whose turn it is may attack, so only their cell is a button.
   * Everyone else's shows the name and does nothing: the column is also how the
   * referee reads who did what to whom.
   */
  let {
    attacker,
    target,
    offered,
    onattack,
  }: {
    attacker: string;
    /** The name of who they last went for, or empty. */
    target: string;
    /** True for the actor whose turn it is, in a round. */
    offered: boolean;
    onattack: () => void;
  } = $props();
</script>

{#if offered}
  <button type="button" tabindex={-1} aria-label="{attacker} attacks" onclick={() => onattack()}>
    {target || '…'}
  </button>
{:else}
  <span class="spent">{target}</span>
{/if}

<style>
  button {
    background: var(--surface);
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    cursor: pointer;
    font: inherit;
    line-height: 1;
    min-width: 4rem;
    padding: 2px 8px;
    text-align: left;
  }

  button:hover {
    background: var(--selected-bg);
  }

  .spent {
    color: var(--muted);
  }
</style>
