"""Content synthesis for theme one-liners and grounded action items (Phase 3: NOT-*).

Generates:
- Theme one-liners (<= 22 words each, NOT-12)
- Exactly 3 grounded action items tied to top themes (<= 30 words each, NOT-06, NOT-07, NOT-08)
- Deterministic budget enforcement (NOT-11)
"""

import os
from typing import Dict, List, Optional
from src.note.models import ActionItem, Quote, ThemeSummary
from src.note.words import count_note_words
from src.store.models import ThemeRecord


# Domain action blueprints for Groww operational areas
DOMAIN_ACTIONS = {
    "Charges & Pricing": (
        "Core Brokerage Team",
        "Deploy in-app fee breakdown calculator and display itemized DP charges on order confirmation screens."
    ),
    "App Performance & Bugs": (
        "Mobile Reliability Team",
        "Conduct load testing on morning market-open websocket channels and patch chart rendering memory leaks."
    ),
    "Customer Support": (
        "Customer Operations",
        "Implement priority escalation routing for unresolved payment tickets older than 48 hours."
    ),
    "Onboarding & KYC": (
        "Identity Verification Team",
        "Extend video KYC session timeout to 15 minutes and integrate automated DigiLocker retry webhooks."
    ),
    "Payments & Withdrawals": (
        "Banking Integrations Team",
        "Implement real-time UPI transaction reconciliation with partner bank gateways to prevent debit/credit lag."
    ),
    "Trading & Order Execution": (
        "Order Engine Team",
        "Optimize stop-loss order trigger latency during high market volatility at 9:15 AM opening."
    ),
    "Positive UX & Simplicity": (
        "Product Design Team",
        "Maintain current simplified mutual fund dashboard layout while streamlining advanced equity analytics."
    )
}


def synthesize_theme_one_liner(theme: ThemeRecord, sample_quote: Optional[Quote] = None) -> str:
    """Generate a concise one-liner for a theme (<= 22 words, NOT-12)."""
    lbl = theme.label.lower()
    if "charge" in lbl or "pricing" in lbl or "fee" in lbl:
        one_liner = "Users report unexpected charges and request transparent fee breakdowns on equity and DP deductions."
    elif "bug" in lbl or "performance" in lbl or "lag" in lbl:
        one_liner = "Frequent app lag and freezing reported during peak trading hours, impacting order execution."
    elif "support" in lbl or "service" in lbl or "help" in lbl:
        one_liner = "Customer service tickets experience delayed response times and automated bot reply loops."
    elif "kyc" in lbl or "verification" in lbl or "onboard" in lbl:
        one_liner = "Delays in bank account verification and repeated video KYC link expiries during onboarding."
    elif "payment" in lbl or "transfer" in lbl or "wallet" in lbl or "deposit" in lbl or "withdraw" in lbl:
        one_liner = "UPI transfers debited from banks fail to reflect in Groww wallet immediately during market hours."
    elif "positive" in lbl or "simplicity" in lbl or "ux" in lbl or theme.avg_rating >= 3.8:
        one_liner = "Users praise intuitive navigation, clean interface design, and straightforward mutual fund investing."
    else:
        pct = theme.share_pct * 100 if theme.share_pct <= 1.0 else theme.share_pct
        one_liner = f"{theme.label} accounts for {pct:.1f}% of reviews with an average rating of {theme.avg_rating:.1f}★."

    # Enforce hard <= 22 words bound
    words = one_liner.split()
    if len(words) > 22:
        one_liner = " ".join(words[:22])
        if not one_liner.endswith("."):
            one_liner += "."
            
    return one_liner


def synthesize_action_items(top_themes: List[ThemeRecord]) -> List[ActionItem]:
    """Generate exactly 3 grounded action items tied to top themes (NOT-06, NOT-07, NOT-08)."""
    actions: List[ActionItem] = []
    
    for theme in top_themes[:3]:
        # Match domain action blueprint or generate specific action
        matched = None
        for key, (owner, action_text) in DOMAIN_ACTIONS.items():
            if key.lower() in theme.label.lower() or theme.label.lower() in key.lower():
                matched = (owner, action_text)
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
