<script lang="ts">
  // `resolve` applies the app's base path, so the links keep working if the
  // site is ever served from a subdirectory rather than the domain root.
  import { resolve } from '$app/paths';
  import { start, status } from '$lib/store/session.svelte';

  let { children } = $props();

  // One timer for the whole app, wherever you happen to be standing.
  $effect(start);

  const label = $derived(
    status.state === 'blocked'
      ? 'Sync — needs attention'
      : status.changes > 0
        ? `Sync — ${status.changes} waiting`
        : 'Sync',
  );
</script>

<nav>
  <a href={resolve('/actors')}>Actors</a>
  <a href={resolve('/parties')}>Parties</a>
  <a href={resolve('/situation')}>Situation</a>
  <a
    href={resolve('/sync')}
    class:pending={status.changes > 0 && status.state !== 'blocked'}
    class:blocked={status.state === 'blocked'}>{label}</a
  >
</nav>

{@render children()}

<style>
  :global(body) {
    font: 14px/1.5 system-ui;
    margin: 0;
    padding: 1.5rem 2rem;
  }
  nav {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  nav a {
    color: #2563eb;
    text-decoration: none;
  }
</style>
