<script lang="ts">
  /**
   * Where the data lives. Paste a repository URL and a token.
   *
   * The token is a fine-grained GitHub PAT scoped to that one private repo
   * with `Contents: Read and write`. It is kept in this browser's local
   * storage and nowhere else — Forget removes it.
   */
  import { clearConnection, loadConnection, parseRepository, saveConnection } from './connection';
  import { GitHubRepository } from './github';
  import { reconnect, now } from './session.svelte';

  const existing = loadConnection();
  let url = $state(existing ? `${existing.owner}/${existing.repo}` : '');
  let token = $state(existing?.token ?? '');
  let branch = $state(existing?.branch ?? 'main');
  let device = $state(existing?.device ?? '');
  let status = $state(existing ? `Connected to ${existing.owner}/${existing.repo}.` : '');
  let busy = $state(false);

  async function connect() {
    const repository = parseRepository(url);
    if (!repository) return void (status = `"${url}" does not name a repository.`);
    if (!token.trim()) return void (status = 'A token is needed to reach a private repo.');

    busy = true;
    status = 'Checking…';
    const settings = {
      ...repository,
      branch: branch.trim() || 'main',
      token: token.trim(),
      device: device.trim(),
    };
    try {
      // Prove it works before storing it: a token that cannot read is worse
      // than no token, because it looks configured.
      await new GitHubRepository(settings).head();
      saveConnection(settings);
      reconnect();
      status = `Connected to ${settings.owner}/${settings.repo}.`;
      await now();
    } catch (failure) {
      status = failure instanceof Error ? failure.message : String(failure);
    } finally {
      busy = false;
    }
  }

  function forget() {
    clearConnection();
    url = '';
    token = '';
    status = 'Forgotten. The local copy is untouched; nothing more is sent.';
    reconnect();
  }
</script>

<section>
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
    <label>
      This machine
      <input bind:value={device} placeholder="thinkpad" size="14" />
    </label>
    <button onclick={connect} disabled={busy}>Connect</button>
    <button onclick={forget} disabled={busy}>Forget</button>
  </div>
  {#if status}<p class="status">{status}</p>{/if}
  <p class="hint">
    A fine-grained token, scoped to that repository alone, with Contents: Read and write. It is kept in this
    browser only.
  </p>
</section>

<style>
  section {
    border: 1px solid #e5e7eb;
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    max-width: 60rem;
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
