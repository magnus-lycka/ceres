<script lang="ts">
  import type { z } from 'zod';
  import { careerInput, formValues, type Values } from './api';
  let {
    spec,
    busy,
    onsubmit,
  }: { spec: z.infer<typeof careerInput>; busy: boolean; onsubmit: (values: Values) => void } = $props();
  let careerName = $state('');
  let precareerName = $state('');
  const career = $derived(spec.career_options.find((c) => c.name === careerName) ?? spec.career_options[0]);
  const precareer = $derived(
    spec.precareer_options.find((c) => c.name === precareerName) ?? spec.precareer_options[0],
  );
  function submit(event: SubmitEvent) {
    event.preventDefault();
    onsubmit(formValues(event.currentTarget as HTMLFormElement));
  }
</script>

{#if career}
  <form onsubmit={submit}>
    <fieldset disabled={busy}>
      <legend>Career</legend>
      <label
        >Career<select
          name="career"
          value={career.name}
          onchange={(e) => (careerName = e.currentTarget.value)}
        >
          {#each spec.career_options as c (c.name)}<option>{c.name}</option>{/each}
        </select></label
      >
      <p>{career.description}</p>
      <p>Qualification: {career.qualification.characteristic} {career.qualification.target}+</p>
      {#key career.name}<label
          >Assignment<select name="assignment"
            >{#each career.assignments as a (a.name)}<option value={a.name}>{a.name} — {a.description}</option
              >{/each}</select
          ></label
        >{/key}
      <label
        >Qualification roll (2D, before DMs)<input
          name="roll"
          type="number"
          min="2"
          max="12"
          required
        /></label
      >
      <button>Attempt qualification</button>
    </fieldset>
  </form>
{/if}
{#if precareer}
  <form onsubmit={submit}>
    <fieldset disabled={busy}>
      <legend>Pre-career education</legend>
      <input type="hidden" name="kind" value="precareer_entry" />
      <label
        >Pre-career<select
          name="precareer"
          value={precareer.name}
          onchange={(e) => (precareerName = e.currentTarget.value)}
        >
          {#each spec.precareer_options as c (c.name)}<option>{c.name}</option>{/each}
        </select></label
      >
      <p>{precareer.entry_requirement}</p>
      {#if precareer.curricula.length}{#key precareer.name}<label
            >Curriculum<select name="curriculum"
              >{#each precareer.curricula as c (c)}<option>{c}</option>{/each}</select
            ></label
          >{/key}{/if}
      <label>Entry roll (2D)<input name="roll" type="number" min="2" max="12" required /></label>
      <button>Attempt entry</button>
    </fieldset>
  </form>
{/if}
{#if spec.can_finish}<button disabled={busy} onclick={() => onsubmit({ kind: 'finish_creation' })}
    >Finish character creation</button
  >{/if}

<style>
  fieldset {
    border: 1px solid var(--border);
    border-radius: 0.4rem;
    margin: 1rem 0;
    padding: 1rem;
  }
  label {
    display: grid;
    gap: 0.3rem;
    margin: 0.6rem 0;
  }
  select,
  input {
    font: inherit;
    padding: 0.5rem;
    max-width: 100%;
  }
  button {
    padding: 0.5rem 1rem;
  }
</style>
