<script lang="ts">
  /**
   * Deciding who is in the fight and what they rolled.
   *
   * A different screen from the round table on purpose, because it is a
   * different job with a different grid. Here you sort, filter, type down a
   * column and paste a block in from a spreadsheet — the things a library grid
   * is for, and the way this has always been done in a sheet. There, the order
   * is the turn order and is not yours to change, the colours mean whose turn
   * it is, and nothing is typed at all.
   *
   * Two grids that behaved differently while looking the same would be worse
   * than either. The switch between them is meant to be visible.
   *
   * Four columns is the whole job. Id is here because actor names are not
   * unique — ten chickens may all be called Chicken — so a row has to be
   * tellable from its twin.
   */
  import { SvGrid, type GridColumns, type SvGridApi, type TableFeatures } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';
  import { afterPaste, isPasteKey } from '$lib/grid/pasted';
  import type { Situation } from '$lib/schema/situation';
  import type { Actor, ActorId } from '$lib/schema/actor';

  let {
    situation,
    roster,
    oninitiative,
    onparty,
    onselect,
  }: {
    situation: Situation;
    /** The actors the rows refer to, for their names. */
    roster: Actor[];
    oninitiative: (actor: ActorId, initiative: number | null) => void;
    onparty: (actor: ActorId, party: string) => void;
    /**
     * The actor whose row the cursor is in, or null when none is.
     *
     * Row indices stop here, as in the library grids: the page is told which
     * actor is under the cursor so it can act on that one.
     */
    onselect?: (actor: ActorId | null) => void;
  } = $props();

  type Row = {
    id: ActorId;
    name: string;
    party: string;
    initiative: number | null;
  };

  /**
   * Stored order, not turn order.
   *
   * Sorting is the referee's here — by party to set a side's initiative
   * together, by name to find someone. Imposing turn order would fight that,
   * and turn order is what the round table is for.
   */
  const rows = $derived(
    situation.members.map((member) => ({
      id: member.actor,
      name: roster.find((actor) => actor.id === member.actor)?.name ?? 'unknown',
      party: member.party,
      initiative: member.initiative,
    })),
  );

  const columns: GridColumns<Row> = [
    { field: 'id', header: 'Id', width: 60, editable: false },
    { field: 'name', header: 'Name', editable: false },
    { field: 'party', header: 'Party', editorType: 'text' },
    { field: 'initiative', header: 'Ini', width: 80, editorType: 'number' },
  ];

  let api = $state<SvGridApi<TableFeatures, Row> | null>(null);

  /**
   * Persist what a paste changed.
   *
   * This is how one initiative reaches a whole side: copy the cell, select the
   * rest of the column and paste, exactly as in a spreadsheet. SvGrid's paste
   * writes into its own row data without firing `onCellValueChange`, so
   * without this the values would show and reach the situation never — and
   * these rows are derived from the situation, so they would vanish on the
   * next redraw. See `$lib/grid/pasted`.
   */
  function persistPaste() {
    const before = new Map(rows.map((row) => [row.id, row]));
    afterPaste(
      () => rows,
      () => api?.getData() ?? [],
      (row) => {
        const was = before.get(row.id);
        if (!was) return;
        if (row.party !== was.party) onparty(row.id, String(row.party ?? ''));
        if (row.initiative === was.initiative) return;
        const typed = Number(row.initiative);
        oninitiative(row.id, row.initiative === null || !Number.isFinite(typed) ? null : typed);
      },
    );
  }
</script>

<div
  class="grid"
  onpastecapture={persistPaste}
  onkeydowncapture={(event) => isPasteKey(event) && persistPaste()}
>
  <SvGrid
    data={rows}
    {columns}
    sortable
    filterable
    selectionMode="cell"
    enableInlineEditing
    containerHeight="auto"
    enableRowSummaries={false}
    onApiReady={(ready) => (api = ready)}
    onActiveCellChange={(cell) => {
      const row = cell && cell.rowIndex >= 0 ? (api?.getData()[cell.rowIndex] ?? null) : null;
      onselect?.(row?.id ?? null);
    }}
    onCellValueChange={(change) => {
      if (change.columnId === 'party') {
        onparty(change.row.id, String(change.newValue ?? ''));
        return;
      }
      if (change.columnId !== 'initiative') return;
      const typed = Number(change.newValue);
      oninitiative(change.row.id, Number.isFinite(typed) ? typed : null);
    }}
  />
</div>

<style>
  /*
   * The library grids' blue cursor, and no row colour at all — row background
   * means turn state, and there are no turns here yet.
   */
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
