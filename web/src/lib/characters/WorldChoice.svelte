<script lang="ts">
  import { z } from 'zod';
  import { worldInput, type Values } from './api';
  import WorldPicker from './WorldPicker.svelte';
  let {
    spec,
    busy,
    onsubmit,
  }: {
    spec: z.infer<typeof worldInput>;
    busy: boolean;
    onsubmit: (values: Values) => void;
  } = $props();
  let opened = $state(false);
</script>

{#if spec.open_label && !opened}
  <button
    disabled={busy}
    onclick={() => {
      opened = true;
    }}>{spec.open_label}</button
  >
{/if}
{#if spec.skip_values}
  <button
    disabled={busy}
    onclick={() => {
      if (spec.skip_values) onsubmit(spec.skip_values);
    }}>Skip</button
  >
{/if}
{#if !spec.open_label || opened}
  <WorldPicker {spec} {busy} {onsubmit} />
{/if}

<style>
  button {
    padding: 0.5rem 1rem;
    margin: 0 0.5rem 0.5rem 0;
  }
</style>
