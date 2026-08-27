/**
 * What a tag list is, in a grid.
 *
 * One definition, used by every grid that shows tags. `$lib/schema/tags` owns
 * what a tag list *is*; this owns how one *appears in a spreadsheet*, which is
 * a different question with a different reason to change. The two grids used
 * to answer it twice, in two files, with the clipboard half in a third place.
 */
import { getContext, setContext } from 'svelte';
import { registerCellEditor, renderComponent, type GridColumns } from '@svgrid/grid';
import { formatTags, parseTags } from '$lib/schema/tags';
import TagsCell from './TagsCell.svelte';
import TagsLauncher from './TagsLauncher.svelte';

/** Anything a tags column can be put on. */
export type Tagged = { tags: string[] };

/**
 * The editor type name for a tags cell.
 *
 * Naming a *registered* editor rather than a built-in one is load-bearing: it
 * keeps the cell editable, so SvGrid's paste will write to it, while making
 * every attempt to edit it open the form instead of a text box. See
 * `TagsLauncher` for why the cell cannot simply be marked uneditable.
 */
const TAGS_EDITOR = 'ceres-tags';

/** The field a tags column reads, named once so the clipboard rule agrees. */
const TAGS_FIELD = 'tags';

registerCellEditor(TAGS_EDITOR, TagsLauncher);

/**
 * How `TagsLauncher` reaches the grid that mounted it.
 *
 * The editor registry is global — one registration serves every grid on the
 * page — so the launcher cannot be handed anything grid-specific through it.
 * Context can: SvGrid mounts the editor inside its own component tree, which
 * is inside the grid component's, so what that component provided is in scope.
 *
 * This carries no row. The launcher opens the form for the row the cursor is
 * already in, which is the row it was mounted for, and the grid component
 * knows which actor or party that is without anyone passing a row id around.
 */
const OPEN_TAGS_FORM = Symbol('ceres.tags.open');

/** Called by a grid component: open the tags form for the active row. */
export function provideTagsForm(open: () => void): void {
  setContext(OPEN_TAGS_FORM, open);
}

/**
 * Called by the launcher, while it initialises: how to ask for the form.
 *
 * Must be read during initialisation — that is the only time context is in
 * scope — so this returns the callback rather than calling it.
 */
export function useTagsForm(): () => void {
  const open = getContext<(() => void) | undefined>(OPEN_TAGS_FORM);
  return open ?? (() => {});
}

/**
 * The Tags column.
 *
 * `onedit` is handed the row whose `+` was pressed; the caller opens the form
 * and stores the result. Row indices and cell contexts stop here.
 */
export function tagsColumn<T extends Tagged>(onedit: (row: T) => void): GridColumns<T>[number] {
  return {
    field: TAGS_FIELD,
    header: 'Tags',
    editorType: TAGS_EDITOR,
    // Sorting and filtering both stringify the array, so neither is
    // tag-aware: `contains "pc"` matches an actor tagged `npc`, and the value
    // checklist offers whole combinations rather than tags. Left on because
    // substring matching is still useful, but it is not set membership.
    cell: (ctx) =>
      renderComponent(TagsCell, {
        tags: parseTags(ctx.getValue()),
        onedit: () => onedit(ctx.row.original),
      }),
  };
}

/**
 * How a cell goes onto the clipboard, tags included.
 *
 * `processCellForClipboard` is a grid-level prop in SvGrid rather than a
 * column one, so this cannot live in the column definition above — but it is
 * the same decision, and it belongs in the same file rather than being spelled
 * out again in every grid. Pass it straight to `processCellForClipboard`.
 */
export function cellForClipboard({ value, columnId }: { value: unknown; columnId: string }): unknown {
  return columnId === TAGS_FIELD ? formatTags(value) : value;
}
