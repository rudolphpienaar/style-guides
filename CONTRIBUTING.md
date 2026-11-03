# Contributing

These are personal conventions, published so that collaborators and coding agents can read them, link to them and copy the configurations. Issues and pull requests are welcome, especially where a rule is unclear, an example contradicts its rule, or a configuration does not enforce what the guide says.

## The two guides move together

The Python and TypeScript guides share one outline: the same sections in the same order, the same rules, the same example domain. A change to a rule changes both guides, both configurations and both reference modules in the same pull request, unless the change is about something only one language has. `scripts/guides_compare.py` fails the build when the outlines drift.

Where the languages force a difference, the guide states it in the section concerned rather than silently diverging.

## What to change where

| To change | Edit |
|---|---|
| A rule or its explanation | `python/STYLE-GUIDE.md` and `typescript/STYLE-GUIDE.md` |
| What the linters enforce | `python/ruff.toml`, `typescript/eslint.config.mjs`, `typescript/tsconfig.json` |
| The RPN naming pattern | `python/style_check.py` and the `RPN_REGEX` in `typescript/eslint.config.mjs`, which share one pattern |
| What documentation is required | `python/style_check.py` and `python/ruff.toml` (`D`, `DOC`), and the `jsdoc/*` and `local/file-overview-sections` rules in `typescript/eslint.config.mjs`, which require the same things |
| The worked example | `python/example/transcript.py` and `typescript/example/transcript.ts` (with its test) |

## Checks

Code in this repository follows the guides it contains. Before opening a pull request, run from the repository root:

```sh
# Both guides
python scripts/guides_compare.py python/STYLE-GUIDE.md typescript/STYLE-GUIDE.md

# Python
ruff check . && ruff format --check .
python python/style_check.py python scripts
(cd python && python -m doctest example/transcript.py style_check.py)
python -m doctest scripts/guides_compare.py

# TypeScript
(cd typescript && npm ci && npm run check)
```

CI runs the same checks on every push and pull request.

## Commits

One logical change per commit, with an imperative subject line of at most 72 characters and a body that says why when the subject cannot. Record user-visible changes to a guide or a configuration in `CHANGELOG.md`.

## Licence

By contributing you agree that your contribution is licensed under the MIT licence in `LICENSE`.
