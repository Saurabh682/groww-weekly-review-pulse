import { describe, it, expect } from 'vitest';
import { assertPulseInvariants } from '../src/lib/validators';
import { FIXTURE_PULSE_NOTE } from '../src/data/fixtures/pulseNote';

describe('validators - assertPulseInvariants', () => {
  it('passes on valid standard fixture note', () => {
    const result = assertPulseInvariants(FIXTURE_PULSE_NOTE);
    expect(result.passed).toBe(true);
    expect(result.failures).toHaveLength(0);
    expect(result.checks.every((c) => c.passed)).toBe(true);
  });

  it('fails if topThemes count is not exactly 3', () => {
    const invalidNote = {
      ...FIXTURE_PULSE_NOTE,
      topThemes: FIXTURE_PULSE_NOTE.topThemes.slice(0, 2),
    };
    const result = assertPulseInvariants(invalidNote);
    expect(result.passed).toBe(false);
    expect(result.failures).toContain('Expected exactly 3 top themes, found 2');
  });

  it('fails if quotes count is not 3 or not verbatim', () => {
    const invalidNote = {
      ...FIXTURE_PULSE_NOTE,
      quotes: [
        { ...FIXTURE_PULSE_NOTE.quotes[0], verifiedVerbatim: false },
        FIXTURE_PULSE_NOTE.quotes[1],
        FIXTURE_PULSE_NOTE.quotes[2],
      ],
    };
    const result = assertPulseInvariants(invalidNote);
    expect(result.passed).toBe(false);
    expect(result.failures).toContain('All quotes must be verified verbatim from user reviews');
  });

  it('fails if word count exceeds 250 words limit', () => {
    const invalidNote = {
      ...FIXTURE_PULSE_NOTE,
      wordCount: 284,
    };
    const result = assertPulseInvariants(invalidNote);
    expect(result.passed).toBe(false);
    expect(result.failures.some((f) => f.includes('exceeds 250 words'))).toBe(true);
  });

  it('fails if PII is injected into quotes or themes', () => {
    const invalidNote = {
      ...FIXTURE_PULSE_NOTE,
      quotes: [
        { ...FIXTURE_PULSE_NOTE.quotes[0], text: 'Call me at 9876543210 immediately!' },
        FIXTURE_PULSE_NOTE.quotes[1],
        FIXTURE_PULSE_NOTE.quotes[2],
      ],
    };
    const result = assertPulseInvariants(invalidNote);
    expect(result.passed).toBe(false);
    expect(result.failures).toContain('PII or personal data detected in note content');
  });
});
