"""Quote extraction and selection engine for Groww Weekly Review Pulse (QUO-*).

Picks exactly 3 verbatim quotes from 3 distinct reviews matching the top 3 themes.
Enforces 6-22 word sentence bounds, PII avoidance, profanity/competitor filtering,
and exact substring preservation (the LLM never writes or rewrites quote text).
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from src.note.models import Quote
from src.note.words import count_note_words
from src.store.models import ReviewRecord, ThemeRecord


# Regex protecting abbreviations and decimals from premature sentence splitting (QUO-08)
ABBREVIATIONS = r"\b(?:Rs|e\.g|i\.e|approx|vs|no|dr|mr|mrs|prof)\."
DECIMAL_PATTERN = r"\b\d+\.\d+\b"

PROFANITY_WORDS = {
    "fraud", "scam", "thief", "chor", "cheat", "scammers",
    "court", "police", "fir", "lawsuit", "sue", "illegal"
}

COMPETITOR_NAMES = {
    "zerodha", "kite", "upstox", "angel one", "angelone", "dhan", "paytm money", "5paisa"
}

SPECIFICITY_KEYWORDS = {
    "kyc", "upi", "withdrawal", "wallet", "ticket", "brokerage", "charges", "rupees", "rs",
    "hours", "days", "minutes", "monday", "friday", "pending", "deducted", "credited",
    "mandate", "sip", "digilocker", "demat", "dp", "amc", "stop loss", "verification"
}


def split_sentences(text: str) -> List[str]:
    """Split text into sentences while respecting abbreviations and numeric decimals (QUO-08)."""
    # Temporarily mask decimals and safe periods
    masked = text
    masked = re.sub(r"(\b(?:Rs|e\.g|i\.e|approx|vs|no)\.)", lambda m: m.group(1).replace(".", "§DOT§"), masked, flags=re.IGNORECASE)
    masked = re.sub(r"(\b\d+)\.(\d+\b)", r"\1§DOT§\2", masked)
    
    # Split on sentence terminals: . ! ? or newlines
    raw_sentences = re.split(r"[.!?\n]+", masked)
    
    sentences: List[str] = []
    for s in raw_sentences:
        restored = s.replace("§DOT§", ".").strip()
        if restored:
            sentences.append(restored)
            
    return sentences


def is_candidate_eligible(sentence: str) -> bool:
    """Check if candidate sentence meets length, safety, and content criteria (QUO-07, 09, 10, 12)."""
    wc = count_note_words(sentence)
    if wc < 6 or wc > 22:
        return False
        
    if "[REDACTED]" in sentence:
        return False
        
    s_lower = sentence.lower()
    
    # Profanity / extreme legal claims filter (QUO-09, QUO-10)
    words = set(re.findall(r"\b\w+\b", s_lower))
    if words.intersection(PROFANITY_WORDS):
        return False
        
    # Competitor filter (QUO-10)
    for comp in COMPETITOR_NAMES:
        if comp in s_lower:
            return False
            
    return True


def compute_sentence_score(sentence: str, rating: int, theme_is_negative: bool) -> float:
    """Score candidate sentence by specificity and tone match."""
    score = 1.0
    s_lower = sentence.lower()
    
    # Reward presence of concrete operational tokens
    words = set(re.findall(r"\b\w+\b", s_lower))
    overlap = len(words.intersection(SPECIFICITY_KEYWORDS))
    score += overlap * 0.5
    
    # Reward numbers / quantities (e.g. "4 days", "24 hours", "₹500")
    if re.search(r"\b\d+\b|[₹$]", sentence):
        score += 0.8
        
    # Tone alignment
    if theme_is_negative and rating <= 2:
        score += 1.0
    elif not theme_is_negative and rating >= 4:
        score += 1.0
        
    return score


def extract_verbatim_quote(full_text: str, candidate: str) -> str:
    """Return the exact span from full_text to guarantee verbatim reproduction (QUO-01, QUO-03)."""
    # Look for exact candidate substring
    pos = full_text.find(candidate)
    if pos != -1:
        return full_text[pos:pos + len(candidate)]
    
    # Fallback: whitespace normalized search
    cand_norm = " ".join(candidate.split())
    tokens = cand_norm.split()
    if tokens:
        first, last = tokens[0], tokens[-1]
        pattern = re.escape(first) + r".*?" + re.escape(last)
        m = re.search(pattern, full_text, flags=re.DOTALL)
        if m:
            return m.group(0).strip()
            
    return candidate.strip()


def select_quotes_for_themes(
    top_themes: List[ThemeRecord],
    theme_reviews: Dict[str, List[ReviewRecord]],
    max_quotes: int = 3
) -> List[Quote]:
    """Select 3 verbatim quotes from 3 distinct reviews matching top themes (QUO-01..16)."""
    selected_quotes: List[Quote] = []
    used_review_ids: Set[str] = set()
    
    # Map theme candidates: theme_id -> list of (score, candidate_span, review)
    theme_candidates: Dict[str, List[Tuple[float, str, ReviewRecord]]] = {}
    
    for theme in top_themes:
        candidates: List[Tuple[float, str, ReviewRecord]] = []
        is_neg = theme.avg_rating <= 3.0
        
        for rev in theme_reviews.get(theme.theme_id, []):
            if rev.low_info or not rev.quote_eligible or rev.lang != "en":
                continue
                
            for sent in split_sentences(rev.text):
                if is_candidate_eligible(sent):
                    verbatim_span = extract_verbatim_quote(rev.text, sent)
                    # Double check word bounds on the exact verbatim span
                    if 6 <= count_note_words(verbatim_span) <= 22:
                        sc = compute_sentence_score(verbatim_span, rev.rating, is_neg)
                        candidates.append((sc, verbatim_span, rev))
                        
        # Sort best score first
        candidates.sort(key=lambda x: x[0], reverse=True)
        theme_candidates[theme.theme_id] = candidates

    # Pass 1: Try to select 1 top quote from each top theme
    for theme in top_themes[:max_quotes]:
        for sc, sent, rev in theme_candidates.get(theme.theme_id, []):
            if rev.review_id not in used_review_ids:
                selected_quotes.append(Quote(
                    text=sent,
                    source_review_id=rev.review_id,
                    rating=rev.rating,
                    theme_label=theme.label,
                    date=rev.date
                ))
                used_review_ids.add(rev.review_id)
                break

    # Pass 2: If any theme lacked an eligible quote, fill from remaining top candidates (QUO-04)
    if len(selected_quotes) < max_quotes:
        all_remaining: List[Tuple[float, str, ReviewRecord, str]] = []
        for theme in top_themes:
            for sc, sent, rev in theme_candidates.get(theme.theme_id, []):
                if rev.review_id not in used_review_ids:
                    all_remaining.append((sc, sent, rev, theme.label))
                    
        all_remaining.sort(key=lambda x: x[0], reverse=True)
        for sc, sent, rev, label in all_remaining:
            if len(selected_quotes) >= max_quotes:
                break
            if rev.review_id not in used_review_ids:
                selected_quotes.append(Quote(
                    text=sent,
                    source_review_id=rev.review_id,
                    rating=rev.rating,
                    theme_label=label,
                    date=rev.date
                ))
                used_review_ids.add(rev.review_id)

    return selected_quotes[:max_quotes]
