<script lang="ts">
  /**
   * Health for one actor, edited outside any fight.
   *
   * An actor arrives at a session already hurt, and healing happens between
   * situations rather than during them — so this is where an injury is
   * recorded, corrected, or healed away. Entries made here carry no round:
   * there is no round in the library, and an injury from a previous fight is
   * past the first-aid window in any case.
   *
   * Current values are never edited directly. They are the maximum less what
   * the injuries record, so editing them would mean reverse-engineering the
   * lines that produced them.
   */
  import type { Actor, Injury, Stat } from '$lib/schema/actor';
  import {
    current,
    currentHits,
    healthSummary,
    hurtByCharacteristics,
    recordInjury,
    removeInjury,
    stunPoints,
    stunStat,
  } from '$lib/rules/rounds/health';

  let { actor, onchange }: { actor: Actor; onchange: (updated: Actor) => void } = $props();

  const columns = $derived(
    hurtByCharacteristics(actor)
      ? ([
          ['strength', 'STR'],
          ['dexterity', 'DEX'],
          ['endurance', 'END'],
        ] as const)
      : ([['hits', 'Hits']] as const),
  );

  let kind = $state<Injury['kind']>('lethal');
  let entry = $state<Partial<Record<Stat, number>>>({});

  /** Stun only reduces one stat, so the form offers only that one. */
  const editable = $derived<Stat[]>(kind === 'stun' ? [stunStat(actor)] : columns.map(([stat]) => stat));

  function points(stat: Stat): number {
    return entry[stat] ?? 0;
  }

  function add() {
    const reductions = Object.fromEntries(
      editable.map((stat) => [stat, points(stat)]).filter(([, value]) => (value as number) > 0),
    ) as Partial<Record<Stat, number>>;
    if (Object.keys(reductions).length === 0) return;
    onchange(recordInjury(actor, kind, reductions));
    entry = {};
  }

  function shown(stat: Stat): string {
    const now = stat === 'hits' ? currentHits(actor) : current(actor, stat as 'strength');
    return now === null ? '—' : `${now}/${actor[stat] ?? 0}`;
  }
</script>

<section>
  <h2>Health — {actor.name || '(unnamed)'}</h2>

  <p class="now">
    {#each columns as [stat, header]}
      <span><strong>{header}</strong> {shown(stat)}</span>
    {/each}
    {#if stunPoints(actor)}<span>stun {stunPoints(actor)}</span>{/if}
    {#if healthSummary(actor)}<span class="state">{healthSummary(actor)}</span>{/if}
  </p>

  <table>
    <thead>
      <tr>
        <th>Kind</th>
        {#each columns as [, header]}<th>{header}</th>{/each}
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each actor.injuries as injury, index}
        <tr>
          <td>{injury.kind}</td>
          {#each columns as [stat]}<td>{injury.reductions[stat] ? `-${injury.reductions[stat]}` : '—'}</td>{/each}
          <td><button onclick={() => onchange(removeInjury(actor, index))}>Remove</button></td>
        </tr>
      {:else}
        <tr><td colspan={columns.length + 2}>Unhurt.</td></tr>
      {/each}
      <tr class="add">
        <td>
          <select bind:value={kind}>
            <option value="lethal">lethal</option>
            <option value="stun">stun</option>
          </select>
        </td>
        {#each columns as [stat]}
          <td>
            {#if editable.includes(stat)}
              <input
                type="number"
                min="0"
                value={points(stat)}
                oninput={(event) => (entry = { ...entry, [stat]: Number(event.currentTarget.value) })}
              />
            {:else}
              <span class="barred" title="Stun only reduces {stunStat(actor)}">—</span>
            {/if}
          </td>
        {/each}
        <td><button onclick={add}>Add injury</button></td>
      </tr>
    </tbody>
  </table>
</section>

<style>
  section { margin-top: 1.5rem; }
  h2 { font-size: 1rem; margin-bottom: .25rem; }
  .now { display: flex; gap: 1rem; margin: .25rem 0; }
  .state { color: #b91c1c; }
  table { border-collapse: collapse; }
  th, td { border: 1px solid #e5e7eb; padding: .15rem .5rem; text-align: left; }
  input { width: 4rem; }
  .barred { color: #9ca3af; }
</style>
