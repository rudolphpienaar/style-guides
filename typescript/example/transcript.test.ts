/**
 * @file Tests for the reference module: the JSDoc examples, run.
 *
 * Mirrors the doctests in python/example/transcript.py, so both reference
 * modules are held to the same behaviour.
 *
 * @module
 */

import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

import {
    Paragraph,
    paragraphs_build,
    type Segment,
    segments_load,
    timestamp_format,
    transcript_render,
} from './transcript.ts';

const SEGMENTS: Segment[] = [
    { startTime: 0.0, endTime: 1.0, text: 'One.' },
    { startTime: 1.5, endTime: 2.0, text: 'Two.' },
    { startTime: 9.0, endTime: 10.0, text: 'Three.' },
];

void test('appending a segment extends the paragraph', (): void => {
    const paragraph: Paragraph = new Paragraph({ startTime: 0.0, endTime: 1.0, text: 'One.' });
    paragraph.segment_append({ startTime: 1.5, endTime: 2.0, text: 'Two.' });
    assert.equal(paragraph.text, 'One. Two.');
});

void test('a paragraph starts at its first segment', (): void => {
    const paragraph: Paragraph = new Paragraph({ startTime: 0.0, endTime: 2.5, text: 'Good morning.' });
    assert.equal(paragraph.startTime, 0.0);
});

void test('segments within the gap limit share a paragraph', (): void => {
    const texts: string[] = paragraphs_build(SEGMENTS).map((paragraph: Paragraph): string => paragraph.text);
    assert.deepEqual(texts, ['One. Two.', 'Three.']);
});

void test('a negative gap limit is refused', (): void => {
    assert.throws((): Paragraph[] => paragraphs_build(SEGMENTS, -1), RangeError);
});

void test('timestamps truncate to whole seconds', (): void => {
    assert.equal(timestamp_format(3725.9), '01:02:05');
});

void test('paragraphs render with a leading timestamp', (): void => {
    const rendered: string = transcript_render(
        paragraphs_build([{ startTime: 61.0, endTime: 63.0, text: 'Hello.' }]),
    );
    assert.equal(rendered, '[00:01:01] Hello.');
});

void test('segments load from JSON and text is stripped', (): void => {
    const directory: string = mkdtempSync(join(tmpdir(), 'transcript-'));
    try {
        const path: string = join(directory, 'meeting.json');
        writeFileSync(path, JSON.stringify([{ start: 0.0, end: 2.5, text: ' Good morning. ' }]));
        assert.deepEqual(segments_load(path), [{ startTime: 0.0, endTime: 2.5, text: 'Good morning.' }]);
    } finally {
        rmSync(directory, { recursive: true, force: true });
    }
});
