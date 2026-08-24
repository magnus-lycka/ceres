<script lang="ts">
  let { children } = $props();
</script>

<nav>
  <a href="/actors">Actors</a>
  <a href="/parties">Parties</a>
</nav>

{@render children()}

<style>
  :global(body) { font: 14px/1.5 system-ui; margin: 0; padding: 1.5rem 2rem; }
  nav { display: flex; gap: 1rem; margin-bottom: 1rem; }
  nav a { color: #2563eb; text-decoration: none; }
</style>
