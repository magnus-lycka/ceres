<script lang="ts">
  /**
   * The actor library.
   *
   * State is in memory for now: the open question this screen answers is
   * whether the grid makes roster management pleasant, and persistence would
   * add moving parts without informing that. The service is already written
   * and tested on the Python side whenever this is worth wiring up.
   */
  import { renderSnippet } from '@svgrid/grid';

  type CellRow = { row: { original: Actor } };
  import DataGrid, { type GridApi } from '$lib/grid/DataGrid.svelte';
  import ActorHealth from '$lib/actors/ActorHealth.svelte';
  import { healthSummary } from '$lib/rules/rounds/health';
  import { type Actor, type ActorKind, actorKinds, actorSchema } from '$lib/schema/actor';
  import {
    createIdSequence,
    duplicate,
    formatTags,
    highestId,
    newActor,
    parseTags,
  } from '$lib/rules/rounds/library';

  const seed: Actor[] = [
    { id: 1, name: 'Rin', kind: 'sophont', note: '', tags: ['pc'], strength: 8, dexterity: 8, endurance: 8, hits: null, injuries: [] },
    { id: 2, name: 'Sana', kind: 'sophont', note: '', tags: ['pc', 'marduk'], strength: 6, dexterity: 9, endurance: 7, hits: null, injuries: [] },
    { id: 3, name: 'Kes', kind: 'sophont', note: 'medic', tags: ['pc'], strength: 7, dexterity: 7, endurance: 7, hits: null, injuries: [] },
    { id: 4, name: 'Wolf', kind: 'animal', note: '', tags: ['beasts'], strength: null, dexterity: null, endurance: null, hits: 12, injuries: [] },
    { id: 5, name: 'Pirate', kind: 'sophont', note: '', tags: ['pirates', 'marduk'], strength: 7, dexterity: 8, endurance: 6, hits: null, injuries: [] },
    { id: 6, name: 'Warbot', kind: 'robot', note: 'guards the facility', tags: ['marduk'], strength: null, dexterity: null, endurance: null, hits: 20, injuries: [] },
  ];

  let actors = $state<Actor[]>(seed);
  // Seeded once from what was loaded, then never re-derived from `actors`:
  // deleting the highest-numbered actor must not free its id for reuse.
  const ids = createIdSequence(highestId(seed));
  let api = $state<GridApi | null>(null);
  let activeId = $state<number | null>(null);
  let problem = $state('');

  const hurtByHits = (ctx: CellRow) => ctx.row.original.kind !== 'sophont';
  const hurtByCharacteristics = (ctx: CellRow) => ctx.row.original.kind === 'sophont';

  // Only the fields its kind actually uses are editable; the rest stay blank
  // rather than offering a zero that means "no value".
  const characteristicColumns = (
    [
      ['strength', 'STR'],
      ['dexterity', 'DEX'],
      ['endurance', 'END'],
    ] as const
  ).map(([field, header]) => ({
    field,
    header,
    editorType: 'number',
    size: 80,
    editable: hurtByCharacteristics,
  }));

  const columns = [
    { field: 'id', header: 'Id', size: 60 },
    { field: 'name', header: 'Name', editorType: 'text' },
    // Kind is fixed at creation: it decides how the actor absorbs damage, so
    // changing it would invalidate any injury recorded against it. Becoming a
    // different kind of thing means a new actor, not an edited one.
    { field: 'kind', header: 'Kind', editable: false },
    ...characteristicColumns,
    { field: 'hits', header: 'Hits', editorType: 'number', size: 80, editable: hurtByHits },
    {
      field: 'tags',
      header: 'Tags',
      // Free-form chips: a tag is a whole value, not characters in a string.
      editorType: 'chips',
      editorMultiple: true,
      // A paste writes the raw clipboard text into the cell, so parse it back
      // into a tag list; copy the other way as one readable cell.
      valueParser: (p: { newValue: unknown }) => parseTags(p.newValue),
      processCellForClipboard: (p: { value: unknown }) => formatTags(p.value),
      cell: (ctx: { getValue: () => unknown }) => renderSnippet(pills, parseTags(ctx.getValue())),
    },
    { field: 'note', header: 'Note', editorType: 'text' },
    // Derived from the injury history, so never editable here: the health
    // panel below edits the injuries that produce it.
    {
      field: 'health',
      header: 'Health',
      editable: false,
      cell: (ctx: CellRow) => healthSummary(ctx.row.original),
    },
  ];

  function addActor(kind: ActorKind) {
    actors = [...actors, newActor(kind, ids.next())];
  }

  /** The row the focused cell is in, or null when nothing is focused. */
  function activeActor(): Actor | null {
    const cell = api?.getActiveCell();
    return cell ? (actors[cell.rowIndex] ?? null) : null;
  }

  const selected = $derived(actors.find((actor) => actor.id === activeId) ?? null);

  function replace(updated: Actor) {
    actors = actors.map((actor) => (actor.id === updated.id ? updated : actor));
  }

  function duplicateActive() {
    const source = activeActor();
    if (!source) return void (problem = 'Click a row first.');
    actors = [...actors, duplicate(source, ids.next(), actors)];
    problem = '';
  }

  function deleteActive() {
    const doomed = activeActor();
    if (!doomed) return void (problem = 'Click a row first.');
    // No confirmation: deleting is the referee's business, not the app's.
    actors = actors.filter((actor) => actor.id !== doomed.id);
    problem = '';
  }

  function validate() {
    const failures = actors
      .map((actor) => ({ actor, result: actorSchema.safeParse(actor) }))
      .filter(({ result }) => !result.success);
    problem = failures.length
      ? failures.map(({ actor, result }) => `${actor.name || '(unnamed)'}: ${result.error!.issues[0].message}`).join(' · ')
      : `${actors.length} actors, all valid`;
  }
</script>

{#snippet pills(values: string[])}
  {#each values as tag}<span class="pill">{tag}</span>{/each}
{/snippet}

<h1>Actors</h1>

<div class="bar">
  {#each actorKinds as kind}
    <button onclick={() => addActor(kind)}>Add {kind}</button>
  {/each}
  <button onclick={duplicateActive}>Duplicate</button>
  <button onclick={deleteActive}>Delete</button>
  <button onclick={validate}>Validate</button>
</div>

<p class="hint">
  Duplicate and Delete act on the row your cursor is in.
  ⌘Z undoes a cell edit; it does not undo adding or deleting a row.
  Paste a block from a spreadsheet with ⌘V. Drag-select a range and ⌘C to copy one out.
  {#if problem}<strong>{problem}</strong>{/if}
</p>

<DataGrid
  rows={actors}
  {columns}
  onready={(a) => (api = a)}
  oncellclick={() => (activeId = activeActor()?.id ?? null)}
/>

{#if selected}
  <ActorHealth actor={selected} onchange={replace} />
{:else}
  <p class="hint">Click a row to edit its health.</p>
{/if}

<style>
  .bar { display: flex; gap: .5rem; align-items: center; margin-bottom: .5rem; }
  .pill { background: #e2e8f0; border-radius: 9999px; padding: 1px 8px; margin-right: 4px; }
  .hint { color: #555; }
</style>
