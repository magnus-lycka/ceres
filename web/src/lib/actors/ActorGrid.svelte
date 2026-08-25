<script module lang="ts">
  /** Distinguishes each grid's marker stylesheet from any other on the page. */
  let instances = 0;

  function nextGridId(): string {
    instances += 1;
    return `actor-grid-${instances}`;
  }
</script>

<script lang="ts">
  /**
   * The actor roster as a spreadsheet.
   *
   * This component is built on SvGrid and says so: it imports SvGrid's types
   * and uses its column vocabulary directly. An earlier version hid the grid
   * behind a `columns: unknown[]` wrapper and claimed the library was
   * swappable. It was not — the calling page was writing SvGrid column
   * definitions, editor kinds, clipboard callbacks and row semantics, just
   * without the types that would have made the dependency visible. Concealing
   * coupling is worse than containing it.
   *
   * What is contained here is the boundary worth having, and it is expressed
   * in application concepts rather than grid concepts: this component takes
   * actors and reports which actor the referee is looking at. The page above
   * never sees a column, a cell context or a row index. Replacing SvGrid means
   * rewriting this file — a bounded, comprehensible job — and leaves the rest
   * of the application alone.
   *
   * Two SvGrid details worth keeping written down, because both cost a
   * debugging round to find:
   *  - the accessor key is `field`, not TanStack's `accessorKey`. The wrong
   *    name yields the right row count and no cell content.
   *  - `cell` is a function of the cell context returning a render config
   *    (`renderSnippet(...)`), never a bare snippet.
   *
   * Typing the columns against `GridColumns<Actor>` immediately found three
   * things the old `unknown[]` had hidden: `size` is spelled `width` and was
   * being ignored, `processCellForClipboard` is a grid-level prop rather than
   * a column one and was never called, and `field` must name a real key of
   * `Actor` — a computed column such as Health needs `id` and `fieldFn`.
   *
   * Two SvGrid defaults are overridden below. `containerHeight` is a flat
   * 520px whatever the grid holds, which buries anything the page puts under
   * it beneath a screen of blank. `enableRowSummaries` totals every numeric
   * column, and the sum of a set of ids is a number that means nothing.
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
  import { healthSummary } from '$lib/rules/rounds/health';
  import { formatTags, parseTags } from '$lib/rules/rounds/library';
  import type { Actor } from '$lib/schema/actor';

  let {
    actors,
    onselect,
    onedit,
  }: {
    actors: Actor[];
    /** The actor whose row the cursor is in, or null when none is. */
    onselect: (actor: Actor | null) => void;
    /**
     * An actor after a cell edit, so the page can persist it.
     *
     * The grid has already applied the edit to the row in place. The page must
     * store it *without* replacing `actors` — handing SvGrid a new array mid-
     * edit re-renders the grid and throws away the cursor, which is what made
     * keyboard editing feel broken.
     */
    onedit?: (actor: Actor) => void;
  } = $props();

  type Cell = CellContext<Actor>;

  /** Fill for the row and column markers, as a spreadsheet tints them. */
  const MARKER = '#e8f0fe';

  const hurtByHits = (ctx: Cell) => ctx.row.original.kind !== 'sophont';
  const hurtByCharacteristics = (ctx: Cell) => ctx.row.original.kind === 'sophont';

  // Only the fields its kind actually uses are editable; the rest stay blank
  // rather than offering a zero that means "no value".
  const characteristicColumns: GridColumns<Actor> = (
    [
      ['strength', 'STR'],
      ['dexterity', 'DEX'],
      ['endurance', 'END'],
    ] as const
  ).map(([field, header]) => ({
    field,
    header,
    editorType: 'number',
    width: 80,
    editable: hurtByCharacteristics,
  }));

  const columns: GridColumns<Actor> = [
    // Not data to be typed but the row's marker, as a spreadsheet's row
    // header is. Styled below to show which row the cursor is in.
    { field: 'id', header: 'Id', width: 60, editable: false },
    { field: 'name', header: 'Name', editorType: 'text' },
    // Kind is fixed at creation: it decides how the actor absorbs damage, so
    // changing it would invalidate any injury recorded against it. Becoming a
    // different kind of thing means a new actor, not an edited one.
    { field: 'kind', header: 'Kind', editable: false },
    ...characteristicColumns,
    { field: 'hits', header: 'Hits', editorType: 'number', width: 80, editable: hurtByHits },
    {
      field: 'tags',
      header: 'Tags',
      // Free-form chips: a tag is a whole value, not characters in a string.
      editorType: 'chips',
      editorMultiple: true,
      // A paste writes the raw clipboard text into the cell, so parse it back
      // into a tag list; copy the other way as one readable cell.
      valueParser: (p: ValueParserParams<Actor>) => parseTags(p.newValue),
      cell: (ctx: Cell) => renderSnippet(pills, parseTags(ctx.getValue())),
    },
    { field: 'note', header: 'Note', editorType: 'text' },
    // Derived from the injury history, so never editable here: the health
    // panel edits the injuries that produce it. Computed, so it has no `field`
    // — `fieldFn` supplies the value, which also lets it sort and filter.
    { id: 'health', header: 'Health', fieldFn: healthSummary, editable: false },
  ];

  /**
   * Row index is SvGrid's currency and stops here. The page is told which
   * actor the cursor is in, never which row it sits in.
   *
   * Driven by the active cell rather than by clicks, so arrow keys move the
   * selection exactly as the mouse does.
   */
  function report(rowIndex: number) {
    onselect(rowIndex >= 0 ? (actors[rowIndex] ?? null) : null);
  }

  /**
   * The column the cursor is in, so its header can be marked.
   *
   * Which column that is only exists at runtime, and CSS cannot compare one
   * element's attribute against another's — so the rule is written out for
   * whichever column is active, into a stylesheet of our own scoped to this
   * grid. A rule survives SvGrid re-rendering its header on scroll, where a
   * class set on its elements would not.
   */
  let activeColumn = $state<string | null>(null);
  const uid = nextGridId();
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

  let container = $state<HTMLElement | null>(null);
  let api = $state<SvGridApi<TableFeatures, Actor> | null>(null);
  let claimedFocus = false;

  /**
   * Take the keyboard on arrival.
   *
   * Arrow keys are handled by `table.sv-grid-table`, which needs real DOM
   * focus to receive them — so on a fresh load the grid looks ready and
   * ignores every key until it has been tabbed or clicked into. Only claimed
   * when nothing else has focus, so it never steals the caret from someone
   * mid-way through typing.
   */
  $effect(() => {
    if (claimedFocus || actors.length === 0) return;
    const table = container?.querySelector<HTMLElement>('.sv-grid-table');
    const idle = document.activeElement === null || document.activeElement === document.body;
    if (!table || !idle) return;
    claimedFocus = true;
    api?.setActiveCell(0, 0);
    table.focus({ preventScroll: true });
  });
