# Documentation Index & Registry

This folder (`docs/`) is the central repository for all project documentation, specifications, architectural decisions, and tracking logs for the **Groww Weekly Review Pulse** project. All future markdown documents will be maintained here and updated as milestones are achieved.

---

## Document Registry

| Document | Description | Status |
| :--- | :--- | :--- |
| [groww-weekly-review-pulse-problem.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/groww-weekly-review-pulse-problem.md) | Original problem statement, requirements, constraints, and rubric | Active / Baseline |
| [architecture.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/architecture.md) | System architecture, pipeline stages, MCP integration, data flow | Active / Baseline |
| [implementation-plan.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/implementation-plan.md) | Step-by-step development roadmap and phase-wise tasks | Active / Baseline |
| [edge-case.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/edge-case.md) | Comprehensive edge cases, corner scenarios, and test catalogue (P0/P1/P2) | Active / Baseline |
| [data-source-decision.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/data-source-decision.md) | Data source decision, Play Store import contract & identity exclusion rules | Active / Baseline |
| [tooling-selection.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/tooling-selection.md) | Tooling, model selection, local embeddings, and privacy agreements | Active / Baseline |
| [mcp-server-problem-statement.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/mcp-server-problem-statement.md) | Problem statement & specification for the Gmail + Google Docs MCP server | Active / Baseline |
| [eval.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/eval.md) | Evaluation metrics, automated checks (word count ≤ 250, verbatim quotes, PII gate) | Planned |

---

## Current Decisions & Scope Adjustments

* **Data Ingestion Focus (ADR-8)**: The pipeline focuses strictly on **Google Play Store** reviews for now. Apple App Store ingestion is deferred to simplify the initial ingestion pipeline and verification.
* **MCP Server Location**: The Gmail + Google Docs MCP server is developed in a dedicated subproject folder at [`groww-weekly-review-pulse/gmail-docs-mcp/`](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/gmail-docs-mcp/README.md) with its own [`docs/`](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/gmail-docs-mcp/docs/README.md).

---

## Maintenance Guidelines

1. **Location**: All project-related documentation, design notes, plans, and evaluation records must live inside this `docs/` folder.
2. **Registry Updates**: Whenever a new `.md` file is added or its status changes, update this registry table with its description and status.
3. **Change Tracking**: Keep existing documents in sync with code and pipeline changes as the project evolves.
