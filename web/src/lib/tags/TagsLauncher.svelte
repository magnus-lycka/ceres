<script lang="ts">
  /**
   * The editor that isn't one.
   *
   * The tags column has to stay editable, because SvGrid's paste silently
   * skips a cell that is not — `isCellEditableAt` in its `applyPastedText`
   * decides that, so `editable: false` would quietly cost us pasted tags. But
   * an editable cell is one that F2, a double-click, or simply typing a letter
   * will open an editor in, and a text editor over a tag list is exactly the
   * trap we removed: it invites a delimited string.
   *
   * So the column registers this instead. It renders nothing, commits nothing,
   * and closes itself immediately, asking the grid around it to open the form.
   * Every route into a tags cell then arrives at the same place.
   */
  import { onMount } from 'svelte';
  import type { CellEditorContext } from '@svgrid/grid';
  import { useTagsForm } from './tagsColumn';

  let { onCancel }: CellEditorContext = $props();

  // Read while the component initialises, which is the only time context is
  // in scope. The callback itself is used later, from the microtask below.
  const open = useTagsForm();

  onMount(() => {
    // The grid mounts this from inside its own edit bookkeeping. Closing the
    // edit synchronously would unmount us mid-mount, so let that finish first.
    queueMicrotask(() => {
      onCancel();
      open();
    });
  });
</script>
