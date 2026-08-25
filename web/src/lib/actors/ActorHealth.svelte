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
  import type { Actor, CriticalLocation, Injury, Stat } from '$lib/schema/actor';
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
  import { criticalRows, setCritical } from '$lib/rules/rounds/criticals';

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

  /**
   * The robot combat record: all seven locations, as the card prints them.
   * Only a robot has systems to lose, so this half of the panel is absent for
   * anything else.
   *
   * Severity is set directly rather than accumulated here. In a situation a
   * hit worsens a location by the repeat-hit rule, but this screen is the
   * record between situations — where a repair lowers a severity, or a hit
   * from last session gets written down after the fact.
   *
   * The note is where the severity's actual effect lives. Ceres does not
   * encode the effects table, so "Protection −1D" or "left autocannon
   * destroyed" is read off the handout and kept here.
   */
  const severities = [0, 1, 2, 3, 4, 5, 6] as const;

  function write(location: CriticalLocation, severity: number, note: string) {
    onchange(setCritical(actor, location, severity, note));
  }
</script>

<section>
  <h2>Health — {actor.name || '(unnamed)'}</h2>

  <p class="now">
    {#each columns as [stat, header] (stat)}
      <span><strong>{header}</strong> {shown(stat)}</span>
    {/each}
    {#if stunPoints(actor)}<span>stun {stunPoints(actor)}</span>{/if}
    {#if healthSummary(actor)}<span class="state">{healthSummary(actor)}</span>{/if}
  </p>

  <div class="panels">
    <div class="panel">
      <h3>Injuries</h3>
      <table>
        <thead>
          <tr>
            <th>Kind</th>
            {#each columns as [stat, header] (stat)}<th>{header}</th>{/each}
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each actor.injuries as injury, index (index)}
            <tr>
              <td>{injury.kind}</td>
              {#each columns as [stat] (stat)}
                <td>{injury.reductions[stat] ? `-${injury.reductions[stat]}` : '—'}</td>
              {/each}
              <td><button onclick={() => onchange(removeInjury(actor, index))}>Remove</button></td>
            </tr>
          {:else}
            <tr><td colspan={columns.length + 2}>Unhurt.</td></tr>
          {/each}
          <tr class="add">
            <td>
              <select aria-label="Injury kind" bind:value={kind}>
                <option value="lethal">lethal</option>
                <option value="stun">stun</option>
              </select>
            </td>
            {#each columns as [stat] (stat)}
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
    </div>

    {#if actor.kind === 'robot'}
      <div class="panel">
        <h3>Criticals</h3>
        <table class="record">
          <thead>
            <tr><th>Location</th><th>Severity</th><th>Component / effect</th></tr>
          </thead>
          <tbody>
            {#each criticalRows(actor) as row (row.location)}
              <tr class:hurt={row.severity > 0}>
                <td>{row.location}</td>
                <td>
                  <select
                    aria-label="{row.location} severity"
                    value={row.severity}
                    onchange={(event) => write(row.location, Number(event.currentTarget.value), row.note)}
                  >
                    {#each severities as level (level)}
                      <option value={level}>{level === 0 ? '—' : `S${level}`}</option>
                    {/each}
                  </select>
                </td>
                <td>
                  <input
                    class="note"
                    aria-label="{row.location} note"
                    value={row.note}
                    onchange={(event) => write(row.location, row.severity, event.currentTarget.value)}
                  />
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</section>

<style>
  section {
    margin-top: 1.5rem;
  }
  h2 {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }
  /* Side by side: a robot has two records to keep, and stacking them puts the
     second one below the fold on a screen that is mostly empty to the right. */
  .panels {
    display: flex;
    gap: 2.5rem;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .now {
    display: flex;
    gap: 1rem;
    margin: 0.25rem 0;
  }
  .state {
    color: #b91c1c;
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
  input {
    width: 4rem;
  }
  .barred {
    color: #9ca3af;
  }
  h3 {
    font-size: 0.85rem;
    color: #555;
    margin: 0.5rem 0 0.25rem;
    font-weight: 600;
  }
  .record .hurt {
    background: #fef2f2;
  }
  .note {
    width: 18rem;
  }
</style>
