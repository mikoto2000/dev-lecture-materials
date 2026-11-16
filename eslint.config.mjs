import js from '@eslint/js';
import globals from 'globals';
import ts from 'typescript-eslint';

export default [
  { languageOptions: { globals: globals.browser } },
  js.configs.recommended,
  ...ts.configs.recommended,
  { files: ['scripts/**/*.mjs'], languageOptions: { globals: globals.node } },
  { ignores: ['dist/', 'doc_build/', '.rspress/'] },
];
