<script lang="ts">
  import { onMount } from 'svelte';
  import { replaceState } from '$app/navigation';
  import { resolve } from '$app/paths';
  import {
    characters,
    apiRoot,
    type Character,
    type CharacterListItem,
    type Values,
  } from '$lib/characters/api';
  import Decision from '$lib/characters/Decision.svelte';
  import { sourceFromCharacter } from '$lib/characters/link';
  import CharacterSheet from '$lib/characters/CharacterSheet.svelte';
  import { library, refresh } from '$lib/store/session.svelte';
  let items = $state<CharacterListItem[]>([]);
  let character = $state<Character | null>(null);
  let name = $state('');
  let player = $state('NPC');
  let busy = $state(false);
  let problem = $state('');
  let checked = $state<number[]>([]);
  let added = $state<number | null>(null);
  onMount(() => {
    void load();
  });
  async function work(action: () => Promise<void>) {
    if (busy) return;
    busy = true;
    problem = '';
    try {
      await action();
    } catch (e) {
      problem = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }
  function load() {
    return work(async () => {
      items = await characters.list();
      const id = Number(new URL(location.href).searchParams.get('id'));
      if (id) character = await characters.get(id);
    });
  }
  function show(view: Character | null) {
    character = view;
    added = null;
    const url = new URL(location.href);
    if (view) url.searchParams.set('id', String(view.id));
    else url.searchParams.delete('id');
    replaceState(view ? resolve(`/characters?id=${view.id}`) : resolve('/characters'), {});
  }
  function open(id: number) {
    return work(async () => show(await characters.get(id)));
  }
  function create(event: SubmitEvent) {
    event.preventDefault();
    return work(async () => {
      show(await characters.create(name.trim(), player.trim() || 'NPC'));
      name = '';
    });
  }
  function choose(values: Values) {
    const current = character;
    if (!current?.pending) return;
    return work(async () => {
      character = await characters.choose(current.id, current.pending!.id, values);
    });
  }
  function undo() {
    const current = character;
    if (current)
      return work(async () => {
        character = await characters.undo(current.id);
      });
  }
  function remove(ids: number[]) {
    if (!confirm(`Delete ${ids.length} character(s)? This cannot be undone.`)) return;
    return work(async () => {
      for (const id of ids) await characters.remove(id);
      checked = [];
      show(null);
      items = await characters.list();
    });
  }
  function back() {
    show(null);
    return load();
  }
  function addActor() {
    const current = character;
    if (!current?.finished) return;
    return work(async () => {
      const actor = await library.addCharacter(sourceFromCharacter(current));
      await refresh();
      added = actor.id;
    });
  }
</script>

<svelte:head><title>Characters · Ceres</title></svelte:head>
<header>
  <h1>Characters</h1>
  <p>Create a Traveller, follow their career, and bring them into play.</p>
</header>
{#if problem}<div class="problem" role="alert">
    {problem} <button disabled={busy} onclick={load}>Retry</button>
  </div>{/if}
{#if busy}<p role="status">Working…</p>{/if}
{#if character}
  <div class="toolbar">
    <button disabled={busy} onclick={back}>All characters</button>
    <button disabled={busy} onclick={undo}>Undo last step</button>
    <!-- API download, not an application route. -->
    <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
    <a href={`${apiRoot}/characters/${character.id}/pdf`}>Download PDF</a>
    <button disabled={busy} onclick={() => remove([character!.id])}>Delete character</button>
  </div>
  <div class="creation">
    <section class="decision" aria-label="Current decision">
      {#if character.term_status}<p class="term-status">{character.term_status}</p>{/if}
      {#if character.pending}<h2>Next decision</h2>
        {#key character.pending.id}<Decision pending={character.pending} {busy} onsubmit={choose} />{/key}
      {:else}<h2>Character creation complete</h2>
        <p>{character.name} is ready for play.</p>
        <button disabled={busy} onclick={addActor}>Add to actors</button>{/if}
      {#if added !== null}<p>
          Added to the actor library. <a href={resolve(`/actors?id=${added}`)}>Open actor</a>
        </p>{/if}
      {#if character.changes.length}<section class="changes" aria-live="polite">
          <h3>What happened</h3>
          <ul>
            {#each character.changes as change, i (i)}<li>{change}</li>{/each}
          </ul>
        </section>{/if}
    </section>
    <aside><CharacterSheet {character} /></aside>
  </div>
{:else}
  <form class="new" onsubmit={create}>
    <h2>New character</h2>
    <label>Name<input bind:value={name} required /></label><label>Player<input bind:value={player} /></label
    ><button disabled={busy || !name.trim()}>Create character</button>
  </form>
  <section>
    <h2>Saved characters</h2>
    <button disabled={busy || !checked.length} onclick={() => remove(checked)}>Delete selected</button>
    <div class="table">
      <table>
        <thead><tr><th>Select</th><th>Name</th><th>Sophont</th><th>Player</th></tr></thead><tbody>
          {#each items as item (item.id)}<tr
              ><td
                ><input
                  type="checkbox"
                  aria-label={`Select ${item.name}`}
                  value={item.id}
                  bind:group={checked}
                /></td
              ><td><button disabled={busy} onclick={() => open(item.id)}>{item.name}</button></td><td
                >{item.sophont}</td
              ><td>{item.player}</td></tr
            >{/each}
        </tbody>
      </table>
    </div>
    {#if !items.length && !busy && !problem}<p>No characters yet.</p>{/if}
  </section>
{/if}

<style>
  header p {
    color: var(--muted);
  }
  .toolbar {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
    margin: 1rem 0;
  }
  .creation {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(18rem, 1fr);
    gap: 2rem;
    align-items: start;
  }
  .decision,
  aside,
  .new {
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 1.4rem;
    background: var(--surface);
  }
  .decision h2 {
    margin-top: 0;
  }
  .new {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: end;
    margin: 1rem 0 2rem;
  }
  .new h2 {
    width: 100%;
    margin: 0;
  }
  label {
    display: grid;
    gap: 0.3rem;
  }
  input {
    font: inherit;
    padding: 0.5rem;
  }
  button {
    padding: 0.45rem 0.8rem;
    cursor: pointer;
  }
  button:disabled {
    cursor: default;
  }
  .changes {
    margin-top: 1.5rem;
    border-top: 1px solid var(--border);
    padding-top: 0.5rem;
  }
  .problem {
    padding: 1rem;
    border-left: 3px solid var(--danger);
    background: var(--error-bg);
  }
  .table {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th,
  td {
    text-align: left;
    padding: 0.6rem;
    border-bottom: 1px solid var(--border);
  }
  @media (max-width: 760px) {
    .creation {
      grid-template-columns: minmax(0, 1fr);
    }
    .new {
      display: grid;
    }
    .decision,
    aside {
      padding: 1rem;
    }
  }
</style>
