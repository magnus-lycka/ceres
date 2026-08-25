/**
 * A place files live.
 *
 * Four operations over paths and strings. This is a genuine abstraction rather
 * than a hopeful one — unlike a grid library, a file store really does have a
 * small stable surface, and its backends differ only in where the bytes go.
 * The library layer above depends on this interface and never learns whether
 * it is talking to GitHub, to memory, or to a disk.
 */
export interface FileStore {
  /** Every path under a directory, in no particular order. */
  list(prefix: string): Promise<string[]>;
  /** The file's contents, or null when it is not there. */
  read(path: string): Promise<string | null>;
  write(path: string, content: string, message: string): Promise<void>;
  remove(path: string, message: string): Promise<void>;
}
