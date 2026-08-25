/**
 * Which repository holds the data, and the credential to reach it.
 *
 * Neither is a constant in the source. This code repo is public and the data
 * repo is private, so the code must not carry the data repo's name, and it
 * certainly must not carry a token. Both are supplied at runtime and kept in
 * the browser's local storage on whichever machine they were entered.
 *
 * That does mean a token sits in browser storage. It is a fine-grained one,
 * scoped to a single private repo with `Contents: Read and write` and nothing
 * else, and it can be revoked from GitHub in a moment — `clearConnection` is
 * how a borrowed machine is left tidy.
 */
import { z } from 'zod';
import type { Repository } from './github';

const KEY = 'ceres.connection';

const connectionSchema = z.object({
  owner: z.string().min(1),
  repo: z.string().min(1),
  branch: z.string().min(1).default('main'),
  token: z.string().min(1),
});

/**
 * The owner and repository named by whatever was pasted in, or null when it
 * names no repository at all.
 *
 * People paste what they have to hand: the address bar, the clone button, the
 * SSH remote, or just `owner/repo` said out loud. All of them mean the same
 * thing, so all of them are accepted.
 */
export function parseRepository(input: string): { owner: string; repo: string } | null {
  const trimmed = input
    .trim()
    .replace(/\.git$/, '')
    .replace(/\/$/, '');
  const match =
    /^https?:\/\/[^/]+\/([^/]+)\/([^/]+)$/.exec(trimmed) ??
    /^git@[^:]+:([^/]+)\/([^/]+)$/.exec(trimmed) ??
    /^([^/\s]+)\/([^/\s]+)$/.exec(trimmed);
  return match ? { owner: match[1], repo: match[2] } : null;
}

/** The stored connection, or null when there is none worth trusting. */
export function loadConnection(storage: Storage = localStorage): Repository | null {
  const raw = storage.getItem(KEY);
  if (raw === null) return null;
  try {
    const parsed = connectionSchema.safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data : null;
  } catch {
    // Damaged settings are the same as none. Refusing to start over a bad
    // string in local storage would leave no way back in.
    return null;
  }
}

export function saveConnection(connection: Repository, storage: Storage = localStorage): void {
  storage.setItem(KEY, JSON.stringify(connection));
}

export function clearConnection(storage: Storage = localStorage): void {
  storage.removeItem(KEY);
}
