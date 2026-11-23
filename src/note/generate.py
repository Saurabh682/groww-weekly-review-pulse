"""Content synthesis for theme one-liners and grounded action items (Phase 3: NOT-*).

Generates:
- Theme one-liners (<= 22 words each, NOT-12)
- Exactly 3 grounded action items tied to top themes (<= 30 words each, NOT-06, NOT-07, NOT-08)
- Deterministic budget enforcement (NOT-11)
"""

import os
from typing import Dict, List, Optional
from src.domains.pack import DomainPack
from src.note.models import ActionItem, Quote, ThemeSummary
from src.note.words import count_note_words
from src.store.models import ThemeRecord


def synthesize_theme_one_liner(theme: ThemeRecord, pack: DomainPack) -> str:
    """Generate a concise one-liner for a theme (<= 22 words, NOT-12)."""
    lbl = theme.label.lower()
    one_liner = next(
        (rule.text for rule in pack.one_liners if any(trigger in lbl for trigger in rule.label_triggers)),
        "",
    )
    is_positive = "positive" in lbl or "simplicity" in lbl or "ux" in lbl or theme.avg_rating >= 3.8
    if not one_liner and is_positive and pack.positive_one_liner:
        one_liner = pack.positive_one_liner
    if not one_liner:
        pct = theme.share_pct * 100 if theme.share_pct <= 1.0 else theme.share_pct
        one_liner = f"{theme.label} accounts for {pct:.1f}% of reviews with an average rating of {theme.avg_rating:.1f}★."

    # Enforce hard <= 22 words bound
    words = one_liner.split()
    if len(words) > 22:
        one_liner = " ".join(words[:22])
        if not one_liner.endswith("."):
            one_liner += "."
            
    return one_liner


def synthesize_action_items(top_themes: List[ThemeRecord], pack: DomainPack) -> List[ActionItem]:
    """Generate exactly 3 grounded action items tied to top themes (NOT-06, NOT-07, NOT-08)."""
    actions: List[ActionItem] = []
    
    for theme in top_themes[:3]:
        # Match domain action blueprint or generate specific action
        matched = None
        for key, blueprint in pack.actions.items():
            if key.lower() in theme.label.lower() or theme.label.lower() in key.lower():
                matched = (blueprint.owner, blueprint.text)
                break
                
        if matched:
            owner, action_text = matched
        else:
            owner = "Engineering Team"
            if theme.avg_rating <= 2.5:
                action_text = f"Audit {theme.label.lower()} workflows and deploy targeted reliability patches for high-frequency user failure modes."
            else:
                action_text = f"Analyze positive feedback on {theme.label.lower()} to reinforce design standards across other product modules."

        # Enforce <= 30 words bound
        words = action_text.split()
        if len(words) > 30:
            action_text = " ".join(words[:30])
            if not action_text.endswith("."):
                action_text += "."

        actions.append(ActionItem(
            theme_label=theme.label,
            text=action_text,
            owner_team=owner
        ))
        
    return actions[:3]


def enforce_word_budget(rendered_markdown: str, max_words: int = 250) -> str:
    """Trim text deterministically if note slightly exceeds 250 words (NOT-11)."""
    wc = count_note_words(rendered_markdown)
    if wc <= max_words:
        return rendered_markdown

    lines = rendered_markdown.splitlines()
    # Try trimming trailing explanations in lines
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("- ") or lines[i].startswith("1.") or lines[i].startswith("2.") or lines[i].startswith("3."):
            # Cut last sentence from this bullet
            parts = lines[i].split(". ")
            if len(parts) > 1:
                lines[i] = ". ".join(parts[:-1]) + "."
                if count_note_words("\n".join(lines)) <= max_words:
                    return "\n".join(lines)
                    
    # Last resort word-by-word trim
    result_lines = []
    current_count = 0
    for line in lines:
        line_words = count_note_words(line)
        if current_count + line_words <= max_words:
            result_lines.append(line)
            current_count += line_words
        else:
            # Trim line
            words = line.split()
            keep = []
            for w in words:
                if count_note_words(" ".join(keep + [w])) + current_count <= max_words:
                    keep.append(w)
                else:
                    break
            if keep:
                result_lines.append(" ".join(keep) + "...")
            break

    return "\n".join(result_lines)
