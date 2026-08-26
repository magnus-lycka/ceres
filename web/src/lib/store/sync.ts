/**
 * Reconciling the local copy with the data repository.
 *
 * The application never waits for this. Edits land in IndexedDB immediately;
 * a sync happens on a timer, on demand, and when the page is being left.
 *
 * The whole of conflict detection is one comparison. We remember the commit
 * our copy was last known to match; before pushing we ask what the branch
 * points at now. The intended use is one machine at a time — laptop X this
 * week, laptop Y the next — so that check is nearly always "unchanged", and
 * the push is a fast path.
 *
 * When it has moved there are two cases. With nothing changed locally, this
 * copy is simply behind, and taking the remote wholesale is right and silent.
 * With local changes as well, both sides have moved and **this stops**. It
 * does not merge and it does not guess: git is a better tool for that than
 * anything reasonable to write here, and losing a session's play to a clever
 * automatic resolution would be worse than being asked to sort it out.
 */
import type { GitHubRepository } from './github';
import type { IdbFileStore } from './idb';

export type SyncState =
  /** Local and remote agree. */
  | 'synced'
  /** Local changes are waiting to go up. */
  | 'pending'
  /** Both sides moved. Nothing further happens until a person resolves it. */
  | 'blocked';

export type SyncOutcome = {
  state: SyncState;
  /** How many local changes are waiting, or went up. */
  changes: number;
  at: Date;
  detail?: string;
};

export class Sync {
  constructor(
    private readonly local: IdbFileStore,
    private readonly remote: GitHubRepository,
  ) {}

  /** What a sync would do right now, without doing it. */
  async status(): Promise<SyncOutcome> {
    const changes = (await this.local.changes()).size;
    return { state: changes > 0 ? 'pending' : 'synced', changes, at: new Date() };
  }

  async run(): Promise<SyncOutcome> {
    const changes = await this.local.changes();
    const mine = await this.local.head();
    const theirs = await this.remote.head();
    const at = new Date();

    if (theirs === null) return this.push(changes, null, at);
    if (theirs === mine) {
      return changes.size === 0 ? { state: 'synced', changes: 0, at } : this.push(changes, mine, at);
    }

    // The branch has moved. Behind but unmodified is not a conflict.
    if (changes.size === 0) {
      await this.local.replaceAll(await this.remote.files(theirs));
      await this.local.setHead(theirs);
      return { state: 'synced', changes: 0, at };
    }

    // Never synced, and both sides hold data: we cannot tell what belongs to
    // whom, so this is the same standoff rather than a first push.
    return {
      state: 'blocked',
      changes: changes.size,
      at,
      detail:
        mine === null
          ? 'This browser has unsynced changes and the repository already has data. Resolve with git.'
          : `The repository moved on to ${theirs.slice(0, 7)} while this browser has ${changes.size} unsynced change(s). Resolve with git.`,
    };
  }

  private async push(
    changes: Map<string, { op: 'write' | 'remove'; message: string }>,
    parent: string | null,
    at: Date,
  ): Promise<SyncOutcome> {
    if (changes.size === 0) return { state: 'synced', changes: 0, at };

    const files = await this.local.all();
    const written = [...changes].map(([path, change]) => ({
      path,
      content: change.op === 'remove' ? null : (files.get(path) ?? null),
    }));

    const head = await this.remote.commit(written, describe(changes), parent);
    await this.local.setHead(head);
    await this.local.clearChanges();
    return { state: 'synced', changes: changes.size, at };
  }
}

/**
 * One commit carries a session's worth of changes, so the message has to say
 * more than "sync": the summary line counts them, and the body keeps the
 * per-change reasons the local store recorded as they happened.
 */
function describe(changes: Map<string, { op: 'write' | 'remove'; message: string }>): string {
  const removed = [...changes.values()].filter((change) => change.op === 'remove').length;
  const written = changes.size - removed;
  const parts = [written && `${written} written`, removed && `${removed} deleted`].filter(Boolean);
  const reasons = [...changes.values()].map((change) => `- ${change.message}`).join('\n');
  return `Sync: ${parts.join(', ')}\n\n${reasons}\n`;
}
