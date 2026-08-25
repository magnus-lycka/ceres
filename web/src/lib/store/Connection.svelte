<script lang="ts">
  /**
   * Where the data lives. Paste a repository URL and a token.
   *
   * The token is a fine-grained GitHub PAT scoped to that one private repo
   * with `Contents: Read and write`. It is kept in this browser's local
   * storage and nowhere else — Forget removes it.
   */
  import { clearConnection, loadConnection, parseRepository, saveConnection } from './connection';
  import { GitHubFileStore } from './github';
  import { Library } from './library';

  let { onconnect }: { onconnect: (library: Library | null) => void } = $props();

  const existing = loadConnection();
  let url = $state(existing ? `${existing.owner}/${existing.repo}` : '');
  let token = $state(existing?.token ?? '');
  let branch = $state(existing?.branch ?? 'main');
  let status = $state('');
  let busy = $state(false);
  // Settings, not working surface: once it is connected this collapses to one
  // line, because the roster is what the screen is for.
  let open = $state(existing === null);

  async function connect() {
    const repository = parseRepository(url);
    if (!repository) return void (status = `"${url}" does not name a repository.`);
    if (!token.trim()) return void (status = 'A token is needed to reach a private repo.');

    busy = true;
    status = 'Checking…';
    const settings = { ...repository, branch: branch.trim() || 'main', token: token.trim() };
    try {
      // Prove it works before storing it: a token that cannot read is worse
      // than no token, because it looks configured.
      const library = new Library(new GitHubFileStore(settings));
      const actors = await library.actors();
      saveConnection(settings);
      status = `${actors.length} actors.`;
      open = false;
      onconnect(library);
    } catch (failure) {
      status = failure instanceof Error ? failure.message : String(failure);
      onconnect(null);
    } finally {
      busy = false;
    }
  }

  function forget() {
    clearConnection();
    url = '';
    token = '';
    status = 'Forgotten. Nothing is stored in this browser.';
    open = true;
    onconnect(null);
  }
</script>

<section class:open>
  {#if !open}
    <p class="summary">
      <strong>{parseRepository(url)?.repo ?? 'No data repository'}</strong>
      <span class="detail">{parseRepository(url)?.owner ?? 'nothing is being saved'}</span>
      {#if status}<span class="detail">{status}</span>{/if}
      <button onclick={() => (open = true)}>Change</button>
    </p>
  {:else}
    <h2>Data repository</h2>
    <div class="fields">
      <label>
        Repository
        <input bind:value={url} placeholder="https://github.com/you/your-data" size="42" />
      </label>
      <label>
        Token
        <input bind:value={token} type="password" placeholder="github_pat_…" size="30" />
      </label>
      <label>
        Branch
        <input bind:value={branch} size="8" />
      </label>
      <button onclick={connect} disabled={busy}>Connect</button>
      <button onclick={forget} disabled={busy}>Forget</button>
    </div>
    {#if status}<p class="status">{status}</p>{/if}
    <p class="hint">
      A fine-grained token, scoped to that repository alone, with Contents: Read and write. It is kept in this
      browser only.
    </p>
  {/if}
</section>

<style>
  section {
    margin-bottom: 0.75rem;
  }
  section.open {
    border: 1px solid #e5e7eb;
    padding: 0.75rem 1rem;
  }
  .summary {
    display: flex;
    gap: 0.6rem;
    align-items: baseline;
    margin: 0;
  }
  .detail {
    color: #555;
    font-size: 0.85rem;
  }
  h2 {
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }
  .fields {
    display: flex;
    gap: 1rem;
    align-items: flex-end;
    flex-wrap: wrap;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    font-size: 0.85rem;
    color: #555;
  }
  .status {
    margin: 0.5rem 0 0;
    font-weight: 600;
  }
  .hint {
    color: #555;
    margin: 0.25rem 0 0;
    font-size: 0.85rem;
  }
</style>
