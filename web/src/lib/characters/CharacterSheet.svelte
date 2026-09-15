<script lang="ts">
  import type { Character } from './api';
  let { character }: { character: Character } = $props();
</script>

<section aria-label="Character summary">
  <h2>{character.name}</h2>
  <p>
    {character.sophont} · Age {character.age_display}{character.homeworld ? ` · ${character.homeworld}` : ''}
  </p>
  {#if character.rank_display}<p>{character.rank_display}</p>{/if}
  <p class="ucp">{character.ucp}</p>
  <dl>
    {#each Object.entries(character.characteristics) as [name, value] (name)}<div>
        <dt>{name}</dt>
        <dd>{value}</dd>
      </div>{/each}
  </dl>
  <h3>Skills</h3>
  <p>{character.skills || 'None yet'}</p>
  <h3>Benefits and cash</h3>
  <p>Cr{character.cash.toLocaleString()}</p>
  <ul>
    {#each character.benefits as benefit, i (i)}<li>{benefit}</li>{/each}
  </ul>
  {#if character.connections.length}<h3>Connections</h3>
    <ul>
      {#each character.connections as connection, i (i)}<li>{connection}</li>{/each}
    </ul>{/if}
  {#if character.problems.length}<h3>Problems</h3>
    <ul>
      {#each character.problems as problem, i (i)}<li>{problem}</li>{/each}
    </ul>{/if}
  <details>
    <summary>Creation history ({character.history.length})</summary>
    <ol>
      {#each character.history as event, i (i)}<li>{event}</li>{/each}
    </ol>
  </details>
</section>

<style>
  section {
    min-width: 0;
  }
  h2 {
    margin-top: 0;
  }
  .ucp {
    font: bold 1.4rem monospace;
    letter-spacing: 0.15em;
  }
  dl {
    display: flex;
    flex-wrap: wrap;
    gap: 1.2rem;
  }
  dt {
    font-size: 0.8rem;
    color: var(--muted);
  }
  dd {
    margin: 0;
    font-weight: bold;
  }
  details {
    border-top: 1px solid var(--border);
    padding-top: 1rem;
    margin-top: 1rem;
  }
  summary {
    cursor: pointer;
  }
  li {
    margin: 0.4rem 0;
  }
</style>
