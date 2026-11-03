# Python Style Guide

Rudolph Pienaar's conventions for Python. They apply to code in repositories I start or own. In an existing codebase, follow that codebase's conventions instead: a Django project written to PEP 8 stays PEP 8, and a patch to it should be indistinguishable from the code around it.

Most of this guide is widely shared practice: modern Python, full type hints, models instead of loose dicts, Google docstrings, a clean linter. The [naming](#naming) section is the idiosyncratic part, and the part most likely to differ from what a contributor expects.

Snippets below elide bodies and docstrings (`...`) where the point being made is elsewhere. [`example/transcript.py`](example/transcript.py) is a complete module that applies every rule at full strength and passes `ruff check` with [`ruff.toml`](ruff.toml). When in doubt, copy its shape.

---

## Language version

**Python 3.11 or later.** Use the modern features:

- Union syntax: `str | None`, not `Optional[str]`.
- `from __future__ import annotations` as the first import of every module, so annotations are never evaluated at import time and forward references need no quotes.
- Abstract collection types from `collections.abc` (`Iterable`, `Mapping`, `Sequence`), not from `typing`.
- Structural pattern matching (`match`) where it makes branching on shape clearer than an `if` chain.

---

## Naming

### Functions and methods: RPN, `subject_action`

Functions and methods name the subject first and the action second, in the order of Reverse Polish Notation (RPN): operand, then operator.

```
<subject>[Qualifier]_<action>[Modifier]
```

The subject is lowerCamelCase; the action is a verb, also lowerCamelCase if it has more than one word.

```python
# Conventional Python (verb first)
def get_user_names() -> list[str]: ...
def is_login_valid() -> bool: ...
def parse_user_data(raw: str) -> UserRecord: ...

# RPN (subject first)
def userNames_get() -> list[str]: ...
def login_isValid() -> bool: ...
def userData_parse(raw: str) -> UserRecord: ...
```

More examples, from the reference module:

```python
def segments_load(path: Path) -> list[Segment]: ...
def paragraphs_build(segments: list[Segment], gapLimit: float) -> list[Paragraph]: ...
def timestamp_format(seconds: float) -> str: ...
def transcript_render(paragraphs: list[Paragraph]) -> str: ...
```

Why:

- **Subject first.** The name says what is being operated on before it says what happens to it.
- **Grouping.** Operations on the same subject sort together in an editor outline, an API listing or a module index.
- **Searchability.** `grep -n 'paragraphs_'` finds everything that acts on paragraphs.

### Variables, parameters and fields: lowerCamelCase

Local variables, function parameters, module-level variables and class or dataclass fields are lowerCamelCase.

```python
siteCount: int = len(sites)
previousEnd: float | None = None

def paragraphs_build(segments: list[Segment], gapLimit: float) -> list[Paragraph]: ...

@dataclass
class Segment:
    startTime: float
    endTime: float
    text: str
```

### Everything else

| Kind | Convention | Example |
|---|---|---|
| Class, dataclass, model, exception | PascalCase | `TranscriptSegment`, `ConfigError` |
| Constant | UPPER_SNAKE_CASE | `PARAGRAPH_GAP_SECONDS` |
| Property | lowerCamelCase noun, named like a field | `paragraph.startTime` |
| Module, package | lowercase, short, underscores only if needed | `transcript.py` |
| Private member or helper | leading underscore, otherwise as above | `_cache`, `_segment_split()` |

### Where frameworks win

Names that a framework or the language dictates keep their required spelling: `__init__`, `model_config` in Pydantic, `setUp` in `unittest`, Django's `get_queryset`, an argparse `dest` that must match a published flag. Do not wrap them to rename them.

Field names that mirror an external schema (a JSON API, a database column, an environment variable) stay lowerCamelCase in Python and map to the external name with an alias, so the outside world sees its own spelling:

```python
class StudyRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    studyInstanceUid: str = Field(alias="study_instance_uid")
```

---

## Type hints: pervasive and explicit

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

`Any` is not a type hint; it is the absence of one. Use the specific type, a `Protocol`, a `TypeVar`, or `object` when a value is genuinely opaque.

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

The same applies to model fields: a field that holds a list of dicts is a list of a smaller model waiting to be named.

### Which model

| Use | Model | Why |
|---|---|---|
| Plain data inside the program | `@dataclass` (`frozen=True` when it should not change) | Standard library, no dependency, cheap |
| Settings from environment variables or `.env` | Pydantic `BaseSettings` | Reads and validates the environment |
| Data crossing a boundary (API request or response, file, message) | Pydantic `BaseModel` | Validation and serialisation |
| Data with non-trivial invariants | Pydantic `BaseModel` with validators | Constraints live with the data |

Settings, Pydantic v2:

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
        if "url" in database:
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
siteCount = 10 * (1.25 ** year)
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

Order: the module docstring, then `from __future__ import annotations`, then standard library, third-party and local imports, each group separated by a blank line and sorted within the group. `ruff check` with the `I` rules enforces the order; `ruff check --fix` applies it.

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

Every module, class and function has a docstring in the Google style.

### Modules

The module docstring says:

- what the module is for, and its scope;
- its key classes and functions, one line each;
- typical usage;
- dependencies and assumptions (input formats, units).

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

- **Args:** every parameter, with its meaning, units and constraints.
- **Returns:** the structure and meaning of the result, including edge cases (empty input, missing data).
- **Raises:** every exception a caller should expect.
- **Example:** typical use, as a doctest where it can run.

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

Properties are documented like attributes: a one-line description of the value, no Args or Returns.

### Classes and dataclasses

Purpose, an **Attributes** section covering every field, and an **Example** of construction and use.

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

Doctests should pass: `python -m doctest -v module.py`. Mark an example that needs files or a network with `# doctest: +SKIP`.

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

## Tooling: ruff, zero tolerance

- `ruff check` reports nothing. `ruff format --check` reports nothing.
- Fix the cause of a finding rather than silencing it. A `# noqa` or `# type: ignore` needs a comment on the same line saying why the rule is wrong for that line.
- A project's own `[tool.ruff]` or `ruff.toml` wins. Start from [`ruff.toml`](ruff.toml), which selects pep8-naming and then ignores exactly the rules the [naming](#naming) section overrides (`N802`, `N803`, `N806`, `N815`, `N816`). Every other naming rule stays on.
- Anyone proposing code, a person or a coding agent, runs `ruff check` first and shows the clean output with the change.

---

## Checklist

- [ ] Python 3.11+ features; `from __future__ import annotations` first.
- [ ] Functions and methods named `subject_action`.
- [ ] Variables, parameters and fields in lowerCamelCase; classes PascalCase; constants UPPER_SNAKE_CASE.
- [ ] Type hints on every parameter and return, and on non-obvious locals; specific collection types; no `Any`.
- [ ] Non-primitive returns are a `dataclass` or a Pydantic model, never a bare dict or loose tuple.
- [ ] Functions refactored on nesting, responsibility, clarity and repetition, not on length.
- [ ] Named constants; one source of truth; specific types at interfaces.
- [ ] Imports grouped: `__future__`, standard library, third-party, local.
- [ ] Module docstring with purpose, key components, usage and dependencies.
- [ ] Every function and method: summary, Args, Returns, Raises, Example.
- [ ] Every class: purpose, Attributes, Example.
- [ ] Comments explain why, not what.
- [ ] `ruff check` and `ruff format --check` clean; doctests pass.
