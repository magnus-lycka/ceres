/**
 * A GitHub repository, reached through the Git Data API.
 *
 * The only module that knows GitHub exists. It is not a file store and does
 * not pretend to be one: the application reads and writes IndexedDB, and this
 * is what `sync.ts` reconciles that against, now and then.
 *
 * The contents API — one request to read a file, two to write it, a commit per
 * write — is what made the app slow, and it treated a history of commits as a
 * key-value store. A whole session's changes go up here as **one commit in
 * five requests**, whatever the number of files: read the ref, read its tree,
 * build a new tree, commit it, move the ref. File contents go inline in the
 * tree, so there is no per-file round trip.
 *
 * **The application still owns its persistence.** GitHub is storage. Nothing
 * else writes into these directories: data proposed from outside arrives as an
 * issue or an `inbox/` file and is validated and installed by the application,
 * not dropped into `actors/` behind its back.
 */

const API = 'https://api.github.com';

export type Repository = {
  owner: string;
  repo: string;
  branch: string;
  /** Fine-grained token with `contents: read and write` on this repo alone. */
  token: string;
  /** Which machine this is, so a commit says where it came from. */
  device?: string;
};

/** A file to write, or a path to delete when `content` is null. */
export type Change = { path: string; content: string | null };

export class GitHubRepository {
  constructor(private readonly repository: Repository) {}

  /**
   * The commit the branch points at, or null when the repository has none.
   *
   * This one value is the whole of conflict detection: if it has not moved
   * since we last synced, nobody else has written and a push is safe.
   */
  async head(): Promise<string | null> {
    const response = await this.request(`/git/ref/heads/${this.repository.branch}`);
    if (response.status === 404 || response.status === 409) return null;
    const ref = (await this.parse(response)) as { object: { sha: string } };
    return ref.object.sha;
  }

  /** Every file in a commit, path to contents. */
  async files(commit: string): Promise<Map<string, string>> {
    const listing = (await this.parse(await this.request(`/git/trees/${commit}?recursive=1`))) as {
      tree: { path: string; sha: string; type: string }[];
    };
    const blobs = listing.tree.filter((entry) => entry.type === 'blob');
    const contents = await Promise.all(blobs.map((entry) => this.blob(entry.sha)));
    return new Map(blobs.map((entry, index) => [entry.path, contents[index]]));
  }

  /**
   * Write every change as a single commit and move the branch to it.
   *
   * `parent` is the commit the changes were made against. Passing the head we
   * checked is what keeps the push honest: GitHub refuses to move a ref onto a
   * commit that is not a descendant of where the ref is now.
   */
  async commit(changes: Change[], message: string, parent: string | null): Promise<string> {
    const base = parent ? await this.treeOf(parent) : null;
    const tree = (await this.parse(
      await this.request('/git/trees', {
        method: 'POST',
        body: JSON.stringify({
          ...(base ? { base_tree: base } : {}),
          tree: changes.map(({ path, content }) => ({
            path,
            mode: '100644',
            type: 'blob',
            // A null sha and no content is how a tree deletes a path.
            ...(content === null ? { sha: null } : { content }),
          })),
        }),
      }),
    )) as { sha: string };

    const device = this.repository.device?.trim();
    const created = (await this.parse(
      await this.request('/git/commits', {
        method: 'POST',
        body: JSON.stringify({
          message,
          tree: tree.sha,
          parents: parent ? [parent] : [],
          // Without this every machine's commits are stamped with the token
          // owner, so "which laptop was that?" has no answer.
          ...(device ? { author: { name: device, email: `${device}@ceres.local` } } : {}),
        }),
      }),
    )) as { sha: string };

    await this.moveBranch(created.sha, parent !== null);
    return created.sha;
  }

  private async moveBranch(sha: string, exists: boolean): Promise<void> {
    const route = `/git/refs${exists ? `/heads/${this.repository.branch}` : ''}`;
    const body = exists ? { sha } : { ref: `refs/heads/${this.repository.branch}`, sha };
    await this.parse(
      await this.request(route, { method: exists ? 'PATCH' : 'POST', body: JSON.stringify(body) }),
    );
  }

  private async treeOf(commit: string): Promise<string> {
    const body = (await this.parse(await this.request(`/git/commits/${commit}`))) as {
      tree: { sha: string };
    };
    return body.tree.sha;
  }

  private async blob(sha: string): Promise<string> {
    const body = (await this.parse(await this.request(`/git/blobs/${sha}`))) as { content: string };
    return decode(body.content);
  }

  private request(route: string, init: RequestInit = {}): Promise<Response> {
    const { owner, repo, token } = this.repository;
    return fetch(`${API}/repos/${owner}/${repo}${route}`, {
      ...init,
      // GitHub answers authenticated reads with `Cache-Control: private,
      // max-age=60`, so the browser will happily replay a minute-old answer —
      // which showed up as deleted actors walking back in after a reload.
      cache: 'no-store',
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
 * Blobs come back base64. `atob` speaks bytes rather than text, so anything
 * outside Latin-1 — a Vargr name, an em dash in a note — needs an explicit
 * UTF-8 round trip.
 */
function decode(base64: string): string {
  const binary = atob(base64.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(binary, (character) => character.charCodeAt(0)));
}
