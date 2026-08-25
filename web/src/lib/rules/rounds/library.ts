/**
 * Library operations, as plain functions over plain data.
 *
 * Nothing here imports from Svelte, and nothing here touches the DOM. That is
 * the boundary that replaces the one Python used to enforce for free: when the
 * rules live beside the UI, the only thing keeping them separable is that this
 * directory refuses to know the UI exists.
 */
import type { Actor, ActorKind } from '../../schema/actor';

/** The highest id ever used in a set of actors, for seeding a sequence. */
export function highestId(actors: readonly Actor[]): number {
  return actors.reduce((highest, actor) => Math.max(highest, actor.id), 0);
}

/**
 * A monotonic id allocator.
 *
 * Ids only ever climb, and deliberately do not come from the actors currently
 * loaded: `max(id) + 1` hands a deleted actor's id to the next new one, so a
 * stale reference that should resolve to nothing resolves to somebody else
 * instead — an old situation quietly gains a stranger.
 *
 * Seed it from `highestId` when loading and let it run ahead of deletions.
 * This is the browser-side stand-in for the service's persisted counter; when
 * persistence lands, the service allocates and this goes away.
 */
export function createIdSequence(seed = 0): { next: () => number } {
  let last = seed;
  return {
    next() {
      last += 1;
      return last;
    },
  };
}

/**
 * One independent copy of an actor, named so repeated duplication stays
 * distinct: Wolf becomes Wolf 1, then Wolf 2, and duplicating Wolf 1 continues
 * the same series rather than starting a second one.
 *
 * The copy arrives unhurt — no injuries and no criticals — because that is the
 * whole point of copying: ten chickens in a fight are ten actors, and each is
 * hurt separately. Duplicating the one that has already been shot should not
 * hand you a second casualty.
 */
export function duplicate(source: Actor, id: number, actors: readonly Actor[]): Actor {
  const base = source.name.replace(/\s+\d+$/, '').trim();
  const taken = new Set(actors.map((actor) => actor.name));
  let suffix = 1;
  while (taken.has(`${base} ${suffix}`)) suffix += 1;
  return {
    ...source,
    id,
    name: `${base} ${suffix}`,
    tags: [...source.tags],
    injuries: [],
    criticals: {},
  };
}

/**
 * A new actor of a given kind, carrying only the fields that kind uses.
 *
 * Kind is settled here and never changes afterwards: it decides how the actor
 * absorbs damage, so an actor that changed kind would have an injury history
 * recorded against a damage model it no longer has. A sophont that should have
 * been an animal is a new actor and a deleted one.
 */
export function newActor(kind: ActorKind, id: number): Actor {
  const physical = kind === 'sophont';
  return {
    id,
    name: '',
    kind,
    note: '',
    tags: [],
    strength: physical ? 7 : null,
    dexterity: physical ? 7 : null,
    endurance: physical ? 7 : null,
    hits: physical ? null : 10,
    injuries: [],
    criticals: {},
  };
}

/**
 * A tag list from whatever a cell edit or a clipboard paste produced.
 *
 * Pasting writes the raw clipboard text into the cell, so a tags cell can
 * arrive as `"pc marduk"` where the model says `string[]`. Without this the
 * value is a string that merely looks right and renders one pill per letter.
 * Separators are spaces or commas, so a block pasted from a spreadsheet works
 * whichever the other tool used.
 */
export function parseTags(input: unknown): string[] {
  if (Array.isArray(input))
    return input
      .map(String)
      .map((tag) => tag.trim())
      .filter(Boolean);
  if (input === null || input === undefined) return [];
  return String(input)
    .split(/[\s,]+/)
    .filter(Boolean);
}

/** Tags as one cell of text, for the clipboard and for spreadsheets. */
export function formatTags(tags: unknown): string {
  return parseTags(tags).join(' ');
}
