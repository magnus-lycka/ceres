<script lang="ts">
  /**
   * A critical hit on a robot, worked through one question at a time.
   *
   * What a critical does depends on rolls only the referee can make: the
   * location, and the dice an effect costs. The rules ask for them in turn
   * (`$lib/rules/rounds/robotCriticals`), and each answer is applied before the
   * next question, so the record is never left half done. This only asks, and
   * shows what has happened.
   */
  import type { Choice, Flow } from '$lib/rules/rounds/robotCriticals';
  import { prompt } from '$lib/rules/rounds/robotCriticals';

  /** True while the current question is a location roll: only there does the robot's own build decide. */

  let {
    flow,
    onanswer,
    ondiscard,
    ondone,
  }: {
    flow: Flow;
    /** The referee's answer. It comes back as a new flow, the same one if it was not an answer. */
    onanswer: (value: number | Choice) => void;
    /** The referee says this location does not apply: a hardened brain, ignored rather than re-rolled. */
    ondiscard: () => void;
    ondone: () => void;
  } = $props();

  let dialog: HTMLDialogElement;
  let typed = $state('');
  const asking = $derived(prompt(flow));
  /** What the roll can be, so a mistyped one is said to be mistyped rather than ignored. */
  const range = $derived(
    asking?.kind === 'location' ? [2, 12] : asking?.kind === 'dice' ? [asking.dice, asking.dice * 6] : null,
  );
  let refused = $state(false);
  /** What has happened, without the question being asked: that is shown once, below. */
  const done = $derived(
    flow.log.filter(
      (line, index) => !(index === flow.log.length - 1 && asking !== null && line === asking.why),
    ),
  );

  $effect(() => {
    dialog.showModal();
  });

  // A new question starts with an empty box and no complaint.
  $effect(() => {
    void asking;
    typed = '';
    refused = false;
  });

  function submit(event: SubmitEvent) {
    event.preventDefault();
    const value = Number(typed);
    if (typed === '' || !range || !Number.isInteger(value) || value < range[0] || value > range[1]) {
      refused = true;
      return;
    }
    onanswer(value);
  }
</script>

<dialog bind:this={dialog} aria-label="Critical hit" onclose={() => ondone()}>
  <h2>Critical hit — {flow.actor.name}</h2>

  {#if done.length > 0}
    <ul class="log">
      {#each done as line, index (index)}
        <li>{line}</li>
      {/each}
    </ul>
  {/if}

  {#if asking}
    <p class="asking">{asking.why}</p>
    {#if asking.kind === 'pace'}
      <div class="buttons">
        <button type="button" onclick={() => onanswer('movement')}>Movement</button>
        <button type="button" onclick={() => onanswer('speed')}>Speed</button>
      </div>
    {:else}
      <form onsubmit={submit}>
        <label>
          Roll
          <input type="number" bind:value={typed} />
        </label>
        {#if range}<span class="range"
            >{asking.kind === 'location' ? '2D' : `${asking.dice}D`}: {range[0]}–{range[1]}</span
          >{/if}
        <button type="submit">Apply</button>
        {#if asking.kind === 'location'}
          <button type="button" onclick={() => (typed = '')}>Reroll</button>
          <button type="button" onclick={() => ondiscard()}>Discard</button>
        {/if}
        {#if refused}<span class="refused">That is not a roll those dice can make.</span>{/if}
      </form>
    {/if}
  {:else}
    <button type="button" onclick={() => ondone()}>Done</button>
  {/if}
</dialog>

<style>
  .log {
    margin: 0 0 0.5rem;
    padding-left: 1.2rem;
  }
  .asking {
    font-weight: 600;
  }
  form {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .range {
    color: var(--muted);
  }
  .refused {
    color: var(--danger);
  }
  .buttons {
    display: flex;
    gap: 0.5rem;
  }
</style>
