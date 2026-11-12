"""Shared canonical word counting function for Groww Weekly Review Pulse (VAL-07, NOT-04, NOT-05)."""

import re


def strip_markdown(text: str) -> str:
    """Strip Markdown syntax so formatting markers do not inflate word counts (NOT-05)."""
    # Remove horizontal rules
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Remove header markers (# Title -> Title)
    text = re.sub(r"^\s*#+\s+", "", text, flags=re.MULTILINE)
    # Remove list bullet and number prefixes (- item -> item, 1. item -> item)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Remove blockquotes (> quote -> quote)
    text = re.sub(r"^\s*>\s+", "", text, flags=re.MULTILINE)
    # Replace markdown links [text](url) with text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove inline code backticks
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Replace table pipes, bullet symbols, em-dashes with spaces
    text = re.sub(r"[|•—–]", " ", text)
    return text


def count_note_words(text: str) -> int:
    """Canonical word counter for rendered notes and components.
    
    Handles:
    - Currency and decimals: '₹5,000', '4.5★' as 1 word
    - Hyphenated and compound terms: 'UPI/NEFT', 'e-mail' as 1 word
    - Standalone punctuation characters: ignored
    - Markdown syntax: stripped beforehand (NOT-05)
    """
    cleaned = strip_markdown(text)
    
    # Split on whitespace
    raw_tokens = cleaned.split()
    words = 0
    for tok in raw_tokens:
        # Strip trailing punctuation commonly attached to words: .,:;!?"'()[]{}
        core = tok.strip(".,:;!?'\"()[]{}")
        if not core:
            continue
        # If token contains any word/alphanumeric or currency character, count it
        if re.search(r"[\w₹$€£★]", core):
            words += 1
            
    return words
