import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['dist/', 'public/'] },
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
    },
  },
  {
    files: ['*.config.js', 'test/**/*.js'],
    languageOptions: { globals: { ...globals.node } },
  },
];
