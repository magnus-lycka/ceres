<script lang="ts">
  /**
   * One attack, entered from what the referee rolled at the table.
   *
   * A captive dialog rather than a grid row: an attack involves two actors, and
   * a row can only speak for one of them. It asks for the numbers the dice
   * gave; the arithmetic that follows is `$lib/rules/rounds/attack`'s.
   */
  import type { Actor, ActorId } from '$lib/schema/actor';
  import { hurtByCharacteristics } from '$lib/rules/rounds/health';
  import { protectionAgainst, type Strike } from '$lib/rules/rounds/attack';

  let {
    attacker,
    candidates,
    previous,
    onapply,
    oncancel,
  }: {
    attacker: Actor;
    /** Everyone who could be attacked: whoever else is in the fight, not the attacker. */
    candidates: Actor[];
    /** Who they went for last time, so the next attack starts from them. */
    previous: ActorId | null;
    onapply: (strike: Strike) => void;
    oncancel: () => void;
  } = $props();

  let dialog: HTMLDialogElement;

  /** What the referee picked, once they have. Until then, the last target. */
  let chosen = $state<string | null>(null);
  const target = $derived(chosen ?? String(previous ?? candidates[0]?.id ?? ''));
  /** The check's Effect: named for what it is, because `effect` is a rune. */
  let checkEffect = $state(0);
  /** A Stun weapon: END only, and never lethal. */
  let stun = $state(false);

  /** Protection the weapon ignores. */
  let ap = $state(0);
  /**
   * Protection for this attack. Until the referee types one it is whatever the
   * target wears; typing overrides it for this attack alone, which covers cover
   * and anything else unusual with one control.
   */
  let typedProtection = $state<number | null>(null);
  const victim = $derived(candidates.find((candidate) => String(candidate.id) === target));
  /** A Shotgun with pellet ammunition: armour is doubly effective. */
  let shotgun = $state(false);
  /** What the target's Protection comes to against this weapon, before anything is typed. */
  const met = $derived(victim ? protectionAgainst(victim, { shotgun, stun }) : 0);
  const protection = $derived(typedProtection ?? met);
  /** Why it is not what the target wears, so the number cannot be silently wrong. */
  const why = $derived.by(() => {
    if (typedProtection !== null || !victim) return '';
    const reasons = [];
    if (shotgun) reasons.push('doubled: Shotgun');
    if (stun && victim.kind === 'robot') reasons.push('halved: stunner against a robot');
    return reasons.join('; ');
  });

  /** The target's choice of what takes the excess once END is gone. */
  let excessTo = $state<'strength' | 'dexterity'>('dexterity');
  /** Only something hurt through characteristics has a choice to make. */
  const choosesExcess = $derived(victim !== undefined && hurtByCharacteristics(victim));
  let roll = $state(0);

  $effect(() => {
    dialog.showModal();
  });

  function apply(event: SubmitEvent) {
    event.preventDefault();
    onapply({
      attacker: attacker.id,
      target: Number(target) as ActorId,
      effect: checkEffect,
      roll,
      ap,
      protection: typedProtection ?? undefined,
      shotgun,
      excessTo: choosesExcess ? excessTo : undefined,
      stun,
    });
  }
</script>

<dialog bind:this={dialog} aria-label="Attack" onclose={() => oncancel()}>
  <h2>{attacker.name} attacks</h2>
  <form onsubmit={apply}>
    <label>
      Target
      <select value={target} onchange={(event) => (chosen = event.currentTarget.value)}>
        {#each candidates as candidate (candidate.id)}
          <option value={String(candidate.id)}>{candidate.name}</option>
        {/each}
      </select>
    </label>
    <label>Effect <input type="number" bind:value={checkEffect} /></label>
    <label>Damage roll <input type="number" min="0" bind:value={roll} /></label>
    {#if choosesExcess}
      <label>
        Excess to
        <select bind:value={excessTo}>
          <option value="dexterity">DEX</option>
          <option value="strength">STR</option>
        </select>
      </label>
    {/if}
    <label><input type="checkbox" bind:checked={stun} /> Stun</label>
    <label><input type="checkbox" bind:checked={shotgun} /> Shotgun</label>
    <label>AP <input type="number" min="0" bind:value={ap} /></label>
    <label>
      Protection
      <input
        type="number"
        min="0"
        value={protection}
        oninput={(event) => (typedProtection = event.currentTarget.valueAsNumber)}
      />
      {#if why}<span class="why">{why}</span>{/if}
    </label>
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
  .why {
    color: var(--muted);
    font-size: 0.85em;
  }
  .buttons {
    display: flex;
    gap: 0.5rem;
  }
</style>
