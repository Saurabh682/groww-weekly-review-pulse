"""Walking skeleton for Groww Weekly Review Pulse (Phase 0 Task 0.8).

Proves the end-to-end flow with synthetic/throwaway data:
1. Loads pulse config and MCP capability map.
2. Formats a one-page note respecting the <=250 words, 3 themes, 3 quotes, 3 actions constraints.
3. Invokes MCP client (or dry_run mock contract) to stage a Google Doc and Gmail draft.
4. Generates a local markdown fallback in outputs/<week>/note.md.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.config import load_pulse_config, PulseConfig, get_project_root, resolve_project_path
from src.mcp.capabilities import load_mcp_config, resolve_capability, MCPConfigData


def count_words(markdown_text: str) -> int:
    """Calculate word count per definition in architecture §8.3:
    Whitespace-separated tokens after stripping markdown syntax markers.
    """
    # Remove markdown headings, bold, italic, list markers
    cleaned = re.sub(r"[#*_>`\-]", " ", markdown_text)
    # Strip markdown link URLs, keep link text
    cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned)
    tokens = cleaned.split()
    return len(tokens)


def build_skeleton_note(week_str: str) -> str:
    """Construct a compliant one-page pulse note under 250 words with 3 themes, 3 quotes, and 3 actions."""
    note = f"""# Groww Weekly Review Pulse | Week of {week_str}
Window: 12 weeks | Reviews analyzed: 210 | Avg rating: 3.4★

## Top 3 Themes
1. **Payments & UPI** (38% of reviews, avg 2.1★): Pending wallet credits and UPI timeouts during peak market hours.
2. **Account Opening & KYC** (27% of reviews, avg 2.5★): Document verification delays and stuck video KYC links.
3. **App Performance** (19% of reviews, avg 2.8★): Market opening chart lag and biometric login failures.

## What Users Said
- "Money debited from bank account via UPI but not credited to Groww wallet."
- "KYC process is stuck since 4 days. Customer support is not responding to tickets."
- "App crashed right at 9:15 AM market opening. Could not place stop loss."

## Action Ideas
1. **Payments:** Add real-time bank status banner and auto-reconciliation retry within 15 minutes. (Owner: Payments Eng)
2. **KYC:** Instrument Digilocker retry telemetry and alert users on document blur before submission. (Owner: Onboarding PM)
3. **App Performance:** Optimize socket reconnect throttling between 9:10 and 9:25 AM. (Owner: Mobile Infra)
"""
    return note.strip()


class SkeletonMCPRunner:
    """Mock/Dry-run MCP executor for testing tool contracts without direct Google dependencies."""

    def __init__(self, mcp_config: MCPConfigData):
        self.mcp_config = mcp_config

    def create_doc(self, title: str, content: str) -> Dict[str, Any]:
        target = resolve_capability(self.mcp_config, "docs.create")
        return {
            "status": "success",
            "server": target.server,
            "tool": target.tool,
            "doc_id": "doc_skeleton_mock_12345",
            "doc_url": "https://docs.google.com/document/d/doc_skeleton_mock_12345/edit",
            "title": title,
            "characters": len(content),
        }

    def create_draft(self, to: str, subject: str, body: str, doc_url: str) -> Dict[str, Any]:
        target = resolve_capability(self.mcp_config, "gmail.create_draft")
        full_body = f"{body}\n\n---\nGoogle Doc: {doc_url}"
        return {
            "status": "success",
            "server": target.server,
            "tool": target.tool,
            "draft_id": "draft_skeleton_mock_67890",
            "to": to,
            "subject": subject,
            "body_length": len(full_body),
            "is_sent": False, # Guarantees draft is never sent
        }


def run_skeleton(
    config_path: Path | str = "config/pulse.yaml",
    week_str: str = "2026-11-10",
    output_base: Path | str = "outputs"
) -> Dict[str, Any]:
    """Execute the Phase 0 walking skeleton run."""
    pulse_cfg = load_pulse_config(config_path)
    mcp_cfg = load_mcp_config(pulse_cfg.mcp.config)

    note_text = build_skeleton_note(week_str)
    word_count = count_words(note_text)

    # Validate constraints
    if word_count > pulse_cfg.note.max_words:
        raise ValueError(
            f"Skeleton note exceeds max_words constraint: {word_count} > {pulse_cfg.note.max_words}"
        )

    # Run MCP tools via contract adapter
    runner = SkeletonMCPRunner(mcp_cfg)
    doc_res = runner.create_doc(
        title=f"Groww Weekly Review Pulse: Week of {week_str}",
        content=note_text
    )
    draft_res = runner.create_draft(
        to=pulse_cfg.email.to,
        subject=f"Groww Weekly Review Pulse | Week of {week_str}",
        body=note_text,
        doc_url=doc_res["doc_url"]
    )

    # Write local fallback and report
    base_dir = Path(output_base)
    if not base_dir.is_absolute():
        base_dir = get_project_root() / base_dir
    week_output_dir = base_dir / week_str
    week_output_dir.mkdir(parents=True, exist_ok=True)

    note_file = week_output_dir / "note.md"
    note_file.write_text(note_text, encoding="utf-8")

    report = {
        "run_id": f"run_{week_str}_skeleton",
        "week": week_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "word_count": word_count,
        "max_words_allowed": pulse_cfg.note.max_words,
        "themes_count": 3,
        "quotes_count": 3,
        "actions_count": 3,
        "doc_result": doc_res,
        "draft_result": draft_res,
        "local_fallback": str(note_file),
    }

    report_file = week_output_dir / "run_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = run_skeleton()
    print("Skeleton run succeeded:")
    print(json.dumps(report, indent=2))
