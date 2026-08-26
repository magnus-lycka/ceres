<script lang="ts">
  /**
   * Who is in one party.
   *
   * Members are references, so a member whose actor has been deleted shows as
   * a hole rather than disappearing. Nothing prunes them automatically: a
   * party that is short a member is telling you something true, and quietly
   * closing the gap would hide it. Removing the hole is a decision, so it is a
   * button.
   *
   * Order is the order they were added, and it is kept — a Situation copies a
   * party in, and reading down the list should match the table.
   */
  import type { Actor, ActorId } from '$lib/schema/actor';
  import type { Party } from '$lib/schema/party';

  let {
    party,
    members,
    actors,
    onchange,
  }: {
    party: Party;
    /** Resolved members in stored order, null where one has been deleted. */
    members: (Actor | null)[];
    /** Everyone in the library, to add from. */
    actors: Actor[];
    onchange: (updated: Party) => void;
  } = $props();

  let adding = $state<string>('');

  // An actor may be in a party once. Adding the same one twice would give two
  // rows that are one creature, which is exactly what the Situation must not
  // have to reason about.
  const available = $derived(actors.filter((actor) => !party.actors.includes(actor.id)));

  function add() {
    const id = Number(adding);
    if (!id) return;
    onchange({ ...party, actors: [...party.actors, id as ActorId] });
    adding = '';
  }

  function removeAt(index: number) {
    onchange({ ...party, actors: party.actors.filter((_, position) => position !== index) });
  }
</script>

<section>
  <h2>Members — {party.name || '(unnamed)'}</h2>

  <table>
    <thead>
      <tr><th>Actor</th><th>Kind</th><th></th></tr>
    </thead>
    <tbody>
      {#each members as member, index (index)}
        <tr class:gone={member === null}>
          <td>{member ? member.name || '(unnamed)' : 'deleted actor'}</td>
          <td>{member?.kind ?? '—'}</td>
          <td><button onclick={() => removeAt(index)}>Remove</button></td>
        </tr>
      {:else}
        <tr><td colspan="3">Nobody yet.</td></tr>
      {/each}
      <tr class="add">
        <td colspan="2">
          <select bind:value={adding} aria-label="Actor to add">
            <option value="">Choose an actor…</option>
            {#each available as actor (actor.id)}
              <option value={String(actor.id)}>{actor.name || '(unnamed)'} — {actor.kind}</option>
            {/each}
          </select>
        </td>
        <td><button onclick={add} disabled={!adding}>Add</button></td>
      </tr>
    </tbody>
  </table>
</section>

<style>
  section {
    margin-top: 1.5rem;
  }
  h2 {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }
  table {
    border-collapse: collapse;
  }
  th,
  td {
    border: 1px solid #e5e7eb;
    padding: 0.15rem 0.5rem;
    text-align: left;
  }
  .gone td {
    color: #9ca3af;
    font-style: italic;
  }
</style>
