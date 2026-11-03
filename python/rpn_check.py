"""Check that Python function names follow the style guide's RPN convention.

Ruff checks most of the style guide, but it cannot express the naming rule:
functions and methods are named ``<subject>[Qualifier]_<verb>[Adverb]``, with
lowerCamelCase halves, exactly one underscore, and a verb, not a preposition,
after it. This script checks that rule with the standard library's ``ast``,
using the same pattern as the TypeScript ESLint configuration in this
repository, so the two languages are held to one definition.

Key components:
    - Violation: one misnamed function, with its location and the reason.
    - functionName_check: judge one function definition.
    - violations_collect: walk one source file and judge every definition.
    - main: command-line entry point.

Typical usage:
    python rpn_check.py src/ tests/

Exemptions, all of them names a framework or the language dictates:
    - dunder methods (``__init__``, ``__repr__``);
    - methods decorated with ``@override``, from ``typing`` or
      ``typing_extensions`` (``setUp``, Django's ``get_queryset``);
    - pytest's ``test_*`` functions;
    - ``main``.
Properties are named like fields, as lowerCamelCase nouns.

Dependencies:
    Standard library only. Exits 0 when every name passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

PREPOSITIONS: str = "of|to|with|from|for|by|as|in|on|at"
RPN_PATTERN: re.Pattern[str] = re.compile(
    rf"^(?:main|[a-z][a-zA-Z0-9]*_(?!(?:{PREPOSITIONS})(?:[A-Z0-9]|$))[a-z][a-zA-Z0-9]*)$"
)
FIELD_PATTERN: re.Pattern[str] = re.compile(r"^[a-z][a-zA-Z0-9]*$")
EXEMPT_DECORATORS: frozenset[str] = frozenset({"override"})
PROPERTY_DECORATORS: frozenset[str] = frozenset({"property", "cached_property"})
PYTEST_PREFIX: str = "test_"
EXIT_CLEAN: int = 0
EXIT_VIOLATIONS: int = 1
DESCRIPTION: str = "Check that Python function names follow the RPN naming convention."
PREPOSITION_REASON: str = (
    "the part after the underscore is a preposition; name the verb (derive, parse, render)"
)

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class Violation:
    """One function whose name breaks the RPN convention.

    Attributes:
        path: Source file the function is defined in.
        lineNumber: One-based line of the ``def``.
        name: The function's name as written.
        reason: What is wrong with it, phrased for the person renaming it.

    Example:
        >>> Violation(Path("a.py"), 3, "getUser", "not subject_verb").report
        'a.py:3: getUser: not subject_verb'
    """

    path: Path
    lineNumber: int
    name: str
    reason: str

    @property
    def report(self) -> str:
        """One line in the ``path:line: name: reason`` form editors can jump to."""
        return f"{self.path}:{self.lineNumber}: {self.name}: {self.reason}"


def decoratorNames_get(node: FunctionNode) -> set[str]:
    r"""Collect the final names of a function's decorators.

    Args:
        node: A function or async function definition.

    Returns:
        Decorator names with any module prefix and call removed, so
        ``@typing.override`` and ``@functools.cached_property()`` give
        ``override`` and ``cached_property``. A setter such as
        ``@startTime.setter`` gives ``property``, because it belongs to one.

    Example:
        >>> tree = ast.parse("@typing.override\ndef f(): pass")
        >>> decoratorNames_get(tree.body[0])
        {'override'}
    """
    names: set[str] = set()
    for decorator in node.decorator_list:
        target: ast.expr = decorator.func if isinstance(decorator, ast.Call) else decorator
        match target:
            case ast.Attribute(attr="setter" | "deleter"):
                names.add("property")
            case ast.Attribute(attr=attr):
                names.add(attr)
            case ast.Name(id=identifier):
                names.add(identifier)
    return names


def functionName_check(node: FunctionNode) -> str | None:
    """Judge one function definition against the naming rule.

    Args:
        node: A function or async function definition.

    Returns:
        ``None`` if the name passes or is exempt, otherwise the reason it fails.

    Example:
        >>> functionName_check(ast.parse("def answerRows_of(): pass").body[0])
        'the part after the underscore is a preposition; name the verb (derive, parse, render)'
    """
    name: str = node.name
    decorators: set[str] = decoratorNames_get(node)
    isExempt: bool = (
        (name.startswith("__") and name.endswith("__"))
        or bool(decorators & EXEMPT_DECORATORS)
        or name.startswith(PYTEST_PREFIX)
    )
    if isExempt:
        return None
    publicName: str = name.removeprefix("_")
    if decorators & PROPERTY_DECORATORS:
        if FIELD_PATTERN.match(publicName):
            return None
        return "a property is named like a field: a lowerCamelCase noun"
    if RPN_PATTERN.match(publicName):
        return None
    verb: str = publicName.partition("_")[2]
    if re.match(rf"^(?:{PREPOSITIONS})(?:[A-Z0-9]|$)", verb):
        return (
            "the part after the underscore is a preposition; name the verb (derive, parse, render)"
        )
    return "expected <subject>_<verb>, lowerCamelCase halves, one underscore"


def violations_collect(path: Path) -> Iterator[Violation]:
    """Walk one source file and judge every function definition in it.

    Args:
        path: A Python source file.

    Returns:
        An iterator over the violations, in the order ``ast.walk`` visits them.

    Raises:
        SyntaxError: If the file does not parse.
        OSError: If the file cannot be read.

    Example:
        >>> list(violations_collect(Path("rpn_check.py")))  # doctest: +SKIP
        []
    """
    tree: ast.Module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, FunctionNode):
            reason: str | None = functionName_check(node)
            if reason is not None:
                yield Violation(path, node.lineno, node.name, reason)


def sources_find(roots: list[Path]) -> Iterator[Path]:
    """Expand files and directories into the Python files under them.

    Args:
        roots: Files and directories named on the command line.

    Returns:
        Each ``.py`` file once, files as given and directories searched
        recursively in sorted order.

    Example:
        >>> sorted(sources_find([Path("example")]))  # doctest: +SKIP
        [PosixPath('example/transcript.py')]
    """
    for root in roots:
        if root.is_dir():
            yield from sorted(root.rglob("*.py"))
        else:
            yield root


def main() -> int:
    """Check every Python file named on the command line.

    Returns:
        ``EXIT_CLEAN`` when every name passes, ``EXIT_VIOLATIONS`` otherwise.
        Violations are printed one per line to standard error.

    Example:
        >>> sys.argv = ["rpn_check.py", "example/"]  # doctest: +SKIP
        >>> main()  # doctest: +SKIP
        0
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("paths", nargs="+", type=Path, help="files or directories to check")
    arguments: argparse.Namespace = parser.parse_args()
    violations: list[Violation] = [
        violation
        for path in sources_find(arguments.paths)
        for violation in violations_collect(path)
    ]
    for violation in violations:
        print(violation.report, file=sys.stderr)
    return EXIT_VIOLATIONS if violations else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
