# TypeScript Style Guide

Rudolph Pienaar's conventions for TypeScript. They apply to code in repositories I start or own. In an existing codebase, follow that codebase's conventions instead, so that a patch is indistinguishable from the code around it.

This guide and the [Python guide](../python/STYLE-GUIDE.md) are kept in step: same sections in the same order, same rules, same example domain. Where the languages force a difference, the guide says so. Most of it is widely shared practice: strict types, named models instead of loose objects, documentation on everything, a clean linter. The [naming](#naming) section is the idiosyncratic part. It departs from the community's verb-first camelCase for functions, and is the part most likely to differ from what a contributor expects.

Snippets below elide bodies and documentation (`...`) where the point being made is elsewhere. [`example/transcript.ts`](example/transcript.ts) is a complete module that applies every rule at full strength and passes `tsc` and ESLint with [`tsconfig.json`](tsconfig.json) and [`eslint.config.mjs`](eslint.config.mjs); [`example/transcript.test.ts`](example/transcript.test.ts) runs its documented examples. When in doubt, copy its shape.

---

## Language version and configuration

**TypeScript 5.8 or later, ES2023, ES modules.**

- `strict: true`, plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride` and `noImplicitReturns`. [`tsconfig.json`](tsconfig.json) is the baseline.
- `erasableSyntaxOnly` and `verbatimModuleSyntax`, so the code runs under Node's type stripping as well as through `tsc`: no `enum`, no `namespace`, no constructor parameter properties; `import type` for types.
- ES modules only (`"type": "module"`). Never `require()`.
- Optional chaining (`?.`), nullish coalescing (`??`), `Array.prototype.at`, and other modern syntax.

---

## Naming

### Functions and methods: RPN, `subject_verb`

Functions and methods name the subject first and the action second, in the order of Reverse Polish Notation (RPN): operand, then operator.

```
<subject>[Qualifier]_<verb>[Adverb]
```

- **subject**: the noun acted on, lowerCamelCase (`user`, `segment`).
- **Qualifier**: optional, narrows the subject, continues the camelCase (`userNames`, `segmentFirst`).
- **verb**: the action, lowercase (`get`, `build`, `parse`, `render`).
- **Adverb**: optional, refines the verb, continues the camelCase (`checkIsValid`, `readFromCache`).

```typescript
// Conventional TypeScript (verb first)
function getUserNames(): string[] { ... }
function isLoginValid(): boolean { ... }
function parseUserData(raw: string): UserRecord { ... }

// RPN (subject first)
function userNames_get(): string[] { ... }
function login_checkIsValid(): boolean { ... }
function userData_parse(raw: string): UserRecord { ... }
```

From the reference module:

```typescript
function segments_load(path: string): Segment[] { ... }
function paragraphs_build(segments: readonly Segment[], gapLimit: number): Paragraph[] { ... }
function timestamp_format(seconds: number): string { ... }
function transcript_render(paragraphs: readonly Paragraph[]): string { ... }
```

Every function and method name has exactly one underscore. `main` is the one name without a subject.

Why:

- **Subject first.** The name says what is being operated on before it says what happens to it.
- **Grouping.** Operations on the same subject sort together in an editor outline, an API listing or a module index: `user_create`, `user_delete`, `user_get`, `userPassword_reset`.
- **Searchability.** `grep -n 'paragraphs_'` finds everything that acts on paragraphs.
- **Machine parsability.** One underscore splits every name into subject and verb, so a regular expression can lint it, index it or build a call graph from it.

### The verb is a verb

The part after the underscore is always a verb. A preposition in its place (`answerRows_of`, `seriesUid_forPath`, `x_to`) names the result without saying what the function does to its input: fetch, derive, parse, render. Say it: `answerRows_derive`, `seriesUid_parse`.

A preposition may follow the verb as part of its adverb (`rows_readFromCache`), or qualify the subject (`dataFromUser_parse`). The lint refuses a verb that is, or starts with, `of`, `to`, `with`, `from`, `for`, `by`, `as`, `in`, `on` or `at`.

### Variables, parameters and fields: lowerCamelCase

Local variables, parameters, module-level variables and class or interface fields are lowerCamelCase.

```typescript
const siteCount: number = sites.length;
let current: Paragraph | null = null;

function paragraphs_build(segments: readonly Segment[], gapLimit: number): Paragraph[] { ... }

interface Segment {
    readonly startTime: number;
    readonly endTime: number;
    readonly text: string;
}
```

### Everything else

| Kind | Convention | Example |
|---|---|---|
| Class, interface, type alias, error | PascalCase | `TranscriptSegment`, `ConfigError` |
| Module-level constant | UPPER_SNAKE_CASE | `PARAGRAPH_GAP_SECONDS` |
| Getter | lowerCamelCase noun, named like a field | `paragraph.startTime` |
| File | lowerCamelCase, matching its main export where there is one | `transcript.ts` |
| Private member or helper | `private`, or not exported; named as above | `private get segmentFirst()` |

### Where frameworks win

Names a framework or the platform dictates keep their required spelling:

- A method that overrides a base class keeps the base class's name, and says so with `override` (`override toString()`). The lint exempts `override` methods.
- A method a framework calls by name without inheritance (`toJSON`, `connectedCallback`) cannot carry `override`. Disable the naming rule on that line and say why:
  `// eslint-disable-next-line @typescript-eslint/naming-convention -- JSON.stringify calls toJSON by name`

Keys that mirror an external schema keep that schema's spelling, and are mapped to lowerCamelCase at the boundary. Quoted keys (`'study_instance_uid'`) pass as written; environment-variable names pass in UPPER_CASE. See the settings example under [which model](#which-model).

---

## Types: pervasive and explicit

Every parameter and every return value has a type. Local variables get one whenever the type is not obvious from the right-hand side.

```typescript
// Good: complete signature
function paragraphs_build(segments: readonly Segment[], gapLimit: number): Paragraph[] { ... }

// Bad: missing return type and implicitly typed parameters
function paragraphs_build(segments, gapLimit) { ... }
```

```typescript
// Good: the annotation says what the empty container will hold
const paragraphsByRecording: Map<string, Paragraph[]> = new Map();

// Bad: what goes in here?
const result = {};
```

Name the contents of collections:

```typescript
// Good
function columns_get(): string[] { ... }
function resultsByScenario_get(): Map<string, ProjectionResult> { ... }

// Bad: the element type is hidden
function columns_get(): unknown[] { ... }
function resultsByScenario_get(): object { ... }
```

`any` is not a type; it is the absence of one. Use the specific type, a generic, or `unknown` when a value is genuinely opaque, and narrow it before use. Parse untrusted input (`JSON.parse`, a request body, a file) into `unknown` and validate it into a named type, as `segment_parse` does in the reference module.

---

## Return types: models for anything non-primitive

A function that returns more than a primitive (`number`, `string`, `boolean`, `bigint`, `undefined`, `null`) or a homogeneous collection of known types returns a named model. Never an anonymous `Record<string, ...>`, and never a tuple of loosely related values.

```typescript
// Good
interface CostSplit {
    readonly variableCost: number;
    readonly staffingCost: number;
}

function costs_calculate(revenue: number, siteCount: number): CostSplit { ... }

// Bad: callers must remember what the keys or positions mean
function costs_calculate(revenue: number, siteCount: number): Record<string, number> { ... }
function costs_calculate(revenue: number, siteCount: number): [number, number] { ... }
```

The same applies to fields: a field that holds an array of records is an array of a smaller model waiting to be named.

### Which model

| Use | Model | Why |
|---|---|---|
| Plain data inside the program | `interface` with `readonly` fields | No runtime cost; the default |
| Data with behaviour or an invariant to keep | `class` | Methods and getters live with the data |
| Settings from environment variables | `zod` schema, parsed once at start-up | Reads and validates the environment |
| Data crossing a boundary (API request or response, file, message) | `zod` schema, or a hand-written parser into an `interface` | Validation at the edge; plain types inside |

Settings, with `zod`:

```typescript
import { z } from 'zod';

const transcribeSettingsSchema = z
    .object({
        TRANSCRIBE_MODEL: z.string().default('large-v3'),
        TRANSCRIBE_DEVICE: z.enum(['cpu', 'cuda']).default('cpu'),
    })
    .transform((env) => ({
        modelName: env.TRANSCRIBE_MODEL,
        computeDevice: env.TRANSCRIBE_DEVICE,
    }));

/** Runtime settings for a transcription run. */
export type TranscribeSettings = z.output<typeof transcribeSettingsSchema>;

/**
 * Read and validate settings from the environment.
 *
 * @param env - Environment to read; the process environment by default.
 * @returns Validated settings.
 * @throws {z.ZodError} If a variable is present but invalid.
 */
export function settings_load(env: NodeJS.ProcessEnv = process.env): TranscribeSettings {
    return transcribeSettingsSchema.parse(env);
}
```

---

## Function length: refactor on signals, not line counts

There is no line limit. Refactor when one of these appears:

1. **Nesting deeper than three levels.**
2. **More than one responsibility.** The function does two things a reader would describe with "and".
3. **No one-sentence summary.** If the first line of its documentation cannot say what it does, it does too much.
4. **Repetition.** The same logic appears twice.

A long function with a single responsibility, a linear flow and well-named intermediate values is fine:

```typescript
function projection_build(assumptions: ScenarioAssumptions, years: Iterable<number>): ProjectionResult {
    const yearRows: YearRow[] = [];
    let previousSites: number = 0;
    for (const year of [...new Set(years)].sort((a: number, b: number): number => a - b)) {
        const siteCount: number = siteTrajectory_calculate(assumptions, year);
        const newSites: number = Math.max(siteCount - previousSites, 0);
        const revenue: RevenueStreams = revenueStreams_calculate(assumptions, year, siteCount, newSites);
        const costs: CostSplit = costs_calculate(revenue.total, siteCount);
        yearRows.push({ year, siteCount, revenue, costs });
        previousSites = siteCount;
    }
    return { scenario: assumptions.name, rows: yearRows };
}
```

Deep nesting with mixed concerns is not:

```typescript
// Bad: four levels deep, parsing and validation tangled together
function config_process(rawConfig: Record<string, unknown>): ProcessedConfig {
    if ('database' in rawConfig) {
        const database = rawConfig.database;
        if (typeof database === 'object' && database !== null && 'url' in database) {
            if (typeof database.url === 'string' && database.url.startsWith('postgres://')) {
                const hostPort: string[] = database.url.split('://')[1]?.split(':') ?? [];
                if (hostPort.length === 2) {
                    ...
```

```typescript
// Good: one step per function, each nameable
function config_process(rawConfig: Record<string, unknown>): ProcessedConfig {
    const databaseRaw: DatabaseRaw = databaseConfig_extract(rawConfig);
    const database: DatabaseConfig = databaseConfig_validate(databaseRaw);
    return { database };
}
```

---

## Code structure principles

### Explicit over implicit

Name the constants. A literal that carries meaning gets a name; a large literal uses digit separators.

```typescript
// Good
const USD_PER_MILLION: number = 1_000_000;
const installRevenue: number = (newSites * installFee) / USD_PER_MILLION;

// Bad: what is 1e6, and why?
const installRevenue = (newSites * installFee) / 1e6;
```

### One source of truth

Behaviour comes from configuration or a single definition, not from values repeated or hard-coded at the point of use.

```typescript
// Good
const siteCount: number = siteTrajectory_calculate(assumptions, year);

// Bad: where do 10 and 1.25 come from, and where else are they?
const siteCount = 10 * 1.25 ** year;
```

### Type safety over flexibility

Specific types at interfaces, even when a looser type would also work.

```typescript
// Good
function results_merge(base: ProjectionResult, overlay: ProjectionResult): ProjectionResult { ... }

// Bad
function results_merge(base: any, overlay: any): any { ... }
```

---

## Imports

Order: Node.js built-ins (with the `node:` prefix), then third-party packages, then local modules, each group separated by a blank line and sorted within the group. ESLint's `import/order` rule enforces the order; `eslint --fix` applies it. Types are imported with `import type`, or `type` on the individual name.

```typescript
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { Command } from 'commander';
import { z } from 'zod';

import { type Segment, segments_load } from './transcript.ts';
```

A package's own scope (`@fnndsc/cumin`) is third-party to every other package, even in the same monorepo. No comment headers over the groups: the blank lines already say where a group starts.

---

## Documentation: JSDoc everywhere

Every file, and every function, class, method, type and field in it, private ones included, has a JSDoc comment. Getters and `override` methods need only the comment; everything else carries the tags below. The checks named here are enforced: see [tooling](#tooling-tsc-and-eslint-zero-tolerance). Types belong in the TypeScript, not in the JSDoc: `@param name - meaning`, never `@param {string} name`.

### Modules

Every file is a module, and opens with a block carrying `@file` and `@module`. It says what the file is for and its scope, then has three sections, required everywhere but in test files (`*.test.ts`, `*.spec.ts`):

- **Key components:** its key exports, one line each;
- **Typical usage:** how a caller uses it;
- **Dependencies:** what it needs, and its assumptions (input formats, units).

```typescript
/**
 * @file Merge timed transcript segments into readable paragraphs.
 *
 * Speech-to-text engines such as Whisper emit short timed segments. This module
 * groups consecutive segments into paragraphs wherever the silence between them
 * is shorter than a threshold, and renders the result as plain text with a
 * timestamp at the start of each paragraph.
 *
 * Key components:
 * - Segment: one timed span of recognised speech.
 * - Paragraph: consecutive segments merged into one block.
 * - segments_load: read segments from a JSON file.
 * - paragraphs_build: group segments into paragraphs by silence gap.
 * - transcript_render: render paragraphs as timestamped plain text.
 *
 * Typical usage:
 * ```ts
 * const segments: Segment[] = segments_load('meeting.json');
 * const paragraphs: Paragraph[] = paragraphs_build(segments, PARAGRAPH_GAP_SECONDS);
 * console.log(transcript_render(paragraphs));
 * ```
 *
 * Dependencies: Node.js built-ins only. Input JSON is an array of objects with
 * `start` and `end` (seconds, number) and `text` (string) keys.
 *
 * @module
 */
```

### Functions and methods

A one-line summary, a paragraph of detail if the behaviour is not obvious, then the tags:

- **`@param`**: every parameter, with its meaning, units and constraints. Required for each parameter.
- **`@returns`**: the structure and meaning of the result, including edge cases (empty input, missing data). Required whenever the function returns a value.
- **`@throws`**: every exception the function throws itself, and any other a caller should expect, with its class. Required whenever the function contains a `throw`.
- **`@example`**: typical use. Tests run the examples, so they stay true. Required on every exported function, class, interface and public method.

```typescript
/**
 * Group consecutive segments into paragraphs by silence gap.
 *
 * A new paragraph starts whenever the silence between one segment's end and
 * the next segment's start exceeds `gapLimit`.
 *
 * @param segments - Segments in time order.
 * @param gapLimit - Longest silence, in seconds, that still joins two segments
 *   into the same paragraph. Must be non-negative.
 * @returns Paragraphs in time order. Empty if `segments` is empty.
 * @throws {RangeError} If `gapLimit` is negative.
 *
 * @example
 * ```ts
 * const paragraphs: Paragraph[] = paragraphs_build([
 *     { startTime: 0.0, endTime: 1.0, text: 'One.' },
 *     { startTime: 1.5, endTime: 2.0, text: 'Two.' },
 *     { startTime: 9.0, endTime: 10.0, text: 'Three.' },
 * ]);
 * paragraphs.map((paragraph: Paragraph): string => paragraph.text); // ['One. Two.', 'Three.']
 * ```
 */
```

Getters are documented like fields: a one-line description of the value, no `@returns`.

### Classes and data types

Purpose, an `@example` on an exported type, and a one-line comment on each field other than a class's private ones, attached to the field itself, so editors show it on hover. This is where TypeScript differs from the Python guide's `Attributes:` section: `@property` tags duplicate the type system, and the lint rejects them.

```typescript
/**
 * One timed span of recognised speech.
 *
 * @example
 * ```ts
 * const segment: Segment = { startTime: 0.0, endTime: 2.5, text: 'Good morning.' };
 * ```
 */
export interface Segment {
    /** Offset of the first word from the start of the recording, in seconds. */
    readonly startTime: number;
    /** Offset of the end of the last word, in seconds. */
    readonly endTime: number;
    /** Recognised text, stripped of surrounding whitespace. */
    readonly text: string;
}
```

### Comments

Prefer clear names to comments. A comment explains **why** a decision was made, never **what** the next line does.

```typescript
// Good: explains a choice the code cannot
// Truncate rather than round, so a timestamp never points past the speech it labels.
const wholeSeconds: number = Math.trunc(seconds);

// Bad: repeats the code
// Convert seconds to an integer
const wholeSeconds = Math.trunc(seconds);
```

---

## Tooling: tsc and ESLint, zero tolerance

- `tsc --noEmit` reports nothing. `eslint --max-warnings 0 .` reports nothing. The tests pass.
- Fix the cause of a finding rather than silencing it. An `eslint-disable` comment or `@ts-expect-error` names the rule and gives the reason after `--`. `@ts-ignore` and `as unknown as` are not used.
- A project's own configuration wins. Start from [`tsconfig.json`](tsconfig.json) and [`eslint.config.mjs`](eslint.config.mjs). The ESLint configuration builds on `typescript-eslint`'s strict type-checked rules and adds the [naming](#naming) rule, including the ban on prepositions as verbs; it uses the same pattern as the Python [`style_check.py`](../python/style_check.py). A local rule in the same file, `local/file-overview-sections`, requires the file comment's sections, as `style_check.py` does for a module docstring. Between them, the rules require what ruff and `style_check.py` require in Python, rule for rule.
- Anyone proposing code, a person or a coding agent, runs the checks first and shows the clean output with the change. `npm run check` runs all three here.

---

## Checklist

- [ ] TypeScript 5.8+, ES2023, ES modules; strict `tsconfig.json`; erasable syntax only.
- [ ] Functions and methods named `subject_verb`, exactly one underscore; the verb is a verb.
- [ ] Variables, parameters and fields in lowerCamelCase; types PascalCase; module constants UPPER_SNAKE_CASE.
- [ ] Types on every parameter and return, and on non-obvious locals; specific collection types; no `any`.
- [ ] Non-primitive returns are a named `interface` or `class`, never an anonymous record or loose tuple.
- [ ] Untrusted input parsed into `unknown` and validated into a named type.
- [ ] Functions refactored on nesting, responsibility, clarity and repetition, not on length.
- [ ] Named constants; one source of truth; specific types at interfaces.
- [ ] Imports grouped: `node:` built-ins, third-party, local; `import type` for types.
- [ ] File block with `@file`, purpose, then Key components, Typical usage and Dependencies sections, and `@module`.
- [ ] Every function and method, private ones included: summary, `@param`, `@returns`, `@throws`; `@example` if exported.
- [ ] Every type: purpose and a comment on each field; `@example` if exported.
- [ ] Comments explain why, not what.
- [ ] `tsc`, ESLint and tests clean.
