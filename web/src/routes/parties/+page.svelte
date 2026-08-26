<script lang="ts">
  /**
   * The party library: reusable named sets of actors — the PCs, a wolf pack,
   * starport security.
   *
   * A party holds no combat state. A Situation copies one in and forgets it,
   * so parties may be edited or deleted at any time without disturbing a fight
   * already under way.
   */
  import PartyGrid from '$lib/parties/PartyGrid.svelte';
  import PartyMembers from '$lib/parties/PartyMembers.svelte';
  import { partyId, UNSAVED, type Actor, type PartyId } from '$lib/schema/actor';
  import type { Party } from '$lib/schema/party';
  import { library, refresh } from '$lib/store/session.svelte';

  let parties = $state<Party[]>([]);
  let actors = $state<Actor[]>([]);
  let members = $state<(Actor | null)[]>([]);
  let selectedId = $state<PartyId | null>(null);
  const selected = $derived(parties.find((party) => party.id === selectedId) ?? null);
  let problem = $state('');
  let busy = $state(0);

  $effect(() => {
    void load();
  });

  // Files the library could not read. Shown rather than swallowed: a damaged
  // file used to empty the whole list with nothing said about it.
  let unreadable = $state<string[]>([]);

  async function load() {
    parties = await library.parties();
    const listing = [...library.problems];
    actors = await library.actors();
    unreadable = [...listing, ...library.problems];
  }

  // Members are resolved through the library rather than held on the party,
  // because a reference may point at an actor that has since been deleted.
  $effect(() => {
    const id = selectedId;
    if (id === null) return void (members = []);
    void library.partyMembers(id).then((resolved) => (members = resolved));
  });

  let gate: Promise<void> = Promise.resolve();

  async function keep(work: () => Promise<void>) {
    busy += 1;
    const mine = gate.then(async () => {
      try {
        problem = '';
        await work();
      } catch (failure) {
        problem = failure instanceof Error ? failure.message : String(failure);
      }
      await refresh();
    });
    gate = mine;
    await mine;
    busy -= 1;
  }

  function addParty() {
    return keep(async () => {
      const saved = await library.saveParty({
        id: partyId(UNSAVED),
        name: '',
        note: '',
        tags: [],
        actors: [],
      });
      parties = [...parties, saved];
      selectedId = saved.id;
    });
  }

  /** From the member panel, which hands back a new party object. */
  function replace(updated: Party) {
    return keep(async () => {
      const saved = await library.saveParty(updated);
      parties = parties.map((party) => (party.id === saved.id ? saved : party));
      members = await library.partyMembers(saved.id);
    });
  }

  /**
   * From the grid, which has already applied the edit to the row in place.
   * Only storage needs telling — replacing `parties` would re-render the grid
   * out from under the cursor.
   */
  function edited(party: Party) {
    return keep(async () => void (await library.saveParty(party)));
  }

  function deleteSelected() {
    if (!selected) return void (problem = 'Click a row first.');
    const doomed = selected.id;
    // No confirmation, and nothing goes looking for situations that copied it:
    // a Situation took its own copy and does not point back here.
    return keep(async () => {
      await library.deleteParty(doomed);
      parties = parties.filter((party) => party.id !== doomed);
      selectedId = null;
    });
  }
</script>

<h1>Parties</h1>

<div class="bar">
  <button onclick={addParty} disabled={busy > 0}>Add party</button>
  <button onclick={deleteSelected} disabled={busy > 0}>Delete</button>
  {#if busy > 0}<span class="hint">saving…</span>{/if}
</div>

{#if problem}<p class="problem">{problem}</p>{/if}
{#each unreadable as trouble (trouble)}<p class="problem">{trouble}</p>{/each}

<PartyGrid {parties} onselect={(party) => (selectedId = party?.id ?? null)} onedit={edited} />

{#if selected}
  <PartyMembers party={selected} {members} {actors} onchange={replace} />
{:else}
  <p class="hint">Click a row to edit its members.</p>
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
  .problem {
    background: #fef2f2;
    border-left: 3px solid #b91c1c;
    color: #7c2c1a;
    padding: 0.4rem 0.75rem;
    margin: 0 0 0.5rem;
  }
</style>
