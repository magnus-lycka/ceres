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
  import {
    SvGrid,
    renderSnippet,
    type CellContext,
    type GridColumns,
    type SvGridApi,
    type TableFeatures,
    type ValueParserParams,
  } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';
  import { afterPaste, isPasteKey } from '$lib/grid/pasted';
  import { formatTags, parseTags } from '$lib/schema/tags';
  import type { Party } from '$lib/schema/party';

  let {
    parties,
    onselect,
    onedit,
  }: {
    parties: Party[];
    onselect: (party: Party | null) => void;
    /** A party after a cell edit; the page persists it without redrawing. */
    onedit?: (party: Party) => void;
  } = $props();

  type Cell = CellContext<Party>;

  const MARKER = '#e8f0fe';
  const uid = nextGridId();

  const columns: GridColumns<Party> = [
    { field: 'id', header: 'Id', width: 60, editable: false },
    { field: 'name', header: 'Name', editorType: 'text' },
    {
      field: 'tags',
      header: 'Tags',
      // Plain text, split on commit. The chips editor mis-places its popup
      // over the row below and drops keystrokes; tags are short and a space
      // separated string is a better thing to type than a widget.
      editorType: 'text',
      // Without this an edit stores the raw string, which the schema then
      // refuses to read back — and one such file hid every party.
      valueParser: (p: ValueParserParams<Party>) => parseTags(p.newValue),
      cell: (ctx: Cell) => renderSnippet(pills, parseTags(ctx.getValue())),
    },
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

{#snippet pills(values: string[])}
  {#each values as tag (tag)}<span class="pill">{tag}</span>{/each}
{/snippet}

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
    processCellForClipboard={(p) => (p.columnId === 'tags' ? formatTags(p.value) : p.value)}
    onApiReady={(ready) => (api = ready)}
    onActiveCellChange={(cell) => {
      activeColumn = cell?.columnId ?? null;
      onselect(cell && cell.rowIndex >= 0 ? (parties[cell.rowIndex] ?? null) : null);
    }}
    onCellValueChange={(change) => onedit?.(change.row)}
  />
</div>

<style>
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
  .pill {
    background: #e2e8f0;
    border-radius: 9999px;
    padding: 1px 8px;
    margin-right: 4px;
  }
</style>
