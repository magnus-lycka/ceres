/**
 * A file store in a Map.
 *
 * Used by the library tests, which have plenty to say about ids, staleness and
 * round-tripping and nothing to say about HTTP. Keeping those tests off the
 * network is what lets there be a lot of them.
 */
import type { FileStore } from './files';

export class MemoryFileStore implements FileStore {
  private files = new Map<string, string>();

  /** Commit messages the writes carried, oldest first. */
  readonly messages: string[] = [];

  async list(prefix: string): Promise<string[]> {
    return [...this.files.keys()].filter((path) => path.startsWith(`${prefix}/`));
  }

  async read(path: string): Promise<string | null> {
    return this.files.get(path) ?? null;
  }

  async write(path: string, content: string, message: string): Promise<void> {
    this.files.set(path, content);
    this.messages.push(message);
  }

  async remove(path: string, message: string): Promise<void> {
    this.files.delete(path);
    this.messages.push(message);
  }
}
