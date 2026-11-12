"""Validator for Groww Weekly Review Pulse notes (Phase 3: VAL-*, NOT-*, QUO-*).

Enforces hard invariants:
- Word count <= 250
- Exactly 3 top themes, 3 verbatim quotes, 3 actions
- Total themes <= 5
- Distinct source reviews for quotes
- Verbatim substring matches for quotes (no paraphrasing)
- No PII tokens in quotes or rendered note
- Action grounding in top-3 themes
- Play Store scope (no App Store references)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.clean.pii import scrub_pii
from src.note.models import WeeklyPulseNote
from src.note.words import count_note_words
from src.store.models import ReviewRecord


@dataclass
class ValidationResult:
    """Outcome of running validation checks on a pulse note."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    word_count: int = 0
    checks_passed: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.is_valid:
            return f"VALID: Note passed all {len(self.checks_passed)} checks ({self.word_count} words)."
        return f"INVALID: {len(self.errors)} failure(s) detected ({self.word_count} words):\n- " + "\n- ".join(self.errors)


def is_verbatim_substring(quote_text: str, source_text: str) -> bool:
    """Check if quote_text is an exact normalized substring of source_text (QUO-01, QUO-11)."""
    # Normalize internal spaces
    q_norm = " ".join(quote_text.strip().split())
    s_norm = " ".join(source_text.strip().split())
    return q_norm in s_norm


def validate_note(
    note: WeeklyPulseNote,
    rendered_text: str,
    source_reviews: Optional[Dict[str, ReviewRecord]] = None
) -> ValidationResult:
    """Execute all blocking validation checks on the note and rendered text.
    Fails closed if any check fails or if an unexpected exception occurs (VAL-01, VAL-02).
    """
    errors: List[str] = []
    checks_passed: List[str] = []
    
    try:
        # 1. Shared Word Count Check (NOT-02, NOT-03, VAL-07)
        wc = count_note_words(rendered_text)
        if wc > 250:
            errors.append(f"NOT-03: Word count exceeds 250-word cap (got {wc} words).")
        else:
            checks_passed.append("word_count_cap")

        # 2. Theme Count Invariants (CFG-01, NOT-01)
        if len(note.top_themes) > 5:
            errors.append(f"CFG-01: Total top themes exceeds hard cap of 5 (got {len(note.top_themes)}).")
        elif len(note.top_themes) != 3 and not note.policy_allows_fewer:
            errors.append(f"NOT-01: Exactly 3 top themes required (got {len(note.top_themes)}).")
        else:
            checks_passed.append("theme_count")

        # Theme labels uniqueness
        theme_labels = [t.label for t in note.top_themes]
        if len(set(theme_labels)) != len(theme_labels):
            errors.append("THM-20: Top theme labels must be unique.")
        else:
            checks_passed.append("theme_labels_unique")

        # Theme one-liner length (NOT-12)
        for t in note.top_themes:
            one_liner_words = count_note_words(t.one_liner)
            if one_liner_words > 22:
                errors.append(f"NOT-12: Theme '{t.label}' one-liner exceeds 22 words ({one_liner_words} words).")

        # 3. Quotes Invariants (CFG-03, QUO-01..16)
        if len(note.quotes) != 3:
            errors.append(f"CFG-03: Exactly 3 quotes required (got {len(note.quotes)}).")
        else:
            checks_passed.append("quotes_count")

        # Distinct source reviews (QUO-05)
        source_ids = [q.source_review_id for q in note.quotes]
        if len(set(source_ids)) != len(source_ids):
            errors.append(f"QUO-05: Quotes must originate from 3 distinct reviews (got {len(set(source_ids))} distinct IDs).")
        else:
            checks_passed.append("quotes_distinct_reviews")

        # Quote properties and verbatim checks
        for idx, q in enumerate(note.quotes, 1):
            q_words = count_note_words(q.text)
            if q_words < 6 or q_words > 22:
                errors.append(f"QUO-07: Quote #{idx} length must be between 6 and 22 words (got {q_words} words).")
            
            if "[REDACTED]" in q.text:
                errors.append(f"QUO-12: Quote #{idx} contains [REDACTED] tokens.")

            if source_reviews:
                if q.source_review_id not in source_reviews:
                    errors.append(f"QUO-16: Quote #{idx} source review '{q.source_review_id}' not found in review dataset.")
                else:
                    src_rec = source_reviews[q.source_review_id]
                    if not is_verbatim_substring(q.text, src_rec.text):
                        errors.append(f"QUO-01: Quote #{idx} is not a verbatim substring of source review {q.source_review_id}.")
                    else:
                        checks_passed.append(f"quote_{idx}_verbatim")

            if q.theme_label not in theme_labels and not note.policy_allows_fewer:
                errors.append(f"QUO-15: Quote #{idx} theme '{q.theme_label}' does not match any top-3 theme.")

        # 4. Action Items Invariants (CFG-03, NOT-06, NOT-07, NOT-08)
        if len(note.actions) != 3:
            errors.append(f"NOT-06: Exactly 3 action items required (got {len(note.actions)}).")
        else:
            checks_passed.append("actions_count")

        for idx, act in enumerate(note.actions, 1):
            if act.theme_label not in theme_labels and not note.policy_allows_fewer:
                errors.append(f"NOT-07: Action #{idx} references theme '{act.theme_label}' which is not in top-3 themes.")
            
            act_words = count_note_words(act.text)
            if act_words > 30:
                errors.append(f"NOT-06: Action #{idx} exceeds 30 words ({act_words} words).")
            elif act_words < 4:
                errors.append(f"NOT-08: Action #{idx} is too short or generic ({act_words} words).")
            
            # Check generic phrase traps (NOT-08)
            generic_traps = ["improve the app", "fix bugs", "make it better", "general improvements"]
            if any(trap in act.text.lower() for trap in generic_traps):
                errors.append(f"NOT-08: Action #{idx} contains generic non-actionable phrase '{act.text}'.")

        # 5. Scope & Platform Invariant (NOT-14)
        if "App Store" in rendered_text or "iOS" in rendered_text:
            errors.append("NOT-14: Note contains prohibited references to 'App Store' or 'iOS' (Google Play only scope).")
        elif "Google Play" not in rendered_text:
            errors.append("NOT-14: Note must explicitly state source as 'Google Play'.")
        else:
            checks_passed.append("google_play_scope")

        # 6. Overall PII Scan (PII-30, NOT-18, INV-04)
        scrub_res = scrub_pii(rendered_text)
        if scrub_res.pii_found:
            errors.append(f"INV-04: PII detected in rendered note ({scrub_res.redaction_count} occurrences).")
        else:
            checks_passed.append("pii_free_rendered_note")

    except Exception as exc:
        # VAL-02: Treated as fail
        errors.append(f"VAL-02: Validator crashed with internal error: {str(exc)}")

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        word_count=count_note_words(rendered_text),
        checks_passed=checks_passed
    )
