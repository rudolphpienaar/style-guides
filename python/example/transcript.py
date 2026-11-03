"""Merge timed transcript segments into readable paragraphs.

Speech-to-text engines such as Whisper emit short timed segments. This module
groups consecutive segments into paragraphs wherever the silence between them
is shorter than a threshold, and renders the result as plain text with a
timestamp at the start of each paragraph.

It exists as the complete, ruff-clean reference for the Python style guide in
this repository: every rule in the guide is applied here at full strength.

Key components:
    - Segment: one timed span of recognised speech.
    - Paragraph: consecutive segments merged into one block.
    - segments_load: read segments from a JSON file.
    - paragraphs_build: group segments into paragraphs by silence gap.
    - timestamp_format: format a second offset as HH:MM:SS.
    - transcript_render: render paragraphs as timestamped plain text.

Typical usage:
    segments = segments_load(Path("meeting.json"))
    paragraphs = paragraphs_build(segments, gapLimit=PARAGRAPH_GAP_SECONDS)
    print(transcript_render(paragraphs))

Dependencies:
    Standard library only. Input JSON is a list of objects with ``start`` and
    ``end`` (seconds, number) and ``text`` (string) keys.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

PARAGRAPH_GAP_SECONDS: float = 2.0
SECONDS_PER_HOUR: int = 3_600
SECONDS_PER_MINUTE: int = 60
PARAGRAPH_SEPARATOR: str = "\n\n"


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


@dataclass
class Paragraph:
    """Consecutive segments merged into one block of text.

    Attributes:
        segments: Member segments in time order. Never empty once built by
            ``paragraphs_build``.

    Example:
        >>> paragraph = Paragraph(segments=[Segment(0.0, 2.5, "Good morning.")])
        >>> paragraph.startTime
        0.0
    """

    segments: list[Segment] = field(default_factory=list)

    @property
    def startTime(self) -> float:
        """Start of the first member segment, in seconds."""
        return self.segments[0].startTime

    @property
    def text(self) -> str:
        """Member segment texts joined by single spaces."""
        return " ".join(segment.text for segment in self.segments)


def segments_load(path: Path) -> list[Segment]:
    """Read timed segments from a JSON file.

    Args:
        path: JSON file holding a list of objects with ``start``, ``end`` and
            ``text`` keys, as written by the transcription step.

    Returns:
        Segments in file order, with text stripped of surrounding whitespace.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If an entry lacks ``start``, ``end`` or ``text``.

    Example:
        >>> segments = segments_load(Path("meeting.json"))  # doctest: +SKIP
        >>> segments[0].text  # doctest: +SKIP
        'Good morning.'
    """
    rawEntries: list[dict[str, float | str]] = json.loads(path.read_text(encoding="utf-8"))
    return [
        Segment(
            startTime=float(entry["start"]),
            endTime=float(entry["end"]),
            text=str(entry["text"]).strip(),
        )
        for entry in rawEntries
    ]


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
    if gapLimit < 0:
        raise ValueError(f"gapLimit must be non-negative, got {gapLimit}")
    paragraphs: list[Paragraph] = []
    previousEnd: float | None = None
    for segment in segments:
        startsParagraph: bool = previousEnd is None or segment.startTime - previousEnd > gapLimit
        if startsParagraph:
            paragraphs.append(Paragraph())
        paragraphs[-1].segments.append(segment)
        previousEnd = segment.endTime
    return paragraphs


def timestamp_format(seconds: float) -> str:
    """Format an offset in seconds as ``HH:MM:SS``.

    Fractions of a second are truncated, not rounded, so a timestamp never
    points past the start of the speech it labels.

    Args:
        seconds: Non-negative offset from the start of the recording.

    Returns:
        Zero-padded ``HH:MM:SS`` string. Hours grow past two digits if needed.

    Example:
        >>> timestamp_format(3725.9)
        '01:02:05'
    """
    wholeSeconds: int = int(seconds)
    hours, remainder = divmod(wholeSeconds, SECONDS_PER_HOUR)
    minutes, secondsPart = divmod(remainder, SECONDS_PER_MINUTE)
    return f"{hours:02d}:{minutes:02d}:{secondsPart:02d}"


def transcript_render(paragraphs: list[Paragraph]) -> str:
    """Render paragraphs as plain text with a leading timestamp on each.

    Args:
        paragraphs: Paragraphs in time order, each with at least one segment.

    Returns:
        One block per paragraph, ``[HH:MM:SS] text``, separated by a blank line.
        Empty string if ``paragraphs`` is empty.

    Example:
        >>> paragraphs = paragraphs_build([Segment(61.0, 63.0, "Hello.")])
        >>> transcript_render(paragraphs)
        '[00:01:01] Hello.'
    """
    blocks: list[str] = [
        f"[{timestamp_format(paragraph.startTime)}] {paragraph.text}" for paragraph in paragraphs
    ]
    return PARAGRAPH_SEPARATOR.join(blocks)
