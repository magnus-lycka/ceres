<script lang="ts">
  /**
   * The situations there are, as a way to get to one.
   *
   * Each is a real link to its own screen, so it opens in a tab of its own; the
   * screen has everything else. Only what makes no sense from inside a
   * situation happens here: making a new one, and deleting one.
   */
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { newSituation } from '$lib/rules/rounds/lifecycle';
  import { library, refresh } from '$lib/store/session.svelte';
  import type { Situation } from '$lib/schema/situation';

  let situations = $state<Situation[]>([]);
  let problem = $state('');
  let busy = $state(0);

  $effect(() => {
    void load();
  });

  async function load() {
    situations = await library.situations();
  }

  /** One write at a time, and the screen shows only what the repository accepted. */
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

  let gate: Promise<void> = Promise.resolve();

  function create() {
    return keep(async () => {
      const saved = await library.saveSituation(newSituation(`Situation ${situations.length + 1}`));
      situations = [...situations, saved];
      await goto(resolve('/situation/[id]', { id: String(saved.id) }));
    });
  }

  function remove(situation: Situation) {
    return keep(async () => {
      await library.deleteSituation(situation.id);
      situations = situations.filter((each) => each.id !== situation.id);
    });
  }

  const label: Record<Situation['state'], string> = {
    planned: 'Planned',
    current: 'Running',
    past: 'Over',
  };
</script>

<h1>Situations</h1>

<div class="bar">
  <button type="button" onclick={create} disabled={busy > 0}>New situation</button>
  {#if busy > 0}<span class="hint">saving…</span>{/if}
</div>

<ul class="list">
  {#each situations as situation (situation.id)}
    <li>
      <a class="pick" href={resolve('/situation/[id]', { id: String(situation.id) })}>
        <span class="state {situation.state}">{label[situation.state]}</span>
        {situation.name}
        <span class="hint">{situation.members.length} in it</span>
      </a>
      {#if situation.state !== 'current'}
        <button type="button" onclick={() => remove(situation)}>Delete</button>
      {/if}
    </li>
  {:else}
    <li class="hint">Nothing yet. A new situation starts out planned.</li>
  {/each}
</ul>

{#if problem}<p class="problem">{problem}</p>{/if}

<style>
  .bar {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }
  .list {
    list-style: none;
    padding: 0;
    margin: 0 0 1rem;
  }
  .list li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.15rem 0.25rem;
  }
  .pick {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: inherit;
    text-decoration: none;
    padding: 0.2rem;
  }
  /* The state is what decides everything else on the row, so it reads first. */
  .state {
    border-radius: 4px;
    font-size: 0.8em;
    padding: 1px 6px;
    white-space: nowrap;
  }
  .state.planned {
    background: var(--selected-bg);
    color: var(--selected-text);
  }
  .state.current {
    background: var(--success-bg);
    color: var(--success-text);
  }
  .state.past {
    background: var(--subtle-bg);
    color: var(--muted);
  }
  .hint {
    color: var(--muted);
  }
  .problem {
    background: var(--error-bg);
    border-left: 3px solid var(--danger);
    color: var(--error-text);
    padding: 0.4rem 0.75rem;
    margin: 0.5rem 0;
  }
</style>
