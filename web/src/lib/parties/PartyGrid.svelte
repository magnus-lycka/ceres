<script module lang="ts">
  /** Distinguishes each grid's marker stylesheet from any other on the page. */
  let instances = 0;

  function nextGridId(): string {
    instances += 1;
    return `party-grid-${instances}`;
  }
</script>

<script lang="ts">
  /**
   * The party list as a spreadsheet.
   *
   * Built on SvGrid openly, as `ActorGrid` is, and for the same reason: the
   * column vocabulary is this library's and hiding it behind a generic wrapper
   * would conceal the coupling rather than contain it. The boundary worth
   * having is this one — parties in, selected party out.
   */
  import { SvGrid, type GridColumns, type SvGridApi, type TableFeatures } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';
  import { afterPaste, isPasteKey } from '$lib/grid/pasted';
  import { cellForClipboard, provideTagsForm, tagsColumn } from '$lib/tags/tagsColumn';
  import TagPicker from '$lib/tags/TagPicker.svelte';
  import { distinctTags } from '$lib/schema/tags';
  import type { Party } from '$lib/schema/party';

  let {
    parties,
    onselect,
    onedit,
    ontags,
  }: {
    parties: Party[];
    onselect: (party: Party | null) => void;
    /** A party after a cell edit; the page persists it without redrawing. */
    onedit?: (party: Party) => void;
    /**
     * A party whose tags the form changed. Not already applied — the page
     * stores it and seats it, as `ActorGrid` describes at more length.
     */
    ontags?: (party: Party) => void;
  } = $props();

  /** The party whose tags are being chosen, or null when no form is open. */
  let tagging = $state<Party | null>(null);
  /** The party the cursor is in, for the form opened by a keystroke. */
  let activeRow = $state<Party | null>(null);

  // A keystroke on a tags cell opens the same form the `+` does.
  provideTagsForm(() => (tagging = activeRow));
  const vocabulary = $derived(distinctTags(parties));

  const MARKER = '#e8f0fe';
  const uid = nextGridId();

  const columns: GridColumns<Party> = [
    { field: 'id', header: 'Id', width: 60, editable: false },
    { field: 'name', header: 'Name', editorType: 'text' },
    tagsColumn<Party>((party) => (tagging = party)),
    { field: 'note', header: 'Note', editorType: 'text' },
    // Members as stored, including any whose actor has since been deleted:
    // a party that looks short is telling you something true.
    {
      id: 'size',
      header: 'Members',
      width: 90,
      editable: false,
      fieldFn: (party: Party) => party.actors.length,
    },
  ];

  let api = $state<SvGridApi<TableFeatures, Party> | null>(null);

  /**
   * Persist what a paste changed. SvGrid's paste writes into its own row data
   * without firing `onCellValueChange`, so pasted values showed on screen and
   * were never stored. See `ActorGrid` for the longer note.
   */
  function persistPaste() {
    afterPaste(
      () => parties,
      () => api?.getData() ?? [],
      (row) => onedit?.(row),
    );
  }

  let activeColumn = $state<string | null>(null);
  let sheet: HTMLStyleElement | null = null;

  $effect(() => {
    sheet ??= document.head.appendChild(document.createElement('style'));
    sheet.textContent = activeColumn
      ? `#${uid} th[data-svgrid-header-col="${activeColumn}"] { background: ${MARKER}; }`
      : '';
  });

  $effect(() => () => {
    sheet?.remove();
    sheet = null;
  });
</script>

<div
  class="grid"
  id={uid}
  onpastecapture={persistPaste}
  onkeydowncapture={(event) => isPasteKey(event) && persistPaste()}
>
  <SvGrid
    data={parties}
    {columns}
    sortable
    filterable
    selectionMode="cell"
    enableInlineEditing
    contextMenu
    containerHeight="auto"
    enableRowSummaries={false}
    processCellForClipboard={cellForClipboard}
    onApiReady={(ready) => (api = ready)}
    onActiveCellChange={(cell) => {
      activeColumn = cell?.columnId ?? null;
      activeRow = cell && cell.rowIndex >= 0 ? (parties[cell.rowIndex] ?? null) : null;
      onselect(activeRow);
    }}
    onCellValueChange={(change) => onedit?.(change.row)}
  />
</div>

{#if tagging}
  <!-- Over the page: the grid's container clips whatever a cell renders. -->
  <div class="overlay">
    <TagPicker
      subject={tagging.name}
      tags={tagging.tags}
      {vocabulary}
      onapply={(tags) => {
        const party = tagging;
        tagging = null;
        if (party) ontags?.({ ...party, tags });
      }}
      oncancel={() => (tagging = null)}
    />
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: grid;
    place-items: center;
    background: rgba(15, 23, 42, 0.3);
  }

  /* Same channels as the actor grid: frame for the cursor, fill for the row
     and column markers, row background left alone. */
  .grid {
    --sg-accent: #1a73e8;
    --sg-selection-bg: rgba(26, 115, 232, 0.1);
  }
  .grid :global(.sv-grid-cell-active[data-selected-range='true']) {
    background: transparent;
  }
  .grid :global(tr:has(.sv-grid-cell-active) td[data-col-id='id']) {
    background: #e8f0fe;
    font-weight: 600;
  }
</style>
