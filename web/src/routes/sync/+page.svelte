<script lang="ts">
  /**
   * Where the data lives.
   *
   * Its own page because it is settings: entered once on a machine, then not
   * looked at again. The roster screens read the stored connection on arrival.
   */
  import Connection from '$lib/store/Connection.svelte';
  import { now, status } from '$lib/store/session.svelte';

  const summary = $derived(
    !status.connected
      ? 'No data repository. Everything stays in this browser.'
      : status.state === 'blocked'
        ? 'Stopped. The repository and this browser have both moved on.'
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
  <p class="problem">
    {status.detail}
    <br />
    Resolve it with git, then reload. To undo a push:
    <code>git reset --hard &lt;sha&gt; &amp;&amp; git push --force-with-lease</code>
  </p>
{/if}

<Connection />

<p class="hint">
  Actors, parties and situations are kept as JSON in a private GitHub repository, one commit per change. Any
  machine with the repository and a token sees the same campaign.
</p>

<style>
  .state {
    display: flex;
    gap: 0.75rem;
    align-items: baseline;
  }
  .state.blocked {
    color: #7c2c1a;
    font-weight: 600;
  }
  .detail {
    color: #555;
    font-size: 0.85rem;
  }
  .problem {
    background: #fef2f2;
    border-left: 3px solid #b91c1c;
    padding: 0.5rem 0.75rem;
    max-width: 44rem;
  }
  .hint {
    color: #555;
    max-width: 44rem;
  }
</style>
