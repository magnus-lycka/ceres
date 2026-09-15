import { render } from 'vitest-browser-svelte';
import { afterEach, expect, it } from 'vitest';
import ThemeSwitch from './ThemeSwitch.svelte';

afterEach(() => {
  localStorage.removeItem('ceres-theme');
  delete document.documentElement.dataset.theme;
});

it('switches the page to dark mode, remembers it, and can switch back', async () => {
  localStorage.setItem('ceres-theme', 'light');
  const screen = await render(ThemeSwitch);
  await screen.getByRole('button', { name: 'Dark mode', exact: true }).click();
  await expect.element(screen.getByRole('button', { name: 'Light mode', exact: true })).toBeVisible();
  expect(document.documentElement.dataset.theme).toBe('dark');
  expect(getComputedStyle(document.body).backgroundColor).toBe('rgb(20, 24, 31)');
  expect(localStorage.getItem('ceres-theme')).toBe('dark');
  await screen.unmount();
  const reopened = await render(ThemeSwitch);
  await expect.element(reopened.getByRole('button', { name: 'Light mode', exact: true })).toBeVisible();
  await reopened.getByRole('button', { name: 'Light mode', exact: true }).click();
  expect(document.documentElement.dataset.theme).toBe('light');
  expect(localStorage.getItem('ceres-theme')).toBe('light');
});
