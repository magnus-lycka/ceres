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
  import {
    knownModifiers,
    reactionsAgainst,
    totalOf,
    type AttackKind,
    type Reaction,
  } from '$lib/rules/rounds/reaction';

  let {
    attacker,
    candidates,
    previous,
    attackerReactions = 0,
    onapply,
    oncancel,
  }: {
    attacker: Actor;
    /** Everyone who could be attacked: whoever else is in the fight, not the attacker. */
    candidates: Actor[];
    /** Who they went for last time, so the next attack starts from them. */
    previous: ActorId | null;
    /** Reactions the attacker has taken, each DM-1 on this roll. */
    attackerReactions?: number;
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
  /** Melee or ranged: which reactions the target has depends on it. */
  let kind = $state<AttackKind>('ranged');
  /** What the target does about it, before anything is rolled. */
  let chosenReaction = $state<Reaction | ''>('');
  const reaction = $derived<Reaction | null>(chosenReaction === '' ? null : chosenReaction);
  // A reaction the attack no longer allows is dropped, not merely hidden: left
  // in the state it would leave the box blank with nothing selected.
  $effect.pre(() => {
    if (chosenReaction !== '' && !reactionsAgainst(kind).includes(chosenReaction)) chosenReaction = '';
  });
  const reactionNames: Record<Reaction, string> = { dodge: 'Dodge', dive: 'Dive for cover', parry: 'Parry' };

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

  /** The DMs the app knows of: a reminder before the roll, never applied to it. */
  const modifiers = $derived(
    victim ? knownModifiers({ defender: victim, reaction, attack: kind, shotgun, attackerReactions }) : [],
  );
  const known = $derived(totalOf(modifiers));

  /** A DM as it is written on the table: a real minus sign, and ? for what cannot be known. */
  function written(dm: number | null): string {
    if (dm === null) return '?';
    return dm < 0 ? `−${-dm}` : dm > 0 ? `+${dm}` : '0';
  }

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
      reaction,
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
    <fieldset class="kind">
      <legend>Attack</legend>
      <label><input type="radio" name="kind" value="ranged" bind:group={kind} /> Ranged</label>
      <label><input type="radio" name="kind" value="melee" bind:group={kind} /> Melee</label>
    </fieldset>
    <label>
      Reaction
      <select bind:value={chosenReaction}>
        <option value="">—</option>
        {#each reactionsAgainst(kind) as each (each)}
          <option value={each}>{reactionNames[each]}</option>
        {/each}
      </select>
    </label>
    {#if modifiers.length > 0}
      <table class="known" aria-label="Known DMs">
        <tbody>
          {#each modifiers as modifier (modifier.label)}
            <tr>
              <td>{modifier.label}</td>
              <td class="dm">{written(modifier.dm)}</td>
            </tr>
          {/each}
          <tr class="total">
            <td>Known DMs</td>
            <td class="dm">{written(known.dm)}</td>
          </tr>
        </tbody>
      </table>
      <p class="why">
        A reminder for your roll. The Effect you type already includes it.{known.complete
          ? ''
          : ' Not every DM is known here.'}
      </p>
    {/if}
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
  .kind {
    display: flex;
    gap: 0.75rem;
    border: 0;
    padding: 0;
    margin: 0;
  }
  .kind legend {
    float: left;
    padding: 0;
    margin-right: 0.5rem;
  }
  .known {
    border-collapse: collapse;
  }
  .known td {
    padding: 0.1rem 0.5rem;
  }
  .known .dm {
    text-align: right;
  }
  .known .total td {
    border-top: 1px solid #cbd5e1;
    font-weight: 600;
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
