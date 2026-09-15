<script lang="ts">
  /**
   * Where the data lives.
   *
   * Its own page because it is settings: entered once on a machine, then not
   * looked at again. The roster screens read the stored connection on arrival.
   */
  import Connection from '$lib/store/Connection.svelte';
  import { keepMine, now, status, transient } from '$lib/store/session.svelte';

  const summary = $derived(
    !status.connected
      ? 'No data repository. Everything stays in this browser.'
      : status.state === 'blocked'
        ? 'Syncing is paused: the repository and this browser have both moved on. Editing still works.'
        : status.changes > 0
          ? `${status.changes} change(s) waiting to go up.`
          : 'Everything here is in the repository.',
  );
</script>

<h1>Sync</h1>

<p class="state" class:blocked={status.state === 'blocked'}>
  {summary}
  <button onclick={() => now()} disabled={status.busy || !status.connected}>
    {status.busy ? 'Syncing…' : 'Sync now'}
  </button>
  {#if status.at}<span class="detail">last checked {status.at.toLocaleTimeString()}</span>{/if}
</p>

{#if status.detail}
  <p class="problem" class:transient={transient()}>
    {status.detail}
    {#if transient()}
      <br />
      Nothing is lost — edits are kept here and will go up on the next attempt.
    {:else}
      <br />
      Nothing here is lost: editing carries on, and the changes waiting are still waiting. If the work in this browser
      is the copy to keep, send it up over what the repository has:
      <br />
      <button onclick={() => keepMine()} disabled={status.busy}>
        {status.busy ? 'Sending…' : `Keep this browser's copy`}
      </button>
      <br />
      To take the repository's copy instead, and lose what is waiting here, resolve it with git and reload. To undo
      a push: <code>git reset --hard &lt;sha&gt; &amp;&amp; git push --force-with-lease</code>
    {/if}
  </p>
{/if}

{#if status.imported}
  <p class="imported">{status.imported}</p>
{/if}

{#if status.problems.length > 0}
  <!--
    A proposal that could not be installed stays in the inbox, so it has to be
    said out loud: its author is somewhere else and will otherwise be waiting
    for a party that is never going to appear.
  -->
  <div class="problem">
    <strong>Some proposals could not be imported:</strong>
    <ul>
      {#each status.problems as trouble (trouble)}<li>{trouble}</li>{/each}
    </ul>
  </div>
{/if}

<Connection />

<p class="hint">
  Actors, parties and situations are kept as JSON in a private GitHub repository, one commit per change. Any
  machine with the repository and a token sees the same campaign.
</p>

<style>
  .imported {
    background: var(--success-bg);
    border-left: 3px solid var(--success-text);
    color: var(--success-text);
    padding: 0.4rem 0.75rem;
  }
  .problem ul {
    margin: 0.25rem 0 0;
    padding-left: 1.25rem;
  }

  .state {
    display: flex;
    gap: 0.75rem;
    align-items: baseline;
  }
  .state.blocked {
    color: var(--error-text);
    font-weight: 600;
  }
  .detail {
    color: var(--muted);
    font-size: 0.85rem;
  }
  .problem {
    background: var(--error-bg);
    border-left: 3px solid var(--danger);
    padding: 0.5rem 0.75rem;
    max-width: 44rem;
  }
  /* Not reaching the repository is a delay, not a problem to solve. */
  .problem.transient {
    background: var(--warning-bg);
    border-left-color: var(--warning-text);
  }
  .hint {
    color: var(--muted);
    max-width: 44rem;
  }
</style>
