/**
 * @file Merge timed transcript segments into readable paragraphs.
 *
 * Speech-to-text engines such as Whisper emit short timed segments. This module
 * groups consecutive segments into paragraphs wherever the silence between them
 * is shorter than a threshold, and renders the result as plain text with a
 * timestamp at the start of each paragraph.
 *
 * It exists as the complete, lint-clean reference for the TypeScript style
 * guide in this repository, and mirrors python/example/transcript.py line for
 * line in what it does.
 *
 * Key components:
 * - Segment: one timed span of recognised speech.
 * - Paragraph: consecutive segments merged into one block.
 * - segments_load: read segments from a JSON file.
 * - paragraphs_build: group segments into paragraphs by silence gap.
 * - timestamp_format: format a second offset as HH:MM:SS.
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

import { readFileSync } from 'node:fs';

/** Longest silence, in seconds, that still joins two segments into one paragraph. */
export const PARAGRAPH_GAP_SECONDS: number = 2.0;
const SECONDS_PER_HOUR: number = 3_600;
const SECONDS_PER_MINUTE: number = 60;
const PARAGRAPH_SEPARATOR: string = '\n\n';

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

/**
 * Consecutive segments merged into one block of text.
 *
 * A paragraph always holds at least one segment: it is created from its first.
 *
 * @example
 * ```ts
 * const paragraph: Paragraph = new Paragraph({ startTime: 0.0, endTime: 2.5, text: 'Good morning.' });
 * paragraph.startTime; // 0
 * ```
 */
export class Paragraph {
    /** Member segments in time order; never empty. */
    readonly segments: Segment[];

    /**
     * Create a paragraph from its first segment.
     *
     * @param first - The segment that opens the paragraph.
     */
    constructor(first: Segment) {
        this.segments = [first];
    }

    /** Start of the first member segment, in seconds. */
    get startTime(): number {
        return this.segmentFirst.startTime;
    }

    /** End of the last member segment, in seconds. */
    get endTime(): number {
        return this.segmentLast.endTime;
    }

    /** Member segment texts joined by single spaces. */
    get text(): string {
        return this.segments.map((segment: Segment): string => segment.text).join(' ');
    }

    /**
     * Append a segment to the end of the paragraph.
     *
     * @param segment - Segment that follows the current last one in time.
     */
    segment_append(segment: Segment): void {
        this.segments.push(segment);
    }

    private get segmentFirst(): Segment {
        return this.segments[0] ?? paragraphEmpty_throw();
    }

    private get segmentLast(): Segment {
        return this.segments.at(-1) ?? paragraphEmpty_throw();
    }
}

/**
 * Report a paragraph that has lost its segments, which the constructor rules out.
 *
 * @throws {Error} Always.
 */
function paragraphEmpty_throw(): never {
    throw new Error('Paragraph has no segments');
}

/**
 * Validate one parsed JSON entry and convert it to a segment.
 *
 * @param entry - One element of the parsed JSON array.
 * @returns The segment, with text stripped of surrounding whitespace.
 * @throws {TypeError} If the entry lacks a numeric `start` or `end` or a string `text`.
 */
function segment_parse(entry: unknown): Segment {
    if (typeof entry !== 'object' || entry === null) {
        throw new TypeError('segment entry is not an object');
    }
    const start: unknown = 'start' in entry ? entry.start : undefined;
    const end: unknown = 'end' in entry ? entry.end : undefined;
    const text: unknown = 'text' in entry ? entry.text : undefined;
    if (typeof start !== 'number' || typeof end !== 'number' || typeof text !== 'string') {
        throw new TypeError('segment entry needs numeric start and end and string text');
    }
    return { startTime: start, endTime: end, text: text.trim() };
}

/**
 * Read timed segments from a JSON file.
 *
 * @param path - JSON file holding an array of objects with `start`, `end` and
 *   `text` keys, as written by the transcription step.
 * @returns Segments in file order, with text stripped of surrounding whitespace.
 * @throws {Error} If the file cannot be read (ENOENT and similar).
 * @throws {SyntaxError} If the file is not valid JSON.
 * @throws {TypeError} If the JSON is not an array, or an entry is malformed.
 *
 * @example
 * ```ts
 * const segments: Segment[] = segments_load('meeting.json');
 * segments[0]?.text; // 'Good morning.'
 * ```
 */
export function segments_load(path: string): Segment[] {
    const parsed: unknown = JSON.parse(readFileSync(path, 'utf8'));
    if (!Array.isArray(parsed)) {
        throw new TypeError(`${path}: expected a JSON array of segments`);
    }
    return parsed.map((entry: unknown): Segment => segment_parse(entry));
}

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
export function paragraphs_build(
    segments: readonly Segment[],
    gapLimit: number = PARAGRAPH_GAP_SECONDS,
): Paragraph[] {
    if (gapLimit < 0) {
        throw new RangeError(`gapLimit must be non-negative, got ${String(gapLimit)}`);
    }
    const paragraphs: Paragraph[] = [];
    let current: Paragraph | null = null;
    for (const segment of segments) {
        if (current === null || segment.startTime - current.endTime > gapLimit) {
            current = new Paragraph(segment);
            paragraphs.push(current);
        } else {
            current.segment_append(segment);
        }
    }
    return paragraphs;
}

/**
 * Format an offset in seconds as `HH:MM:SS`.
 *
 * Fractions of a second are truncated, not rounded, so a timestamp never
 * points past the start of the speech it labels.
 *
 * @param seconds - Non-negative offset from the start of the recording.
 * @returns Zero-padded `HH:MM:SS` string. Hours grow past two digits if needed.
 *
 * @example
 * ```ts
 * timestamp_format(3725.9); // '01:02:05'
 * ```
 */
export function timestamp_format(seconds: number): string {
    const wholeSeconds: number = Math.trunc(seconds);
    const hours: number = Math.trunc(wholeSeconds / SECONDS_PER_HOUR);
    const minutes: number = Math.trunc((wholeSeconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
    const secondsPart: number = wholeSeconds % SECONDS_PER_MINUTE;
    return [hours, minutes, secondsPart]
        .map((part: number): string => String(part).padStart(2, '0'))
        .join(':');
}

/**
 * Render paragraphs as plain text with a leading timestamp on each.
 *
 * @param paragraphs - Paragraphs in time order.
 * @returns One block per paragraph, `[HH:MM:SS] text`, separated by a blank
 *   line. Empty string if `paragraphs` is empty.
 *
 * @example
 * ```ts
 * transcript_render(paragraphs_build([{ startTime: 61.0, endTime: 63.0, text: 'Hello.' }]));
 * // '[00:01:01] Hello.'
 * ```
 */
export function transcript_render(paragraphs: readonly Paragraph[]): string {
    return paragraphs
        .map((paragraph: Paragraph): string => `[${timestamp_format(paragraph.startTime)}] ${paragraph.text}`)
        .join(PARAGRAPH_SEPARATOR);
}
