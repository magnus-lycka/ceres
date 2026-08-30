/**
 * The application's data, and its relationship with the repository.
 *
 * One library for the whole app, backed by IndexedDB, so every screen sees the
 * same actors and every edit is immediate. Syncing is a background concern:
 * on a timer, when the page is being left, and on demand.
 *
 * Shared as a module rather than passed down through pages because the nav bar
 * needs the sync state too, and threading it through every route to reach one
 * indicator would be worse than a module that owns it.
 */
import { Library } from './library';
import { IdbFileStore } from './idb';
import { GitHubRepository } from './github';
import { Sync, type SyncState } from './sync';
import { loadConnection } from './connection';

const local = new IdbFileStore();

/** Always available: the local copy needs no repository and no network. */
export const library = new Library(local);

export const status = $state<{
  state: SyncState;
  changes: number;
  at: Date | null;
  detail: string;
  connected: boolean;
  busy: boolean;
  /** What the last sync installed from the inbox, ready to read. */
  imported: string;
  /** Proposals that arrived but could not be installed, with the reason. */
  problems: string[];
}>({
  state: 'synced',
  changes: 0,
  at: null,
  detail: '',
  connected: false,
  busy: false,
  imported: '',
  problems: [],
});

/** Whether the last attempt failed for a reason that will likely pass. */
export function transient(): boolean {
  return status.detail !== '' && status.state !== 'blocked';
}

/** Every minute. Often enough to lose almost nothing, rare enough to ignore. */
const INTERVAL = 60_000;

let sync: Sync | null = null;

/** Rebuild the connection from stored settings — after Connect, or on load. */
export function reconnect(): void {
  const settings = loadConnection();
  sync = settings ? new Sync(local, new GitHubRepository(settings)) : null;
  status.connected = sync !== null;
  if (!sync) {
    status.state = 'synced';
    status.detail = '';
  }
}

/** Recount what is waiting. Cheap, local, and asks the network nothing. */
export async function refresh(): Promise<void> {
  const changes = (await local.changes()).size;
  status.changes = changes;
  // A standoff stays a standoff until a sync resolves it; a new edit does not
  // clear it.
  if (status.state !== 'blocked') status.state = changes > 0 ? 'pending' : 'synced';
}

/**
 * Install whatever the sync just brought down, and push the result.
 *
 * A proposal arrives as a file in `inbox/`, so it is already here by the time
 * sync reports success — installing it is a local operation, and the second
 * sync is only to send the actors, party, receipt and the inbox deletion back.
 * That second run happens against the head we have just pulled, so it is an
 * ordinary push rather than another reconciliation.
 *
 * Nothing here runs when sync is blocked: a standoff means the local copy was
 * not advanced, so any inbox file present is one we have already seen.
 */
async function consumeInbox(): Promise<void> {
  const { installed, problems } = await library.importInbox();
  status.problems = problems;
  if (installed.length === 0) return;

  const actors = installed.reduce((count, receipt) => count + receipt.actors.length, 0);
  const issues = installed.map((receipt) => `#${receipt.issue}`).join(', ');
  status.imported = `Imported ${actors} actor${actors === 1 ? '' : 's'} and ${installed.length} part${installed.length === 1 ? 'y' : 'ies'} from ${issues}.`;

  const outcome = await sync!.run();
  status.state = outcome.state;
  status.changes = outcome.state === 'blocked' ? outcome.changes : 0;
  status.detail = outcome.detail ?? '';
}

export async function now(): Promise<void> {
  if (!sync || status.busy) return void (await refresh());
  status.busy = true;
  status.imported = '';
  try {
    const outcome = await sync.run();
    status.state = outcome.state;
    status.changes = outcome.state === 'blocked' ? outcome.changes : 0;
    status.at = outcome.at;
    status.detail = outcome.detail ?? '';
    if (outcome.state !== 'blocked') await consumeInbox();
  } catch (failure) {
    /*
     * Not being able to reach the repository is not a conflict, and must never
     * stop the app: editing carries on locally and there is simply more to
     * push next time. Only `Sync` itself declares a standoff, because only it
     * knows both sides have moved.
     */
    status.detail = failure instanceof Error ? failure.message : String(failure);
  } finally {
    status.busy = false;
    await refresh();
  }
}

let started = false;

/** Called once, from the layout. */
export function start(): () => void {
  reconnect();
  void refresh();
  if (started) return () => {};
  started = true;

  const timer = setInterval(() => void now(), INTERVAL);
  // Leaving the page is the last chance to save a session's play; hiding it is
  // the signal that survives a closed laptop lid, where unload often does not.
  const onHide = () => {
    if (document.visibilityState === 'hidden') void now();
  };
  document.addEventListener('visibilitychange', onHide);

  return () => {
    clearInterval(timer);
    document.removeEventListener('visibilitychange', onHide);
    started = false;
  };
}
