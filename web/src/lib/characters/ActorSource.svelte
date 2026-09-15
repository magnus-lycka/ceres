<script lang="ts">
  import type { Actor } from '$lib/schema/actor';
  import { library, refresh } from '$lib/store/session.svelte';
  import { characterSource, characterSheetUrl, sourceFromCharacter, type SourceStatus } from './link';
  let { actor, onchange }: { actor: Actor; onchange: (actor: Actor) => void } = $props();
  let status = $state<SourceStatus | null>(null);
  let busy = $state(false);
  let problem = $state('');
  $effect(() => {
    const url = actor.character?.url;
    status = null;
    if (url) {
      let current = true;
      void characterSource(url).then((result) => {
        if (current) status = result;
      });
      return () => {
        current = false;
      };
    }
  });
  async function check() {
    const url = actor.character?.url;
    if (!url) return;
    busy = true;
    status = await characterSource(url);
    busy = false;
  }
  async function update() {
    const url = actor.character?.url;
    if (!url) return;
    busy = true;
    problem = '';
    try {
      status = await characterSource(url);
      if (status.state === 'available') {
        const updated = await library.refreshCharacter(actor.id, sourceFromCharacter(status.character, url));
        await refresh();
        onchange(updated);
      }
    } catch (e) {
      problem = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }
</script>

{#if actor.character}
  <section aria-label="Source character">
    <h2>Source character</h2>
    <!-- A source can live on another Ceres server. -->
    <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
    <a href={characterSheetUrl(actor.character.url)}>Full character sheet</a>
    {#if status?.state === 'deleted'}<p>Source character deleted</p>
    {:else if status?.state === 'unavailable'}<p>Source unavailable</p>
    {:else if status?.state === 'available'}<p>
        {status.character.name}{status.character.finished ? '' : ' — creation in progress'}
      </p>
    {:else}<p>Checking source…</p>{/if}
    <button onclick={update} disabled={busy || status?.state !== 'available' || !status.character.finished}
      >Update from character</button
    >
    <button onclick={check} disabled={busy}>Check source</button>
    {#if problem}<p role="alert">{problem}</p>{/if}
  </section>
{/if}

<style>
  section {
    border-top: 1px solid var(--border);
    margin-top: 1rem;
    padding-top: 0.5rem;
  }
  button {
    margin-right: 0.5rem;
    padding: 0.5rem;
  }
</style>
