<script lang="ts">
  /**
   * A robot's damaged systems, as a glance rather than the record: how many
   * locations are hit and the worst of them, in a colour that reads worse as
   * the score climbs. Opening the panel is how you read what each one did.
   */
  import type { Actor } from '$lib/schema/actor';
  import { criticalRows } from '$lib/rules/rounds/criticals';
  import { criticalHeat, criticalScore } from '$lib/rules/rounds/criticalHeat';

  let { actor }: { actor: Actor } = $props();

  const score = $derived(criticalScore(actor));
  const rows = $derived(score !== null ? criticalRows(actor).filter((row) => row.severity > 0) : []);
  const worst = $derived(rows.length > 0 ? Math.max(...rows.map((row) => row.severity)) : 0);
</script>

{#if score !== null && rows.length > 0}
  <span class="crit-heat" style:--crit-heat={criticalHeat(score)}>{rows.length} hit, worst S{worst}</span>
{/if}
