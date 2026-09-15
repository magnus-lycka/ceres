<script lang="ts">
  import { formValues, type Pending, type Values } from './api';
  import CareerChoice from './CareerChoice.svelte';
  import WorldChoice from './WorldChoice.svelte';
  let { pending, busy, onsubmit }: { pending: Pending; busy: boolean; onsubmit: (values: Values) => void } =
    $props();
  let problem = $state('');
  function submit(event: SubmitEvent) {
    event.preventDefault();
    const values = formValues(event.currentTarget as HTMLFormElement);
    for (const spec of pending.inputs) {
      if (spec.kind !== 'Select') continue;
      const chosen = values[spec.name];
      const count = Array.isArray(chosen) ? chosen.length : chosen ? 1 : 0;
      if (count < spec.min_select || count > spec.max_select) {
        problem = `${spec.label}: choose ${spec.min_select}–${spec.max_select}.`;
        return;
      }
    }
    problem = '';
    onsubmit(values);
  }
</script>

{#if !pending.inputs.some((spec) => spec.kind === 'Select' && spec.label === pending.instruction)}
  <p>{pending.instruction}</p>
{/if}
{#if problem}<p role="alert">{problem}</p>{/if}
{#each pending.inputs as spec, index (index)}
  {#if spec.kind === 'CareerChoice'}<CareerChoice {spec} {busy} {onsubmit} />
  {:else if spec.kind === 'SelectWorld'}<WorldChoice {spec} {busy} {onsubmit} />
  {:else if spec.kind === 'ActionChoice'}
    <div class="actions">
      {#each spec.options as [label, value] (value)}
        <button type="button" disabled={busy} onclick={() => onsubmit({ [spec.name]: value })}>{label}</button
        >
      {/each}
    </div>
  {:else if spec.kind === 'InfoText'}<p>{spec.text}</p>{/if}
{/each}
{#if !pending.inputs.some((spec) => spec.kind === 'CareerChoice' || spec.kind === 'SelectWorld' || spec.kind === 'ActionChoice')}
  <form onsubmit={submit}>
    <fieldset disabled={busy}>
      {#each pending.inputs as spec, index (index)}
        {#if spec.kind === 'NumberEntry'}
          <label
            >{spec.label}<input
              type="number"
              name={spec.name}
              min={spec.min}
              max={spec.max}
              required
            /></label
          >
        {:else if spec.kind === 'Select'}
          <fieldset>
            <legend>{spec.label}</legend>
            {#each spec.options as [label, value], i (value)}
              <label class="option"
                ><input
                  type={spec.max_select > 1 ? 'checkbox' : 'radio'}
                  name={spec.name}
                  {value}
                  checked={spec.max_select === 1 &&
                    (spec.default !== null ? value === spec.default : i === 0)}
                />{label}</label
              >
            {/each}
            {#if spec.max_select > 1}<small>Choose {spec.min_select}–{spec.max_select}.</small>{/if}
          </fieldset>
        {:else if spec.kind === 'Reference'}<input type="hidden" name={spec.name} value={spec.value} />
        {:else if spec.kind === 'TextEntry'}
          <label
            >{spec.label}
            {#if spec.multiline}<textarea name={spec.name} value={spec.value} placeholder={spec.placeholder}
              ></textarea>
            {:else}<input name={spec.name} value={spec.value} placeholder={spec.placeholder} />{/if}
          </label>
        {/if}
      {/each}
      <button type="submit">Confirm</button>
    </fieldset>
  </form>
{/if}

<style>
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 1rem;
  }
  label {
    display: grid;
    gap: 0.3rem;
    margin: 0.6rem 0;
  }
  .option {
    display: flex;
    align-items: center;
  }
  input,
  textarea {
    padding: 0.5rem;
    font: inherit;
    max-width: 100%;
  }
  button {
    padding: 0.5rem 1rem;
  }
</style>
