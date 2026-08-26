/**
 * The local file store: IndexedDB, and the source of truth during a session.
 *
 * Every edit lands here first and answers in a millisecond or two. Nothing in
 * the application waits for a network. What reaches GitHub, and when, is
 * `sync.ts`'s business — writing through to a version control system on every
 * keystroke-completing edit is what made the app slow, and it treated a
 * history of commits as though it were a key-value store.
 *
 * Alongside the files it keeps two pieces of bookkeeping the sync needs: which
 * paths have changed since the last sync, and the commit this copy was last
 * known to match.
 */
import { createStore, del, get, keys, set } from 'idb-keyval';
import type { FileStore } from './files';

/** What happened to a path since the last sync, and why. */
export type Change = { op: 'write' | 'remove'; message: string };

const DIRTY = 'dirty';
const HEAD = 'head';

export class IdbFileStore implements FileStore {
  private readonly files;
  private readonly meta;

  /**
   * Two databases rather than two object stores in one: `createStore` gives a
   * database exactly one store, so asking the same database for a second name
   * opens it without that store and every access fails.
   */
  constructor(name = 'ceres') {
    this.files = createStore(`${name}-files`, 'files');
    this.meta = createStore(`${name}-meta`, 'meta');
  }

  async list(prefix: string): Promise<string[]> {
    const all = (await keys(this.files)) as string[];
    return all.filter((path) => path.startsWith(`${prefix}/`));
  }

  async read(path: string): Promise<string | null> {
    return (await get<string>(path, this.files)) ?? null;
  }

  async write(path: string, content: string, message: string): Promise<void> {
    await set(path, content, this.files);
    await this.note(path, { op: 'write', message });
  }

  async remove(path: string, message: string): Promise<void> {
    await del(path, this.files);
    await this.note(path, { op: 'remove', message });
  }

  /**
   * Everything, for a sync to push. Kept separate from `list` because a sync
   * works on the whole repository rather than one entity's directory.
   */
  async all(): Promise<Map<string, string>> {
    const paths = (await keys(this.files)) as string[];
    const entries = await Promise.all(paths.map(async (path) => [path, await this.read(path)] as const));
    return new Map(entries.filter(([, content]) => content !== null) as [string, string][]);
  }

  /** Paths changed since the last sync, with the reason each changed. */
  async changes(): Promise<Map<string, Change>> {
    return new Map(Object.entries((await get<Record<string, Change>>(DIRTY, this.meta)) ?? {}));
  }

  /**
   * A write followed by a remove is a remove; a remove followed by a write is
   * a write. Only the latest matters, because the sync pushes the current
   * state of the path rather than replaying what happened to it.
   */
  private async note(path: string, change: Change): Promise<void> {
    const dirty = (await get<Record<string, Change>>(DIRTY, this.meta)) ?? {};
    dirty[path] = change;
    await set(DIRTY, dirty, this.meta);
  }

  async clearChanges(): Promise<void> {
    await set(DIRTY, {}, this.meta);
  }

  /** The commit this copy was last known to match, or null before any sync. */
  async head(): Promise<string | null> {
    return (await get<string>(HEAD, this.meta)) ?? null;
  }

  async setHead(sha: string): Promise<void> {
    await set(HEAD, sha, this.meta);
  }

  /** Replace everything with what a pull fetched. */
  async replaceAll(contents: Map<string, string>): Promise<void> {
    for (const path of (await keys(this.files)) as string[]) await del(path, this.files);
    for (const [path, content] of contents) await set(path, content, this.files);
    await this.clearChanges();
  }
}
