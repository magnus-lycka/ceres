/** Character-to-actor translation; a source's URL identifies its server too. */
import { z } from 'zod';
import { apiRoot, characterSchema, type Character } from './api';
import type { CharacterSource } from '$lib/store/library';

export function sourceFromCharacter(
  character: Character,
  url = new URL(`${apiRoot}/characters/${character.id}`, location.origin).href,
): CharacterSource {
  if (!character.finished) throw new Error('Finish character creation before adding or refreshing an actor.');
  return {
    url,
    name: character.name,
    strength: z.number().int().parse(character.characteristics.STR),
    dexterity: z.number().int().parse(character.characteristics.DEX),
    endurance: z.number().int().parse(character.characteristics.END),
  };
}
export type SourceStatus =
  { state: 'available'; character: Character } | { state: 'deleted' | 'unavailable' };
export async function characterSource(url: string): Promise<SourceStatus> {
  try {
    const response = await fetch(url);
    const raw: unknown = await response.json();
    if (
      response.status === 404 &&
      z.object({ detail: z.literal('Source character deleted') }).safeParse(raw).success
    )
      return { state: 'deleted' };
    if (!response.ok) return { state: 'unavailable' };
    const parsed = characterSchema.safeParse(raw);
    return parsed.success ? { state: 'available', character: parsed.data } : { state: 'unavailable' };
  } catch {
    return { state: 'unavailable' };
  }
}
export function characterSheetUrl(source: string): string {
  const url = new URL(source);
  const match = /\/api\/characters\/(\d+)$/.exec(url.pathname);
  if (!match) throw new Error('Unrecognized character source');
  url.pathname = url.pathname.replace(/\/api\/characters\/\d+$/, '/characters');
  url.search = `?id=${match[1]}`;
  return url.href;
}
