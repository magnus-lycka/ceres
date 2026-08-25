/**
 * Lint rules for the Svelte front end — the counterpart to `ruff check` on the
 * Python side.
 *
 * The house style beyond this is Prettier's; `eslint-config-prettier` comes
 * last so the two never argue about formatting. What is left here is the part
 * a formatter cannot see: unused code, unsafe types, and the Svelte-specific
 * mistakes that produce a component which compiles and then misbehaves.
 */
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';
import prettier from 'eslint-config-prettier';
import svelteConfig from './svelte.config.js';

export default ts.config(
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs.recommended,
  prettier,
  ...svelte.configs.prettier,
  {
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts'],
    languageOptions: {
      parserOptions: {
        projectService: true,
        extraFileExtensions: ['.svelte'],
        parser: ts.parser,
        svelteConfig,
      },
    },
  },
  {
    rules: {
      // An unused name is nearly always a leftover from a change that was not
      // finished. The underscore prefix is the deliberate escape hatch, used
      // for the discarded half of a destructuring.
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      // `any` erases the type checking this project is relying on. The one
      // legitimate hole is the grid wrapper's `unknown` boundary, which is
      // cast explicitly and commented.
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
  { ignores: ['build/', '.svelte-kit/', 'node_modules/', 'static/'] },
);
