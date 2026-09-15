import { render } from 'vitest-browser-svelte';
import { afterEach, expect, it, vi } from 'vitest';
import { actorSchema } from '$lib/schema/actor';
import ActorSource from './ActorSource.svelte';
const actor = actorSchema.parse({
  name: 'Guard',
  kind: 'sophont',
  strength: 8,
  dexterity: 8,
  endurance: 8,
  character: { url: 'http://ceres.test/api/characters/1' },
});
afterEach(() => vi.unstubAllGlobals());
it('distinguishes confirmed deletion from an unavailable source', async () => {
  const fetcher = vi.fn().mockRejectedValue(new TypeError('offline'));
  vi.stubGlobal('fetch', fetcher);
  const screen = await render(ActorSource, { actor, onchange: vi.fn() });
  await expect.element(screen.getByText('Source unavailable', { exact: true })).toBeVisible();
  fetcher.mockResolvedValue(Response.json({ detail: 'Source character deleted' }, { status: 404 }));
  await screen.getByRole('button', { name: 'Check source' }).click();
  await expect.element(screen.getByText('Source character deleted', { exact: true })).toBeVisible();
  await expect.element(screen.getByRole('button', { name: 'Update from character' })).toBeDisabled();
});
