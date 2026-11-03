# Changelog

Changes to the guides and to what the configurations enforce. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/), where a major version tightens a rule existing code may break.

## [1.0.0] - 2026-11-03

### Added

- Python guide, cleaned up from the earlier "ChRONOS Python Style Guide": neutral title and examples, stated scope, lowerCamelCase variables written in, examples that follow their own rules, Pydantic v2 settings.
- TypeScript guide, from the guide kept in the `mise` packages, including its rule that the verb in an RPN name is a verb and never a preposition.
- Both guides on one outline, with `scripts/guides_compare.py` to keep them there.
- `python/ruff.toml` and `python/rpn_check.py`, which enforces the RPN naming rule ruff cannot express.
- `typescript/tsconfig.json` and `typescript/eslint.config.mjs`, all rules at error severity, with the same RPN pattern as `rpn_check.py`.
- A reference module in each language (`example/transcript.*`) that applies every rule, with doctests and a test file that run its documented examples.
- CI running every check on push and pull request.
