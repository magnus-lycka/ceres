<script lang="ts">
  /**
   * One situation on a screen of its own: planning it, running it, and reading
   * it once it is over.
   *
   *     [New] → planned → (Start) → current → (End) → past
   *
   * The three states are the same object at different times, so they are the
   * same screen; what changes is what may be done. The list of situations is
   * elsewhere, deliberately: mid-fight the others are noise.
   *
   * The rules live in `$lib/rules/rounds/`: `lifecycle` owns the transitions
   * and the one-current-fight-per-actor rule, `situation` owns the round. This
   * component owns only what is on screen and what gets stored.
   */
  import { resolve } from '$app/paths';
  import ActorHealth from '$lib/actors/ActorHealth.svelte';
  import Workspace from '$lib/Workspace.svelte';
  import AttackDialog from './AttackDialog.svelte';
  import SetupGrid from '$lib/situations/SetupGrid.svelte';
  import SituationGrid from '$lib/situations/SituationGrid.svelte';
  import { library, refresh } from '$lib/store/session.svelte';
  import {
    act,
    addActors,
    delay,
    removeActor,
    roundComplete,
    setInitiative,
    setParty,
  } from '$lib/rules/rounds/situation';
  import { beginRound, end, engagedElsewhere, nextRound, start } from '$lib/rules/rounds/lifecycle';
  import { carryOutAttack, type Strike } from '$lib/rules/rounds/attack';
  import type { Actor, ActorId } from '$lib/schema/actor';
  import type { Party } from '$lib/schema/party';
  import type { Situation, SituationId } from '$lib/schema/situation';

  let { id }: { id: SituationId } = $props();

  /** All of them, because starting one depends on who is busy in the others. */
  let situations = $state<Situation[]>([]);
  let parties = $state<Party[]>([]);
  /** Every actor a row might refer to, for names and the DEX tie-break. */
  let roster = $state<Actor[]>([]);
  let problem = $state('');

  let partyToAdd = $state('');
  let actorToAdd = $state('');
  /** The row the cursor is in on the setup grid, for Remove to act on. */
  let picked = $state<ActorId | null>(null);
  /** Who is attacking, while the attack dialog is open. */
  let attacking = $state<ActorId | null>(null);
  const attackingActor = $derived(roster.find((actor) => actor.id === attacking) ?? null);
  const pickedActor = $derived(roster.find((actor) => actor.id === picked) ?? null);
  const pickedName = $derived(pickedActor?.name ?? '');

  const open = $derived(situations.find((each) => each.id === id) ?? null);
  /**
   * Which table is on screen.
   *
   * Planning and the before-round phase are the same job — deciding who is in
   * it and what they rolled — so they share the setup grid. A fight in a round,
   * and a fight that is over, both show the round table: one to act in, one to
   * read.
   */
  const setting = $derived(
    open !== null && (open.state === 'planned' || (open.state === 'current' && open.phase === 'setup')),
  );
  /** A past situation is a record, not a workspace. */
  const readonly = $derived(open?.state === 'past');

  $effect(() => {
    void load();
  });

  async function load() {
    situations = await library.situations();
    parties = await library.parties();
    roster = await library.actors();
  }

  /**
   * Every change goes through here, so the screen only ever shows what the
   * repository accepted, and one write at a time — the same bargain the actor
   * and party pages make.
   */
  async function keep(work: () => Promise<void>) {
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
  }

  let gate: Promise<void> = Promise.resolve();

  /** Store a situation and seat it back in the list. */
  async function store(situation: Situation) {
    const saved = await library.saveSituation(situation);
    situations = situations.some((each) => each.id === saved.id)
      ? situations.map((each) => (each.id === saved.id ? saved : each))
      : [...situations, saved];
    return saved;
  }

  /** A correction to an actor belongs to the actor, not to this fight. */
  const correct = (actor: Actor) =>
    keep(async () => {
      const saved = await library.saveActor(actor);
      roster = roster.map((each) => (each.id === saved.id ? saved : each));
    });

  /** Carry out what the dialog asked for: the target's hurt, and the turn spent. */
  function strike(attack: Strike) {
    if (!open) return;
    const result = carryOutAttack(open, roster, attack);
    attacking = null;
    return keep(async () => {
      const saved = await library.saveActor(result.target);
      roster = roster.map((each) => (each.id === saved.id ? saved : each));
      await store(result.situation);
    });
  }

  const change = (situation: Situation) => keep(async () => void (await store(situation)));

  /**
   * Begin the fight, unless one of its actors is already in another.
   *
   * The refusal names the actors rather than just saying no: a plan that has
   * aged badly is the normal case, and what the referee needs is to know who
   * is busy so they can decide what to do about it.
   */
  function begin(situation: Situation) {
    const result = start(situation, situations);
    if (!result.ok) {
      const names = result.blocked
        .map((id) => roster.find((actor) => actor.id === id)?.name ?? `actor ${id}`)
        .join(', ');
      problem = `Already in another situation: ${names}.`;
      return;
    }
    return change(result.situation);
  }

  /** Who is committed to another fight happening right now. */
  const engaged = $derived(open ? engagedElsewhere(situations, open.id) : new Set<ActorId>());

  /** Who may still be added: not already seated, and not busy elsewhere. */
  const available = $derived(
    open
      ? roster.filter(
          (actor) =>
            !open.members.some((member) => member.actor === actor.id) &&
            !(open.state === 'current' && engaged.has(actor.id)),
        )
      : [],
  );

  async function addParty() {
    if (!open) return;
    const party = parties.find((each) => String(each.id) === partyToAdd);
    if (!party) return;
    const members = (await library.partyMembers(party.id)).filter((actor): actor is Actor => actor !== null);
    if (members.length === 0) {
      problem = `${party.name} has no members to bring in.`;
      return;
    }
    partyToAdd = '';
    return change(addActors(open, members, party.name, engaged));
  }

  /** Take the row under the cursor out of the fight. */
  function removePicked() {
    if (!open || picked === null) return;
    const going = picked;
    picked = null;
    return change(removeActor(open, going));
  }

  function addActor() {
    if (!open) return;
    const actor = roster.find((each) => String(each.id) === actorToAdd);
    if (!actor) return;
    actorToAdd = '';
    return change(addActors(open, [actor], '', engaged));
  }
