<script lang="ts">
  /**
   * The actor library.
   *
   * State is in memory for now: the open question this screen answers is
   * whether the grid makes roster management pleasant, and persistence would
   * add moving parts without informing that. The service is already written
   * and tested on the Python side whenever this is worth wiring up.
   *
   * Nothing here knows a grid is involved. `ActorGrid` takes actors and
   * reports which one the cursor is in; columns, cell contexts and row
   * indices stop at that boundary.
   */
  import ActorGrid from '$lib/actors/ActorGrid.svelte';
  import ActorHealth from '$lib/actors/ActorHealth.svelte';
  import { type Actor, type ActorKind, actorKinds, actorSchema } from '$lib/schema/actor';
  import { createIdSequence, duplicate, highestId, newActor } from '$lib/rules/rounds/library';

  const seed: Actor[] = [
    {
      id: 1,
      name: 'Rin',
      kind: 'sophont',
      note: '',
      tags: ['pc'],
      strength: 8,
      dexterity: 8,
      endurance: 8,
      hits: null,
      injuries: [],
      criticals: {},
    },
    {
      id: 2,
      name: 'Sana',
      kind: 'sophont',
      note: '',
      tags: ['pc', 'marduk'],
      strength: 6,
      dexterity: 9,
      endurance: 7,
      hits: null,
      injuries: [],
      criticals: {},
    },
    {
      id: 3,
      name: 'Kes',
      kind: 'sophont',
      note: 'medic',
      tags: ['pc'],
      strength: 7,
      dexterity: 7,
      endurance: 7,
      hits: null,
      injuries: [],
      criticals: {},
    },
    {
      id: 4,
      name: 'Wolf',
      kind: 'animal',
      note: '',
      tags: ['beasts'],
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 12,
      injuries: [],
      criticals: {},
    },
    {
      id: 5,
      name: 'Pirate',
      kind: 'sophont',
      note: '',
      tags: ['pirates', 'marduk'],
      strength: 7,
      dexterity: 8,
      endurance: 6,
      hits: null,
      injuries: [],
      criticals: {},
    },
    {
      id: 6,
      name: 'Warbot',
      kind: 'robot',
      note: 'guards the facility',
      tags: ['marduk'],
      strength: null,
      dexterity: null,
      endurance: null,
      hits: 20,
      injuries: [],
      criticals: {},
    },
  ];

  let actors = $state<Actor[]>(seed);
  // Seeded once from what was loaded, then never re-derived from `actors`:
  // deleting the highest-numbered actor must not free its id for reuse.
  const ids = createIdSequence(highestId(seed));
  let selected = $state<Actor | null>(null);
  let problem = $state('');

  function addActor(kind: ActorKind) {
    actors = [...actors, newActor(kind, ids.next())];
  }

  function replace(updated: Actor) {
    actors = actors.map((actor) => (actor.id === updated.id ? updated : actor));
    selected = updated;
  }

  function duplicateSelected() {
    if (!selected) return void (problem = 'Click a row first.');
    actors = [...actors, duplicate(selected, ids.next(), actors)];
    problem = '';
  }

  function deleteSelected() {
    if (!selected) return void (problem = 'Click a row first.');
    const doomed = selected.id;
    // No confirmation: deleting is the referee's business, not the app's.
    actors = actors.filter((actor) => actor.id !== doomed);
    selected = null;
    problem = '';
  }

  function validate() {
    const failures = actors
      .map((actor) => ({ actor, result: actorSchema.safeParse(actor) }))
      .filter(({ result }) => !result.success);
    problem = failures.length
      ? failures
          .map(({ actor, result }) => `${actor.name || '(unnamed)'}: ${result.error!.issues[0].message}`)
          .join(' · ')
      : `${actors.length} actors, all valid`;
  }
</script>

<h1>Actors</h1>

<div class="bar">
  {#each actorKinds as kind (kind)}
    <button onclick={() => addActor(kind)}>Add {kind}</button>
  {/each}
  <button onclick={duplicateSelected}>Duplicate</button>
  <button onclick={deleteSelected}>Delete</button>
  <button onclick={validate}>Validate</button>
</div>

<p class="hint">
  Duplicate and Delete act on the row your cursor is in. ⌘Z undoes a cell edit; it does not undo adding or
  deleting a row. Paste a block from a spreadsheet with ⌘V. Drag-select a range and ⌘C to copy one out.
  {#if problem}<strong>{problem}</strong>{/if}
</p>

<ActorGrid {actors} onselect={(actor) => (selected = actor)} />

{#if selected}
  <ActorHealth actor={selected} onchange={replace} />
{:else}
  <p class="hint">Click a row to edit its health.</p>
{/if}

<style>
  .bar {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  .hint {
    color: #555;
  }
</style>
