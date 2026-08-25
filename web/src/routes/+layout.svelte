<script lang="ts">
  // `resolve` applies the app's base path, so the links keep working if the
  // site is ever served from a subdirectory rather than the domain root.
  import { resolve } from '$app/paths';

  let { children } = $props();
</script>

<nav>
  <a href={resolve('/actors')}>Actors</a>
  <a href={resolve('/parties')}>Parties</a>
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
