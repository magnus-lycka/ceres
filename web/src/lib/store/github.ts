/**
 * A file store backed by a GitHub repository.
 *
 * The only module that knows GitHub exists. Everything above it works in
 * entities and paths, so moving to a different host means writing another
 * `FileStore` and changing nothing else.
 *
 * The repo is a private one holding data only — never the code repo. Each
 * write is a commit, which makes the history of a campaign readable and gives
 * undo for free through git rather than through anything this app has to keep.
 *
 * **The application still owns its persistence.** GitHub is storage, the way a
 * disk is storage. Nothing else writes into these directories: data proposed
 * from outside arrives as an issue or an `inbox/` file, and is validated and
 * installed by the application, not dropped into `actors/` behind its back.
 */
import type { FileStore } from './files';

const API = 'https://api.github.com';

export type Repository = {
  owner: string;
  repo: string;
  branch: string;
  /** Fine-grained token with `contents: read and write` on this repo alone. */
  token: string;
};

/** Raised when a write lands on a file that changed underneath it. */
export class ConflictError extends Error {
  constructor(path: string) {
    super(`${path} changed in the repository since it was read — reload and try again`);
    this.name = 'ConflictError';
  }
}

export class GitHubFileStore implements FileStore {
  /**
   * Blob sha per path, as GitHub last reported it. Updating a file requires
   * the sha it is replacing; that is also what makes a stale write fail loudly
   * rather than silently clobbering another machine's edit.
   */
  private shas = new Map<string, string>();

  constructor(private readonly repository: Repository) {}

  async list(prefix: string): Promise<string[]> {
    const tree = await this.tree();
    return tree.filter((entry) => entry.path.startsWith(`${prefix}/`)).map((entry) => entry.path);
  }

  async read(path: string): Promise<string | null> {
    const response = await this.request(`/contents/${path}?ref=${this.repository.branch}`);
    if (response.status === 404) return null;
    const file = (await this.parse(response)) as { content: string; sha: string };
    this.shas.set(path, file.sha);
    return decode(file.content);
  }

  async write(path: string, content: string, message: string): Promise<void> {
    const response = await this.request(`/contents/${path}`, {
      method: 'PUT',
      body: JSON.stringify({
        message,
        content: encode(content),
        branch: this.repository.branch,
        sha: this.shas.get(path),
      }),
    });
    if (response.status === 409 || response.status === 422) throw new ConflictError(path);
    const written = (await this.parse(response)) as { content: { sha: string } };
    this.shas.set(path, written.content.sha);
    this.cachedTree = null;
  }

  async remove(path: string, message: string): Promise<void> {
    const sha = this.shas.get(path) ?? (await this.shaOf(path));
    // Already gone. Deletion is unguarded and idempotent: asking twice is not
    // an error, it is the same answer.
    if (sha === null) return;
    const response = await this.request(`/contents/${path}`, {
      method: 'DELETE',
      body: JSON.stringify({ message, sha, branch: this.repository.branch }),
    });
    if (response.status === 409 || response.status === 422) throw new ConflictError(path);
    await this.parse(response);
    this.shas.delete(path);
    this.cachedTree = null;
  }

  /**
   * One request for the whole layout, rather than one per directory. Reset
   * whenever this store writes; a change made elsewhere is only noticed on the
   * next reload, which is what the conflict on write is there to catch.
   */
  private cachedTree: { path: string; sha: string }[] | null = null;

  private async tree(): Promise<{ path: string; sha: string }[]> {
    if (this.cachedTree) return this.cachedTree;
    const response = await this.request(`/git/trees/${this.repository.branch}?recursive=1`);
    // An empty repository has no tree at all, which is not an error here.
    if (response.status === 404 || response.status === 409) return (this.cachedTree = []);
    const body = (await this.parse(response)) as {
      tree: { path: string; sha: string; type: string }[];
    };
    const files = body.tree.filter((entry) => entry.type === 'blob');
    for (const entry of files) this.shas.set(entry.path, entry.sha);
    return (this.cachedTree = files.map(({ path, sha }) => ({ path, sha })));
  }

  private async shaOf(path: string): Promise<string | null> {
    const tree = await this.tree();
    return tree.find((entry) => entry.path === path)?.sha ?? null;
  }

  private request(route: string, init: RequestInit = {}): Promise<Response> {
    const { owner, repo, token } = this.repository;
    return fetch(`${API}/repos/${owner}/${repo}${route}`, {
      ...init,
      headers: {
        accept: 'application/vnd.github+json',
        authorization: `Bearer ${token}`,
        'x-github-api-version': '2022-11-28',
        ...(init.body ? { 'content-type': 'application/json' } : {}),
      },
    });
  }

  private async parse(response: Response): Promise<unknown> {
    if (response.ok) return response.json();
    const detail = await response.text();
    throw new Error(`GitHub responded ${response.status}: ${detail.slice(0, 200)}`);
  }
}

/**
 * GitHub carries file contents as base64. `btoa` and `atob` speak bytes rather
 * than text, so anything outside Latin-1 — a Vargr name, an em dash in a note
 * — has to go through an explicit UTF-8 round trip.
 */
function encode(text: string): string {
  const bytes = new TextEncoder().encode(text);
  return btoa(String.fromCharCode(...bytes));
}

function decode(base64: string): string {
  const binary = atob(base64.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(binary, (character) => character.charCodeAt(0)));
}
