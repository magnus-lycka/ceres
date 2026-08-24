<script lang="ts">
  /**
   * The one place the application talks to a grid library.
   *
   * Every grid screen goes through this component, so swapping SvGrid for
   * something else is an edit here rather than a rewrite of every screen. That
   * matters more than usual: the choice between SvGrid, SVAR and RevoGrid was
   * made on a spike, not on five years of evidence, and it should stay cheap
   * to revisit.
   *
   * Two SvGrid API details worth keeping written down, because both cost a
   * debugging round to find:
   *  - the accessor key is `field`, not TanStack's `accessorKey`. The wrong
   *    name yields the right row count and no cell content.
   *  - `cell` is a function of the cell context returning a render config
   *    (`renderSnippet(...)`), never a bare snippet.
   */
  import { SvGrid } from '@svgrid/grid';
  import '@svgrid/grid/themes/excel.css';

  type Props = {
    // Deliberately untyped at this boundary: screens describe columns without
    // importing SvGrid's types, so replacing the library touches this file
    // only. The single cast below is the cost of that isolation.
    rows: readonly unknown[];
    columns: readonly unknown[];
    /** Cell-range selection, so ⌘C / ⌘V behave like a spreadsheet. */
    selectionMode?: 'cell' | 'row' | 'both' | 'none';
    editable?: boolean;
    onready?: (api: GridApi) => void;
    /** Fired after the focused cell moves, so a screen can track the row. */
    oncellclick?: () => void;
  };

  /** Only what screens actually use, so the wrapper stays swappable. */
  export type GridApi = {
    undo(): boolean;
    redo(): boolean;
    canUndo(): boolean;
    canRedo(): boolean;
    openFind(): void;
    /** The focused cell, or null when nothing is focused. */
    getActiveCell(): { rowIndex: number; colIndex: number; columnId: string } | null;
  };

  let {
    rows,
    columns,
    selectionMode = 'cell',
    editable = true,
    onready,
    oncellclick,
  }: Props = $props();
</script>

<SvGrid
  data={rows as never}
  columns={columns as never}
  sortable
  filterable
  {selectionMode}
  enableInlineEditing={editable}
  contextMenu
  onApiReady={(api: GridApi) => onready?.(api)}
  onCellClick={() => oncellclick?.()}
/>
