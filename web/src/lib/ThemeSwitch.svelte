<script lang="ts">
  import { onMount } from 'svelte';
  import './theme.css';

  let dark = $state(false);

  function apply(value: boolean) {
    dark = value;
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  }

  onMount(() => {
    let preference: string | null = null;
    try {
      preference = localStorage.getItem('ceres-theme');
    } catch {
      // The switch still works when browser storage is unavailable.
    }
    apply(
      preference === 'dark' || (preference !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches),
    );
  });

  function toggle() {
    apply(!dark);
    try {
      localStorage.setItem('ceres-theme', dark ? 'dark' : 'light');
    } catch {
      // Keep the selected theme for this page even without persistence.
    }
  }
</script>

<button type="button" onclick={toggle}>{dark ? 'Light mode' : 'Dark mode'}</button>

<style>
  button {
    margin-left: auto;
    padding: 0.25rem 0.75rem;
  }
</style>
