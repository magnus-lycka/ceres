<script lang="ts">
  /**
   * A table with the details of what is picked beside it, never below it.
   *
   * Below, the details fall off the bottom of any long list and the referee
   * scrolls to find what they just clicked. Beside, they stay where the eye
   * already is. The panel column is sticky and scrolls on its own, so neither a
   * long table nor a tall panel pushes the other out of view.
   */
  import type { Snippet } from 'svelte';

  let { children, panels }: { children: Snippet; panels: Snippet } = $props();
</script>

<div class="workspace">
  <div class="table">{@render children()}</div>
  <aside class="panels">{@render panels()}</aside>
</div>

<style>
  .workspace {
    display: flex;
    gap: 1.5rem;
    align-items: flex-start;
  }
  .table {
    flex: 1;
    min-width: 0;
  }
  .panels {
    flex: 0 0 26rem;
    position: sticky;
    top: 1rem;
    max-height: calc(100vh - 2rem);
    overflow: auto;
  }
</style>
