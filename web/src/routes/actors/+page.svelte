<script lang="ts">
  /**
   * The actor library.
   *
   * Backed by the data repository once one is connected, and by nothing at all
   * before that: without a repository this is a scratch pad that forgets
   * everything on reload, which is honest about what it is.
   *
   * Nothing here knows a grid is involved. `ActorGrid` takes actors and
   * reports which one the cursor is in; columns, cell contexts and row
   * indices stop at that boundary.
   */
  import { resolve } from '$app/paths';
  import ActorGrid from '$lib/actors/ActorGrid.svelte';
  import ActorHealth from '$lib/actors/ActorHealth.svelte';
  import { GitHubFileStore } from '$lib/store/github';
  import { Library } from '$lib/store/library';
  import { loadConnection } from '$lib/store/connection';
  import { type Actor, type ActorKind, actorKinds, actorSchema } from '$lib/schema/actor';
  import { duplicate, newActor } from '$lib/rules/rounds/library';

  let actors = $state<Actor[]>([]);
  let library = $state<Library | null>(null);
  // The id rather than the actor: `actors` is replaced on every save, and an
  // actor held directly would go stale the moment its row was rewritten.
  let selectedId = $state<number | null>(null);
  const selected = $derived(actors.find((actor) => actor.id === selectedId) ?? null);
  let problem = $state('');
  let grid = $state<ReturnType<typeof ActorGrid> | null>(null);
  // How many writes are in flight. The buttons stay disabled until the repo
  // has answered, because pressing Add again while the first is still going is
  // exactly what produced a screen full of duplicate ids.
  let busy = $state(0);

  // Reconnect from what this browser already knows, so a reload lands back on
  // the same data rather than on an empty screen and a form.
  $effect(() => {
    const settings = loadConnection();
    if (settings && !library) connected(new Library(new GitHubFileStore(settings)));
  });

  async function connected(next: Library | null) {
    library = next;
    actors = next ? await next.actors() : [];
    selectedId = null;
  }

  /**
   * Every change goes through here, so the screen only ever shows what the
   * repository accepted. A save that fails leaves the grid alone rather than
   * seating an actor that does not exist anywhere.
   */
  async function keep(work: () => Promise<void>) {
    busy += 1;
    // One change at a time. Each of these reads `actors`, awaits the
    // repository, and writes `actors` back — so two running at once both
    // start from the same list and the second silently discards the first.
    // That is what made the grid disagree with what had actually been stored.
    const mine = gate.then(async () => {
      try {
        problem = '';
        await work();
      } catch (failure) {
        problem = failure instanceof Error ? failure.message : String(failure);
      }
    });
    gate = mine;
    await mine;
    busy -= 1;
  }

  let gate: Promise<void> = Promise.resolve();

  /** Saved when there is a repository; otherwise it stays in this browser. */
  async function store(actor: Actor): Promise<Actor> {
    return library ? await library.saveActor(actor) : { ...actor, id: actor.id || nextScratchId() };
  }

  // Without a repository there is no counter to allocate from, so the scratch
  // pad keeps its own. Ids still only climb.
  let scratch = 0;
  function nextScratchId(): number {
    scratch = Math.max(scratch, ...actors.map((actor) => actor.id), 0) + 1;
    return scratch;
  }

  function addActor(kind: ActorKind) {
    return keep(async () => {
      const saved = await store(newActor(kind, 0));
      actors = [...actors, saved];
      // On the new row, ready to type its name.
      grid?.focus(actors.length - 1);
    });
  }

  /** From the health panel, which hands back a new actor object. */
  function replace(updated: Actor) {
    return keep(async () => {
      const saved = await store(updated);
      actors = actors.map((actor) => (actor.id === saved.id ? saved : actor));
    });
  }

  /**
   * From the grid, which has already applied the edit to the row in place.
   * Only the repository needs telling — replacing `actors` here would re-render
   * the grid out from under the cursor.
   */
  function edited(actor: Actor) {
    return keep(async () => void (await store(actor)));
  }

  function duplicateSelected() {
    if (!selected) return void (problem = 'Click a row first.');
    const source = selected;
    return keep(async () => {
      const copy = await store({ ...duplicate(source, 0, actors), id: 0 });
      actors = [...actors, copy];
      grid?.focus(actors.length - 1);
    });
  }

  function deleteSelected() {
    if (!selected) return void (problem = 'Click a row first.');
    const doomed = selected.id;
    // No confirmation: deleting is the referee's business, not the app's.
    return keep(async () => {
      await library?.deleteActor(doomed);
      const gone = actors.findIndex((actor) => actor.id === doomed);
      actors = actors.filter((actor) => actor.id !== doomed);
      selectedId = null;
      grid?.focus(Math.min(gone, actors.length - 1));
    });
  }

  function validate() {
    const failures = actors
      .map((actor) => ({ actor, result: actorSchema.safeParse(actor) }))
      .filter(({ result }) => !result.success);
    problem = failures.length
      ? failures
          .map(({ actor, result }) => `${actor.name || '(unnamed)'}: ${result.error!.issues[0].message}`)
          .join(' \u00b7 ')
      : `${actors.length} actors, all valid`;
  }
</script>

<h1>Actors</h1>

{#if !library}
  <p class="hint">
    No data repository, so nothing is being saved. Set one up under
    <a href={resolve('/sync')}>Sync</a>.
  </p>
{/if}

<div class="bar">
  {#each actorKinds as kind (kind)}
    <button onclick={() => addActor(kind)} disabled={busy > 0}>Add {kind}</button>
  {/each}
  <button onclick={duplicateSelected} disabled={busy > 0}>Duplicate</button>
  <button onclick={deleteSelected} disabled={busy > 0}>Delete</button>
  <button onclick={validate}>Validate</button>
  {#if busy > 0}<span class="busy">saving…</span>{/if}
</div>

{#if problem}<p class="problem">{problem}</p>{/if}

<p class="hint">
  Duplicate and Delete act on the row your cursor is in. ⌘Z undoes a cell edit; it does not undo adding or
  deleting a row. Paste a block from a spreadsheet with ⌘V. Drag-select a range and ⌘C to copy one out.
</p>

<ActorGrid bind:this={grid} {actors} onselect={(actor) => (selectedId = actor?.id ?? null)} onedit={edited} />

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
  .busy {
    color: #555;
  }
  .problem {
    background: #fef2f2;
    border-left: 3px solid #b91c1c;
    color: #7c2c1a;
    padding: 0.4rem 0.75rem;
    margin: 0 0 0.5rem;
  }
</style>
