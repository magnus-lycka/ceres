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
import {
  actorId,
  actorSchema,
  partyId,
  UNSAVED,
  type Actor,
  type ActorId,
  type PartyId,
} from '$lib/schema/actor';
import { partySchema, type Party } from '$lib/schema/party';
import type { z } from 'zod';
import type { FileStore } from './files';

const ACTORS = 'actors';
const PARTIES = 'parties';
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

  /**
   * Files that could not be read, from the most recent listing.
   *
   * A single unreadable file used to reject the whole listing, so one party
   * with a malformed tag list hid every party there was. Reporting the file
   * and returning the rest is the useful answer: the good entries are still
   * good, and the bad one is named rather than silently dropped.
   */
  readonly problems: string[] = [];

  async actors(): Promise<Actor[]> {
    return this.readAll(ACTORS, actorSchema.safeParse.bind(actorSchema), 'actor');
  }

  /**
   * Null when it has been deleted — or when what is stored cannot be read.
   *
   * Both are the same answer to a caller: there is nothing usable here. A
   * throw would be worse than useless, because a single damaged file would
   * take out every list that resolves references through this.
   */
  async actor(id: ActorId): Promise<Actor | null> {
    return this.readOne(path(ACTORS, id), actorSchema.safeParse.bind(actorSchema), 'actor');
  }

  saveActor(actor: Actor): Promise<Actor> {
    return this.queued(async () => {
      const saved = actor.id === UNSAVED ? { ...actor, id: actorId(await this.nextId(ACTORS)) } : actor;
      await this.files.write(
        path(ACTORS, saved.id),
        `${JSON.stringify(saved, null, 2)}\n`,
        `Save actor ${saved.id}: ${saved.name || '(unnamed)'}`,
      );
      return saved;
    });
  }

  deleteActor(id: ActorId): Promise<void> {
    return this.queued(() => this.files.remove(path(ACTORS, id), `Delete actor ${id}`));
  }

  async parties(): Promise<Party[]> {
    return this.readAll(PARTIES, partySchema.safeParse.bind(partySchema), 'party');
  }

  private async readAll<T extends { id: number }>(
    kind: string,
    check: (value: unknown) => { success: true; data: T } | { success: false; error: z.ZodError },
    what: string,
  ): Promise<T[]> {
    this.problems.length = 0;
    const paths = await this.files.list(kind);
    const read = await Promise.all(
      paths.map(async (file) => {
        const raw = await this.files.read(file);
        const result = check(JSON.parse(raw ?? 'null'));
        if (result.success) return result.data;
        this.problems.push(`${file} is not a valid ${what}: ${result.error.issues[0].message}`);
        return null;
      }),
    );
    return read.filter((entry) => entry !== null).sort((left, right) => left.id - right.id);
  }

  /** Null when it has been deleted, or cannot be read. */
  async party(id: PartyId): Promise<Party | null> {
    return this.readOne(path(PARTIES, id), partySchema.safeParse.bind(partySchema), 'party');
  }

  private async readOne<T>(
    file: string,
    check: (value: unknown) => { success: true; data: T } | { success: false; error: z.ZodError },
    what: string,
  ): Promise<T | null> {
    const raw = await this.files.read(file);
    if (raw === null) return null;
    const result = check(JSON.parse(raw));
    if (result.success) return result.data;
    this.problems.push(`${file} is not a valid ${what}: ${result.error.issues[0].message}`);
    return null;
  }

  saveParty(party: Party): Promise<Party> {
    return this.queued(async () => {
      const saved = party.id === UNSAVED ? { ...party, id: partyId(await this.nextId(PARTIES)) } : party;
      await this.files.write(
        path(PARTIES, saved.id),
        `${JSON.stringify(saved, null, 2)}\n`,
        `Save party ${saved.id}: ${saved.name || '(unnamed)'}`,
      );
      return saved;
    });
  }

  deleteParty(id: PartyId): Promise<void> {
    return this.queued(() => this.files.remove(path(PARTIES, id), `Delete party ${id}`));
  }

  /**
   * The members in stored order, with a hole where one has been deleted.
   *
   * Deleting an actor is unguarded and nothing goes back to tidy the parties
   * that referenced it, so a party may point at an actor that no longer
   * exists. The hole is the honest answer: the party did have a member there,
   * and something has to say so rather than quietly closing the gap.
   */
  async partyMembers(id: PartyId): Promise<(Actor | null)[]> {
    const party = await this.party(id);
    if (party === null) return [];
    return Promise.all(party.actors.map((member) => this.actor(member)));
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
