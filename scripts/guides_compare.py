"""Check that the language style guides in this repository share one outline.

The guides are kept in step: same sections in the same order, and the same
number of checklist items. A heading may differ after its first colon, where
a guide names a language-specific tool (``Documentation: JSDoc everywhere``
against ``Documentation: Google-style docstrings everywhere``); everything
before the colon must match.

Key components:
    - Outline: the comparable shape of one guide.
    - outline_read: extract an outline from a guide's Markdown.
    - outlines_compare: describe every difference between two outlines.
    - main: command-line entry point.

Typical usage:
    python scripts/guides_compare.py python/STYLE-GUIDE.md typescript/STYLE-GUIDE.md

Dependencies:
    Standard library only. Exits 0 when the outlines match, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path

HEADING_PATTERN: re.Pattern[str] = re.compile(r"^(#{2,3}) (.+)$")
CHECKLIST_PATTERN: re.Pattern[str] = re.compile(r"^- \[ \] ")
FENCE: str = "```"
EXIT_CLEAN: int = 0
EXIT_DIFFERENT: int = 1
DESCRIPTION: str = "Check that the style guides share one outline."


@dataclass(frozen=True)
class Outline:
    """The comparable shape of one guide.

    Attributes:
        path: The guide the outline was read from.
        headings: Level-two and level-three headings in order, each cut at its
            first colon, with its ``##`` or ``###`` prefix kept.
        checklistCount: Number of ``- [ ]`` items in the guide.

    Example:
        >>> Outline(Path("a.md"), ("## Naming",), 2).checklistCount
        2
    """

    path: Path
    headings: tuple[str, ...]
    checklistCount: int


def outline_read(path: Path) -> Outline:
    """Extract an outline from a guide's Markdown.

    Headings inside fenced code blocks are ignored, so a ``## `` line in an
    example does not count as a section.

    Args:
        path: A style guide in Markdown.

    Returns:
        The guide's outline.

    Raises:
        OSError: If the file cannot be read.

    Example:
        >>> outline_read(Path("python/STYLE-GUIDE.md")).headings[0]  # doctest: +SKIP
        '## Language version and configuration'
    """
    headings: list[str] = []
    checklistCount: int = 0
    inFence: bool = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(FENCE):
            inFence = not inFence
            continue
        if inFence:
            continue
        heading: re.Match[str] | None = HEADING_PATTERN.match(line)
        if heading is not None:
            headings.append(f"{heading.group(1)} {heading.group(2).split(':')[0]}")
        elif CHECKLIST_PATTERN.match(line):
            checklistCount += 1
    return Outline(path=path, headings=tuple(headings), checklistCount=checklistCount)


def outlines_compare(first: Outline, second: Outline) -> list[str]:
    """Describe every difference between two outlines.

    Args:
        first: Outline of one guide.
        second: Outline of the other.

    Returns:
        One line per difference, empty when the outlines match.

    Example:
        >>> a = Outline(Path("a.md"), ("## Naming", "## Imports"), 3)
        >>> b = Outline(Path("b.md"), ("## Naming", "## Tooling"), 4)
        >>> for difference in outlines_compare(a, b):
        ...     print(difference)
        heading 2: a.md has '## Imports', b.md has '## Tooling'
        checklist: a.md has 3 items, b.md has 4
    """
    differences: list[str] = []
    for index, (left, right) in enumerate(
        zip_longest(first.headings, second.headings, fillvalue="(none)"), start=1
    ):
        if left != right:
            differences.append(
                f"heading {index}: {first.path} has {left!r}, {second.path} has {right!r}"
            )
    if first.checklistCount != second.checklistCount:
        differences.append(
            f"checklist: {first.path} has {first.checklistCount} items, "
            f"{second.path} has {second.checklistCount}"
        )
    return differences


def main() -> int:
    """Compare the outlines of the guides named on the command line.

    Every guide is compared with the first one named.

    Returns:
        ``EXIT_CLEAN`` when every outline matches the first, ``EXIT_DIFFERENT``
        otherwise. Differences are printed one per line to standard error.

    Example:
        >>> sys.argv = ["guides_compare.py", "python/STYLE-GUIDE.md"]  # doctest: +SKIP
        >>> main()  # doctest: +SKIP
        0
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("guides", nargs="+", type=Path, help="style guides to compare")
    arguments: argparse.Namespace = parser.parse_args()
    outlines: list[Outline] = [outline_read(path) for path in arguments.guides]
    differences: list[str] = [
        difference
        for outline in outlines[1:]
        for difference in outlines_compare(outlines[0], outline)
    ]
    for difference in differences:
        print(difference, file=sys.stderr)
    return EXIT_DIFFERENT if differences else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
