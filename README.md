# style-guides

[![check](https://github.com/rudolphpienaar/style-guides/actions/workflows/check.yml/badge.svg)](https://github.com/rudolphpienaar/style-guides/actions/workflows/check.yml)

Coding conventions for Python and TypeScript that I use in repositories I start or own. In an existing codebase, its own conventions win.

The two guides are kept in step: same sections in the same order, same rules, same worked example. Each comes with the lint configuration that enforces it and a reference module that passes it.

| | Python | TypeScript |
|---|---|---|
| Guide | [`python/STYLE-GUIDE.md`](python/STYLE-GUIDE.md) | [`typescript/STYLE-GUIDE.md`](typescript/STYLE-GUIDE.md) |
| Lint and type configuration | [`ruff.toml`](python/ruff.toml) | [`eslint.config.mjs`](typescript/eslint.config.mjs), [`tsconfig.json`](typescript/tsconfig.json) |
| RPN naming check | [`rpn_check.py`](python/rpn_check.py) | `@typescript-eslint/naming-convention` in the ESLint configuration |
| Reference module | [`example/transcript.py`](python/example/transcript.py) | [`example/transcript.ts`](typescript/example/transcript.ts) |
| Examples run by | doctest | [`example/transcript.test.ts`](typescript/example/transcript.test.ts) (`node --test`) |

## In short

- **Naming.** Functions and methods are `subject_verb` (Reverse Polish Notation, RPN): `segments_load`, `paragraphs_build`, `transcript_render`. Variables, parameters and fields are lowerCamelCase. The verb after the underscore is a verb, never a preposition.
- **Types.** On every parameter and return, and on non-obvious locals. No `Any` or `any`.
- **Models.** Anything non-primitive a function returns is a named model (dataclass, Pydantic model, interface, class), never a loose dict, record or tuple.
- **Documentation.** On every module, class and function: Google-style docstrings in Python, JSDoc in TypeScript.
- **Linters clean.** Code is shown only after the checks pass.

## Adopting a guide

Link the guide from the project's `CONTRIBUTING` file and copy its configuration: `ruff.toml` (or its contents under `[tool.ruff]` in `pyproject.toml`) and `rpn_check.py` for Python; `eslint.config.mjs` and `tsconfig.json`, with the devDependencies listed in [`typescript/package.json`](typescript/package.json), for TypeScript.

## Layout

```
python/          Python guide, ruff configuration, RPN checker, reference module
typescript/      TypeScript guide, ESLint and tsc configuration, reference module and test
scripts/         guides_compare.py: checks that the two guides share one outline
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) lists the checks and how a change to one guide carries to the other. [`CHANGELOG.md`](CHANGELOG.md) records changes to the rules.

## Licence and citation

MIT, see [`LICENSE`](LICENSE). To cite, see [`CITATION.cff`](CITATION.cff).
