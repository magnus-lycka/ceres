<script lang="ts">
  import { untrack } from 'svelte';
  import { SvelteURLSearchParams } from 'svelte/reactivity';
  import { z } from 'zod';
  import { request, worldInput, type Values } from './api';
  let {
    spec,
    busy,
    onsubmit,
  }: { spec: z.infer<typeof worldInput>; busy: boolean; onsubmit: (values: Values) => void } = $props();
  const resultSchema = z.object({
    name: z.string().nullable(),
    options: z.record(z.string(), z.array(z.string())),
    worlds: z.array(
      z.object({
        sector: z.string(),
        sector_abbreviation: z.string(),
        hex: z.string(),
        name: z.string(),
        uwp: z.string(),
        remarks: z.string(),
        distance: z.number().nullable(),
      }),
    ),
  });
  let sector = $state('');
  let worldQuery = $state('');
  let referenceHex = $state('');
  let filters = $state<Record<string, string[]>>({});
  let sectors = $state<{ abbreviation: string; names: string[] }[]>([]);
  let result = $state<z.infer<typeof resultSchema> | null>(null);
  let problem = $state('');
  let loading = $state(false);
  $effect(() => {
    sector = spec.reference_world?.sector_abbreviation ?? spec.sector_abbreviation ?? '';
    filters = $state.snapshot(spec.filters);
    referenceHex = spec.reference_world?.hex ?? '';
    untrack(() => {
      if (sector) void load();
    });
  });
  async function search() {
    loading = true;
    problem = '';
    try {
      sectors = z
        .array(z.object({ abbreviation: z.string(), names: z.array(z.string()) }))
        .parse(await request(`/sectors?q=${encodeURIComponent(sector)}`));
    } catch (e) {
      problem = String(e);
    } finally {
      loading = false;
    }
  }
  async function load() {
    loading = true;
    problem = '';
    result = null;
    const params = new SvelteURLSearchParams({
      q: worldQuery,
      reference_hex: referenceHex,
    });
    for (const [key, values] of Object.entries(filters))
      for (const value of values) params.append(key, value);
    try {
      result = resultSchema.parse(await request(`/worlds/${encodeURIComponent(sector)}?${params}`));
    } catch (e) {
      problem = String(e);
    } finally {
      loading = false;
    }
  }
</script>

<section aria-label={spec.label}>
  <h3>{spec.label}</h3>
  <form
    onsubmit={(e) => {
      e.preventDefault();
      void load();
    }}
  >
    <label>Reference sector<input bind:value={sector} placeholder="Name or abbreviation" required /></label>
    <button type="button" disabled={loading || busy || !sector.trim()} onclick={search}>Find sector</button>
    {#if sectors.length}<ul>
        {#each sectors as s (s.abbreviation)}<li>
            <button
              type="button"
              disabled={loading || busy}
              onclick={() => {
                sector = s.abbreviation;
                sectors = [];
                void load();
              }}>{s.names[0]} ({s.abbreviation})</button
            >
          </li>{/each}
      </ul>{/if}
    <label
      >Reference hex<input
        bind:value={referenceHex}
        pattern="(?:0[1-9]|[12][0-9]|3[0-2])(?:0[1-9]|[123][0-9]|40)"
        placeholder="Optional, e.g. 0202"
      /></label
    >
    <p>
      Leave hex empty to search the whole sector. With a hex, search within 12 pc across sector borders,
      nearest first.
    </p>
    <label>World name or hex<input bind:value={worldQuery} /></label>
    {#if result}<details>
        <summary>World filters</summary>
        {#each Object.entries(result.options) as [key, values] (key)}
          <fieldset>
            <legend>{key.replaceAll('_', ' ')}</legend>{#each values as value (value)}<label class="option"
                ><input type="checkbox" {value} bind:group={filters[key]} />{value}</label
              >{/each}
          </fieldset>
        {/each}
        <button
          type="button"
          onclick={() => {
            filters = {};
            void load();
          }}>Clear filters</button
        >
      </details>{/if}
    <button disabled={loading || busy}>Load worlds</button>
  </form>
  {#if loading}<p role="status">Loading worlds…</p>{/if}
  {#if problem}<p role="alert">{problem}</p>{/if}
  {#if result}<p>{result.worlds.length} worlds in {result.name}</p>
    <div class="worlds">
      <table>
        <thead
          ><tr
            ><th scope="col">World</th><th scope="col">Sector</th><th scope="col">Hex</th><th scope="col"
              >UWP</th
            ><th scope="col">Remarks</th><th scope="col">Distance</th></tr
          ></thead
        ><tbody>
          {#each result.worlds as world (`${world.sector_abbreviation}/${world.hex}`)}<tr
              ><td
                ><button
                  disabled={busy || loading}
                  onclick={() => onsubmit({ sector: world.sector_abbreviation, hex_code: world.hex })}
                  >{world.name || world.hex}</button
                ></td
              ><td>{world.sector}</td><td>{world.hex}</td><td>{world.uwp}</td><td>{world.remarks}</td><td
                >{world.distance === null ? '' : `${world.distance} pc`}</td
              ></tr
            >{/each}
        </tbody>
      </table>
    </div>{/if}
</section>

<style>
  label {
    display: grid;
    gap: 0.3rem;
    margin: 0.6rem 0;
  }
  input {
    font: inherit;
    padding: 0.5rem;
  }
  button {
    padding: 0.4rem 0.7rem;
    margin: 0.3rem 0;
  }
  fieldset {
    margin: 0.5rem 0;
  }
  .option {
    display: inline-flex;
    margin-right: 0.8rem;
    align-items: center;
  }
  .worlds {
    max-height: 25rem;
    overflow: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th,
  td {
    text-align: left;
    padding: 0.4rem;
    border-bottom: 1px solid var(--border);
  }
</style>