</script>

{#snippet pills(values: string[])}
  {#each values as tag (tag)}<span class="pill">{tag}</span>{/each}
{/snippet}

<div class="grid" id={uid} bind:this={container}>
  <SvGrid
    data={actors}
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
      report(cell?.rowIndex ?? -1);
    }}
    onCellValueChange={(change) => onedit?.(change.row)}
  />
</div>

<style>
  /*
   * Spreadsheet convention, as Google Sheets and Excel use it: the cell you
   * are in gets a frame, and its row marker gets a fill. Row *background* is
   * deliberately left alone — that channel belongs to what an actor is, not
   * to where the cursor is, and the Situation grid needs it for green
   * "can act" and grey "spent".
   */
  .grid {
    /* The excel theme paints both of these Excel green — the ring #107c41 and
       the range wash a 10% tint of it — which is exactly the colour that has
       to mean "can act". */
    --sg-accent: #1a73e8;
    --sg-selection-bg: rgba(26, 115, 232, 0.1);
  }

  /* The cell the cursor is in is framed, never filled: a spreadsheet tints the
     rest of a dragged range but leaves the anchor cell plain. */
  .grid :global(.sv-grid-cell-active[data-selected-range='true']) {
    background: transparent;
  }

  /* The Id column stands in for a spreadsheet's row header. */
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
