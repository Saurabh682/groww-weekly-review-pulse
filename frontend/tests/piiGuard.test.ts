import { describe, it, expect } from 'vitest';
import { hasPii, sanitizePii } from '../src/lib/piiGuard';

describe('piiGuard', () => {
  it('detects Indian phone numbers and emails', () => {
    expect(hasPii('Contact me at user@groww.in')).toBe(true);
    expect(hasPii('My mobile number is 9876543210')).toBe(true);
    expect(hasPii('Call +91 9123456789 for help')).toBe(true);
  });

  it('detects transaction IDs and order numbers', () => {
    expect(hasPii('Failed transaction ORD-847291 on app')).toBe(true);
    expect(hasPii('Reference UPI-9928172901 stuck')).toBe(true);
  });

  it('does NOT falsely flag currency, durations, versions, or dates', () => {
    expect(hasPii('Added ₹5,000 for mutual fund investment')).toBe(false);
    expect(hasPii('Waited 48 hours for KYC verification')).toBe(false);
    expect(hasPii('App version v14.2.0 is running smoothly')).toBe(false);
    expect(hasPii('Week of 09 Nov 2026 report')).toBe(false);
    expect(hasPii('Rating dropped by 2.4% this week')).toBe(false);
    expect(hasPii('UPI & Autopay Reconciliation Lag')).toBe(false);
  });

  it('sanitizes detected PII with redaction tokens', () => {
    const raw = 'User test@domain.com with phone 9876543210 reported issue on ORD-9921';
    const sanitized = sanitizePii(raw);
    expect(sanitized).toContain('[REDACTED_EMAIL]');
    expect(sanitized).toContain('[REDACTED_PHONE]');
    expect(sanitized).toContain('[REDACTED_ID]');
    expect(hasPii(sanitized)).toBe(false);
  });
});