</script>

{#if open}
  <!--
    One row for everything about the situation itself: the way back, its name
    as the title, its note, and the one thing that moves it along. Every row
    above the table is a row the table does not get, in a fight that is mostly
    the table.
  -->
  <div class="bar head">
    <a href={resolve('/situation')}>‹ Situations</a>
    <input
      class="title"
      type="text"
      aria-label="Name"
      value={open.name}
      disabled={readonly}
      onchange={(event) => change({ ...open, name: event.currentTarget.value })}
    />
    <input
      class="grow"
      type="text"
      aria-label="Note"
      placeholder="Note"
      value={open.note}
      disabled={readonly}
      onchange={(event) => change({ ...open, note: event.currentTarget.value })}
    />
    {#if open.state === 'planned'}
      <button type="button" onclick={() => begin(open)}>Start</button>
    {:else if open.state === 'current'}
      <button type="button" onclick={() => change(end(open))}>End</button>
    {/if}
  </div>

  <!--
    Who is in the fight is decided between rounds, never inside one. A round is
    six seconds: someone arriving can wait for it, and adding a row mid-round
    left it with no party and no initiative and no way to give it either.
  -->
  {#if setting}
    <div class="bar">
      <label>
        Party
        <select bind:value={partyToAdd}>
          <option value="">Choose…</option>
          {#each parties as party (party.id)}
            <option value={String(party.id)}>{party.name}</option>
          {/each}
        </select>
      </label>
      <button type="button" onclick={addParty} disabled={partyToAdd === ''}>Add party</button>

      <label>
        Actor
        <select bind:value={actorToAdd}>
          <option value="">Choose…</option>
          {#each available as actor (actor.id)}
            <option value={String(actor.id)}>{actor.name}</option>
          {/each}
        </select>
      </label>
      <button type="button" onclick={addActor} disabled={actorToAdd === ''}>Add actor</button>

      <!--
        Acts on the row the cursor is in, as Delete does on the Actors page.
        Only the membership row goes: the actor and everything that has
        happened to it stay in the library.
      -->
      <button type="button" onclick={removePicked} disabled={picked === null}>
        {pickedName ? `Remove ${pickedName}` : 'Remove'}
      </button>
    </div>
  {/if}

  <!--
    The two tables never swap by themselves. A round does not end because
    everyone has acted, and a round does not begin because initiative has been
    typed: both crossings are the referee's to make, in both directions, and
    each is one button. An automatic switch would move the ground under
    whoever was mid-sentence at the table.
  -->
  {#if open.state === 'current'}
    <div class="bar phase">
      {#if open.phase === 'setup'}
        <strong>Before round {open.round}</strong>
        <span class="hint">Set initiative. Nobody acts until the round begins.</span>
        <button type="button" class="cross" onclick={() => change(beginRound(open))}>
          Begin round {open.round}
        </button>
      {:else}
        <strong>Round {open.round}</strong>
        {#if roundComplete(open, roster)}
          <span class="hint">Everyone has acted or is waiting.</span>
        {/if}
        <button type="button" class="cross" onclick={() => change(nextRound(open))}> Finish round </button>
      {/if}
    </div>
  {/if}

  {#if attackingActor}
    <AttackDialog
      attacker={attackingActor}
      candidates={roster.filter(
        (actor) => actor.id !== attackingActor.id && open.members.some((member) => member.actor === actor.id),
      )}
      previous={open.members.find((member) => member.actor === attackingActor.id)?.target ?? null}
      onapply={strike}
      oncancel={() => (attacking = null)}
    />
  {/if}

  <Workspace>
    {#if open.members.length === 0}
      <p class="hint">Nobody in it yet.</p>
    {:else if setting}
      <SetupGrid
        situation={open}
        {roster}
        oninitiative={(actor: ActorId, initiative: number | null) =>
          change(setInitiative(open, actor, initiative))}
        onparty={(actor: ActorId, party: string) => change(setParty(open, actor, party))}
        onselect={(actor: ActorId | null) => (picked = actor)}
      />
    {:else}
      <SituationGrid
        situation={open}
        {roster}
        ondone={(actor: ActorId) => change(act(open, actor))}
        onwait={(actor: ActorId) => change(delay(open, actor))}
        onselect={(actor: ActorId | null) => (picked = actor)}
        onattack={(actor: ActorId) => (attacking = actor)}
      />
    {/if}

    {#snippet panels()}
      {#if pickedActor}
        <ActorHealth actor={pickedActor} onchange={correct} />
      {/if}
    {/snippet}
  </Workspace>

  {#if open.state === 'planned'}
    <p class="hint">Planned: decide who is in it. Rounds begin once you press Start.</p>
  {:else if open.state === 'past'}
    <p class="hint">Over, and kept as a record. Nothing here can be changed.</p>
  {/if}
{/if}

{#if problem}<p class="problem">{problem}</p>{/if}

<style>
  .bar {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }
  label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  .grow {
    flex: 1;
    min-width: 8rem;
  }
  /* The name is the title: it reads as one, and turns into a field on hover or focus. */
  .title {
    font: inherit;
    font-size: 1.15rem;
    font-weight: 600;
    border: 1px solid transparent;
    background: transparent;
    padding: 0.1rem 0.3rem;
    min-width: 10rem;
  }
  .title:hover:not(:disabled),
  .title:focus {
    border-color: #cbd5e1;
    background: var(--surface);
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
