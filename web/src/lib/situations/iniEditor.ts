/**
 * Registers `IniEditor` as a named cell-editor type, the way `tagsColumn.ts`
 * registers tags — once, at module load, so any grid's column can name it.
 */
import { registerCellEditor } from '@svgrid/grid';
import IniEditor from './IniEditor.svelte';

/**
 * A distinct editor for Initiative, over the library's own "number" type:
 * initiative is routinely negative (the Effect of a failed DEX or INT
 * check), and the native spinner this editor keeps is a way to get there
 * without typing a minus sign — see `IniEditor` for why that matters.
 */
export const INI_EDITOR = 'ceres-ini';

registerCellEditor(INI_EDITOR, IniEditor);
