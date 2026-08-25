<script lang="ts">
  /**
   * Where the data lives.
   *
   * Its own page because it is settings: entered once on a machine, then not
   * looked at again. The roster screens read the stored connection on arrival.
   */
  import Connection from '$lib/store/Connection.svelte';
</script>

<h1>Sync</h1>

<Connection />

<p class="hint">
  Actors, parties and situations are kept as JSON in a private GitHub repository, one commit per change. Any
  machine with the repository and a token sees the same campaign.
</p>

<style>
  .hint {
    color: #555;
    max-width: 44rem;
  }
</style>
