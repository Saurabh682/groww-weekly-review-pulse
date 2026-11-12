/**
 * Client-side PII sanitizer and validator.
 * Prevents rendering reviewer personal info.
 */

// Regex patterns (WITHOUT global flag for testing, WITH global flag for replacement)
const EMAIL_PATTERN = '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}';
const PHONE_PATTERN = '(?:(?:\\+|0{0,2})91[\\s.-]?)?[6-9]\\d{4}[\\s.-]?\\d{5}\\b';

// Transaction / Order IDs must have a prefix followed by delimiter or digits (e.g. ORD-12345, TXN_98765, UPI:123456)
// Requires at least one digit so words like "UPI Autopay" or "Account opening" are never flagged
const TXN_ID_PATTERN = '\\b(?:ORD|TXN|UPI|REF|CRN|ACCT|A\\/C)[-_:#]?(?=[A-Za-z0-9]*\\d)[A-Za-z0-9]{4,24}\\b';

// Long account numbers: 11 to 18 digits (excluding currency like ₹50,000 or version v12.4.0)
const LONG_DIGITS_PATTERN = '\\b(?!\\b₹|\\bRs\\.?|\\bv|\\bver)\\d{11,18}\\b';

export function hasPii(text: string): boolean {
  if (!text || typeof text !== 'string') return false;
  
  if (new RegExp(EMAIL_PATTERN, 'i').test(text)) return true;
  if (new RegExp(PHONE_PATTERN).test(text)) return true;
  if (new RegExp(TXN_ID_PATTERN, 'i').test(text)) return true;
  if (new RegExp(LONG_DIGITS_PATTERN).test(text)) return true;
  
  return false;
}

export function sanitizePii(text: string): string {
  if (!text || typeof text !== 'string') return text;
  return text
    .replace(new RegExp(EMAIL_PATTERN, 'gi'), '[REDACTED_EMAIL]')
    .replace(new RegExp(PHONE_PATTERN, 'g'), '[REDACTED_PHONE]')
    .replace(new RegExp(TXN_ID_PATTERN, 'gi'), '[REDACTED_ID]')
    .replace(new RegExp(LONG_DIGITS_PATTERN, 'g'), '[REDACTED_ACCOUNT]');
}
