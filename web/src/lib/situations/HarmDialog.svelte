<script lang="ts">
  /**
   * Injury with nobody to blame: a fall, a fire, a hull breach.
   *
   * No attack check is in it, so no Effect, AP, Protection or reaction: the
   * referee enters the damage as it lands, and armour does not stop a fall
   * (refs/core/03_combat.md:400). A separate dialog rather than the attack
   * dialog with most of it hidden, because it shares none of an attack's fields.
   */
  import type { Actor, ActorId } from '$lib/schema/actor';
  import { hurtByCharacteristics } from '$lib/rules/rounds/health';
  import type { Harm } from '$lib/rules/rounds/attack';

  let {
    candidates,
    onapply,
    oncancel,
  }: {
    /** Everyone in the fight. */
    candidates: Actor[];
    onapply: (harm: Harm) => void;
    oncancel: () => void;
  } = $props();

  let dialog: HTMLDialogElement;

  let chosen = $state<string | null>(null);
  const target = $derived(chosen ?? String(candidates[0]?.id ?? ''));
  const victim = $derived(candidates.find((candidate) => String(candidate.id) === target));
  let damage = $state(0);
  let stun = $state(false);
  let excessTo = $state<'strength' | 'dexterity'>('dexterity');
  /** Only something hurt through characteristics has a choice to make. */
  const choosesExcess = $derived(victim !== undefined && hurtByCharacteristics(victim));

  $effect(() => {
    dialog.showModal();
  });

  function apply(event: SubmitEvent) {
    event.preventDefault();
    onapply({
      target: Number(target) as ActorId,
      damage,
      stun,
      excessTo: choosesExcess ? excessTo : undefined,
    });
  }
</script>

<dialog bind:this={dialog} aria-label="Other damage" onclose={() => oncancel()}>
  <h2>Other damage</h2>
  <form onsubmit={apply}>
    <label>
      Target
      <select value={target} onchange={(event) => (chosen = event.currentTarget.value)}>
        {#each candidates as candidate (candidate.id)}
          <option value={String(candidate.id)}>{candidate.name}</option>
        {/each}
      </select>
    </label>
    <label>Damage <input type="number" min="0" bind:value={damage} /></label>
    <label><input type="checkbox" bind:checked={stun} /> Stun</label>
    {#if choosesExcess}
      <label>
        Excess to
        <select bind:value={excessTo}>
          <option value="dexterity">DEX</option>
          <option value="strength">STR</option>
        </select>
      </label>
    {/if}
    <div class="buttons">
      <button type="submit">Apply</button>
      <button type="button" onclick={() => oncancel()}>Cancel</button>
    </div>
  </form>
</dialog>

<style>
  form {
    display: grid;
    gap: 0.5rem;
    justify-items: start;
  }
  label {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .buttons {
    display: flex;
    gap: 0.5rem;
  }
</style>
