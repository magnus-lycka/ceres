<script lang="ts">
  /**
   * The two ways an actor uses up their place in the turn.
   *
   * Done and Wait are separate buttons rather than one toggle because they are
   * not opposites: Done finishes the round for that actor, Wait lets the turn
   * move on while they keep the right to act. Both disappear once the actor is
   * finished, so the row stops offering what it cannot do.
   */
  import type { MemberState } from '$lib/rules/rounds/situation';

  let {
    state,
    offered = true,
    ondone,
    onwait,
  }: {
    state: MemberState;
    /** False while the fight has not started, or is already over. */
    offered?: boolean;
    ondone: () => void;
    onwait: () => void;
  } = $props();
</script>

{#if !offered}
  <span class="spent"></span>
{:else if state === 'acted'}
  <span class="spent">done</span>
{:else}
  <div class="actions">
    <button type="button" tabindex={-1} onclick={() => ondone()}>Done</button>
    <button type="button" tabindex={-1} onclick={() => onwait()}>Wait</button>
  </div>
{/if}

<style>
  .actions {
    display: flex;
    gap: 4px;
  }

  button {
    background: #fff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    cursor: pointer;
    font: inherit;
    line-height: 1;
    padding: 2px 8px;
  }

  button:hover {
    background: #e8f0fe;
  }

  .spent {
    color: #64748b;
  }
</style>
