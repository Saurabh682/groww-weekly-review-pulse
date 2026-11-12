"""Language detection and quote-eligibility rules (LNG-01..04)."""

import re
from dataclasses import dataclass

DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Common Roman-script Hindi / Hinglish keywords
HINGLISH_KEYWORDS = {
    "paisa", "paise", "rupaye", "rupees", "nahi", "nhi", "kya", "kyu", "kyun",
    "karo", "kare", "hai", "hain", "mera", "meri", "mere", "tha", "thi",
    "bhi", "accha", "bahut", "bekar", "bakwas", "chod", "mat", "kuch",
    "ho", "raha", "rahi", "gaya", "gayi", "kaise", "apna", "apni", "pehle"
}


@dataclass
class LangResult:
    lang: str
    quote_eligible: bool


def detect_language(text: str) -> LangResult:
    """Detect language of review and determine quote eligibility.
    
    Default rule: Only 'en' reviews are eligible for verbatim quotes.
    """
    if not text or not text.strip():
        return LangResult(lang="unknown", quote_eligible=False)

    # 1. Check for Devanagari script (LNG-01)
    devanagari_chars = len(DEVANAGARI_REGEX.findall(text))
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha > 0 and (devanagari_chars / total_alpha) > 0.3:
        return LangResult(lang="hi", quote_eligible=False)

    # 2. Tokenize words for Hinglish detection (LNG-02, LNG-04)
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
    if not words:
        return LangResult(lang="unknown", quote_eligible=False)

    hinglish_matches = sum(1 for w in words if w in HINGLISH_KEYWORDS)
    hinglish_ratio = hinglish_matches / len(words)

    # If significant Hinglish keywords detected
    if hinglish_ratio >= 0.25 or (hinglish_matches >= 2 and len(words) <= 10):
        return LangResult(lang="mixed", quote_eligible=False)

    # If mostly latin characters
    if len(words) >= 3:
        return LangResult(lang="en", quote_eligible=True)

    # Very short single words or uncertain text (LNG-03)
    if len(words) < 2 and devanagari_chars == 0:
        return LangResult(lang="unknown", quote_eligible=False)

    return LangResult(lang="en", quote_eligible=True)
