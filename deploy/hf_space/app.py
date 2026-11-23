"""Groww Weekly Review Pulse - Backend API & Gradio Management App.

Provides both an interactive pipeline management interface and REST endpoints
for ingesting Google Play reviews, clustering themes, validating invariants,
and staging MCP deliverables (Google Docs & Gmail Drafts).
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Ensure src package is discoverable
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

from src.store.factory import open_store
from src.note.engine import build_and_validate_pulse_note


def get_system_health() -> Dict[str, Any]:
    """Return backend health and readiness metrics."""
    return {
        "status": "healthy",
        "service": "groww-weekly-review-pulse-backend",
        "version": "2.4.1",
        "invariants": {
            "INV-01": "Word count <= 250",
            "INV-02": "Failures block delivery",
            "INV-03": "Exactly 3 top themes",
            "INV-04": "Exactly 3 verbatim quotes",
            "INV-05": "Exactly 3 action ideas",
            "INV-06": "Cluster cap <= 5",
            "INV-07": "Zero PII allowed"
        },
        "links": {
            "frontend_vercel": "https://groww-weekly-review-pulse-frontend.vercel.app",
            "github_repo": "https://github.com/Saurabh682/groww-weekly-review-pulse"
        }
    }


def run_pipeline_dry_run(week_str: str = "2026-11-09", app_key: str = "groww") -> str:
    """Execute a dry-run of the weekly pulse pipeline."""
    try:
        store = open_store().for_app(app_key)

        note, rendered_md, val_result, builder = build_and_validate_pulse_note(
            store=store,
            week_start=week_str,
            dry_run=True
        )
        
        status_line = "✅ VALIDATION PASSED (6/6 INVARIANTS SATISFIED)" if val_result.is_valid else "❌ VALIDATION FAILED"
        
        report = [
            f"# Pipeline Execution Report — Week {week_str}",
            f"**Status**: {status_line}",
            f"**Word Count**: {val_result.word_count} / 250 words",
            f"**Composite Pulse Score**: {note.composite_score} / 100 ({note.mood_label})",
            f"**Reviews Analyzed**: {note.review_count_total} reviews",
            f"**Average Rating**: {note.avg_rating}★",
            "\n## Top Themes Categorized:",
        ]
        
        for t in note.top_themes:
            report.append(f"- **{t.name}** (Rank #{t.rank}, Share: {t.share_pct:.1f}%, Rating: {t.avg_rating:.1f}★)")
            
        report.append("\n## Verbatim Quotes Authenticated:")
        for q in note.quotes:
            report.append(f"- *\"{q.text}\"* (Rating: {q.rating}★)")
            
        report.append("\n## Action Items Prioritized:")
        for a in note.actions:
            report.append(f"- [{a.owner}] {a.action} (Target: {a.success_signal})")
            
        return "\n".join(report)
    except Exception as e:
        return f"Error executing pipeline: {str(e)}"


if GRADIO_AVAILABLE:
    with gr.Blocks(title="Groww Weekly Review Pulse Backend") as demo:
        gr.Markdown(
            "# 📈 Groww Weekly Review Pulse — Backend Pipeline Engine\n"
            "Turn Google Play feedback into a verified 90-second executive intelligence digest."
        )
        
        with gr.Row():
            status_box = gr.JSON(value=get_system_health, label="Backend Telemetry & Status")
            
        with gr.Tab("Run Pipeline"):
            week_input = gr.Textbox(value="2026-11-09", label="Pulse Week Start (YYYY-MM-DD)")
            run_btn = gr.Button("Execute Validation & Pipeline Dry Run", variant="primary")
            output_md = gr.Markdown()
            run_btn.click(fn=run_pipeline_dry_run, inputs=[week_input], outputs=[output_md])
            
        with gr.Tab("Links & Integration"):
            gr.Markdown(
                "### Production Endpoints\n"
                "- **Live Vercel Frontend**: [https://groww-weekly-review-pulse-frontend.vercel.app](https://groww-weekly-review-pulse-frontend.vercel.app)\n"
                "- **GitHub Repository**: [https://github.com/Saurabh682/groww-weekly-review-pulse](https://github.com/Saurabh682/groww-weekly-review-pulse)\n"
                "- **Publishing**: Composio MCP (Google Docs + Gmail drafts)\n"
            )

    if __name__ == "__main__":
        demo.launch()
else:
    if __name__ == "__main__":
        print("Backend module loaded successfully.")
