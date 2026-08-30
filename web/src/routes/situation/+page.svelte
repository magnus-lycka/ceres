<script lang="ts">
  /**
   * Situations: planning them, running them, and keeping the ones that are
   * over.
   *
   *     [New] → planned → (Start) → current → (End) → past
   *              ↓ Delete                              ↓ Delete
   *
   * One screen rather than a list page and a run page, because the three
   * states are the same object at different times and the referee moves
   * between them constantly — picking tonight's ambush out of the list,
   * running it, ending it, and glancing back at last week's.
   *
   * The rules live in `$lib/rules/rounds/`: `lifecycle` owns the transitions
   * and the one-current-fight-per-actor rule, `situation` owns the round. This
   * page owns only what is on screen and what gets stored.
   */
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
  import {
    beginRound,
    end,
    engagedElsewhere,
    newSituation,
    nextRound,
    start,
  } from '$lib/rules/rounds/lifecycle';
  import type { Actor, ActorId } from '$lib/schema/actor';
  import type { Party } from '$lib/schema/party';
  import type { Situation, SituationId } from '$lib/schema/situation';

  let situations = $state<Situation[]>([]);
  let parties = $state<Party[]>([]);
  /** Every actor a row might refer to, for names and the DEX tie-break. */
  let roster = $state<Actor[]>([]);
  let openId = $state<SituationId | null>(null);
  let problem = $state('');
  let busy = $state(0);

  let partyToAdd = $state('');
  let actorToAdd = $state('');
  /** The row the cursor is in on the setup grid, for Remove to act on. */
  let picked = $state<ActorId | null>(null);
  const pickedName = $derived(roster.find((actor) => actor.id === picked)?.name ?? '');

  const open = $derived(situations.find((each) => each.id === openId) ?? null);
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

  /** Store a situation and seat it back in the list. */
  async function store(situation: Situation) {
    const saved = await library.saveSituation(situation);
    situations = situations.some((each) => each.id === saved.id)
      ? situations.map((each) => (each.id === saved.id ? saved : each))
      : [...situations, saved];
    return saved;
  }

  const change = (situation: Situation) => keep(async () => void (await store(situation)));

  function create() {
    return keep(async () => {
      const saved = await store(newSituation(`Situation ${situations.length + 1}`));
      openId = saved.id;
    });
  }

  function remove(situation: Situation) {
    return keep(async () => {
      await library.deleteSituation(situation.id);
      situations = situations.filter((each) => each.id !== situation.id);
      if (openId === situation.id) openId = null;
    });
  }

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
    <li class:open={situation.id === openId}>
      <button type="button" class="pick" onclick={() => (openId = situation.id)}>
        <span class="state {situation.state}">{label[situation.state]}</span>
        {situation.name}
        <span class="hint">{situation.members.length} in it</span>
      </button>
      {#if situation.state === 'planned'}
        <button type="button" onclick={() => begin(situation)}>Start</button>
        <button type="button" onclick={() => remove(situation)}>Delete</button>
      {:else if situation.state === 'current'}
        <button type="button" onclick={() => change(end(situation))}>End</button>
      {:else}
        <button type="button" onclick={() => remove(situation)}>Delete</button>
      {/if}
    </li>
  {:else}
    <li class="hint">Nothing yet. A new situation starts out planned.</li>
  {/each}
</ul>

{#if open}
  <h2>{open.name}</h2>

  <div class="bar">
    <label>
      Name
      <input
        type="text"
        value={open.name}
        disabled={readonly}
        onchange={(event) => change({ ...open, name: event.currentTarget.value })}
      />
    </label>
    <label class="grow">
      Note
      <input
        type="text"
        value={open.note}
        disabled={readonly}
        onchange={(event) => change({ ...open, note: event.currentTarget.value })}
      />
    </label>
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
        {#if roundComplete(open)}
          <span class="hint">Everyone has acted or is waiting.</span>
        {/if}
        <button type="button" class="cross" onclick={() => change(nextRound(open))}> Finish round </button>
      {/if}
    </div>
  {/if}

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
    />
  {/if}

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
    border-left: 3px solid transparent;
  }
  .list li.open {
    border-left-color: #1a73e8;
    background: #f5f8ff;
  }
  .pick {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: 0;
    cursor: pointer;
    font: inherit;
    text-align: left;
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
    background: #e8f0fe;
    color: #174ea6;
  }
  .state.current {
    background: #e6f4ea;
    color: #137333;
  }
  .state.past {
    background: #f1f3f4;
    color: #5f6368;
  }
  label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  .grow {
    flex: 1;
  }
  .grow input {
    flex: 1;
  }
  .hint {
    color: #555;
  }
  .problem {
    background: #fef2f2;
    border-left: 3px solid #b91c1c;
    color: #7c2c1a;
    padding: 0.4rem 0.75rem;
    margin: 0.5rem 0;
  }
</style>
