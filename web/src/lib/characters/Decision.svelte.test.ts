import { render } from 'vitest-browser-svelte';
import { expect, it, vi } from 'vitest';
import Decision from './Decision.svelte';

it.each(['Reenlist', 'Muster out'])('submits %s directly without an empty Confirm step', async (action) => {
  const submit = vi.fn();
  const screen = await render(Decision, {
    pending: {
      id: '12.0',
      instruction: 'Reenlist or muster out?',
      inputs: [
        {
          kind: 'ActionChoice',
          name: 'reenlist',
          options: [
            ['Reenlist', 'true'],
            ['Muster out', 'false'],
          ],
        },
      ],
    },
    busy: false,
    onsubmit: submit,
  });
  await expect.element(screen.getByRole('button', { name: 'Confirm', exact: true })).not.toBeInTheDocument();
  await screen.getByRole('button', { name: action, exact: true }).click();
  expect(submit).toHaveBeenCalledWith({ reenlist: action === 'Reenlist' ? 'true' : 'false' });
});

it('shows a choice instruction once and keeps it as the accessible group label', async () => {
  const instruction = 'Backstab the fellow rogue or refuse?';
  const submit = vi.fn();
  const screen = await render(Decision, {
    pending: {
      id: '2.0',
      instruction,
      inputs: [
        {
          kind: 'Select',
          name: 'choice',
          label: instruction,
          options: [
            ['Backstab', 'backstab'],
            ['Refuse', 'refuse'],
          ],
          min_select: 1,
          max_select: 1,
          default: null,
        },
      ],
    },
    busy: false,
    onsubmit: submit,
  });
  await expect.element(screen.getByText(instruction, { exact: true })).toBeVisible();
  await expect.element(screen.getByRole('group', { name: instruction, exact: true })).toBeVisible();
  await screen.getByRole('radio', { name: 'Refuse', exact: true }).click();
  await screen.getByRole('button', { name: 'Confirm', exact: true }).click();
  expect(submit).toHaveBeenCalledWith({ choice: 'refuse' });
});

it('offers Change Homeworld or Skip for an optional relocation without submitting an empty choice', async () => {
  const submit = vi.fn();
  const screen = await render(Decision, {
    pending: {
      id: '4.0',
      instruction: 'You may relocate.',
      inputs: [
        {
          kind: 'SelectWorld',
          name: 'homeworld',
          label: 'New homeworld',
          sector_abbreviation: null,
          reference_world: null,
          filters: {},
          open_label: 'Change Homeworld',
          skip_values: { keep: '1' },
        },
      ],
    },
    busy: false,
    onsubmit: submit,
  });
  await expect.element(screen.getByRole('button', { name: 'Confirm', exact: true })).not.toBeInTheDocument();
  await screen.getByRole('button', { name: 'Change Homeworld', exact: true }).click();
  await expect.element(screen.getByRole('textbox', { name: 'Reference sector', exact: true })).toBeVisible();
  expect(submit).not.toHaveBeenCalled();
  await screen.getByRole('button', { name: 'Skip', exact: true }).click();
  expect(submit).toHaveBeenCalledWith({ keep: '1' });
});

it('renders backend-defined choices and submits all selected values', async () => {
  const submit = vi.fn();
  const screen = await render(Decision, {
    pending: {
      id: '2.0',
      instruction: 'Choose your background skills',
      inputs: [
        {
          kind: 'Select',
          name: 'skills',
          label: 'Skills',
          options: [
            ['Pilot', 'pilot'],
            ['Medic', 'medic'],
          ],
          min_select: 2,
          max_select: 2,
          default: null,
        },
        { kind: 'Reference', name: 'kind', value: 'background' },
      ],
    },
    onsubmit: submit,
    busy: false,
  });
  await screen.getByLabelText('Pilot').click();
  await screen.getByLabelText('Medic').click();
  await screen.getByRole('button', { name: 'Confirm', exact: true }).click();
  expect(submit).toHaveBeenCalledWith({ skills: ['pilot', 'medic'], kind: 'background' });
});

it('accepts new backend career and assignment names without a frontend catalogue', async () => {
  const submit = vi.fn();
  const screen = await render(Decision, {
    pending: {
      id: '4.0',
      instruction: 'Choose a career',
      inputs: [
        {
          kind: 'CareerChoice',
          can_finish: true,
          precareer_options: [],
          career_options: [
            {
              name: 'Xeno Cartographer',
              description: 'Map new worlds',
              qualification: { characteristic: 'INT', target: 6 },
              assignments: [{ name: 'Surveyor', description: 'Explore' }],
            },
          ],
        },
      ],
    },
    busy: false,
    onsubmit: submit,
  });
  await screen.getByLabelText('Qualification roll (2D, before DMs)').fill('8');
  await screen.getByRole('button', { name: 'Attempt qualification' }).click();
  expect(submit).toHaveBeenCalledWith({ career: 'Xeno Cartographer', assignment: 'Surveyor', roll: '8' });
});
