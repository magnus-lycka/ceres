/**
 * The only way in and out of stored entities.
 *
 * Mirrors `ceres.rounds.library.store` on the Python side, deliberately: both
 * read the same repo, so they must agree about layout — one JSON file per
 * entity under a directory named for its kind, plus `counters.json`.
 *
 * Callers hand over and receive entities. They never learn what a path is,
 * which is what lets the backing store change without anything above noticing.
 *
 * Deletion is unguarded. Nothing checks whether an entity is referenced,
 * because a single-user tool has no business arguing with its user about it.
 * What the library owes instead is that a stale reference resolves to nothing
 * rather than raising — the same bargain as ON DELETE SET NULL.
 */
import { actorSchema, UNSAVED, type Actor } from '$lib/schema/actor';
import type { FileStore } from './files';

const ACTORS = 'actors';
const COUNTERS = 'counters.json';

/** Keyed by entity kind, as the Python store names them. */
type Counters = Record<string, number>;

export class Library {
  constructor(private readonly files: FileStore) {}

  /**
   * Writes run one at a time, in the order they were asked for.
   *
   * Allocating an id is read-then-write on `counters.json`, so two saves in
   * flight at once both read the same counter. Against a real repository that
   * surfaces as the second write being refused for carrying a stale sha —
   * which is exactly what pressing Add twice while the first is still going
   * used to produce. A queue is enough because there is one browser doing the
   * writing; a second machine editing at the same time is what the conflict on
   * write is for.
   */
  private pending: Promise<unknown> = Promise.resolve();

  private queued<T>(work: () => Promise<T>): Promise<T> {
    const result = this.pending.then(work, work);
    // The queue must survive a failed operation, or one error stops every
    // later write for the life of the session.
    this.pending = result.catch(() => undefined);
    return result;
  }

  async actors(): Promise<Actor[]> {
    const paths = await this.files.list(ACTORS);
    const actors = await Promise.all(paths.map((path) => this.parse(path)));
    return actors.sort((left, right) => left.id - right.id);
  }

  /** Null when it has been deleted, which callers must expect. */
  async actor(id: number): Promise<Actor | null> {
    const raw = await this.files.read(path(ACTORS, id));
    return raw === null ? null : actorSchema.parse(JSON.parse(raw));
  }

  saveActor(actor: Actor): Promise<Actor> {
    return this.queued(async () => {
      const saved = actor.id === UNSAVED ? { ...actor, id: await this.nextId(ACTORS) } : actor;
      await this.files.write(
        path(ACTORS, saved.id),
        `${JSON.stringify(saved, null, 2)}\n`,
        `Save actor ${saved.id}: ${saved.name || '(unnamed)'}`,
      );
      return saved;
    });
  }

  deleteActor(id: number): Promise<void> {
    return this.queued(() => this.files.remove(path(ACTORS, id), `Delete actor ${id}`));
  }

  private async parse(file: string): Promise<Actor> {
    const raw = await this.files.read(file);
    const result = actorSchema.safeParse(JSON.parse(raw ?? 'null'));
    if (!result.success) {
      throw new Error(`${file} is not a valid actor: ${result.error.issues[0].message}`);
    }
    return result.data;
  }

  /**
   * Ids only ever climb, so a deleted one is never handed out again.
   *
   * The stored counter is the memory of what has been issued; the highest id
   * actually present guards against a file that arrived some other way — by
   * hand, or through an import — and sits above it.
   */
  private async nextId(kind: string): Promise<number> {
    const counters = await this.counters();
    const present = (await this.files.list(kind)).map(idFromPath);
    const allocated = Math.max(counters[kind] ?? 0, ...present, 0) + 1;
    await this.files.write(
      COUNTERS,
      `${JSON.stringify({ ...counters, [kind]: allocated }, null, 2)}\n`,
      `Allocate ${kind} id ${allocated}`,
    );
    return allocated;
  }

  private async counters(): Promise<Counters> {
    const raw = await this.files.read(COUNTERS);
    return raw === null ? {} : (JSON.parse(raw) as Counters);
  }
}

function path(kind: string, id: number): string {
  return `${kind}/${id}.json`;
}

function idFromPath(file: string): number {
  return Number(file.split('/').pop()?.replace('.json', ''));
}
