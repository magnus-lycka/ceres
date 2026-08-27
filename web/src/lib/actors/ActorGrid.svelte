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
    type CellContext,
    type GridColumns,
    type SvGridApi,
    type TableFeatures,
  } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';
  import { healthSummary } from '$lib/rules/rounds/health';
  import { afterPaste, isPasteKey } from '$lib/grid/pasted';
  import { cellForClipboard, provideTagsForm, tagsColumn } from '$lib/tags/tagsColumn';
  import TagPicker from '$lib/tags/TagPicker.svelte';
  import { distinctTags } from '$lib/schema/tags';
  import type { Actor } from '$lib/schema/actor';

  let {
    actors,
    onselect,
    onedit,
    ontags,
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
    /**
     * An actor whose tags the referee has changed in the form.
     *
     * Unlike `onedit` this is *not* already applied: the form hands back a
     * fresh actor for the page to store and seat, the way the health panel
     * does. Replacing `actors` is safe here — the form has closed, so there is
     * no cursor mid-edit to lose.
     */
    ontags?: (actor: Actor) => void;
  } = $props();

  /** The actor whose tags are being chosen, or null when no form is open. */
  let tagging = $state<Actor | null>(null);

  // A keystroke on a tags cell opens the same form the `+` does. The launcher
  // mounted by the grid has no way of naming its row, so it asks for the row
  // the cursor is in — which is the one it was mounted for.
  provideTagsForm(() => (tagging = activeRow));

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
    tagsColumn<Actor>((actor) => (tagging = actor)),
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
    activeRow = rowIndex >= 0 ? (actors[rowIndex] ?? null) : null;
    onselect(activeRow);
  }

  /**
   * The actor the cursor is in, kept because `TagsLauncher` cannot say which
   * row it was mounted for without handing out a row id.
   */
  let activeRow = $state<Actor | null>(null);

  /**
   * Store the chosen tags, close the form, and put the keyboard back.
   *
   * The row is found again rather than remembered as an index: storing
   * replaces `actors`, and a sorted or filtered grid may seat it elsewhere.
   */
  function applyTags(tags: string[]) {
    const actor = tagging;
    tagging = null;
    if (!actor) return;
    ontags?.({ ...actor, tags });
    focus(actors.findIndex((each) => each.id === actor.id));
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

  /**
   * Persist what a paste changed.
   *
   * SvGrid's paste writes straight into its own row data and, unlike every
   * other way of changing a cell, never fires `onCellValueChange` — so pasted
   * values showed on screen and were never stored, reverting on the next
   * reload. Nor does it run `valueParser`, so a tags cell arrives as raw text.
   *
   * The grid's own rows are the truth about what the paste produced, so after
   * it settles they are compared against what we handed it and anything
   * changed is reported as an edit.
   */
  function persistPaste() {
    afterPaste(
      () => actors,
      () => api?.getData() ?? [],
      (row) => onedit?.(row),
    );
  }

  /**
   * The tags in use across the roster, offered by the form as suggestions.
   *
   * Derived from the actors themselves rather than stored anywhere: a tag
   * exists because an actor carries it, so the two cannot drift apart.
   */
  const vocabulary = $derived(distinctTags(actors));

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
    const idle = document.activeElement === null || document.activeElement === document.body;
    if (!idle) return;
    claimedFocus = focus(0);
  });

  /**
   * Put the keyboard back in the grid, on a given row.
   *
   * Pressing a toolbar button moves focus to that button, and nothing hands it
   * back — so after Add or Delete the arrow keys are dead until the grid is
   * clicked. The page calls this when an action finishes.
   *
   * Moving focus the other way — out of the grid and into a panel — is still
   * to come, and the binding is decided: **Alt/Option plus a letter**, not F6.
   * A MacBook needs fn+F6, which is two hands for what should be a flick.
   *
   * Two things to know when implementing it. SvGrid leaves Alt alone entirely
   * (it only ever tests `altKey` to exclude itself), so those combinations are
   * free, unlike arrows, Home/End, PageUp/Down, Enter, Tab, Space, F2, Delete,
   * Ctrl+F and every printable character, which it has claimed. And on macOS
   * Option+J yields `event.key === '∆'`, so match on `event.code === 'KeyJ'`
   * with `altKey` — reading `event.key` will simply not work.
   */
  export function focus(rowIndex: number): boolean {
    const table = container?.querySelector<HTMLElement>('.sv-grid-table');
    if (!table) return false;
    api?.setActiveCell(Math.max(rowIndex, 0), 0);
    table.focus({ preventScroll: true });
    return true;
  }
</script>

<div
  class="grid"
  id={uid}
  bind:this={container}
  onpastecapture={persistPaste}
  onkeydowncapture={(event) => isPasteKey(event) && persistPaste()}
>
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
    processCellForClipboard={cellForClipboard}
    onApiReady={(ready) => (api = ready)}
    onActiveCellChange={(cell) => {
      activeColumn = cell?.columnId ?? null;
      report(cell?.rowIndex ?? -1);
    }}
    onCellValueChange={(change) => onedit?.(change.row)}
  />
</div>

{#if tagging}
  <!--
    Over the page rather than inside the cell. The grid's own container is the
    scroll container and clips whatever a cell renders, which is what made
    every in-cell popup unusable on the last visible row.
  -->
  <div class="overlay">
    <TagPicker
      subject={tagging.name}
      tags={tagging.tags}
      {vocabulary}
      onapply={applyTags}
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
</style>
