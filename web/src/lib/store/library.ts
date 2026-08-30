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
import { importReceiptSchema, libraryBundleSchema, type ImportReceipt } from '$lib/schema/import';
import { situationId, situationSchema, type Situation, type SituationId } from '$lib/schema/situation';
import type { z } from 'zod';
import type { FileStore } from './files';

const ACTORS = 'actors';
const PARTIES = 'parties';
const SITUATIONS = 'situations';
const COUNTERS = 'counters.json';
/** Proposals waiting to be installed, written by the data repository. */
const INBOX = 'inbox';
/** What installing one produced. Kept, so a bundle installs exactly once. */
const IMPORTS = 'imports';

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
      await this.putActor(saved);
      return saved;
    });
  }

  /**
   * Write without queueing.
   *
   * An import installs several entities as one task, and must keep the queue
   * from reservation through to deleting the inbox entry — an ordinary save
   * interleaving halfway would allocate against a counter the import has
   * already moved. So the queued methods above wrap these, and the importer
   * calls them directly.
   */
  private async putActor(actor: Actor): Promise<void> {
    await this.files.write(
      path(ACTORS, actor.id),
      `${JSON.stringify(actor, null, 2)}\n`,
      `Save actor ${actor.id}: ${actor.name || '(unnamed)'}`,
    );
  }

  private async putParty(party: Party): Promise<void> {
    await this.files.write(
      path(PARTIES, party.id),
      `${JSON.stringify(party, null, 2)}\n`,
      `Save party ${party.id}: ${party.name || '(unnamed)'}`,
    );
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
      await this.putParty(saved);
      return saved;
    });
  }

  deleteParty(id: PartyId): Promise<void> {
    return this.queued(() => this.files.remove(path(PARTIES, id), `Delete party ${id}`));
  }

  /**
   * Every situation, planned, current and past alike.
   *
   * A finished fight is kept rather than discarded — it may be of interest,
   * and storing it costs almost nothing — so this list grows with play. What
   * separates them is `state`, not which list they are in.
   */
  async situations(): Promise<Situation[]> {
    return this.readAll(SITUATIONS, situationSchema.safeParse.bind(situationSchema), 'situation');
  }

  /** Null when it has been deleted, or cannot be read. */
  async situation(id: SituationId): Promise<Situation | null> {
    return this.readOne(path(SITUATIONS, id), situationSchema.safeParse.bind(situationSchema), 'situation');
  }

  saveSituation(situation: Situation): Promise<Situation> {
    return this.queued(async () => {
      const saved =
        situation.id === UNSAVED
          ? { ...situation, id: situationId(await this.nextId(SITUATIONS)) }
          : situation;
      await this.files.write(
        path(SITUATIONS, saved.id),
        `${JSON.stringify(saved, null, 2)}\n`,
        `Save situation ${saved.id}: ${saved.name || '(unnamed)'}`,
      );
      return saved;
    });
  }

  deleteSituation(id: SituationId): Promise<void> {
    return this.queued(() => this.files.remove(path(SITUATIONS, id), `Delete situation ${id}`));
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
    return (await this.reserveIds(kind, 1))[0];
  }

  /**
   * A block of consecutive ids, the counter advanced once for all of them.
   *
   * Importing a party of eight needs eight actor ids at once, and taking them
   * one at a time would write the counter eight times and leave eight chances
   * to stop halfway. One reservation is also what lets a receipt record the
   * ids *before* any entity exists, which is what makes the install resumable.
   *
   * Keeps `nextId`'s guard: it starts above both the stored counter and every
   * id actually present, so a file that arrived by hand or through an import
   * cannot have its id handed out a second time.
   */
  private async reserveIds(kind: string, count: number): Promise<number[]> {
    const counters = await this.counters();
    const present = (await this.files.list(kind)).map(idFromPath);
    const first = Math.max(counters[kind] ?? 0, ...present, 0) + 1;
    const last = first + count - 1;
    await this.files.write(
      COUNTERS,
      `${JSON.stringify({ ...counters, [kind]: last }, null, 2)}\n`,
      count === 1 ? `Allocate ${kind} id ${first}` : `Allocate ${kind} ids ${first}-${last}`,
    );
    return Array.from({ length: count }, (_, step) => first + step);
  }

  /** Proposals waiting in the inbox, by name — `issue-123`, oldest id first. */
  async inbox(): Promise<string[]> {
    return (await this.files.list(INBOX)).map(nameFromPath).sort();
  }

  /**
   * Install every proposal waiting in the inbox.
   *
   * One bad bundle must not hold up the good ones, so each is installed on its
   * own and a failure is collected rather than thrown: an author who wrote one
   * bad actor should not stop somebody else's party from arriving. What fails
   * keeps its inbox file, so it stays visible and can be retried or discarded.
   */
  async importInbox(): Promise<{ installed: ImportReceipt[]; problems: string[] }> {
    const installed: ImportReceipt[] = [];
    const problems: string[] = [];
    for (const name of await this.inbox()) {
      try {
        installed.push(await this.importBundle(name));
      } catch (failure) {
        problems.push(failure instanceof Error ? failure.message : String(failure));
      }
    }
    return { installed, problems };
  }

  /**
   * Install one proposal, and say what it produced.
   *
   * The whole installation is a single queued task. Nothing inside it queues
   * again — that would deadlock on the task already holding the queue — and
   * nothing inside it calls the public saves, so from reserving ids to
   * deleting the inbox entry no ordinary edit can interleave and allocate
   * against a counter this has already moved.
   *
   * Safe to run twice, which matters because sync may bring the same file back
   * after it was consumed. The receipt is the memory: complete means the work
   * is done and the file is simply stale, and `installing` means a previous
   * attempt stopped partway and its ids are to be reused rather than a second
   * set allocated.
   */
  async importBundle(name: string): Promise<ImportReceipt> {
    return this.queued(async () => {
      const done = await this.readOne(
        entry(IMPORTS, name),
        importReceiptSchema.safeParse.bind(importReceiptSchema),
        'import receipt',
      );
      if (done?.status === 'complete') {
        // Already installed. The file re-appearing is a stale copy, not a
        // second proposal, so it goes without creating anything.
        await this.files.remove(entry(INBOX, name), `Discard already-imported ${name}`);
        return done;
      }

      // CI validated this, but CI is feedback rather than a trust boundary and
      // the running application may have a newer schema than the one that
      // passed it.
      const raw = await this.files.read(entry(INBOX, name));
      if (raw === null) throw new Error(`${name} is no longer in the inbox.`);
      const proposed = libraryBundleSchema.safeParse(JSON.parse(raw));
      if (!proposed.success) {
        throw new Error(`${name} is not a valid library bundle: ${reasons(proposed.error)}`);
      }
      const bundle = proposed.data;

      // Reserve before recording. Stopping here wastes ids, which is harmless;
      // stopping after the receipt reuses them, which is what stops a retry
      // from creating everybody twice.
      const receipt: ImportReceipt =
        done ??
        importReceiptSchema.parse({
          schemaVersion: 1,
          bundle: name,
          issue: issueNumber(name),
          status: 'installing',
          actors: await this.reserveIds(ACTORS, bundle.actors.length),
          party: await this.nextId(PARTIES),
        });
      if (!done) await this.writeReceipt(receipt);

      // Healthy, whatever the fight they are about to walk into: a proposal
      // carries no injuries, so the schema's own defaults supply the rest.
      for (const [index, proposedActor] of bundle.actors.entries()) {
        await this.putActor(actorSchema.parse({ ...proposedActor, id: receipt.actors[index] }));
      }
      await this.putParty(
        partySchema.parse({
          id: receipt.party,
          name: bundle.name,
          note: bundle.note,
          tags: bundle.tags,
          actors: receipt.actors,
        }),
      );

      const complete: ImportReceipt = { ...receipt, status: 'complete' };
      await this.writeReceipt(complete);
      await this.files.remove(entry(INBOX, name), `Consume ${name}`);
      return complete;
    });
  }

  private async writeReceipt(receipt: ImportReceipt): Promise<void> {
    await this.files.write(
      entry(IMPORTS, receipt.bundle),
      `${JSON.stringify(receipt, null, 2)}\n`,
      `${receipt.status === 'complete' ? 'Imported' : 'Importing'} ${receipt.bundle}`,
    );
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

/** Inbox entries and receipts are named, not numbered: `inbox/issue-123.json`. */
function entry(kind: string, name: string): string {
  return `${kind}/${name}.json`;
}

function nameFromPath(file: string): string {
  return (
    file
      .split('/')
      .pop()
      ?.replace(/\.json$/, '') ?? ''
  );
}

/**
 * The issue an entry came from.
 *
 * Within the one configured data repository the issue number is the whole
 * identity, which is what makes an edited issue an update rather than a second
 * proposal.
 */
function issueNumber(name: string): number {
  const found = /^issue-(\d+)$/.exec(name);
  if (!found) throw new Error(`${name} is not an issue bundle name.`);
  return Number(found[1]);
}

/** Zod paths and messages, for someone who cannot run the validator. */
function reasons(error: z.ZodError): string {
  return error.issues.map((issue) => `${issue.path.join('.') || '(root)'}: ${issue.message}`).join('; ');
}
