"""Rendering templates for Groww Weekly Review Pulse notes (Phase 3: NOT-14..17, MCP-19..21).

Produces:
- Deterministic Markdown output (<= 250 words total)
- Clean HTML for Gmail draft body
- Plain-text fallback for environments without HTML
"""

import html
from typing import Optional
from src.note.models import WeeklyPulseNote
from src.note.words import count_note_words


def render_markdown(note: WeeklyPulseNote) -> str:
    """Render WeeklyPulseNote into clean, compliant Markdown."""
    sections = []
    
    # Title
    sections.append(f"# Groww Weekly Review Pulse: Week of {note.week_start}")
    
    # Metadata / Scope line (NOT-14)
    meta = f"Google Play reviews ({note.window_start} to {note.window_end}) • Total: {note.total_reviews} • Analyzed: {note.analyzed_reviews} • Avg Rating: {note.avg_rating:.1f}★"
    sections.append(meta)
    
    # Short coverage caveat if applicable (NOT-16)
    if note.short_coverage_flag:
        sections.append(f"*Notice: Available reviews span {note.coverage_weeks:.1f} weeks (target: 8–12 weeks).*")

    # Top Themes
    sections.append("## Top Themes")
    for idx, t in enumerate(note.top_themes, 1):
        pct = t.share_pct * 100 if t.share_pct <= 1.0 else t.share_pct
        sections.append(f"**{idx}. {t.label}** ({pct:.1f}% share, {t.avg_rating:.1f}★)\n{t.one_liner}")

    # Customer Voice (Verbatim Quotes)
    sections.append("## Customer Voice")
    for q in note.quotes:
        # Escape markdown backticks and asterisks within quote
        safe_q = q.text.replace("`", "'").replace("*", "")
        sections.append(f"> \"{safe_q}\"\n> — {q.rating}★ review ({q.date}) • {q.theme_label}")

    # Recommended Actions
    sections.append("## Recommended Actions")
    for idx, act in enumerate(note.actions, 1):
        owner_str = f" *(Owner: {act.owner_team})*" if act.owner_team else ""
        sections.append(f"{idx}. **[{act.theme_label}]** {act.text}{owner_str}")

    return "\n\n".join(sections)


def render_html(note: WeeklyPulseNote) -> str:
    """Render WeeklyPulseNote into clean HTML for email body (MCP-20)."""
    h_title = html.escape(f"Groww Weekly Review Pulse: Week of {note.week_start}")
    h_meta = html.escape(f"Google Play reviews ({note.window_start} to {note.window_end}) • Analyzed: {note.analyzed_reviews} • Rating: {note.avg_rating:.1f}★")
    
    items_themes = "".join(
        f"<li><strong>{html.escape(t.label)}</strong> ({(t.share_pct * 100 if t.share_pct <= 1.0 else t.share_pct):.1f}% share, {t.avg_rating:.1f}★)<br>{html.escape(t.one_liner)}</li>"
        for t in note.top_themes
    )
    
    items_quotes = "".join(
        f"<blockquote style='border-left: 3px solid #00d09c; padding-left: 10px; margin: 8px 0; color: #333;'>"
        f"&ldquo;{html.escape(q.text)}&rdquo;<br>"
        f"<small style='color: #666;'>— {q.rating}★ review ({html.escape(q.date)}) • {html.escape(q.theme_label)}</small>"
        f"</blockquote>"
        for q in note.quotes
    )
    
    items_actions = "".join(
        f"<li><strong>[{html.escape(act.theme_label)}]</strong> {html.escape(act.text)}"
        f"{f' <em>(Owner: {html.escape(act.owner_team)})</em>' if act.owner_team else ''}</li>"
        for act in note.actions
    )

    body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 680px; margin: 0 auto; line-height: 1.5; color: #1a1a1a;">
  <h2 style="color: #00d09c; margin-bottom: 4px;">{h_title}</h2>
  <p style="color: #666; font-size: 14px; margin-top: 0;">{h_meta}</p>
  
  <h3 style="border-bottom: 1px solid #eee; padding-bottom: 4px;">Top Themes</h3>
  <ol style="padding-left: 20px;">{items_themes}</ol>
  
  <h3 style="border-bottom: 1px solid #eee; padding-bottom: 4px;">Customer Voice</h3>
  <div>{items_quotes}</div>
  
  <h3 style="border-bottom: 1px solid #eee; padding-bottom: 4px;">Recommended Actions</h3>
  <ol style="padding-left: 20px;">{items_actions}</ol>
</div>"""
    return body


def render_plain_text(note: WeeklyPulseNote) -> str:
    """Render clean plain text fallback without markdown syntax (MCP-20)."""
    lines = [
        f"Groww Weekly Review Pulse: Week of {note.week_start}",
        f"Google Play reviews ({note.window_start} to {note.window_end}) | Total: {note.total_reviews} | Rating: {note.avg_rating:.1f}★",
        "",
        "TOP THEMES:"
    ]
    for idx, t in enumerate(note.top_themes, 1):
        pct = t.share_pct * 100 if t.share_pct <= 1.0 else t.share_pct
        lines.append(f"{idx}. {t.label} ({pct:.1f}% share, {t.avg_rating:.1f}★): {t.one_liner}")
        
    lines.extend(["", "CUSTOMER VOICE:"])
    for q in note.quotes:
        lines.append(f"- \"{q.text}\" ({q.rating}★, {q.date}, {q.theme_label})")
        
    lines.extend(["", "RECOMMENDED ACTIONS:"])
    for idx, act in enumerate(note.actions, 1):
        owner = f" [Owner: {act.owner_team}]" if act.owner_team else ""
        lines.append(f"{idx}. [{act.theme_label}] {act.text}{owner}")
        
    return "\n".join(lines)
