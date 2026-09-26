<script lang="ts">
  /** Wiring only: which situation the address names. Everything else is the screen's. */
  import { page } from '$app/state';
  import SituationScreen from '$lib/situations/SituationScreen.svelte';
  import { situationId } from '$lib/schema/situation';
</script>

<SituationScreen id={situationId(Number(page.params.id))} />
