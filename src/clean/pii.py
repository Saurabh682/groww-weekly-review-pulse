"""PII detection and scrubbing for Groww Weekly Review Pulse.

Implements all detection and redaction rules from docs/edge-case.md §5:
- Emails (standard & obfuscated)
- Indian and international phone numbers (including spaced/dotted variants)
- PAN-like and Aadhaar-like numbers
- UPI IDs
- Account, order, transaction, folio, and ticket numbers
- URLs and social @handles
- Sign-offs and self-introductions
- IMEI, MAC addresses, UUIDs, DOB, address-like PIN codes
- Preserves durations, currency amounts, versions, ratings, percentages, brand words (PIIN-01..08)
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Tuple

# Devanagari to ASCII digit translation table
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


@dataclass
class ScrubResult:
    cleaned_text: str
    pii_found: bool
    quote_eligible: bool
    redaction_count: int


def normalize_unicode_digits(text: str) -> str:
    """Normalize fullwidth characters and Devanagari digits to standard ASCII (PII-18, NRM-02)."""
    # NFKC normalizes fullwidth characters (e.g., ９ -> 9) and decomposes compatibility chars
    normalized = unicodedata.normalize("NFKC", text)
    # Translate Devanagari digits
    return normalized.translate(DEVANAGARI_DIGITS)


# ----------------------------------------------------------------------
# Regex Patterns
# ----------------------------------------------------------------------

# 1. Standard and obfuscated emails (PII-01, PII-02)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE
)
OBFUSCATED_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+\s*(?:@|\(at\)|\[at\]|\bat\b)\s*[A-Za-z0-9.-]+\s*(?:\.|\(dot\)|\[dot\]|\bdot\b)\s*(?:com|in|org|net|co|io|edu|gov)\b",
    re.IGNORECASE
)

# 2. UPI IDs (PII-07)
UPI_PATTERN = re.compile(
    r"\b[a-zA-Z0-9.\-_]{2,256}@(okhdfcbank|okaxis|oksbi|okicici|paytm|ybl|ibl|upi|axl|apl|sbi|hdfcbank|icici|kotak|barodampay)\b",
    re.IGNORECASE
)

# 3. PAN card format: 5 letters + 4 digits + 1 letter (PII-06)
PAN_PATTERN = re.compile(
    r"\b[A-Za-z]{5}[-\s]?[0-9]{4}[-\s]?[A-Za-z]{1}\b"
)

# 4. Aadhaar format: 12 digits (with optional spaces or dashes in 4-4-4 format) (PII-08)
AADHAAR_PATTERN = re.compile(
    r"\b[2-9]{1}[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b"
)

# 5. Phone numbers:
# Indian (+91, 0, 10-digit starting with 6-9, spaced or dotted) (PII-03, PII-05)
INDIAN_PHONE_PATTERN = re.compile(
    r"(?:(?:\+91|0091|0)[\s\-]?)?(?:[6-9][\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d[\s\.\-]?\d)\b"
)

# International phone numbers (+1..., 0044...) (PII-04)
INTL_PHONE_PATTERN = re.compile(
    r"(?:\+|00)[1-9]\d{0,3}[\s\-]?(?:\(\d{1,4}\)[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}\b"
)

# 6. URLs and @handles (PII-10, PII-11)
URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)[^\s/$.?#].[^\s]*",
    re.IGNORECASE
)
HANDLE_PATTERN = re.compile(
    r"(?<!\w)@[A-Za-z0-9_]{3,25}\b"
)

# 7. Device IDs, IMEI (15 digits), MAC, UUID (PII-14)
UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
IMEI_PATTERN = re.compile(
    r"\b\d{15}\b"
)
MAC_PATTERN = re.compile(
    r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b"
)

# 8. Keyword-proximate IDs (order, txn, folio, ticket, account ending NNNN, OTP values) (PII-09, PII-15, PIIN-08)
KEYWORD_ID_PATTERN = re.compile(
    r"\b(?:order(?:\s*id)?|txn(?:\s*no|\s*id)?|transaction(?:\s*id)?|folio(?:\s*no)?|account(?:\s*no)?|ticket(?:\s*#|\s*no)?|ref(?:\s*no)?)\s*[:#\-]?\s*((?=[A-Za-z0-9/\-]*\d)[A-Za-z0-9/\-]{4,30})\b",
    re.IGNORECASE
)
ACCOUNT_ENDING_PATTERN = re.compile(
    r"\b(?:account|card|acct)\s+ending\s+(?:in\s+)?([0-9]{4})\b",
    re.IGNORECASE
)
OTP_VALUE_PATTERN = re.compile(
    r"\b(?:otp|one\s*time\s*password)\s*(?:is|was|:|#|-)?\s*([0-9]{4,8})\b",
    re.IGNORECASE
)

# 9. Date of birth (PII-16)
DOB_PATTERN = re.compile(
    r"\b(?:dob|born\s+on|date\s+of\s+birth)\s*[:\-]?\s*(\d{1,2}[\s/\-](?:\d{1,2}|[A-Za-z]+)[\s/\-]\d{2,4})\b",
    re.IGNORECASE
)

# 10. Sign-off names & self-introductions (PII-12, PII-13)
SIGNOFF_PATTERN = re.compile(
    r"(?:(?:\b(?:regards|thanks|thank\s+you|yours\s+truly|cheers|sincerely)\b[\s,:\-]*)|(?:^|\n|[.!?])[ \t]*[-–—][ \t]*)([A-Z][a-z]+(?:\s+[A-Z][a-z\.]*)*)[ \t]*$",
    re.IGNORECASE | re.MULTILINE
)
SELF_INTRO_PATTERN = re.compile(
    r"\b(?:my\s+name\s+is|i\s+am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
    re.IGNORECASE
)

# 11. Address-like with PIN code (PII-17)
ADDRESS_PIN_PATTERN = re.compile(
    r"\b(?:flat|house|road|nagar|street|colony|sector|lane)[\w\s,.-]+?\b([1-9][0-9]{5})\b",
    re.IGNORECASE
)


def scrub_pii(text: str, is_title: bool = False) -> ScrubResult:
    """Scan text for PII patterns and replace with [REDACTED].
    
    Sets quote_eligible=False whenever PII is redacted or sign-off/self-intro is detected.
    Protects safe tokens (PIIN-01..08) from over-redaction.
    """
    if not text:
        return ScrubResult(cleaned_text="", pii_found=False, quote_eligible=True, redaction_count=0)

    # 1. Normalize unicode digits and forms first (PII-18)
    scrubbed = normalize_unicode_digits(text)
    pii_found = False
    quote_eligible = True
    redaction_count = 0

    def replace_token(match: re.Match) -> str:
        nonlocal pii_found, redaction_count
        pii_found = True
        redaction_count += 1
        return "[REDACTED]"

    # Order of redactions:
    # A. Obfuscated and standard emails
    if OBFUSCATED_EMAIL_PATTERN.search(scrubbed):
        scrubbed = OBFUSCATED_EMAIL_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    if EMAIL_PATTERN.search(scrubbed):
        scrubbed = EMAIL_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # B. UPI IDs
    if UPI_PATTERN.search(scrubbed):
        scrubbed = UPI_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # C. URLs and @handles
    if URL_PATTERN.search(scrubbed):
        scrubbed = URL_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    if HANDLE_PATTERN.search(scrubbed):
        scrubbed = HANDLE_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # D. PAN numbers
    if PAN_PATTERN.search(scrubbed):
        scrubbed = PAN_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # E. Aadhaar numbers
    if AADHAAR_PATTERN.search(scrubbed):
        scrubbed = AADHAAR_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # F. UUIDs, IMEI, MAC
    if UUID_PATTERN.search(scrubbed):
        scrubbed = UUID_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    if IMEI_PATTERN.search(scrubbed):
        scrubbed = IMEI_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    if MAC_PATTERN.search(scrubbed):
        scrubbed = MAC_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # G. Keyword-proximate IDs
    def replace_keyword_group(m: re.Match) -> str:
        nonlocal pii_found, quote_eligible, redaction_count
        full = m.group(0)
        target = m.group(1)
        # Avoid redacting small numbers like "order took 2 days"
        if len(target) >= 4:
            pii_found = True
            quote_eligible = False
            redaction_count += 1
            return full.replace(target, "[REDACTED]")
        return full

    scrubbed = KEYWORD_ID_PATTERN.sub(replace_keyword_group, scrubbed)

    def replace_account_ending(m: re.Match) -> str:
        nonlocal pii_found, quote_eligible, redaction_count
        full = m.group(0)
        target = m.group(1)
        pii_found = True
        quote_eligible = False
        redaction_count += 1
        return full.replace(target, "[REDACTED]")

    scrubbed = ACCOUNT_ENDING_PATTERN.sub(replace_account_ending, scrubbed)

    # OTP value redaction
    def replace_otp_value(m: re.Match) -> str:
        nonlocal pii_found, quote_eligible, redaction_count
        full = m.group(0)
        target = m.group(1)
        pii_found = True
        quote_eligible = False
        redaction_count += 1
        return full.replace(target, "[REDACTED]")

    scrubbed = OTP_VALUE_PATTERN.sub(replace_otp_value, scrubbed)

    # H. DOB & Address PIN codes
    if DOB_PATTERN.search(scrubbed):
        scrubbed = DOB_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    if ADDRESS_PIN_PATTERN.search(scrubbed):
        scrubbed = ADDRESS_PIN_PATTERN.sub(replace_token, scrubbed)
        quote_eligible = False

    # I. Phone numbers (Indian & International)
    # Check phone after keyword/currency guards
    # We must ensure currency amounts like "₹5000", "Rs. 25,000", and versions like "14.3.0" are NOT matched as phones
    # Phone matcher requires >= 10 digits
    if INDIAN_PHONE_PATTERN.search(scrubbed):
        # Verify match has at least 10 digits
        def replace_phone(m: re.Match) -> str:
            nonlocal pii_found, quote_eligible, redaction_count
            digits = re.sub(r"\D", "", m.group(0))
            if len(digits) >= 10:
                pii_found = True
                quote_eligible = False
                redaction_count += 1
                return "[REDACTED]"
            return m.group(0)

        scrubbed = INDIAN_PHONE_PATTERN.sub(replace_phone, scrubbed)

    if INTL_PHONE_PATTERN.search(scrubbed):
        def replace_intl_phone(m: re.Match) -> str:
            nonlocal pii_found, quote_eligible, redaction_count
            digits = re.sub(r"\D", "", m.group(0))
            if len(digits) >= 10:
                pii_found = True
                quote_eligible = False
                redaction_count += 1
                return "[REDACTED]"
            return m.group(0)

        scrubbed = INTL_PHONE_PATTERN.sub(replace_intl_phone, scrubbed)

    # J. Sign-offs and self-introductions (PII-12, PII-13)
    def replace_signoff(m: re.Match) -> str:
        nonlocal pii_found, quote_eligible, redaction_count
        name = m.group(1).strip()
        # Ensure brand/app words are not treated as names
        safe_words = {"groww", "nifty", "bse", "nse", "sensex", "app", "team"}
        if name.lower() not in safe_words:
            pii_found = True
            quote_eligible = False
            redaction_count += 1
            return m.group(0).replace(name, "[REDACTED]")
        return m.group(0)

    scrubbed = SIGNOFF_PATTERN.sub(replace_signoff, scrubbed)

    def replace_self_intro(m: re.Match) -> str:
        nonlocal pii_found, quote_eligible, redaction_count
        name = m.group(1).strip()
        safe_words = {"groww", "a user", "a beginner", "an investor", "trader"}
        if name.lower() not in safe_words:
            pii_found = True
            quote_eligible = False
            redaction_count += 1
            return m.group(0).replace(name, "[REDACTED]")
        return m.group(0)

    scrubbed = SELF_INTRO_PATTERN.sub(replace_self_intro, scrubbed)

    # If the review already literally contained "[REDACTED]", mark quote_ineligible (PII-36, PII-37)
    if "[REDACTED]" in scrubbed:
        quote_eligible = False

    return ScrubResult(
        cleaned_text=scrubbed.strip(),
        pii_found=pii_found,
        quote_eligible=quote_eligible,
        redaction_count=redaction_count,
    )
