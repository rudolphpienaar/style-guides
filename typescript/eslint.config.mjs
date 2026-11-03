// @ts-check
/**
 * @file ESLint flat config for the TypeScript style guide in this directory.
 *
 * Copy into a project as eslint.config.mjs and adjust `files`. Every rule is an
 * error: the guide asks for a clean lint, so there is no warning tier to burn
 * down. The section names in the comments match STYLE-GUIDE.md.
 *
 * Requires (devDependencies): eslint, typescript, typescript-eslint,
 * eslint-plugin-jsdoc, eslint-plugin-import.
 *
 * @module
 */

import importPlugin from 'eslint-plugin-import';
import jsdoc from 'eslint-plugin-jsdoc';
import tseslint from 'typescript-eslint';

/**
 * Prepositions that may not stand where the verb of a method goes
 * (`answerRows_of`, `seriesUID_forPath`). Shared with python/rpn_check.py.
 */
const PREPOSITIONS = 'of|to|with|from|for|by|as|in|on|at';

/**
 * RPN function name: `<subject>[Qualifier]_<verb>[Adverb]`, both halves
 * lowerCamelCase, exactly one underscore, and a verb (not a preposition) after
 * it. `main` is the one name without a subject. Shared with python/rpn_check.py.
 */
const RPN_REGEX = `^(?:main|[a-z][a-zA-Z0-9]*_(?!(?:${PREPOSITIONS})(?:[A-Z0-9]|$))[a-z][a-zA-Z0-9]*)$`;

/** Naming: functions RPN, values lowerCamelCase, types PascalCase, constants UPPER_CASE. */
const namingRules = [
  { selector: 'default', format: ['camelCase'], leadingUnderscore: 'allow' },
  {
    selector: ['function', 'classMethod', 'objectLiteralMethod', 'typeMethod'],
    format: null,
    leadingUnderscore: 'allow',
    custom: { regex: RPN_REGEX, match: true },
  },
  // A method that overrides a base class keeps the base class's name.
  { selector: 'classMethod', modifiers: ['override'], format: null },
  {
    selector: 'variable',
    types: ['function'],
    format: null,
    custom: { regex: RPN_REGEX, match: true },
  },
  { selector: 'variable', modifiers: ['const'], format: ['camelCase', 'UPPER_CASE'] },
  { selector: 'typeLike', format: ['PascalCase'] },
  { selector: 'import', format: null },
  // Keys that mirror an external schema keep its spelling: quoted keys
  // ('study_instance_uid') as written, environment variables in UPPER_CASE.
  { selector: 'objectLiteralProperty', format: ['camelCase', 'UPPER_CASE'] },
  { selector: 'objectLiteralProperty', modifiers: ['requiresQuotes'], format: null },
];

export default tseslint.config(
  { ignores: ['node_modules/**', 'dist/**', 'eslint.config.mjs'] },
  ...tseslint.configs.strictTypeChecked,
  jsdoc.configs['flat/recommended-typescript-error'],
  {
    files: ['**/*.ts'],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { import: importPlugin },
    rules: {
      // Naming
      '@typescript-eslint/naming-convention': ['error', ...namingRules],

      // Typing: pervasive and explicit
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/explicit-function-return-type': 'error',
      '@typescript-eslint/explicit-module-boundary-types': 'error',
      // Locals are annotated when the right-hand side does not make the type
      // obvious; that is a judgement, so it is left to review, as in Python.
      '@typescript-eslint/typedef': [
        'error',
        { parameter: true, memberVariableDeclaration: true, propertyDeclaration: true },
      ],

      // Function length: refactor on nesting and complexity, not line count
      'max-depth': ['error', 3],
      complexity: ['error', 15],

      // Imports: node built-ins, third-party, local; ES modules only
      'import/order': [
        'error',
        {
          groups: ['builtin', 'external', ['internal', 'parent', 'sibling', 'index']],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],
      'import/first': 'error',
      'import/no-cycle': 'error',
      '@typescript-eslint/no-require-imports': 'error',

      // Documentation
      'jsdoc/require-file-overview': ['error', { tags: { file: { mustExist: true } } }],
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: true,
          require: {
            ClassDeclaration: true,
            FunctionDeclaration: true,
            MethodDefinition: true,
          },
          contexts: ['TSInterfaceDeclaration', 'TSTypeAliasDeclaration', 'TSEnumDeclaration'],
        },
      ],

      // Blank lines between description, tags and examples, as in the guide's examples.
      'jsdoc/tag-lines': ['error', 'any', { startLines: 1 }],
      // A getter is documented like a field: one line, no @returns.
      'jsdoc/require-returns': ['error', { checkGetters: false }],

      // Reliability: no silent failures
      'no-empty': ['error', { allowEmptyCatch: false }],
    },
  },
);
