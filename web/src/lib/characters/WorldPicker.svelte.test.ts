import { render } from 'vitest-browser-svelte';
import { afterEach, expect, it, vi } from 'vitest';
import WorldPicker from './WorldPicker.svelte';
afterEach(() => vi.unstubAllGlobals());
it('loads worlds with the supplied filters and submits the chosen location', async () => {
  const fetcher = vi.fn<typeof fetch>(async () =>
    Response.json({
      name: 'Spinward Marches',
      options: { remarks: ['Ga', 'Va'] },
      worlds: [
        {
          sector: 'Core',
          sector_abbreviation: 'Core',
          hex: '3202',
          name: 'Other world',
          uwp: 'A788899-C',
          remarks: 'Ga',
          distance: 10,
        },
        {
          sector: 'Dagudashaag',
          sector_abbreviation: 'Dagu',
          hex: '3202',
          name: 'Lir',
          uwp: 'C576442-9',
          remarks: 'Ga',
          distance: 2,
        },
      ],
    }),
  );
  vi.stubGlobal('fetch', fetcher);
  const submit = vi.fn();
  const screen = await render(WorldPicker, {
    spec: {
      kind: 'SelectWorld',
      name: 'homeworld',
      label: 'Choose homeworld',
      sector_abbreviation: 'Spin',
      reference_world: null,
      filters: { remarks: ['Ga'] },
    },
    busy: false,
    onsubmit: submit,
  });
  await expect.element(screen.getByRole('columnheader', { name: 'Sector', exact: true })).toBeVisible();
  await expect.element(screen.getByRole('cell', { name: 'Dagudashaag', exact: true })).toBeVisible();
  expect(String(fetcher.mock.calls[0]?.[0])).toContain('remarks=Ga');
  await screen.getByRole('button', { name: 'Lir', exact: true }).click();
  expect(submit).toHaveBeenCalledWith({ sector: 'Dagu', hex_code: '3202' });
});
