# Python Style Guide

Rudolph Pienaar's conventions for Python. They apply to code in repositories I start or own. In an existing codebase, follow that codebase's conventions instead: a Django project written to PEP 8 stays PEP 8, and a patch to it should be indistinguishable from the code around it.

This guide and the [TypeScript guide](../typescript/STYLE-GUIDE.md) are kept in step: same sections in the same order, same rules, same example domain. Where the languages force a difference, the guide says so. Most of it is widely shared practice: modern Python, full type hints, models instead of loose dicts, Google docstrings, a clean linter. The [naming](#naming) section is the idiosyncratic part. It departs from PEP 8, and is the part most likely to differ from what a contributor expects.

Snippets below elide bodies and docstrings (`...`) where the point being made is elsewhere. [`example/transcript.py`](example/transcript.py) is a complete module that applies every rule at full strength and passes `ruff check` with [`ruff.toml`](ruff.toml), `style_check.py`, and its own doctests. When in doubt, copy its shape.

---

## Language version and configuration

**Python 3.11 or later.**

- `from __future__ import annotations` as the first import of every module, so annotations are never evaluated at import time and forward references need no quotes.
- Union syntax: `str | None`, not `Optional[str]`.
- Abstract collection types from `collections.abc` (`Iterable`, `Mapping`, `Sequence`), not from `typing`.
- Structural pattern matching (`match`) where it makes branching on shape clearer than an `if` chain.
- Project metadata and tool configuration in `pyproject.toml`; [`ruff.toml`](ruff.toml) is the baseline for the `[tool.ruff]` section.

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

```python
# Conventional Python (verb first)
def get_user_names() -> list[str]: ...
def is_login_valid() -> bool: ...
def parse_user_data(raw: str) -> UserRecord: ...


# RPN (subject first)
def userNames_get() -> list[str]: ...
def login_checkIsValid() -> bool: ...
def userData_parse(raw: str) -> UserRecord: ...
```

From the reference module:

```python
def segments_load(path: Path) -> list[Segment]: ...
def paragraphs_build(segments: list[Segment], gapLimit: float) -> list[Paragraph]: ...
def timestamp_format(seconds: float) -> str: ...
def transcript_render(paragraphs: list[Paragraph]) -> str: ...
```

Every function and method name has exactly one underscore, apart from a leading underscore that marks it private. `main` is the one name without a subject.

Why:

- **Subject first.** The name says what is being operated on before it says what happens to it.
- **Grouping.** Operations on the same subject sort together in an editor outline, an API listing or a module index: `user_create`, `user_delete`, `user_get`, `userPassword_reset`.
- **Searchability.** `grep -n 'paragraphs_'` finds everything that acts on paragraphs.
- **Machine parsability.** One underscore splits every name into subject and verb, so a regular expression can lint it, index it or build a call graph from it.

### The verb is a verb

The part after the underscore is always a verb. A preposition in its place (`answerRows_of`, `seriesUid_forPath`, `x_to`) names the result without saying what the function does to its input: fetch, derive, parse, render. Say it: `answerRows_derive`, `seriesUid_parse`.

A preposition may follow the verb as part of its adverb (`rows_readFromCache`), or qualify the subject (`dataFromUser_parse`). `style_check.py` refuses a verb that is, or starts with, `of`, `to`, `with`, `from`, `for`, `by`, `as`, `in`, `on` or `at`.

### Variables, parameters and fields: lowerCamelCase

Local variables, parameters, module-level variables and class or dataclass fields are lowerCamelCase.

```python
siteCount: int = len(sites)
current: Paragraph | None = None


def paragraphs_build(segments: list[Segment], gapLimit: float) -> list[Paragraph]: ...


@dataclass(frozen=True)
class Segment:
    startTime: float
    endTime: float
    text: str
```

### Everything else

| Kind | Convention | Example |
|---|---|---|
| Class, dataclass, model, exception | PascalCase | `TranscriptSegment`, `ConfigError` |
| Module-level constant | UPPER_SNAKE_CASE | `PARAGRAPH_GAP_SECONDS` |
| Property | lowerCamelCase noun, named like a field | `paragraph.startTime` |
| Module, package | lowercase, short, underscores only if needed | `transcript.py` |
| Private member or helper | leading underscore, otherwise as above | `_cache`, `_segment_parse()` |

### Where frameworks win

Names a framework or the language dictates keep their required spelling:

- Dunder methods (`__init__`, `__repr__`).
- A method that overrides a base class keeps the base class's name, and says so with `@override` (from `typing` on 3.12+, `typing_extensions` before): `setUp`, Django's `get_queryset`. `style_check.py` exempts `@override` methods from the naming rule and from everything but the docstring.
- pytest's `test_*` functions, which pytest finds by name. `style_check.py` exempts them in the same way, and does not ask a test module's docstring for sections.
- Names a framework requires without inheritance, such as Pydantic's `model_config`.

Fields that mirror an external schema (a JSON API, a database column, an environment variable) stay lowerCamelCase in Python and map to the external name with an alias, so the outside world sees its own spelling. See the settings example under [which model](#which-model).

---

## Types: pervasive and explicit

Every parameter and every return value has a type hint. Local variables get one whenever the type is not obvious from the right-hand side.

```python
# Good: complete signature
def paragraphs_build(segments: list[Segment], gapLimit: float) -> list[Paragraph]: ...


# Bad: missing return type
def paragraphs_build(segments: list[Segment], gapLimit: float): ...
```

```python
# Good: the annotation says what the empty container will hold
paragraphsByRecording: dict[str, list[Paragraph]] = {}

# Bad: what goes in here?
result = {}
```

Name the contents of collections:

```python
# Good
def columns_get() -> list[str]: ...
def resultsByScenario_get() -> dict[str, ProjectionResult]: ...


# Bad: the element type is hidden
def columns_get() -> list: ...
def resultsByScenario_get() -> dict: ...
```

`Any` is not a type hint; it is the absence of one. Use the specific type, a `Protocol`, a `TypeVar`, or `object` when a value is genuinely opaque, and narrow it before use. Parse untrusted input (`json.loads`, a request body, a file) into a validated model at the edge.

---

## Return types: models for anything non-primitive

A function that returns more than a primitive (`int`, `float`, `str`, `bool`, `bytes`, `None`) or a homogeneous collection of known types returns a defined model. Never a bare `dict`, and never a tuple of loosely related values.

```python
# Good
@dataclass(frozen=True)
class CostSplit:
    variableCost: float
    staffingCost: float


def costs_calculate(revenue: float, siteCount: int) -> CostSplit: ...


# Bad: callers must remember what the keys or positions mean
def costs_calculate(revenue: float, siteCount: int) -> dict[str, float]: ...
def costs_calculate(revenue: float, siteCount: int) -> tuple[float, float]: ...
```

The same applies to fields: a field that holds a list of dicts is a list of a smaller model waiting to be named.

### Which model

| Use | Model | Why |
|---|---|---|
| Plain data inside the program | `@dataclass(frozen=True)` | Standard library, no dependency; the default |
| Data with behaviour or an invariant to keep | `@dataclass` with methods and properties | Methods and properties live with the data |
| Settings from environment variables | Pydantic `BaseSettings` | Reads and validates the environment |
| Data crossing a boundary (API request or response, file, message) | Pydantic `BaseModel` | Validation at the edge; plain types inside |

Settings, with Pydantic v2:

```python
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TranscribeSettings(BaseSettings):
    """Runtime settings for a transcription run.

    Attributes:
        modelName: Whisper model to load, from ``TRANSCRIBE_MODEL``.
        computeDevice: Where inference runs, from ``TRANSCRIBE_DEVICE``.
    """

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True)

    modelName: str = Field(default="large-v3", validation_alias="TRANSCRIBE_MODEL")
    computeDevice: Literal["cpu", "cuda"] = Field(
        default="cpu", validation_alias="TRANSCRIBE_DEVICE"
    )
```

---

## Function length: refactor on signals, not line counts

There is no line limit. Refactor when one of these appears:

1. **Nesting deeper than three levels.**
2. **More than one responsibility.** The function does two things a reader would describe with "and".
3. **No one-sentence summary.** If the docstring's first line cannot say what it does, it does too much.
4. **Repetition.** The same logic appears twice.

A long function with a single responsibility, a linear flow and well-named intermediate values is fine:

```python
def projection_build(assumptions: ScenarioAssumptions, years: Iterable[int]) -> ProjectionResult:
    yearRows: list[YearRow] = []
    previousSites: float = 0.0
    for year in sorted(set(years)):
        siteCount: float = siteTrajectory_calculate(assumptions, year)
        newSites: float = max(siteCount - previousSites, 0.0)
        revenue: RevenueStreams = revenueStreams_calculate(assumptions, year, siteCount, newSites)
        costs: CostSplit = costs_calculate(revenue.total, siteCount)
        yearRows.append(YearRow(year=year, siteCount=siteCount, revenue=revenue, costs=costs))
        previousSites = siteCount
    return ProjectionResult(scenario=assumptions.name, rows=yearRows)
```

Deep nesting with mixed concerns is not:

```python
# Bad: four levels deep, parsing and validation tangled together
def config_process(rawConfig: Mapping[str, object]) -> ProcessedConfig:
    if "database" in rawConfig:
        database = rawConfig["database"]
        if isinstance(database, dict) and "url" in database:
            if database["url"].startswith("postgres://"):
                hostPort = database["url"].split("://")[1].split(":")
                if len(hostPort) == 2:
                    ...
```

```python
# Good: one step per function, each nameable
def config_process(rawConfig: Mapping[str, object]) -> ProcessedConfig:
    databaseRaw: DatabaseRaw = databaseConfig_extract(rawConfig)
    database: DatabaseConfig = databaseConfig_validate(databaseRaw)
    return ProcessedConfig(database=database)
```

---

## Code structure principles

### Explicit over implicit

Name the constants. A literal that carries meaning gets a name; a large literal uses digit separators.

```python
# Good
USD_PER_MILLION: float = 1_000_000.0
installRevenue: float = newSites * installFee / USD_PER_MILLION

# Bad: what is 1e6, and why?
installRevenue = newSites * installFee / 1e6
```

### One source of truth

Behaviour comes from configuration or a single definition, not from values repeated or hard-coded at the point of use.

```python
# Good
siteCount: float = siteTrajectory_calculate(assumptions, year)

# Bad: where do 10 and 1.25 come from, and where else are they?
siteCount = 10 * (1.25**year)
```

### Type safety over flexibility

Specific types at interfaces, even when a looser type would also work.

```python
# Good
def results_merge(base: ProjectionResult, overlay: ProjectionResult) -> ProjectionResult: ...


# Bad
def results_merge(base: Any, overlay: Any) -> Any: ...
```

---

## Imports

Order: the module docstring, then `from __future__ import annotations`, then standard library, third-party and local imports, each group separated by a blank line and sorted within the group. Ruff's `I` rules enforce the order; `ruff check --fix` applies it.

```python
"""Module docstring."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import yaml
from pydantic import BaseModel

from transcribe.models import Segment
```

No comment headers over the groups: the blank lines already say where a group starts.

---

## Documentation: Google-style docstrings everywhere

Every module, and every class and function in it, private helpers included, has a docstring in the Google style. Properties, `@override` methods, dunders other than `__init__`, and pytest tests need only the docstring; everything else carries the sections below. The checks named here are enforced: see [tooling](#tooling-ruff-and-style_check-zero-tolerance).

### Modules

The module docstring says what the module is for and its scope, then has three sections, required everywhere but in test modules:

- **Key components:** its key classes and functions, one line each;
- **Typical usage:** how a caller uses it;
- **Dependencies:** what it needs, and its assumptions (input formats, units).

```python
"""Merge timed transcript segments into readable paragraphs.

Speech-to-text engines such as Whisper emit short timed segments. This module
groups consecutive segments into paragraphs wherever the silence between them
is shorter than a threshold, and renders the result as plain text with a
timestamp at the start of each paragraph.

Key components:
    - Segment: one timed span of recognised speech.
    - Paragraph: consecutive segments merged into one block.
    - segments_load: read segments from a JSON file.
    - paragraphs_build: group segments into paragraphs by silence gap.
    - transcript_render: render paragraphs as timestamped plain text.

Typical usage:
    segments = segments_load(Path("meeting.json"))
    paragraphs = paragraphs_build(segments, gapLimit=PARAGRAPH_GAP_SECONDS)
    print(transcript_render(paragraphs))

Dependencies:
    Standard library only. Input JSON is a list of objects with ``start`` and
    ``end`` (seconds, number) and ``text`` (string) keys.
"""
```

### Functions and methods

A one-line summary, a paragraph of detail if the behaviour is not obvious, then the sections:

- **Args:** every parameter, with its meaning, units and constraints. Required whenever the function takes a parameter.
- **Returns:** the structure and meaning of the result, including edge cases (empty input, missing data). Required whenever the function returns a value; a generator has **Yields:** instead.
- **Raises:** every exception the function raises itself, and any other a caller should expect. Required whenever the function contains a `raise`.
- **Example:** typical use, as a doctest, so it stays true. Required on every public function and method.

```python
def paragraphs_build(
    segments: list[Segment], gapLimit: float = PARAGRAPH_GAP_SECONDS
) -> list[Paragraph]:
    """Group consecutive segments into paragraphs by silence gap.

    A new paragraph starts whenever the silence between one segment's end and
    the next segment's start exceeds ``gapLimit``.

    Args:
        segments: Segments in time order.
        gapLimit: Longest silence, in seconds, that still joins two segments
            into the same paragraph. Must be non-negative.

    Returns:
        Paragraphs in time order. Empty if ``segments`` is empty.

    Raises:
        ValueError: If ``gapLimit`` is negative.

    Example:
        >>> segments = [
        ...     Segment(0.0, 1.0, "One."),
        ...     Segment(1.5, 2.0, "Two."),
        ...     Segment(9.0, 10.0, "Three."),
        ... ]
        >>> [paragraph.text for paragraph in paragraphs_build(segments)]
        ['One. Two.', 'Three.']
    """
```

Properties are documented like fields: a one-line description of the value, no Args or Returns.

### Classes and data types

Purpose, an **Attributes** section covering every public field, and, on a public class, an **Example** of construction and use. This is where Python differs from the TypeScript guide, which documents each field on the field itself: Python has no comment syntax that attaches to a dataclass field, and the Google style puts them in the class docstring.

```python
@dataclass(frozen=True)
class Segment:
    """One timed span of recognised speech.

    Attributes:
        startTime: Offset of the first word from the start of the recording,
            in seconds.
        endTime: Offset of the end of the last word, in seconds.
        text: Recognised text, stripped of surrounding whitespace.

    Example:
        >>> Segment(startTime=0.0, endTime=2.5, text="Good morning.")
        Segment(startTime=0.0, endTime=2.5, text='Good morning.')
    """

    startTime: float
    endTime: float
    text: str
```

Doctests pass: `python -m doctest -v module.py`. Mark an example that needs files or a network with `# doctest: +SKIP`.

### Comments

Prefer clear names to comments. A comment explains **why** a decision was made, never **what** the next line does.

```python
# Good: explains a choice the code cannot
# Truncate rather than round, so a timestamp never points past the speech it labels.
wholeSeconds: int = int(seconds)

# Bad: repeats the code
# Convert seconds to int
wholeSeconds = int(seconds)
```

---

## Tooling: ruff and style_check, zero tolerance

- `ruff check` reports nothing. `ruff format --check` reports nothing. `python style_check.py <paths>` reports nothing. Doctests pass.
- Fix the cause of a finding rather than silencing it. A `# noqa` or `# type: ignore` names the rule and gives the reason on the same line.
- A project's own `[tool.ruff]` wins. Start from [`ruff.toml`](ruff.toml), which selects pep8-naming and then ignores exactly the rules the [naming](#naming) section overrides (`N802`, `N803`, `N806`, `N815`, `N816`). Ruff's Returns, Yields and Raises rules (`DOC201`, `DOC202`, `DOC402`, `DOC403`, `DOC501`) are still in preview; `ruff.toml` opts into those five by name and no other preview rule.
- Ruff cannot express the RPN rule or the docstring structure (sections present, every field listed, private helpers documented), so [`style_check.py`](style_check.py) checks those. Between them, ruff and `style_check.py` require what the TypeScript ESLint configuration requires, rule for rule.
- Anyone proposing code, a person or a coding agent, runs the checks first and shows the clean output with the change.

---

## Checklist

- [ ] Python 3.11+; `from __future__ import annotations` first; configuration in `pyproject.toml`.
- [ ] Functions and methods named `subject_verb`, exactly one underscore; the verb is a verb.
- [ ] Variables, parameters and fields in lowerCamelCase; classes PascalCase; module constants UPPER_SNAKE_CASE.
- [ ] Type hints on every parameter and return, and on non-obvious locals; specific collection types; no `Any`.
- [ ] Non-primitive returns are a `dataclass` or a Pydantic model, never a bare dict or loose tuple.
- [ ] Untrusted input validated into a model at the edge.
- [ ] Functions refactored on nesting, responsibility, clarity and repetition, not on length.
- [ ] Named constants; one source of truth; specific types at interfaces.
- [ ] Imports grouped: `__future__`, standard library, third-party, local.
- [ ] Module docstring with purpose, then Key components, Typical usage and Dependencies sections.
- [ ] Every function and method, private ones included: summary, Args, Returns or Yields, Raises; Example if public.
- [ ] Every class: purpose, Attributes for every public field; Example if public.
- [ ] Comments explain why, not what.
- [ ] `ruff check`, `ruff format --check`, `style_check.py` and doctests clean.
